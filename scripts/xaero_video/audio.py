"""Yunxi intro narration and time-aligned subtitles.

The source demo is intentionally absent from this module: its original voice is
carried by the source video and is never mixed with the intro narration.
"""

from pathlib import Path
import re
import shutil
import subprocess
import time

from scripts.xaero_video.storyboard import INTRO_SEGMENTS, Segment, intro_seconds


FFMPEG = "/usr/bin/ffmpeg"
VOICE = "zh-CN-YunxiNeural"
SRT_TIME = re.compile(r"(\d+):(\d{2}):(\d{2}),(\d{3})")
PUNCTUATION = "，。！？；：、,.!?;:"


def locate_edge_tts(build_dir: Path) -> Path:
    candidates = [build_dir / ".venv/bin/edge-tts", Path("build/modmenu-video/.venv/bin/edge-tts")]
    system = shutil.which("edge-tts")
    if system:
        candidates.append(Path(system))
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise RuntimeError("Missing edge-tts; expected build/modmenu-video/.venv/bin/edge-tts")


def parse_time(value: str) -> float:
    match = SRT_TIME.fullmatch(value.strip())
    if not match:
        raise ValueError(f"Invalid SRT timestamp: {value}")
    h, m, s, ms = (int(part) for part in match.groups())
    return h * 3600 + m * 60 + s + ms / 1000


def fmt_time(value: float) -> str:
    millis = round(value * 1000)
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    seconds, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def parse_srt(path: Path, offset: float = 0.0) -> list[tuple[float, float, str]]:
    text = path.read_text(encoding="utf-8")
    rows = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = block.splitlines()
        timing = next((line for line in lines if "-->" in line), None)
        if timing is None:
            continue
        start_text, end_text = re.split(r"\s*-->\s*", timing, maxsplit=1)
        index = lines.index(timing)
        caption = " ".join(line.strip() for line in lines[index + 1:] if line.strip())
        if caption:
            rows.append((parse_time(start_text) + offset, parse_time(end_text) + offset, caption))
    return rows


def wrap_caption(text: str, width: int = 24) -> str:
    if len(text) <= width:
        return text
    target = len(text) / 2
    candidates = [i for i in range(max(1, len(text) - width), min(width, len(text) - 1) + 1) if text[i - 1] in PUNCTUATION]
    split = min(candidates, key=lambda i: abs(i - target)) if candidates else int(target)
    return text[:split].strip() + "\n" + text[split:].strip()


def write_srt(rows: list[tuple[float, float, str]], path: Path) -> None:
    normalized: list[tuple[float, float, str]] = []
    previous_end = 0.0
    for start, end, text in sorted(rows, key=lambda row: (row[0], row[1])):
        start = max(start, previous_end)
        if end <= start:
            continue
        normalized.append((start, end, text))
        previous_end = end
    blocks = []
    for index, (start, end, text) in enumerate(normalized, 1):
        blocks.append(f"{index}\n{fmt_time(start)} --> {fmt_time(end)}\n{wrap_caption(text)}")
    path.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")


def generate_voice(build_dir: Path, edge_tts: Path) -> tuple[Path, ...]:
    narration = build_dir / "narration"
    raw = narration / "raw"
    narration.mkdir(parents=True, exist_ok=True)
    raw.mkdir(parents=True, exist_ok=True)
    all_cues: list[tuple[float, float, str]] = []
    media = []
    cursor = 0.0
    for segment in INTRO_SEGMENTS:
        mp3 = narration / f"{segment.id}.mp3"
        raw_srt = raw / f"{segment.id}.srt"
        command = [
            str(edge_tts), "--voice", VOICE, f"--rate={segment.rate}",
            f"--pitch={segment.pitch}", "--text", segment.narration or "",
            "--write-media", str(mp3), "--write-subtitles", str(raw_srt),
        ]
        for attempt in range(6):
            try:
                subprocess.run(command, check=True, capture_output=True, text=True)
                break
            except subprocess.CalledProcessError:
                if attempt == 5:
                    raise
                time.sleep(min(2 * (attempt + 1), 8))
        all_cues.extend(parse_srt(raw_srt, cursor))
        media.append(mp3)
        cursor += segment.seconds
    subtitle = build_dir / "subtitles/xaero.zh-CN.srt"
    subtitle.parent.mkdir(parents=True, exist_ok=True)
    write_srt(all_cues, subtitle)
    narration_master = build_dir / "xaero-narration.mp3"
    command = [FFMPEG, "-y"]
    for path in media:
        command.extend(["-i", str(path)])
    labels = "".join(f"[{i}:a]" for i in range(len(media)))
    command.extend([
        "-filter_complex", f"{labels}concat=n={len(media)}:v=0:a=1[a]",
        "-map", "[a]", "-c:a", "libmp3lame", "-b:a", "192k", str(narration_master),
    ])
    subprocess.run(command, check=True, capture_output=True)
    preview = build_dir / "voice-preview.mp3"
    preview_inputs = media[:3]
    command = [FFMPEG, "-y"]
    for path in preview_inputs:
        command.extend(["-i", str(path)])
    labels = "".join(f"[{i}:a]" for i in range(len(preview_inputs)))
    command.extend([
        "-filter_complex", f"{labels}concat=n={len(preview_inputs)}:v=0:a=1[a]",
        "-map", "[a]", "-c:a", "libmp3lame", "-b:a", "192k", str(preview),
    ])
    subprocess.run(command, check=True, capture_output=True)
    return (*media, subtitle, narration_master, preview)
