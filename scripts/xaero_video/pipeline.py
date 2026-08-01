"""Build the Xaero Bilibili delivery package."""

import argparse
import json
from pathlib import Path
import subprocess

from scripts.xaero_video.audio import generate_voice, locate_edge_tts
from scripts.xaero_video.publishing import (
    TAGS, TITLE, build_publish_markdown, chapter_lines, description_text,
)
from scripts.xaero_video.storyboard import INTRO_SEGMENTS, SOURCE_VIDEO, all_segments, clock, intro_seconds
from scripts.xaero_video.video import (
    burn_subtitles, compose_master, create_contact_sheet, measure_loudness,
    probe, render_segments, render_slides,
)


ROOT = Path(__file__).resolve().parents[2]
DECK = ROOT / "source/extra/MOD介绍/xaero/index.html"
SOURCE = ROOT / SOURCE_VIDEO
BUILD = ROOT / "build/xaero-video"
COVER = ROOT / "scripts/xaero_video/cover-4x3.html"
SKILL_VERIFY = Path("/home/zhaojd5/.codex/skills/make-bilibili-video/scripts/verify_delivery.py")


def source_duration() -> float:
    return float(probe(SOURCE)["format"]["duration"])


def render_cover() -> tuple[Path, Path]:
    BUILD.mkdir(parents=True, exist_ok=True)
    raw = BUILD / "cover-raw.png"
    png = BUILD / "xaero-cover-1600x1200.png"
    jpg = BUILD / "xaero-cover-1600x1200.jpg"
    subprocess.run([
        "/usr/bin/google-chrome", "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
        "--allow-file-access-from-files", "--force-device-scale-factor=1", "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=1200", "--window-size=1600,1287", f"--screenshot={raw}", COVER.resolve().as_uri(),
    ], check=True, timeout=30, capture_output=True)
    subprocess.run([
        "/usr/bin/ffmpeg", "-y", "-i", str(raw), "-vf", "crop=1600:1200:0:0", "-frames:v", "1", "-update", "1", str(png),
    ], check=True, capture_output=True)
    subprocess.run([
        "/usr/bin/ffmpeg", "-y", "-i", str(png), "-frames:v", "1", "-update", "1", "-q:v", "2", str(jpg),
    ], check=True, capture_output=True)
    raw.unlink(missing_ok=True)
    return png, jpg


def write_publish() -> tuple[Path, ...]:
    outputs = {
        BUILD / "bilibili-publish.md": build_publish_markdown(),
        BUILD / "bilibili-title.txt": TITLE + "\n",
        BUILD / "bilibili-description.txt": description_text() + "\n",
        BUILD / "bilibili-tags.txt": "、".join(TAGS) + "\n",
        BUILD / "chapters.txt": "\n".join(chapter_lines()) + "\n",
        BUILD / "source-voice-note.txt": "实机段使用用户提供视频的原始讲解音轨；前导段使用 zh-CN-YunxiNeural。实机段未叠加第二条配音。\n",
    }
    for path, text in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return tuple(outputs)


def stream(media: dict, codec_type: str) -> dict:
    return next(item for item in media["streams"] if item.get("codec_type") == codec_type)


def verify() -> dict[str, object]:
    duration = source_duration()
    expected = intro_seconds() + duration
    required = (
        BUILD / "xaero-bilibili-clean.mp4", BUILD / "xaero-bilibili.mp4",
        BUILD / "xaero-narration.mp3", BUILD / "voice-preview.mp3",
        BUILD / "subtitles/xaero.zh-CN.srt", BUILD / "xaero-cover-1600x1200.png",
        BUILD / "xaero-cover-1600x1200.jpg", BUILD / "chapters.txt",
        BUILD / "bilibili-publish.md", BUILD / "final-contact.png",
    )
    missing = [str(path) for path in required if not path.is_file() or path.stat().st_size == 0]
    if missing:
        raise RuntimeError("Missing delivery files: " + ", ".join(missing))
    results: dict[str, object] = {
        "source_video": str(SOURCE),
        "source_duration": duration,
        "source_audio_policy": "original voice retained in the complete source segment; no intro narration mixed over it",
        "intro_duration": intro_seconds(),
    }
    for label, path in (("clean", BUILD / "xaero-bilibili-clean.mp4"), ("release", BUILD / "xaero-bilibili.mp4")):
        media = probe(path)
        video, audio = stream(media, "video"), stream(media, "audio")
        actual = float(media["format"]["duration"])
        if (
            video.get("codec_name") != "h264" or (video.get("width"), video.get("height")) != (1920, 1080)
            or video.get("r_frame_rate") != "30/1" or video.get("pix_fmt") != "yuv420p"
            or audio.get("codec_name") != "aac" or audio.get("sample_rate") != "48000"
            or abs(actual - expected) > 1.0
        ):
            raise RuntimeError(f"Invalid {label} media: duration={actual}, video={video}, audio={audio}")
        results[label] = {"duration": actual, "video": video.get("codec_name"), "audio": audio.get("codec_name"), "size": "1920x1080", "fps": video.get("r_frame_rate")}
    loudness = measure_loudness(BUILD / "xaero-bilibili.mp4")
    results["loudness"] = {"integrated_lufs": float(loudness["input_i"]), "true_peak_dbtp": float(loudness["input_tp"])}
    generic = subprocess.run([
        "python3", str(SKILL_VERIFY), "--video", str(BUILD / "xaero-bilibili.mp4"),
        "--subtitle", str(BUILD / "subtitles/xaero.zh-CN.srt"),
        "--cover", str(BUILD / "xaero-cover-1600x1200.png"),
        "--chapters", str(BUILD / "chapters.txt"), "--publish", str(BUILD / "bilibili-publish.md"),
    ], check=True, capture_output=True, text=True)
    results["skill_validation"] = json.loads(generic.stdout)
    (BUILD / "build-report.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return results


def build_all() -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    duration = source_duration()
    print("[slides]")
    render_slides(BUILD, DECK)
    print("[voice]")
    generate_voice(BUILD, locate_edge_tts(BUILD))
    print("[segments]")
    render_segments(BUILD, SOURCE, duration)
    print("[video]")
    clean = compose_master(BUILD, duration)
    burn_subtitles(BUILD, clean)
    create_contact_sheet(BUILD, intro_seconds() + duration)
    print("[cover]")
    render_cover()
    print("[publish]")
    write_publish()
    print("[verify]")
    print(json.dumps(verify(), ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("slides", "voice", "video", "cover", "publish", "verify", "all"))
    args = parser.parse_args()
    duration = source_duration()
    if args.command == "slides":
        print(render_slides(BUILD, DECK))
    elif args.command == "voice":
        print(generate_voice(BUILD, locate_edge_tts(BUILD)))
    elif args.command == "video":
        render_segments(BUILD, SOURCE, duration); clean = compose_master(BUILD, duration); burn_subtitles(BUILD, clean); print(create_contact_sheet(BUILD, intro_seconds() + duration))
    elif args.command == "cover":
        print(render_cover())
    elif args.command == "publish":
        print(write_publish())
    elif args.command == "verify":
        print(json.dumps(verify(), ensure_ascii=False, indent=2))
    else:
        build_all()


if __name__ == "__main__":
    main()
