"""Narration, voice-preview, and subtitle utilities for Tweakeroo."""

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import time

from scripts.tweakeroo_video.storyboard import (
    PREVIEW_SEGMENT_IDS,
    SEGMENTS,
    TRANSITION_SECONDS,
    Segment,
    encoded_seconds,
    timeline,
)


VOICES = (
    "zh-CN-YunxiNeural",
    "zh-CN-YunyangNeural",
    "zh-CN-YunjianNeural",
)
RATE = "-2%"
PITCH = "+0Hz"
CAPTION_WIDTH = 18
MAX_CAPTION_LINES = 2
MAX_TAIL_SILENCE_SECONDS = 1.5
FFMPEG = "/usr/bin/ffmpeg"
FFPROBE = "/usr/bin/ffprobe"

_BOUNDARY_PUNCTUATION = frozenset("，。！？；：、,.!?;:")
_SRT_TIME_PATTERN = re.compile(
    r"(?P<hours>\d+):(?P<minutes>[0-5]\d):"
    r"(?P<seconds>[0-5]\d),(?P<millis>\d{3})"
)
_LATIN_TOKEN_CHARACTER = re.compile(r"[A-Za-z0-9]")


@dataclass(frozen=True)
class Cue:
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class VoicePart:
    text: str
    rate: str
    pitch: str
    pause_ms: int


_DYNAMIC_VOICE_PARTS = {
    "hook-soul": (
        VoicePart("灵魂出窍。", "+6%", "+2Hz", 180),
    ),
    "soul-effect": (
        VoicePart("按下之后，人留在原地。", "+1%", "+1Hz", 140),
        VoicePart(
            "视角出去转一圈。看建筑，查路线，都不用本人跑过去加班。",
            "-1%",
            "+0Hz",
            280,
        ),
        VoicePart("看完，切回来。", "-3%", "-1Hz", 180),
    ),
    "gamma-on": (
        VoicePart(
            "开启后，方块和道路立刻清楚很多。",
            "+1%",
            "+1Hz",
            320,
        ),
        VoicePart("不过，矿洞是亮了。", "-2%", "+0Hz", 220),
        VoicePart(
            "刷怪规则并没有被你说服。该插的火把，还是得插。",
            "-4%",
            "-2Hz",
            160,
        ),
    ),
}


def voice_parts(segment: Segment) -> tuple[VoicePart, ...]:
    return _DYNAMIC_VOICE_PARTS.get(
        segment.id,
        (VoicePart(segment.narration, RATE, PITCH, 0),),
    )


def part_starts(
    durations: list[float],
    parts: tuple[VoicePart, ...],
) -> list[float]:
    if len(durations) != len(parts):
        raise ValueError("Voice-part durations and definitions differ")
    starts = []
    cursor = 0.0
    for duration, part in zip(durations, parts, strict=True):
        if duration <= 0:
            raise ValueError("Voice-part duration must be positive")
        starts.append(round(cursor, 6))
        cursor += duration + part.pause_ms / 1000
    return starts


def parse_srt_time(value: str) -> float:
    match = _SRT_TIME_PATTERN.fullmatch(value.strip())
    if match is None:
        raise ValueError(f"invalid SRT timestamp: {value!r}")
    return (
        int(match.group("hours")) * 3600
        + int(match.group("minutes")) * 60
        + int(match.group("seconds"))
        + int(match.group("millis")) / 1000
    )


def format_srt_time(value: float) -> str:
    millis = round(value * 1000)
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    seconds, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def validate_cues(
    cues: list[Cue],
    label: str = "SRT",
    *,
    max_end: float | None = None,
    allow_overlaps: bool = False,
    width: int | None = None,
) -> None:
    if not cues:
        raise RuntimeError(f"{label} is empty; expected at least one cue")
    previous = None
    for index, cue in enumerate(cues, 1):
        if not cue.text.strip():
            raise RuntimeError(f"{label} cue {index} has empty text")
        if cue.start < 0 or cue.end <= cue.start:
            raise RuntimeError(
                f"{label} cue {index} must have positive duration; "
                f"got {cue.start:.3f}s --> {cue.end:.3f}s"
            )
        if previous is not None:
            if cue.start < previous.start or cue.end < previous.end:
                raise RuntimeError(
                    f"{label} cue {index} is not ordered after cue "
                    f"{index - 1}"
                )
            if not allow_overlaps and cue.start < previous.end:
                raise RuntimeError(
                    f"{label} cues {index - 1} and {index} overlap"
                )
        if max_end is not None and cue.end > max_end + 1e-9:
            raise RuntimeError(
                f"{label} cue {index} ends at {cue.end:.2f}s, beyond "
                f"allowed {max_end:.2f}s"
            )
        if width is not None:
            lines = cue.text.splitlines()
            if len(lines) > MAX_CAPTION_LINES:
                raise RuntimeError(
                    f"{label} cue {index} has too many lines"
                )
            if max(map(len, lines)) > width:
                raise RuntimeError(
                    f"{label} cue {index} exceeds {width} characters"
                )
        previous = cue


def parse_srt(source: str, label: str = "SRT") -> list[Cue]:
    if not source.strip():
        raise RuntimeError(f"{label} is empty; expected subtitle content")
    cues = []
    for block in re.split(r"\n\s*\n", source.strip()):
        lines = block.splitlines()
        timing_indices = [
            index for index, line in enumerate(lines) if "-->" in line
        ]
        cue_number = len(cues) + 1
        if len(timing_indices) != 1:
            raise RuntimeError(
                f"{label} cue {cue_number} is missing a valid timing line"
            )
        timing_index = timing_indices[0]
        timing_parts = re.split(
            r"\s*-->\s*", lines[timing_index].strip()
        )
        if len(timing_parts) != 2:
            raise RuntimeError(f"{label} cue {cue_number} has bad timing")
        text = " ".join(lines[timing_index + 1 :]).strip()
        if not text:
            raise RuntimeError(f"{label} cue {cue_number} has empty text")
        try:
            start = parse_srt_time(timing_parts[0])
            end = parse_srt_time(timing_parts[1])
        except ValueError as error:
            raise RuntimeError(
                f"{label} cue {cue_number} has malformed timing"
            ) from error
        cues.append(Cue(start, end, text))
    validate_cues(cues, label, allow_overlaps=True)
    return cues


def _semantic_boundaries(text: str, lower: int, upper: int) -> list[int]:
    boundaries = []
    for position in range(max(1, lower), min(len(text), upper + 1)):
        before = text[position - 1]
        after = text[position]
        if (
            before in _BOUNDARY_PUNCTUATION
            or before.isspace()
            or after.isspace()
        ):
            boundaries.append(position)
    return boundaries


def _is_latin_token_character(value: str) -> bool:
    return bool(_LATIN_TOKEN_CHARACTER.fullmatch(value))


def _avoid_latin_token_split(
    text: str,
    position: int,
    lower: int,
    upper: int,
) -> int:
    if not (
        0 < position < len(text)
        and _is_latin_token_character(text[position - 1])
        and _is_latin_token_character(text[position])
    ):
        return position
    left = position
    while left > 0 and _is_latin_token_character(text[left - 1]):
        left -= 1
    right = position
    while right < len(text) and _is_latin_token_character(text[right]):
        right += 1
    candidates = [item for item in (left, right) if lower <= item <= upper]
    if not candidates:
        return position
    return min(candidates, key=lambda item: abs(item - position))


def _splits_latin_token(text: str, position: int) -> bool:
    return bool(
        0 < position < len(text)
        and _is_latin_token_character(text[position - 1])
        and _is_latin_token_character(text[position])
    )


def _can_wrap_without_latin_token_split(text: str, width: int) -> bool:
    if len(text) <= width:
        return True
    lower = len(text) - width
    upper = width
    if _semantic_boundaries(text, lower, upper):
        return True
    target = round(len(text) / 2)
    split = _avoid_latin_token_split(text, target, lower, upper)
    return not _splits_latin_token(text, split)


def _caption_chunks(text: str, limit: int) -> list[str]:
    chunks = []
    remaining = text
    width = limit // MAX_CAPTION_LINES
    while len(remaining) > limit:
        boundaries = _semantic_boundaries(remaining, 1, limit)
        split = next(
            (
                candidate
                for candidate in reversed(boundaries)
                if _can_wrap_without_latin_token_split(
                    remaining[:candidate].strip(),
                    width,
                )
            ),
            None,
        )
        if split is None:
            split = _avoid_latin_token_split(remaining, limit, 1, limit)
        chunk = remaining[:split].strip()
        if not chunk:
            raise RuntimeError("Caption cannot be split")
        chunks.append(chunk)
        remaining = remaining[split:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks


def wrap_caption(text: str, width: int = CAPTION_WIDTH) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if not compact:
        raise RuntimeError("Caption text is empty")
    if len(compact) > width * MAX_CAPTION_LINES:
        raise RuntimeError("Caption must be split before wrapping")
    if len(compact) <= width:
        return compact
    lower = len(compact) - width
    upper = width
    target = len(compact) / 2
    candidates = _semantic_boundaries(compact, lower, upper)
    if candidates:
        split = min(
            candidates,
            key=lambda item: (abs(item - target), -item),
        )
    else:
        split = _avoid_latin_token_split(
            compact,
            round(target),
            lower,
            upper,
        )
    wrapped = compact[:split].rstrip() + "\n" + compact[split:].lstrip()
    lines = wrapped.splitlines()
    if len(lines) > MAX_CAPTION_LINES or max(map(len, lines)) > width:
        raise RuntimeError("Caption cannot fit two lines")
    return wrapped


def split_cue(cue: Cue, width: int = CAPTION_WIDTH) -> list[Cue]:
    validate_cues([cue], "Caption source", allow_overlaps=True)
    compact = re.sub(r"\s+", " ", cue.text).strip()
    chunks = _caption_chunks(compact, width * MAX_CAPTION_LINES)
    weights = [len(chunk) for chunk in chunks]
    total_weight = sum(weights)
    total_duration = cue.end - cue.start
    result = []
    cumulative_weight = 0
    for index, (chunk, weight) in enumerate(zip(chunks, weights, strict=True)):
        start = cue.start + total_duration * cumulative_weight / total_weight
        cumulative_weight += weight
        end = (
            cue.end
            if index == len(chunks) - 1
            else cue.start
            + total_duration * cumulative_weight / total_weight
        )
        result.append(Cue(start, end, wrap_caption(chunk, width)))
    validate_cues(result, "Split caption", width=width)
    return result


def normalize_cues(cues: list[Cue], label: str = "SRT") -> list[Cue]:
    validate_cues(cues, label, allow_overlaps=True)
    normalized = list(cues)
    for index in range(len(normalized) - 1):
        current = normalized[index]
        following = normalized[index + 1]
        if current.end > following.start:
            if following.start <= current.start:
                raise RuntimeError(f"{label} overlap cannot be normalized")
            normalized[index] = Cue(
                current.start,
                following.start,
                current.text,
            )
    validate_cues(normalized, label)
    return normalized


def merge_cues(groups: list[list[Cue]], starts: list[float]) -> list[Cue]:
    merged = []
    for group_index, (cues, offset) in enumerate(
        zip(groups, starts, strict=True),
        1,
    ):
        normalized = normalize_cues(cues, f"Subtitle group {group_index}")
        for cue in normalized:
            shifted = Cue(cue.start + offset, cue.end + offset, cue.text)
            merged.extend(split_cue(shifted))
    return normalize_cues(merged, "Merged subtitles")


def cues_to_srt(cues: list[Cue]) -> str:
    blocks = []
    for index, cue in enumerate(cues, 1):
        blocks.append(
            f"{index}\n"
            f"{format_srt_time(cue.start)} --> {format_srt_time(cue.end)}\n"
            f"{cue.text}"
        )
    return "\n\n".join(blocks) + "\n"


def probe_duration(path: Path, ffprobe: str = FFPROBE) -> float:
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
    raise RuntimeError("No approved Chinese male voice is available")


def _generate_tts_part(
    edge_tts: Path,
    voice: str,
    part: VoicePart,
    media: Path,
    srt: Path,
) -> None:
    command = [
        str(edge_tts),
        "--voice",
        voice,
        f"--rate={part.rate}",
        f"--pitch={part.pitch}",
        "--text",
        part.text,
        "--write-media",
        str(media),
        "--write-subtitles",
        str(srt),
    ]
    for attempt in range(3):
        try:
            subprocess.run(command, check=True)
            return
        except subprocess.CalledProcessError:
            if attempt == 2:
                raise
            time.sleep(1)


def compose_voice_parts(
    media_paths: list[Path],
    durations: list[float],
    parts: tuple[VoicePart, ...],
    output: Path,
) -> None:
    if not (len(media_paths) == len(durations) == len(parts)):
        raise ValueError(
            "Voice-part media, durations, and definitions differ"
        )
    command = [FFMPEG, "-y"]
    graph = []
    labels = []
    for index, (media, duration, part) in enumerate(
        zip(media_paths, durations, parts, strict=True)
    ):
        command.extend(["-i", str(media)])
        end = duration + part.pause_ms / 1000
        label = f"part{index}"
        graph.append(
            f"[{index}:a]aresample=24000,"
            f"aformat=channel_layouts=mono,"
            f"apad=pad_dur={part.pause_ms / 1000:.3f},"
            f"atrim=0:{end:.6f}[{label}]"
        )
        labels.append(f"[{label}]")
    graph.append(
        "".join(labels)
        + f"concat=n={len(labels)}:v=0:a=1[voice]"
    )
    command.extend(
        [
            "-filter_complex",
            ";".join(graph),
            "-map",
            "[voice]",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "192k",
            str(output),
        ]
    )
    subprocess.run(command, check=True)


def _allowed_voice_seconds(segment: Segment) -> float:
    if segment.id == SEGMENTS[-1].id:
        return segment.seconds
    return segment.seconds - TRANSITION_SECONDS


def generate_segment_voice(
    build_dir: Path,
    edge_tts: Path,
    segments: tuple[Segment, ...],
) -> tuple[Path, ...]:
    narration_dir = build_dir / "narration"
    parts_dir = narration_dir / "parts"
    parts_dir.mkdir(parents=True, exist_ok=True)
    voice = choose_voice(edge_tts)
    outputs = []
    for segment in segments:
        parts = voice_parts(segment)
        part_media = []
        part_cues = []
        durations = []
        for index, part in enumerate(parts, 1):
            media = parts_dir / f"{segment.id}-{index:02d}.mp3"
            srt = parts_dir / f"{segment.id}-{index:02d}.srt"
            _generate_tts_part(edge_tts, voice, part, media, srt)
            part_media.append(media)
            durations.append(probe_duration(media))
            part_cues.append(
                parse_srt(
                    srt.read_text(encoding="utf-8"),
                    f"{segment.id} part {index}",
                )
            )

        output_media = narration_dir / f"{segment.id}.mp3"
        output_srt = narration_dir / f"{segment.id}.srt"
        starts = part_starts(durations, parts)
        compose_voice_parts(part_media, durations, parts, output_media)
        cues = merge_cues(part_cues, starts)
        output_srt.write_text(cues_to_srt(cues), encoding="utf-8")

        duration = probe_duration(output_media)
        allowed = _allowed_voice_seconds(segment)
        if duration <= 0 or duration > allowed + 1e-9:
            raise RuntimeError(
                f"Narration {segment.id} is {duration:.2f}s; "
                f"allowed maximum is {allowed:.2f}s"
            )
        tail = allowed - duration
        if tail > MAX_TAIL_SILENCE_SECONDS:
            raise RuntimeError(
                f"Narration {segment.id} leaves {tail:.2f}s tail; "
                f"maximum is {MAX_TAIL_SILENCE_SECONDS:.2f}s"
            )
        final_cues = parse_srt(
            output_srt.read_text(encoding="utf-8"),
            segment.id,
        )
        validate_cues(
            final_cues,
            segment.id,
            max_end=allowed,
            allow_overlaps=True,
        )
        outputs.append(output_media)
    return tuple(outputs)


def compose_narration(build_dir: Path) -> Path:
    output = build_dir / "tweakeroo-narration.mp3"
    command = [FFMPEG, "-y"]
    graph_parts = []
    labels = []
    for index, item in enumerate(timeline()):
        media = build_dir / "narration" / f"{item.segment.id}.mp3"
        command.extend(["-i", str(media)])
        delay = round(item.start * 1000)
        label = f"voice{index}"
        graph_parts.append(
            f"[{index}:a]aresample=48000,"
            f"aformat=channel_layouts=stereo,adelay={delay}|{delay}[{label}]"
        )
        labels.append(f"[{label}]")
    graph_parts.append(
        "".join(labels)
        + f"amix=inputs={len(labels)}:duration=longest:normalize=0,"
        f"apad=pad_dur={encoded_seconds()},"
        f"atrim=0:{encoded_seconds()}[narration]"
    )
    command.extend(
        [
            "-filter_complex",
            ";".join(graph_parts),
            "-map",
            "[narration]",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "192k",
            str(output),
        ]
    )
    subprocess.run(command, check=True)
    return output


def generate_voice(
    build_dir: Path,
    edge_tts: Path,
) -> tuple[Path, ...]:
    media = generate_segment_voice(build_dir, edge_tts, SEGMENTS)
    groups = []
    for segment in SEGMENTS:
        path = build_dir / "narration" / f"{segment.id}.srt"
        groups.append(parse_srt(path.read_text(encoding="utf-8"), segment.id))
    merged = merge_cues(groups, [item.start for item in timeline()])
    validate_cues(
        merged,
        "Merged subtitles",
        max_end=encoded_seconds(),
        width=CAPTION_WIDTH,
    )
    subtitle_dir = build_dir / "subtitles"
    subtitle_dir.mkdir(parents=True, exist_ok=True)
    srt = subtitle_dir / "tweakeroo.zh-CN.srt"
    srt.write_text(cues_to_srt(merged), encoding="utf-8")
    narration = compose_narration(build_dir)
    return (*media, srt, narration)


def generate_voice_preview(build_dir: Path, edge_tts: Path) -> Path:
    selected = tuple(
        segment for segment in SEGMENTS if segment.id in PREVIEW_SEGMENT_IDS
    )
    generate_segment_voice(build_dir, edge_tts, selected)
    output = build_dir / "voice-preview.mp3"
    command = [FFMPEG, "-y"]
    for segment_id in PREVIEW_SEGMENT_IDS:
        command.extend(
            ["-i", str(build_dir / "narration" / f"{segment_id}.mp3")]
        )
    inputs = "".join(
        f"[{index}:a]" for index in range(len(PREVIEW_SEGMENT_IDS))
    )
    command.extend(
        [
            "-filter_complex",
            f"{inputs}concat=n={len(PREVIEW_SEGMENT_IDS)}:v=0:a=1[preview]",
            "-map",
            "[preview]",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "192k",
            str(output),
        ]
    )
    subprocess.run(command, check=True)
    return output
