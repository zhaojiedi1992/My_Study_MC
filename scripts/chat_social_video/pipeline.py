"""Command line builder for the chat/social/privacy Bilibili delivery."""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
from urllib.parse import urlencode

from scripts.chat_social_video.audio import generate_voice, generate_voice_preview
from scripts.chat_social_video.publishing import build_publish_markdown
from scripts.chat_social_video.storyboard import encoded_seconds, render_requests
from scripts.chat_social_video.storyboard import SEGMENTS
from scripts.chat_social_video.video import (
    burn_subtitles,
    compose_master,
    create_contact_sheet,
    measure_loudness,
    render_segments,
)


ROOT = Path(__file__).resolve().parents[2]
DECK_PATH = ROOT / "source/extra/MOD介绍/聊天社交与隐私/index.html"
BUILD_DIR = ROOT / "build/chat-social-video"
CHROME = "/usr/bin/google-chrome"
FFPROBE = "/usr/bin/ffprobe"
FFMPEG = "/usr/bin/ffmpeg"
COVER_PATH = ROOT / "scripts/chat_social_video/cover.html"
COVER_4X3_PATH = ROOT / "scripts/chat_social_video/cover-4x3.html"
CAPTURE_SCRIPT = ROOT / "scripts/chat_social_video/capture_fullscreen.cjs"


def build_slide_url(slide: int, state: str) -> str:
    query = urlencode({"export": 1, "slide": slide, "state": state})
    return f"{DECK_PATH.resolve().as_uri()}?{query}"


def slide_path(segment_id: str) -> Path:
    return BUILD_DIR / "slides" / f"{segment_id}.png"


def probe_media(path: Path) -> dict:
    result = subprocess.run(
        [
            FFPROBE,
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
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
    ]
    system = shutil.which("edge-tts")
    if system:
        candidates.append(Path(system))
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise RuntimeError(
        "Missing edge-tts; install edge-tts==7.2.8 in build/chat-social-video/.venv"
    )


def render_slides() -> tuple[Path, ...]:
    output_dir = BUILD_DIR / "slides"
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for request in render_requests():
        output = slide_path(str(request["id"]))
        command = [
            CHROME,
            "--headless",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--hide-scrollbars",
            "--allow-file-access-from-files",
            "--force-device-scale-factor=1",
            "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=1200",
            "--window-size=1920,1080",
            f"--screenshot={output}",
            build_slide_url(int(request["slide"]), str(request["state"])),
        ]
        subprocess.run(command, check=True, timeout=30, capture_output=True)
        stream = probe_media(output)["streams"][0]
        if (stream.get("width"), stream.get("height")) != (1920, 1080):
            raise RuntimeError(f"Unexpected slide size for {output}: {stream}")
        outputs.append(output)
    return tuple(outputs)


def render_cover_source(
    source: Path, width: int, height: int, stem: str
) -> tuple[Path, Path]:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    raw = BUILD_DIR / f"{stem}-raw.png"
    png = BUILD_DIR / f"{stem}.png"
    jpg = BUILD_DIR / f"{stem}.jpg"
    try:
        subprocess.run(
            [
                CHROME,
                "--headless",
                "--no-sandbox",
                "--disable-gpu",
                "--hide-scrollbars",
                "--allow-file-access-from-files",
                "--force-device-scale-factor=1",
                "--run-all-compositor-stages-before-draw",
                "--virtual-time-budget=1000",
                # This Chrome build reserves 87 px for window chrome even in
                # headless mode; add it so the captured CSS viewport is exact.
                f"--window-size={width},{height + 87}",
                f"--screenshot={raw}",
                source.resolve().as_uri(),
            ],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                FFMPEG,
                "-y",
                "-i",
                str(raw),
                "-vf",
                f"crop={width}:{height}:0:0",
                "-frames:v",
                "1",
                "-update",
                "1",
                str(png),
            ],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                FFMPEG,
                "-y",
                "-i",
                str(png),
                "-frames:v",
                "1",
                "-update",
                "1",
                "-q:v",
                "2",
                str(jpg),
            ],
            check=True,
            capture_output=True,
        )
    finally:
        raw.unlink(missing_ok=True)
    return png, jpg


def render_cover() -> tuple[Path, ...]:
    wide = render_cover_source(COVER_PATH, 1600, 1000, "chat-social-cover-1600x1000")
    standard = render_cover_source(
        COVER_4X3_PATH, 1600, 1200, "chat-social-cover-1600x1200"
    )
    return (*wide, *standard)


def write_publish_guide() -> Path:
    output = BUILD_DIR / "bilibili-publish.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_publish_markdown(), encoding="utf-8")
    return output


def render_video() -> tuple[Path, Path, Path]:
    capture_emote_fullscreen()
    render_segments(BUILD_DIR)
    clean = compose_master(BUILD_DIR)
    release = burn_subtitles(BUILD_DIR, clean)
    contact = create_contact_sheet(BUILD_DIR)
    return clean, release, contact


def capture_emote_fullscreen() -> Path:
    output = BUILD_DIR / "emote-fullscreen.mp4"
    emote = next(segment for segment in SEGMENTS if segment.id == "emote")
    subprocess.run(
        [
            "xvfb-run", "-a", "--server-args=-screen 0 1920x1080x24",
            "node", str(CAPTURE_SCRIPT), build_slide_url(5, "default"),
            str(output), str(emote.seconds),
        ],
        check=True,
        timeout=emote.seconds + 45,
    )
    return output


def _stream(media: dict, codec_type: str) -> dict:
    return next(
        stream for stream in media["streams"] if stream.get("codec_type") == codec_type
    )


def verify_delivery() -> dict[str, object]:
    required = (
        BUILD_DIR / "chat-social-bilibili-clean.mp4",
        BUILD_DIR / "chat-social-bilibili.mp4",
        BUILD_DIR / "voice-preview.mp3",
        BUILD_DIR / "chat-social-narration.mp3",
        BUILD_DIR / "subtitles/chat-social.zh-CN.srt",
        BUILD_DIR / "chat-social-cover-1600x1000.png",
        BUILD_DIR / "chat-social-cover-1600x1000.jpg",
        BUILD_DIR / "chat-social-cover-1600x1200.png",
        BUILD_DIR / "chat-social-cover-1600x1200.jpg",
        BUILD_DIR / "bilibili-publish.md",
        BUILD_DIR / "final-contact.png",
    )
    missing = [path for path in required if not path.is_file() or path.stat().st_size == 0]
    if missing:
        raise RuntimeError("Missing delivery files: " + ", ".join(map(str, missing)))

    results: dict[str, object] = {}
    for label, path in (
        ("clean", BUILD_DIR / "chat-social-bilibili-clean.mp4"),
        ("release", BUILD_DIR / "chat-social-bilibili.mp4"),
    ):
        media = probe_media(path)
        video = _stream(media, "video")
        audio = _stream(media, "audio")
        duration = float(media["format"]["duration"])
        if (
            video.get("codec_name") != "h264"
            or (video.get("width"), video.get("height")) != (1920, 1080)
            or video.get("r_frame_rate") != "30/1"
            or audio.get("codec_name") != "aac"
            or abs(duration - encoded_seconds()) > 0.6
        ):
            raise RuntimeError(
                f"Invalid {label} media: video={video}, audio={audio}, duration={duration}"
            )
        results[label] = {
            "duration": duration,
            "video": video.get("codec_name"),
            "audio": audio.get("codec_name"),
            "size": f"{video.get('width')}x{video.get('height')}",
        }

    loudness = measure_loudness(BUILD_DIR / "chat-social-bilibili.mp4")
    integrated = float(loudness["input_i"])
    true_peak = float(loudness["input_tp"])
    if not -17 <= integrated <= -15 or true_peak > -1:
        raise RuntimeError(f"Loudness outside target: I={integrated}, TP={true_peak}")
    results["loudness"] = {
        "integrated_lufs": integrated,
        "true_peak_dbtp": true_peak,
    }

    for image in (
        DECK_PATH.parent / "assets/effects/chatheads-no-mod.png",
        DECK_PATH.parent / "assets/effects/chatheads-with-mod.png",
        DECK_PATH.parent / "assets/effects/nochatreports-no-mod.png",
        DECK_PATH.parent / "assets/effects/nochatreports-with-mod.png",
    ):
        stream = probe_media(image)["streams"][0]
        if stream.get("width", 0) <= 0 or stream.get("height", 0) <= 0:
            raise RuntimeError(f"Unexpected source image size: {image}: {stream}")
    source_stream = _stream(probe_media(
        ROOT / "source/extra/MOD介绍/聊天社交与隐私/assets/emotecraft展示视频.mp4"
    ), "video")
    if (source_stream.get("width"), source_stream.get("height")) != (2880, 1800):
        raise RuntimeError(f"Unexpected Emotecraft source video size: {source_stream}")
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
        choices=(
            "slides",
            "voice-preview",
            "voice",
            "video",
            "cover",
            "publish",
            "verify",
            "all",
        ),
    )
    args = parser.parse_args()
    actions = {
        "slides": render_slides,
        "voice-preview": render_voice_preview,
        "voice": render_voice,
        "video": render_video,
        "cover": render_cover,
        "publish": write_publish_guide,
        "verify": verify_delivery,
    }
    if args.command == "all":
        for name in (
            "slides",
            "voice-preview",
            "voice",
            "video",
            "cover",
            "publish",
            "verify",
        ):
            print(f"[{name}]")
            _print_result(actions[name]())
        return
    _print_result(actions[args.command]())


if __name__ == "__main__":
    main()
