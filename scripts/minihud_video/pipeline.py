import argparse
import json
from pathlib import Path
import subprocess
from urllib.parse import urlencode

from scripts.minihud_video.audio import generate_voice
from scripts.minihud_video.storyboard import render_requests


ROOT = Path(__file__).resolve().parents[2]
DECK_PATH = ROOT / "source/extra/MOD介绍/minihud/index.html"
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("slides", "voice"))
    args = parser.parse_args()
    if args.command == "slides":
        outputs = render_slides()
    else:
        outputs = render_voice()
    for path in outputs:
        print(path)


if __name__ == "__main__":
    main()
