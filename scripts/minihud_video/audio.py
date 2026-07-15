from dataclasses import dataclass
from pathlib import Path
import re
import subprocess

from scripts.minihud_video.storyboard import (
    SEGMENTS,
    TRANSITION_SECONDS,
    timeline,
)


VOICES = ("zh-CN-YunyangNeural", "zh-CN-YunjianNeural")
RATE = "-4%"
PITCH = "-4Hz"


@dataclass(frozen=True)
class Cue:
    start: float
    end: float
    text: str


def parse_srt_time(value: str) -> float:
    hours, minutes, rest = value.split(":")
    seconds, millis = rest.split(",")
    return (
        int(hours) * 3600
        + int(minutes) * 60
        + int(seconds)
        + int(millis) / 1000
    )


def format_srt_time(value: float) -> str:
    millis = round(value * 1000)
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    seconds, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def parse_srt(source: str) -> list[Cue]:
    cues = []
    for block in re.split(r"\n\s*\n", source.strip()):
        lines = block.splitlines()
        timing_index = next(
            i for i, line in enumerate(lines) if " --> " in line
        )
        start, end = lines[timing_index].split(" --> ")
        text = " ".join(lines[timing_index + 1 :]).strip()
        cues.append(Cue(parse_srt_time(start), parse_srt_time(end), text))
    return cues


def wrap_caption(text: str, width: int = 18) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= width:
        return compact
    split = min(width, max(1, len(compact) // 2))
    punctuation = "，。！？；：、 "
    candidates = [
        i
        for i in range(max(1, split - 5), min(len(compact), split + 6))
        if compact[i - 1] in punctuation
    ]
    if candidates:
        split = min(
            candidates,
            key=lambda item: abs(item - len(compact) / 2),
        )
    return compact[:split].rstrip() + "\n" + compact[split:].lstrip()


def split_cue(cue: Cue, width: int = 18) -> list[Cue]:
    compact = re.sub(r"\s+", " ", cue.text).strip()
    chunk_size = width * 2
    chunks = [
        compact[index : index + chunk_size]
        for index in range(0, len(compact), chunk_size)
    ]
    part_duration = (cue.end - cue.start) / len(chunks)
    return [
        Cue(
            cue.start + index * part_duration,
            cue.start + (index + 1) * part_duration,
            wrap_caption(chunk, width),
        )
        for index, chunk in enumerate(chunks)
    ]


def merge_cues(groups: list[list[Cue]], starts: list[float]) -> list[Cue]:
    merged = []
    for cues, offset in zip(groups, starts, strict=True):
        for cue in cues:
            shifted = Cue(
                cue.start + offset,
                cue.end + offset,
                cue.text,
            )
            merged.extend(split_cue(shifted))
    return merged


def cues_to_srt(cues: list[Cue]) -> str:
    blocks = []
    for index, cue in enumerate(cues, 1):
        blocks.append(
            f"{index}\n"
            f"{format_srt_time(cue.start)} --> {format_srt_time(cue.end)}\n"
            f"{cue.text}"
        )
    return "\n\n".join(blocks) + "\n"


def probe_duration(path: Path, ffprobe: str = "/usr/bin/ffprobe") -> float:
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def choose_voice(edge_tts: Path) -> str:
    result = subprocess.run(
        [str(edge_tts), "--list-voices"],
        check=True,
        capture_output=True,
        text=True,
    )
    for voice in VOICES:
        if voice in result.stdout:
            return voice
    raise RuntimeError("Neither approved Chinese male voice is available")


def generate_voice(build_dir: Path, edge_tts: Path) -> tuple[Path, ...]:
    narration_dir = build_dir / "narration"
    subtitle_dir = build_dir / "subtitles"
    narration_dir.mkdir(parents=True, exist_ok=True)
    subtitle_dir.mkdir(parents=True, exist_ok=True)
    voice = choose_voice(edge_tts)
    segment_srts = []
    outputs = []
    for segment in SEGMENTS:
        media = narration_dir / f"{segment.id}.mp3"
        srt = narration_dir / f"{segment.id}.srt"
        subprocess.run(
            [
                str(edge_tts),
                "--voice",
                voice,
                f"--rate={RATE}",
                f"--pitch={PITCH}",
                "--text",
                segment.narration,
                "--write-media",
                str(media),
                "--write-subtitles",
                str(srt),
            ],
            check=True,
        )
        duration = probe_duration(media)
        allowed = (
            segment.seconds
            if segment is SEGMENTS[-1]
            else segment.seconds - TRANSITION_SECONDS
        )
        if duration > allowed:
            raise RuntimeError(
                f"Narration {segment.id} is {duration:.2f}s, "
                f"longer than {allowed:.2f}s"
            )
        outputs.append(media)
        segment_srts.append(parse_srt(srt.read_text(encoding="utf-8")))
    starts = [item.start for item in timeline()]
    merged = merge_cues(segment_srts, starts)
    merged_path = subtitle_dir / "minihud-bilibili.zh-CN.srt"
    merged_path.write_text(cues_to_srt(merged), encoding="utf-8")
    return tuple(outputs)
