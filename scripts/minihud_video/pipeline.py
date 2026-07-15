import argparse
import json
from pathlib import Path
import subprocess
from urllib.parse import urlencode

from scripts.minihud_video.audio import generate_voice
from scripts.minihud_video.publishing import build_publish_markdown
from scripts.minihud_video.storyboard import render_requests
from scripts.minihud_video.video import (
    burn_subtitles,
    compose_master,
    create_contact_sheet,
    render_segments,
)


ROOT = Path(__file__).resolve().parents[2]
DECK_PATH = ROOT / "source/extra/MOD介绍/minihud/index.html"
COVER_PATH = ROOT / "scripts/minihud_video/cover.html"
BUILD_DIR = ROOT / "build/minihud-video"
CHROME = "/usr/bin/google-chrome"
FFPROBE = "/usr/bin/ffprobe"
EDGE_TTS = BUILD_DIR / ".venv/bin/edge-tts"


def build_slide_url(slide: int, state: str) -> str:
    query = urlencode({"export": 1, "slide": slide, "state": state})
    return f"{DECK_PATH.resolve().as_uri()}?{query}"


def slide_path(segment_id: str) -> Path:
    return BUILD_DIR / "slides" / f"{segment_id}.png"


def probe_video(path: Path) -> dict:
    result = subprocess.run(
        [
            FFPROBE,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)["streams"][0]


def render_slides() -> tuple[Path, ...]:
    (BUILD_DIR / "slides").mkdir(parents=True, exist_ok=True)
    outputs = []
    for request in render_requests():
        output = slide_path(str(request["id"]))
        subprocess.run(
            [
                CHROME,
                "--headless",
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--hide-scrollbars",
                "--run-all-compositor-stages-before-draw",
                "--virtual-time-budget=1200",
                "--window-size=1920,1080",
                f"--screenshot={output}",
                build_slide_url(
                    int(request["slide"]),
                    str(request["state"]),
                ),
            ],
            check=True,
        )
        dimensions = probe_video(output)
        if (dimensions["width"], dimensions["height"]) != (1920, 1080):
            raise RuntimeError(
                f"Unexpected slide size for {output}: {dimensions}"
            )
        outputs.append(output)
    return tuple(outputs)


def render_voice() -> tuple[Path, ...]:
    if not EDGE_TTS.is_file():
        raise RuntimeError(
            "Missing edge-tts environment. Create build/minihud-video/.venv "
            "and install edge-tts==7.2.8"
        )
    return generate_voice(BUILD_DIR, EDGE_TTS)


def render_video() -> tuple[Path, Path, Path]:
    render_segments(BUILD_DIR)
    clean = compose_master(BUILD_DIR)
    captioned = burn_subtitles(BUILD_DIR, clean)
    contact = create_contact_sheet(BUILD_DIR)
    return clean, captioned, contact


def render_cover() -> tuple[Path, Path]:
    """Render the HTML cover to the PNG and JPG delivery assets."""

    png = BUILD_DIR / "minihud-cover-1600x1000.png"
    jpg = BUILD_DIR / "minihud-cover-1600x1000.jpg"
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            CHROME,
            "--headless",
            "--no-sandbox",
            "--disable-gpu",
            "--hide-scrollbars",
            "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=1000",
            "--window-size=1600,1000",
            f"--screenshot={png}",
            COVER_PATH.resolve().as_uri(),
        ],
        check=True,
    )
    subprocess.run(
        ["/usr/bin/ffmpeg", "-y", "-i", str(png), "-q:v", "2", str(jpg)],
        check=True,
    )
    return png, jpg


def write_publish_guide() -> Path:
    """Write the generated Bilibili metadata beside the rendered media."""

    output = BUILD_DIR / "bilibili-publish.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_publish_markdown(), encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=("slides", "voice", "video", "cover", "publish", "all"),
    )
    args = parser.parse_args()
    actions = {
        "slides": render_slides,
        "voice": render_voice,
        "video": render_video,
        "cover": render_cover,
        "publish": write_publish_guide,
    }
    if args.command == "all":
        for name in ("slides", "voice", "video", "cover", "publish"):
            result = actions[name]()
            print(name, result)
        return

    result = actions[args.command]()
    if isinstance(result, tuple):
        for path in result:
            print(path)
    else:
        print(result)


if __name__ == "__main__":
    main()
