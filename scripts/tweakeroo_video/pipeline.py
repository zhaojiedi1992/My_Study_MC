"""CLI orchestration for the Tweakeroo Bilibili build."""

import json
from pathlib import Path
import shutil
import subprocess
from urllib.parse import urlencode

from scripts.tweakeroo_video.publishing import build_publish_markdown
from scripts.tweakeroo_video.storyboard import render_requests


ROOT = Path(__file__).resolve().parents[2]
DECK_PATH = ROOT / "source/MOD介绍/tweakeroo/index.html"
BUILD_DIR = ROOT / "build/tweakeroo-video"
CHROME = "/usr/bin/google-chrome"
FFPROBE = "/usr/bin/ffprobe"
FFMPEG = "/usr/bin/ffmpeg"
COVER_PATH = ROOT / "scripts/tweakeroo_video/cover.html"
COVER_4X3_PATH = ROOT / "scripts/tweakeroo_video/cover-4x3.html"


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


def render_cover_source(
    source: Path,
    width: int,
    height: int,
    stem: str,
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
                "--run-all-compositor-stages-before-draw",
                "--virtual-time-budget=1000",
                f"--window-size={width},{height + 87}",
                f"--screenshot={raw}",
                source.resolve().as_uri(),
            ],
            check=True,
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
        )
    finally:
        raw.unlink(missing_ok=True)
    return png, jpg


def render_cover() -> tuple[Path, ...]:
    wide = render_cover_source(
        COVER_PATH,
        1600,
        1000,
        "tweakeroo-cover-1600x1000",
    )
    standard = render_cover_source(
        COVER_4X3_PATH,
        1600,
        1200,
        "tweakeroo-cover-1600x1200",
    )
    return (*wide, *standard)


def write_publish_guide() -> Path:
    output = BUILD_DIR / "bilibili-publish.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_publish_markdown(), encoding="utf-8")
    return output
