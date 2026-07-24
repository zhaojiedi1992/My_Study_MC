"""Microsoft Edge TTS narration and subtitles for the chat/social video."""

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import time

from scripts.chat_social_video.storyboard import (
    PREVIEW_SEGMENT_IDS,
    SEGMENTS,
    TRANSITION_SECONDS,
    Segment,
    encoded_seconds,
    timeline,
)


VOICES = ("zh-CN-YunxiNeural", "zh-CN-YunyangNeural")
CAPTION_WIDTH = 24
MAX_CAPTION_LINES = 2
MAX_TAIL_SILENCE_SECONDS = 4.5
FFMPEG = "/usr/bin/ffmpeg"
FFPROBE = "/usr/bin/ffprobe"
_SRT_TIME = re.compile(
    r"(?P<h>\d+):(?P<m>[0-5]\d):(?P<s>[0-5]\d),(?P<ms>\d{3})"
)
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
    "overview": (
        VoicePart("聊天、社交与隐私。", "+3%", "+1Hz", 220),
        VoicePart("不只是美化聊天栏。", "-1%", "+0Hz", 220),
        VoicePart("四个组件，解决认人、回看、签名关联和动作表达。", "+1%", "+1Hz", 180),
    ),
    "heads": (
        VoicePart("多人聊天，光看名字常认不出人。", "+1%", "+1Hz", 180),
        VoicePart("Chat Heads 在消息旁显示玩家头像。", "+2%", "+1Hz", 210),
        VoicePart("支持 UUID 和昵称别名，纯客户端即可。", "-3%", "-1Hz", 180),
    ),
    "history": (
        VoicePart("聊天刷屏后，错过的消息还能翻回来。", "+1%", "+1Hz", 170),
        VoicePart("More Chat History 把上限从一百条，提高到一万六千三百八十四条。", "-1%", "+0Hz", 240),
        VoicePart("安装后自动生效，只保留当前会话。", "-3%", "-1Hz", 180),
    ),
    "reports": (
        VoicePart("No Chat Reports 处理消息签名，不是聊天内容。", "+1%", "+1Hz", 160),
        VoicePart("服务器允许时，发送未签名消息，减少账号与举报证据关联。", "+0%", "+0Hz", 220),
        VoicePart("客户端和服务端一起部署效果最好。", "-1%", "+0Hz", 190),
        VoicePart("不会隐藏聊天，也不能绕过服务器策略。", "-4%", "-2Hz", 180),
    ),
    "emote": (
        VoicePart("最后是 Emotecraft。", "+3%", "+2Hz", 220),
        VoicePart("表情轮盘默认绑定 B，和路径点冲突时，可以在按键设置里改成空闲按键。", "-1%", "+0Hz", 180),
        VoicePart("点击轮盘里的动作，就能播放挥手、舞蹈或自定义动画。", "+1%", "+1Hz", 220),
        VoicePart("现在点击屏幕上的最大化播放，让动作视频进入内置全屏。", "+2%", "+1Hz", 220),
        VoicePart("完整多人同步，仍需要服务端和其他玩家客户端支持。", "-4%", "-2Hz", 180),
    ),
}


def voice_parts(segment: Segment) -> tuple[VoicePart, ...]:
    return _VOICE_PARTS[segment.id]


def parse_srt_time(value: str) -> float:
    match = _SRT_TIME.fullmatch(value.strip())
    if not match:
        raise RuntimeError(f"Invalid SRT time: {value}")
    return (
        int(match.group("h")) * 3600
        + int(match.group("m")) * 60
        + int(match.group("s"))
        + int(match.group("ms")) / 1000
    )


def format_srt_time(value: float) -> str:
    millis = round(value * 1000)
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    seconds, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


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
            cues.append(
                Cue(parse_srt_time(start_text), parse_srt_time(end_text), text)
            )
    if not cues:
        raise RuntimeError(f"{label} contains no subtitle cues")
    return normalize_cues(cues, label)


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


def _split_text(text: str, limit: int) -> list[str]:
    compact = re.sub(r"\s+", " ", text).strip()
    chunks = []
    while len(compact) > limit:
        candidates = [
            pos
            for pos in range(1, limit + 1)
            if compact[pos - 1] in _PUNCTUATION or compact[pos - 1].isspace()
        ]
        split = candidates[-1] if candidates else limit
        chunks.append(compact[:split].strip())
        compact = compact[split:].strip()
    if compact:
        chunks.append(compact)
    return chunks


def wrap_caption(text: str) -> str:
    if len(text) <= CAPTION_WIDTH:
        return text
    target = len(text) / 2
    lower = max(1, len(text) - CAPTION_WIDTH)
    upper = min(CAPTION_WIDTH, len(text) - 1)
    candidates = [
        pos
        for pos in range(lower, upper + 1)
        if text[pos - 1] in _PUNCTUATION or text[pos - 1].isspace()
    ]
    split = min(candidates, key=lambda pos: abs(pos - target)) if candidates else round(target)
    return text[:split].rstrip() + "\n" + text[split:].lstrip()


def split_cue(cue: Cue) -> list[Cue]:
    chunks = _split_text(cue.text, CAPTION_WIDTH * MAX_CAPTION_LINES)
    if len(chunks) == 1:
        return [Cue(cue.start, cue.end, wrap_caption(chunks[0]))]
    weights = [max(1, len(chunk)) for chunk in chunks]
    total = sum(weights)
    cursor = cue.start
    result = []
    for index, (chunk, weight) in enumerate(zip(chunks, weights, strict=True)):
        end = cue.end if index == len(chunks) - 1 else cursor + (cue.end - cue.start) * weight / total
        result.append(Cue(cursor, end, wrap_caption(chunk)))
        cursor = end
    return result


def cues_to_srt(cues: list[Cue]) -> str:
    blocks = []
    for index, cue in enumerate(cues, 1):
        blocks.append(
            f"{index}\n{format_srt_time(cue.start)} --> {format_srt_time(cue.end)}\n{cue.text}"
        )
    return "\n\n".join(blocks) + "\n"


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            FFPROBE,
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
    raise RuntimeError("Microsoft TTS did not return an approved Chinese voice")


def generate_tts_part(
    edge_tts: Path,
    voice: str,
    part: VoicePart,
    media: Path,
    srt: Path,
) -> None:
    if (
        media.is_file()
        and media.stat().st_size > 0
        and srt.is_file()
        and srt.stat().st_size > 0
    ):
        return
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
    for attempt in range(6):
        media.unlink(missing_ok=True)
        srt.unlink(missing_ok=True)
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
            # The public Microsoft endpoint becomes unreliable when many
            # websocket sessions are opened back-to-back.
            time.sleep(1.25)
            return
        except subprocess.CalledProcessError:
            if attempt == 5:
                raise
            time.sleep(min(2 * (attempt + 1), 8))


def trim_voice_part(source: Path, output: Path) -> None:
    subprocess.run(
        [
            FFMPEG,
            "-y",
            "-i",
            str(source),
            "-af",
            "areverse,silenceremove=start_periods=1:start_duration=0.06:start_threshold=-45dB:start_silence=0.06,areverse",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "192k",
            str(output),
        ],
        check=True,
        capture_output=True,
    )


def compose_parts(
    media_paths: list[Path],
    durations: list[float],
    parts: tuple[VoicePart, ...],
    output: Path,
) -> None:
    command = [FFMPEG, "-y"]
    graph = []
    labels = []
    for index, (media, duration, part) in enumerate(
        zip(media_paths, durations, parts, strict=True)
    ):
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
    subprocess.run(command, check=True, capture_output=True)


def allowed_voice_seconds(segment: Segment) -> float:
    return segment.seconds if segment is SEGMENTS[-1] else segment.seconds - TRANSITION_SECONDS


def generate_segment_voice(
    build_dir: Path,
    edge_tts: Path,
    segments: tuple[Segment, ...],
) -> tuple[Path, ...]:
    narration_dir = build_dir / "narration"
    raw_dir = narration_dir / "parts/raw"
    parts_dir = narration_dir / "parts"
    raw_dir.mkdir(parents=True, exist_ok=True)
    voice = choose_voice(edge_tts)
    outputs = []
    for segment in segments:
        parts = voice_parts(segment)
        media_paths = []
        duration_list = []
        cue_groups = []
        starts = []
        cursor = 0.0
        for index, part in enumerate(parts, 1):
            raw_media = raw_dir / f"{segment.id}-{index:02d}.mp3"
            raw_srt = raw_dir / f"{segment.id}-{index:02d}.srt"
            media = parts_dir / f"{segment.id}-{index:02d}.mp3"
            generate_tts_part(edge_tts, voice, part, raw_media, raw_srt)
            trim_voice_part(raw_media, media)
            duration = probe_duration(media)
            starts.append(cursor)
            media_paths.append(media)
            duration_list.append(duration)
            raw_cues = parse_srt(raw_srt.read_text(encoding="utf-8"), raw_srt.name)
            cue_groups.append(
                [Cue(cue.start, min(cue.end, duration), cue.text) for cue in raw_cues if cue.start < duration]
            )
            cursor += duration + part.pause_ms / 1000

        output_media = narration_dir / f"{segment.id}.mp3"
        output_srt = narration_dir / f"{segment.id}.srt"
        compose_parts(media_paths, duration_list, parts, output_media)
        merged = []
        for group, offset in zip(cue_groups, starts, strict=True):
            for cue in group:
                merged.extend(split_cue(Cue(cue.start + offset, cue.end + offset, cue.text)))
        merged = normalize_cues(merged, segment.id)
        output_srt.write_text(cues_to_srt(merged), encoding="utf-8")

        duration = probe_duration(output_media)
        allowed = allowed_voice_seconds(segment)
        if duration > allowed + 0.02:
            raise RuntimeError(
                f"Narration {segment.id} is {duration:.2f}s; maximum is {allowed:.2f}s"
            )
        if allowed - duration > MAX_TAIL_SILENCE_SECONDS:
            raise RuntimeError(
                f"Narration {segment.id} leaves {allowed - duration:.2f}s of silence"
            )
        outputs.append(output_media)
    return tuple(outputs)


def compose_narration(build_dir: Path) -> Path:
    output = build_dir / "chat-social-narration.mp3"
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
            "-filter_complex",
            ";".join(graph),
            "-map",
            "[narration]",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "192k",
            str(output),
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
            for caption in split_cue(cue):
                merged.append(
                    Cue(
                        caption.start + item.start,
                        caption.end + item.start,
                        caption.text,
                    )
                )
    merged = normalize_cues(merged, "merged subtitles")
    subtitle_dir = build_dir / "subtitles"
    subtitle_dir.mkdir(parents=True, exist_ok=True)
    srt = subtitle_dir / "chat-social.zh-CN.srt"
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
    for segment in selected:
        command.extend(["-i", str(build_dir / "narration" / f"{segment.id}.mp3")])
    inputs = "".join(f"[{index}:a]" for index in range(len(selected)))
    command.extend(
        [
            "-filter_complex",
            f"{inputs}concat=n={len(selected)}:v=0:a=1[preview]",
            "-map",
            "[preview]",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "192k",
            str(output),
        ]
    )
    subprocess.run(command, check=True, capture_output=True)
    return output
