from dataclasses import dataclass
from pathlib import Path
import re
import subprocess

from scripts.minihud_video.storyboard import (
    SEGMENTS,
    TRANSITION_SECONDS,
    encoded_seconds,
    timeline,
)


VOICES = ("zh-CN-YunjianNeural", "zh-CN-YunxiNeural")
RATE = "-2%"
PITCH = "-2Hz"
CAPTION_WIDTH = 18
MAX_CAPTION_LINES = 2
MAX_TAIL_SILENCE_SECONDS = 1.0

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
                f"{label} cue {index} must have positive duration "
                f"with 0 <= start < end; got {cue.start:.3f}s --> "
                f"{cue.end:.3f}s"
            )
        if previous is not None:
            if cue.start < previous.start or cue.end < previous.end:
                raise RuntimeError(
                    f"{label} cue {index} is not ordered after cue "
                    f"{index - 1}"
                )
            if not allow_overlaps and cue.start < previous.end:
                raise RuntimeError(
                    f"{label} cues {index - 1} and {index} overlap by "
                    f"{previous.end - cue.start:.3f}s"
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
                    f"{label} cue {index} has {len(lines)} lines; "
                    f"maximum is {MAX_CAPTION_LINES}"
                )
            longest = max(map(len, lines))
            if longest > width:
                raise RuntimeError(
                    f"{label} cue {index} has a {longest}-character "
                    f"line; maximum is {width}"
                )
        previous = cue


def parse_srt(source: str, label: str = "SRT") -> list[Cue]:
    if not source.strip():
        raise RuntimeError(f"{label} is empty; expected subtitle content")
    cues = []
    for block in re.split(r"\n\s*\n", source.strip()):
        lines = block.splitlines()
        timing_indices = [
            i for i, line in enumerate(lines) if "-->" in line
        ]
        cue_number = len(cues) + 1
        if len(timing_indices) != 1:
            raise RuntimeError(
                f"{label} cue {cue_number} is missing a valid timing line"
            )
        timing_index = timing_indices[0]
        timing_parts = re.split(r"\s*-->\s*", lines[timing_index].strip())
        if len(timing_parts) != 2:
            raise RuntimeError(
                f"{label} cue {cue_number} has malformed timing: "
                f"{lines[timing_index]!r}"
            )
        start, end = timing_parts
        text = " ".join(lines[timing_index + 1 :]).strip()
        if not text:
            raise RuntimeError(f"{label} cue {cue_number} has empty text")
        try:
            start_seconds = parse_srt_time(start)
            end_seconds = parse_srt_time(end)
        except ValueError as error:
            raise RuntimeError(
                f"{label} cue {cue_number} has malformed timing: "
                f"{lines[timing_index]!r}"
            ) from error
        cues.append(Cue(start_seconds, end_seconds, text))
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
            raise RuntimeError("Caption cannot be split into nonempty chunks")
        chunks.append(chunk)
        remaining = remaining[split:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks


def wrap_caption(text: str, width: int = CAPTION_WIDTH) -> str:
    if width <= 0:
        raise ValueError("Caption width must be positive")
    compact = re.sub(r"\s+", " ", text).strip()
    if not compact:
        raise RuntimeError("Caption text is empty")
    if len(compact) > width * MAX_CAPTION_LINES:
        raise RuntimeError(
            f"Caption has {len(compact)} characters; split it before "
            f"wrapping to {MAX_CAPTION_LINES} lines of {width}"
        )
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
        split = round(target)
        split = _avoid_latin_token_split(compact, split, lower, upper)
    wrapped = compact[:split].rstrip() + "\n" + compact[split:].lstrip()
    lines = wrapped.splitlines()
    if len(lines) > MAX_CAPTION_LINES or max(map(len, lines)) > width:
        raise RuntimeError(
            f"Caption cannot fit {MAX_CAPTION_LINES} lines of {width} characters"
        )
    return wrapped


def split_cue(cue: Cue, width: int = CAPTION_WIDTH) -> list[Cue]:
    validate_cues([cue], "Caption source", allow_overlaps=True)
    compact = re.sub(r"\s+", " ", cue.text).strip()
    chunks = _caption_chunks(compact, width * MAX_CAPTION_LINES)
    weights = [len(chunk) for chunk in chunks]
    total_weight = sum(weights)
    total_duration = cue.end - cue.start
    split = []
    cumulative_weight = 0
    for index, (chunk, weight) in enumerate(zip(chunks, weights, strict=True)):
        start = (
            cue.start
            + total_duration * cumulative_weight / total_weight
        )
        cumulative_weight += weight
        end = (
            cue.end
            if index == len(chunks) - 1
            else cue.start
            + total_duration * cumulative_weight / total_weight
        )
        split.append(Cue(start, end, wrap_caption(chunk, width)))
    validate_cues(split, "Split caption", width=width)
    return split


def normalize_cues(cues: list[Cue], label: str = "SRT") -> list[Cue]:
    validate_cues(cues, label, allow_overlaps=True)
    normalized = list(cues)
    for index in range(len(normalized) - 1):
        current = normalized[index]
        following = normalized[index + 1]
        if current.end > following.start:
            if following.start <= current.start:
                raise RuntimeError(
                    f"{label} cues {index + 1} and {index + 2} cannot be "
                    "normalized while preserving positive duration"
                )
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
            shifted = Cue(
                cue.start + offset,
                cue.end + offset,
                cue.text,
            )
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
    for segment_index, segment in enumerate(SEGMENTS):
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
            if segment_index == len(SEGMENTS) - 1
            else segment.seconds - TRANSITION_SECONDS
        )
        if duration <= 0:
            raise RuntimeError(
                f"Narration {segment.id} must have positive duration; "
                f"got {duration:.2f}s"
            )
        if duration > allowed + 1e-9:
            raise RuntimeError(
                f"Narration {segment.id} is {duration:.2f}s, "
                f"longer than {allowed:.2f}s"
            )
        tail_silence = allowed - duration
        if tail_silence > MAX_TAIL_SILENCE_SECONDS + 1e-9:
            raise RuntimeError(
                f"Narration {segment.id} leaves {tail_silence:.2f}s of tail "
                f"silence; maximum is {MAX_TAIL_SILENCE_SECONDS:.2f}s"
            )
        try:
            source = srt.read_text(encoding="utf-8")
        except OSError as error:
            raise RuntimeError(
                f"Subtitle {segment.id} could not be read from {srt}: {error}"
            ) from error
        cues = parse_srt(source, f"Subtitle {segment.id}")
        cues = normalize_cues(cues, f"Subtitle {segment.id}")
        validate_cues(
            cues,
            f"Subtitle {segment.id}",
            max_end=allowed,
        )
        outputs.append(media)
        segment_srts.append(cues)
    starts = [item.start for item in timeline()]
    merged = merge_cues(segment_srts, starts)
    validate_cues(
        merged,
        "Merged subtitles",
        max_end=encoded_seconds(),
        width=CAPTION_WIDTH,
    )
    merged_path = subtitle_dir / "minihud-bilibili.zh-CN.srt"
    merged_path.write_text(cues_to_srt(merged), encoding="utf-8")
    return tuple(outputs)
