"""Microsoft Yunxi narration and synchronized subtitles for InvMove."""

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import time

from scripts.invmove_video.storyboard import (
    PREVIEW_SEGMENT_IDS,
    SEGMENTS,
    TRANSITION_SECONDS,
    Segment,
    encoded_seconds,
    timeline,
)


VOICE = "zh-CN-YunxiNeural"
CAPTION_WIDTH = 24
MAX_TAIL_SILENCE_SECONDS = 4.6
FFMPEG = "/usr/bin/ffmpeg"
FFPROBE = "/usr/bin/ffprobe"
_SRT_TIME = re.compile(r"(?P<h>\d+):(?P<m>[0-5]\d):(?P<s>[0-5]\d),(?P<ms>\d{3})")
_PUNCTUATION = frozenset("，。！？；：、,.!?;:")


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


_VOICE_PARTS = {
    "hook": (
        VoicePart("打开背包，角色就得站住。", "-2%", "-1Hz", 230),
        VoicePart(
            "如果你总在移动和整理物品之间反复切换，InvMove 解决的，就是这一下停顿。",
            "+2%", "+2Hz", 180,
        ),
    ),
    "core": (
        VoicePart("它把移动控制带进游戏界面。", "+3%", "+2Hz", 170),
        VoicePart(
            "背包和工作台打开时，仍可前进、转向、跳跃和疾跑。",
            "+2%", "+1Hz", 200,
        ),
        VoicePart(
            "输入框聚焦时自动停下，打字不会带着角色乱跑。",
            "-3%", "-2Hz", 170,
        ),
    ),
    "blocked": (
        VoicePart("先看没装的情况。", "+2%", "+1Hz", 220),
        VoicePart(
            "背包合成界面一打开，W 键还亮着，角色却已经停下。",
            "-1%", "-1Hz", 160,
        ),
    ),
    "move": (
        VoicePart("装上后，变化很直接。", "+4%", "+2Hz", 210),
        VoicePart(
            "保持前进时打开背包，物品栏和随身合成格照常出现，脚步不会被界面打断。",
            "+2%", "+1Hz", 160,
        ),
    ),
    "workbench": (
        VoicePart("换成工作台也一样。", "+3%", "+1Hz", 220),
        VoicePart("界面保持开启，WASD 仍然响应。", "-2%", "-1Hz", 180),
    ),
    "install": (
        VoicePart(
            "InvMove 必须搭配 Cloth Config。",
            "+2%", "+1Hz", 190,
        ),
        VoicePart(
            "Fabric API 提供切换快捷键，Mod Menu 方便打开配置，二者都可选。",
            "+1%", "+0Hz", 220,
        ),
        VoicePart(
            "选对版本，装进客户端即可。",
            "-4%", "-2Hz", 170,
        ),
    ),
}


def voice_parts(segment: Segment) -> tuple[VoicePart, ...]:
    return _VOICE_PARTS[segment.id]


def parse_srt_time(value: str) -> float:
    match = _SRT_TIME.fullmatch(value.strip())
    if not match:
        raise RuntimeError(f"Invalid SRT time: {value}")
    return (
        int(match["h"]) * 3600
        + int(match["m"]) * 60
        + int(match["s"])
        + int(match["ms"]) / 1000
    )


def format_srt_time(value: float) -> str:
    millis = round(value * 1000)
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    seconds, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def normalize_cues(cues: list[Cue], label: str) -> list[Cue]:
    ordered = sorted(cues, key=lambda cue: (cue.start, cue.end))
    result = []
    for index, cue in enumerate(ordered):
        end = cue.end
        if index + 1 < len(ordered):
            end = min(end, ordered[index + 1].start)
        if end <= cue.start:
            raise RuntimeError(f"{label} has an invalid subtitle cue")
        result.append(Cue(cue.start, end, cue.text))
    return result


def parse_srt(source: str, label: str) -> list[Cue]:
    cues = []
    for block in re.split(r"\n\s*\n", source.strip()):
        lines = block.splitlines()
        timing = next((line for line in lines if "-->" in line), None)
        if timing is None:
            continue
        start_text, end_text = re.split(r"\s*-->\s*", timing.strip())
        timing_index = lines.index(timing)
        text = "\n".join(lines[timing_index + 1 :]).strip()
        text = re.sub(r"([，。！？；：、])[ \t]+", r"\1", text)
        if text:
            cues.append(Cue(parse_srt_time(start_text), parse_srt_time(end_text), text))
    if not cues:
        raise RuntimeError(f"{label} contains no subtitle cues")
    return normalize_cues(cues, label)


def wrap_caption(text: str) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    compact = re.sub(r"\b([A-Za-z])\s+([\u4e00-\u9fff])", r"\1\2", compact)
    if len(compact) <= CAPTION_WIDTH:
        return compact
    target = len(compact) / 2
    lower = max(1, len(compact) - CAPTION_WIDTH)
    upper = min(CAPTION_WIDTH, len(compact) - 1)
    candidates = [
        position
        for position in range(lower, upper + 1)
        if compact[position - 1] in _PUNCTUATION or compact[position - 1].isspace()
    ]
    split = min(candidates, key=lambda position: abs(position - target)) if candidates else round(target)
    return compact[:split].rstrip() + "\n" + compact[split:].lstrip()


def cues_to_srt(cues: list[Cue]) -> str:
    return "\n\n".join(
        f"{index}\n{format_srt_time(cue.start)} --> {format_srt_time(cue.end)}\n{wrap_caption(cue.text)}"
        for index, cue in enumerate(cues, 1)
    ) + "\n"


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            FFPROBE, "-v", "error", "-show_entries", "format=duration",
            "-of", "default=nw=1:nk=1", str(path),
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
    if VOICE not in result.stdout:
        raise RuntimeError(f"Microsoft TTS did not return {VOICE}")
    return VOICE


def generate_tts_part(edge_tts: Path, voice: str, part: VoicePart, media: Path, srt: Path) -> None:
    stamp = media.with_suffix(".source.txt")
    signature = "\n".join((voice, part.rate, part.pitch, part.text)) + "\n"
    if (
        media.is_file()
        and media.stat().st_size > 0
        and srt.is_file()
        and srt.stat().st_size > 0
        and stamp.is_file()
        and stamp.read_text(encoding="utf-8") == signature
    ):
        return
    command = [
        str(edge_tts), "--voice", voice, f"--rate={part.rate}",
        f"--pitch={part.pitch}", "--text", part.text,
        "--write-media", str(media), "--write-subtitles", str(srt),
    ]
    for attempt in range(6):
        media.unlink(missing_ok=True)
        srt.unlink(missing_ok=True)
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
            stamp.write_text(signature, encoding="utf-8")
            time.sleep(1.2)
            return
        except subprocess.CalledProcessError:
            if attempt == 5:
                raise
            time.sleep(min(2 * (attempt + 1), 8))


def trim_voice_part(source: Path, output: Path) -> None:
    subprocess.run(
        [
            FFMPEG, "-y", "-i", str(source), "-af",
            "areverse,silenceremove=start_periods=1:start_duration=0.06:start_threshold=-45dB:start_silence=0.06,areverse",
            "-c:a", "libmp3lame", "-b:a", "192k", str(output),
        ],
        check=True,
        capture_output=True,
    )


def compose_parts(media_paths: list[Path], durations: list[float], parts: tuple[VoicePart, ...], output: Path) -> None:
    command = [FFMPEG, "-y"]
    graph = []
    labels = []
    for index, (media, duration, part) in enumerate(zip(media_paths, durations, parts, strict=True)):
        command.extend(["-i", str(media)])
        pause = part.pause_ms / 1000
        graph.append(
            f"[{index}:a]aresample=24000,aformat=channel_layouts=mono,"
            f"apad=pad_dur={pause:.3f},atrim=0:{duration + pause:.6f}[p{index}]"
        )
        labels.append(f"[p{index}]")
    graph.append("".join(labels) + f"concat=n={len(labels)}:v=0:a=1[voice]")
    command.extend(
        [
            "-filter_complex", ";".join(graph), "-map", "[voice]",
            "-c:a", "libmp3lame", "-b:a", "192k", str(output),
        ]
    )
    subprocess.run(command, check=True, capture_output=True)


def allowed_voice_seconds(segment: Segment) -> float:
    return segment.seconds if segment is SEGMENTS[-1] else segment.seconds - TRANSITION_SECONDS


def generate_segment_voice(build_dir: Path, edge_tts: Path, segments: tuple[Segment, ...]) -> tuple[Path, ...]:
    narration_dir = build_dir / "narration"
    raw_dir = narration_dir / "parts/raw"
    parts_dir = narration_dir / "parts"
    raw_dir.mkdir(parents=True, exist_ok=True)
    voice = choose_voice(edge_tts)
    outputs = []
    for segment in segments:
        media_paths = []
        durations = []
        cue_groups = []
        starts = []
        cursor = 0.0
        parts = voice_parts(segment)
        for index, part in enumerate(parts, 1):
            raw_media = raw_dir / f"{segment.id}-{index:02d}.mp3"
            raw_srt = raw_dir / f"{segment.id}-{index:02d}.srt"
            media = parts_dir / f"{segment.id}-{index:02d}.mp3"
            generate_tts_part(edge_tts, voice, part, raw_media, raw_srt)
            trim_voice_part(raw_media, media)
            duration = probe_duration(media)
            starts.append(cursor)
            media_paths.append(media)
            durations.append(duration)
            raw_cues = parse_srt(raw_srt.read_text(encoding="utf-8"), raw_srt.name)
            cue_groups.append(
                [Cue(cue.start, min(cue.end, duration), cue.text) for cue in raw_cues if cue.start < duration]
            )
            cursor += duration + part.pause_ms / 1000

        output_media = narration_dir / f"{segment.id}.mp3"
        output_srt = narration_dir / f"{segment.id}.srt"
        compose_parts(media_paths, durations, parts, output_media)
        merged = []
        for group, offset in zip(cue_groups, starts, strict=True):
            merged.extend(Cue(cue.start + offset, cue.end + offset, cue.text) for cue in group)
        output_srt.write_text(cues_to_srt(normalize_cues(merged, segment.id)), encoding="utf-8")

        duration = probe_duration(output_media)
        allowed = allowed_voice_seconds(segment)
        if duration > allowed + 0.03:
            raise RuntimeError(f"Narration {segment.id} is {duration:.2f}s; maximum is {allowed:.2f}s")
        if allowed - duration > MAX_TAIL_SILENCE_SECONDS:
            raise RuntimeError(f"Narration {segment.id} leaves {allowed - duration:.2f}s of silence")
        outputs.append(output_media)
    return tuple(outputs)


def compose_narration(build_dir: Path) -> Path:
    output = build_dir / "invmove-narration.mp3"
    command = [FFMPEG, "-y"]
    graph = []
    labels = []
    for index, item in enumerate(timeline()):
        command.extend(["-i", str(build_dir / "narration" / f"{item.segment.id}.mp3")])
        delay = round(item.start * 1000)
        graph.append(
            f"[{index}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={delay}|{delay}[v{index}]"
        )
        labels.append(f"[v{index}]")
    graph.append(
        "".join(labels)
        + f"amix=inputs={len(labels)}:duration=longest:normalize=0,"
        + f"apad=pad_dur={encoded_seconds()},atrim=0:{encoded_seconds()}[narration]"
    )
    command.extend(
        [
            "-filter_complex", ";".join(graph), "-map", "[narration]",
            "-c:a", "libmp3lame", "-b:a", "192k", str(output),
        ]
    )
    subprocess.run(command, check=True, capture_output=True)
    return output


def generate_voice(build_dir: Path, edge_tts: Path) -> tuple[Path, ...]:
    media = generate_segment_voice(build_dir, edge_tts, SEGMENTS)
    merged = []
    for item in timeline():
        source = build_dir / "narration" / f"{item.segment.id}.srt"
        for cue in parse_srt(source.read_text(encoding="utf-8"), item.segment.id):
            merged.append(Cue(cue.start + item.start, cue.end + item.start, cue.text))
    subtitle_dir = build_dir / "subtitles"
    subtitle_dir.mkdir(parents=True, exist_ok=True)
    srt = subtitle_dir / "invmove.zh-CN.srt"
    srt.write_text(cues_to_srt(normalize_cues(merged, "merged subtitles")), encoding="utf-8")
    return (*media, srt, compose_narration(build_dir))


def generate_voice_preview(build_dir: Path, edge_tts: Path) -> Path:
    selected = tuple(segment for segment in SEGMENTS if segment.id in PREVIEW_SEGMENT_IDS)
    generate_segment_voice(build_dir, edge_tts, selected)
    output = build_dir / "voice-preview.mp3"
    command = [FFMPEG, "-y"]
    for segment in selected:
        command.extend(["-i", str(build_dir / "narration" / f"{segment.id}.mp3")])
    inputs = "".join(f"[{index}:a]" for index in range(len(selected)))
    command.extend(
        [
            "-filter_complex", f"{inputs}concat=n={len(selected)}:v=0:a=1[preview]",
            "-map", "[preview]", "-c:a", "libmp3lame", "-b:a", "192k", str(output),
        ]
    )
    subprocess.run(command, check=True, capture_output=True)
    return output
