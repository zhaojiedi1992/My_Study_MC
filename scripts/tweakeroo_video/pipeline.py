"""CLI orchestration for the Tweakeroo Bilibili build."""

import json
from pathlib import Path
import shutil
import subprocess
from urllib.parse import urlencode

from scripts.tweakeroo_video.storyboard import render_requests


ROOT = Path(__file__).resolve().parents[2]
DECK_PATH = ROOT / "source/MOD介绍/tweakeroo/index.html"
BUILD_DIR = ROOT / "build/tweakeroo-video"
CHROME = "/usr/bin/google-chrome"
FFPROBE = "/usr/bin/ffprobe"


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
    system_edge_tts = shutil.which("edge-tts")
    candidates = [BUILD_DIR / ".venv/bin/edge-tts"]
    if system_edge_tts:
        candidates.append(Path(system_edge_tts))
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise RuntimeError(
        "Missing edge-tts. Create build/tweakeroo-video/.venv and "
        "install edge-tts==7.2.8"
    )


def render_slides() -> tuple[Path, ...]:
    output_dir = BUILD_DIR / "slides"
    output_dir.mkdir(parents=True, exist_ok=True)
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
        media = probe_media(output)
        stream = media["streams"][0]
        if (stream["width"], stream["height"]) != (1920, 1080):
            raise RuntimeError(
                f"Unexpected slide size for {output}: {stream}"
            )
        outputs.append(output)
    return tuple(outputs)
