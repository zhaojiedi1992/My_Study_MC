"""Command line builder for the InvMove Bilibili delivery."""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
from urllib.parse import urlencode

from scripts.invmove_video.audio import generate_voice, generate_voice_preview
from scripts.invmove_video.publishing import (
    TAGS,
    TITLE,
    build_publish_markdown,
    chapter_lines,
    description_text,
)
from scripts.invmove_video.storyboard import SEGMENTS, encoded_seconds, render_requests
from scripts.invmove_video.video import (
    burn_subtitles,
    compose_master,
    create_contact_sheet,
    measure_loudness,
    render_segments,
)


ROOT = Path(__file__).resolve().parents[2]
DECK_PATH = ROOT / "source/extra/MOD介绍/invmove/index.html"
VIDEO_DIR = DECK_PATH.parent / "videos"
BUILD_DIR = ROOT / "build/invmove-video"
CHROME = "/usr/bin/google-chrome"
FFMPEG = "/usr/bin/ffmpeg"
FFPROBE = "/usr/bin/ffprobe"
COVER_PATH = ROOT / "scripts/invmove_video/cover-4x3.html"
SKILL_VERIFIER = Path(
    "/home/zhaojd5/.codex/skills/make-bilibili-video/scripts/verify_delivery.py"
)
SOURCE_VIDEOS = {
    "blocked": VIDEO_DIR / "打开合成器后，无法移动.mp4",
    "move": VIDEO_DIR / "移动中可以打开背包合成器.mp4",
    "workbench": VIDEO_DIR / "工作台打开后，可以继续移动.mp4",
}


def build_slide_url(slide: int) -> str:
    query = urlencode({"export": 1, "slide": slide})
    return f"{DECK_PATH.resolve().as_uri()}?{query}"


def probe_media(path: Path) -> dict:
    result = subprocess.run(
        [
            FFPROBE, "-v", "error", "-show_streams", "-show_format",
            "-of", "json", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def locate_edge_tts() -> Path:
    candidates = [
        BUILD_DIR / ".venv/bin/edge-tts",
        ROOT / "build/modmenu-video/.venv/bin/edge-tts",
        ROOT / "build/chat-social-video/.venv/bin/edge-tts",
    ]
    system = shutil.which("edge-tts")
    if system:
        candidates.append(Path(system))
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise RuntimeError("Missing edge-tts; install edge-tts==7.2.8")


def render_slides() -> tuple[Path, ...]:
    output_dir = BUILD_DIR / "slides"
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for request in render_requests():
        output = output_dir / f"{request['id']}.png"
        subprocess.run(
            [
                CHROME, "--headless", "--no-sandbox", "--disable-gpu",
                "--disable-dev-shm-usage", "--hide-scrollbars",
                "--allow-file-access-from-files", "--force-device-scale-factor=1",
                "--run-all-compositor-stages-before-draw", "--virtual-time-budget=9000",
                "--window-size=1920,1080", f"--screenshot={output}",
                build_slide_url(int(request["slide"])),
            ],
            check=True,
            timeout=35,
            capture_output=True,
        )
        stream = probe_media(output)["streams"][0]
        if (stream.get("width"), stream.get("height")) != (1920, 1080):
            raise RuntimeError(f"Unexpected slide size for {output}: {stream}")
        outputs.append(output)
    return tuple(outputs)


def capture_demos() -> tuple[Path, ...]:
    output_dir = BUILD_DIR / "demos"
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for segment in SEGMENTS:
        if segment.kind != "demo":
            continue
        output = output_dir / f"{segment.id}.mp4"
        source = SOURCE_VIDEOS[segment.id]
        source_duration = float(probe_media(source)["format"]["duration"])
        tail = max(0.0, segment.seconds - segment.click_delay - source_duration)
        slide = BUILD_DIR / "slides" / f"{segment.id}.png"
        graph = (
            f"[0:v]scale=1920:1080:force_original_aspect_ratio=increase,"
            f"crop=1920:1080,fps=30,settb=AVTB,trim=duration={segment.click_delay},"
            f"setpts=PTS-STARTPTS[slide];"
            "[1:v]scale=1920:1080:force_original_aspect_ratio=decrease,"
            "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black,fps=30,settb=AVTB,"
            "setpts=PTS-STARTPTS[demo];"
            f"[slide][demo]concat=n=2:v=1:a=0,"
            f"tpad=stop_mode=clone:stop_duration={tail:.3f},"
            f"trim=duration={segment.seconds},setpts=PTS-STARTPTS[v]"
        )
        subprocess.run(
            [
                FFMPEG, "-y", "-loop", "1", "-framerate", "30",
                "-t", str(segment.click_delay), "-i", str(slide),
                "-i", str(source), "-filter_complex", graph,
                "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "medium",
                "-crf", "17", "-pix_fmt", "yuv420p", "-r", "30",
                "-movflags", "+faststart", str(output),
            ],
            check=True,
            capture_output=True,
        )
        media = probe_media(output)
        video = next(stream for stream in media["streams"] if stream.get("codec_type") == "video")
        duration = float(media["format"]["duration"])
        if (
            (video.get("width"), video.get("height")) != (1920, 1080)
            or abs(duration - segment.seconds) > 0.15
        ):
            raise RuntimeError(f"Invalid browser demo capture {output}: {media}")
        outputs.append(output)
    return tuple(outputs)


def extract_cover_frame() -> Path:
    output = BUILD_DIR / "cover-game.jpg"
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            FFMPEG, "-y", "-ss", "2.2", "-i", str(SOURCE_VIDEOS["move"]),
            "-frames:v", "1", "-update", "1", "-q:v", "2", str(output),
        ],
        check=True,
        capture_output=True,
    )
    return output


def render_cover() -> tuple[Path, Path]:
    extract_cover_frame()
    raw = BUILD_DIR / "invmove-cover-1600x1200-raw.png"
    png = BUILD_DIR / "invmove-cover-1600x1200.png"
    jpg = BUILD_DIR / "invmove-cover-1600x1200.jpg"
    try:
        subprocess.run(
            [
                CHROME, "--headless", "--no-sandbox", "--disable-gpu",
                "--hide-scrollbars", "--allow-file-access-from-files",
                "--force-device-scale-factor=1", "--run-all-compositor-stages-before-draw",
                "--virtual-time-budget=1200", "--window-size=1600,1287",
                f"--screenshot={raw}", COVER_PATH.resolve().as_uri(),
            ],
            check=True,
            timeout=30,
            capture_output=True,
        )
        subprocess.run(
            [
                FFMPEG, "-y", "-i", str(raw), "-vf", "crop=1600:1200:0:0",
                "-frames:v", "1", "-update", "1", str(png),
            ],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                FFMPEG, "-y", "-i", str(png), "-frames:v", "1",
                "-update", "1", "-q:v", "2", str(jpg),
            ],
            check=True,
            capture_output=True,
        )
    finally:
        raw.unlink(missing_ok=True)
    return png, jpg


def render_video() -> tuple[Path, Path, Path]:
    render_segments(BUILD_DIR)
    clean = compose_master(BUILD_DIR)
    release = burn_subtitles(BUILD_DIR, clean)
    contact = create_contact_sheet(BUILD_DIR, encoded_seconds())
    return clean, release, contact


def write_publish_guide() -> tuple[Path, ...]:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        BUILD_DIR / "bilibili-publish.md": build_publish_markdown(),
        BUILD_DIR / "bilibili-title.txt": TITLE + "\n",
        BUILD_DIR / "bilibili-description.txt": description_text() + "\n",
        BUILD_DIR / "bilibili-tags.txt": "、".join(TAGS) + "\n",
        BUILD_DIR / "chapters.txt": "\n".join(chapter_lines()) + "\n",
    }
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8")
    return tuple(outputs)


def _stream(media: dict, codec_type: str) -> dict:
    return next(stream for stream in media["streams"] if stream.get("codec_type") == codec_type)


def verify_delivery() -> dict[str, object]:
    required = (
        BUILD_DIR / "invmove-bilibili-clean.mp4",
        BUILD_DIR / "invmove-bilibili.mp4",
        BUILD_DIR / "voice-preview.mp3",
        BUILD_DIR / "invmove-narration.mp3",
        BUILD_DIR / "subtitles/invmove.zh-CN.srt",
        BUILD_DIR / "invmove-cover-1600x1200.png",
        BUILD_DIR / "invmove-cover-1600x1200.jpg",
        BUILD_DIR / "bilibili-publish.md",
        BUILD_DIR / "bilibili-title.txt",
        BUILD_DIR / "bilibili-description.txt",
        BUILD_DIR / "bilibili-tags.txt",
        BUILD_DIR / "chapters.txt",
        BUILD_DIR / "final-contact.png",
    )
    missing = [path for path in required if not path.is_file() or path.stat().st_size == 0]
    if missing:
        raise RuntimeError("Missing delivery files: " + ", ".join(map(str, missing)))

    results: dict[str, object] = {
        "source_audio_policy": "source video visuals are used directly; source audio is muted and only Yunxi narration is mixed"
    }
    for label, path in (
        ("clean", BUILD_DIR / "invmove-bilibili-clean.mp4"),
        ("release", BUILD_DIR / "invmove-bilibili.mp4"),
    ):
        media = probe_media(path)
        video = _stream(media, "video")
        audio = _stream(media, "audio")
        duration = float(media["format"]["duration"])
        if (
            video.get("codec_name") != "h264"
            or (video.get("width"), video.get("height")) != (1920, 1080)
            or video.get("r_frame_rate") != "30/1"
            or video.get("pix_fmt") != "yuv420p"
            or audio.get("codec_name") != "aac"
            or audio.get("sample_rate") != "48000"
            or abs(duration - encoded_seconds()) > 0.6
        ):
            raise RuntimeError(f"Invalid {label} media: video={video}, audio={audio}, duration={duration}")
        results[label] = {
            "duration": duration,
            "video": video.get("codec_name"),
            "audio": audio.get("codec_name"),
            "size": f"{video.get('width')}x{video.get('height')}",
            "fps": video.get("r_frame_rate"),
        }

    loudness = measure_loudness(BUILD_DIR / "invmove-bilibili.mp4")
    integrated = float(loudness["input_i"])
    true_peak = float(loudness["input_tp"])
    if not -17 <= integrated <= -15 or true_peak > -1:
        raise RuntimeError(f"Loudness outside target: I={integrated}, TP={true_peak}")
    results["loudness"] = {"integrated_lufs": integrated, "true_peak_dbtp": true_peak}

    for segment in SEGMENTS:
        if segment.kind != "demo":
            continue
        capture = probe_media(BUILD_DIR / "demos" / f"{segment.id}.mp4")
        results[f"demo_{segment.id}"] = {
            "duration": float(capture["format"]["duration"]),
            "source_duration": float(probe_media(SOURCE_VIDEOS[segment.id])["format"]["duration"]),
            "completed": True,
        }

    generic = subprocess.run(
        [
            "python3", str(SKILL_VERIFIER),
            "--video", str(BUILD_DIR / "invmove-bilibili.mp4"),
            "--subtitle", str(BUILD_DIR / "subtitles/invmove.zh-CN.srt"),
            "--cover", str(BUILD_DIR / "invmove-cover-1600x1200.png"),
            "--chapters", str(BUILD_DIR / "chapters.txt"),
            "--publish", str(BUILD_DIR / "bilibili-publish.md"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    results["skill_verifier"] = json.loads(generic.stdout)
    report = BUILD_DIR / "build-report.json"
    report.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return results


def render_voice_preview() -> Path:
    return generate_voice_preview(BUILD_DIR, locate_edge_tts())


def render_voice() -> tuple[Path, ...]:
    return generate_voice(BUILD_DIR, locate_edge_tts())


def _print_result(result: object) -> None:
    if isinstance(result, tuple):
        for path in result:
            print(path)
    elif isinstance(result, dict):
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=("slides", "voice-preview", "voice", "demos", "video", "cover", "publish", "verify", "all"),
    )
    args = parser.parse_args()
    actions = {
        "slides": render_slides,
        "voice-preview": render_voice_preview,
        "voice": render_voice,
        "demos": capture_demos,
        "video": render_video,
        "cover": render_cover,
        "publish": write_publish_guide,
        "verify": verify_delivery,
    }
    if args.command == "all":
        for name in ("slides", "voice-preview", "voice", "demos", "video", "cover", "publish", "verify"):
            print(f"[{name}]")
            _print_result(actions[name]())
        return
    _print_result(actions[args.command]())


if __name__ == "__main__":
    main()
