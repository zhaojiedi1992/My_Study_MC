"""Build the complete 信息 HUD Bilibili delivery from the deck and live footage."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
from urllib.parse import urlencode

from scripts.info_hud_video.publishing import (
    TAGS,
    TITLE,
    build_publish_markdown,
    chapter_lines,
    description_text,
)
from scripts.info_hud_video.storyboard import (
    SEGMENTS,
    TRANSITION_SECONDS,
    Segment,
    VoicePart,
    encoded_seconds,
    timeline,
)


ROOT = Path(__file__).resolve().parents[2]
DECK = ROOT / "source/extra/MOD介绍/信息HUD与生存辅助/index.html"
VIDEO_DIR = DECK.parent / "videos"
BUILD = ROOT / "build/info-hud-video"
CHECKS = BUILD / "checks"
CHROME = "/usr/bin/google-chrome"
FFMPEG = "/usr/bin/ffmpeg"
FFPROBE = "/usr/bin/ffprobe"
VOICE = "zh-CN-YunxiNeural"
SRT_TIME = re.compile(r"(?P<h>\d+):(?P<m>[0-5]\d):(?P<s>[0-5]\d)[,.](?P<ms>\d{3})")
CAPTION_WIDTH = 24
SKILL_VERIFIER = Path("/home/zhaojd5/.codex/skills/make-bilibili-video/scripts/verify_delivery.py")
SOURCE_VIDEOS = {
    "durability_before": VIDEO_DIR / "03-show-durability-未安装.mp4",
    "durability_after": VIDEO_DIR / "04-show-durability-已安装.mp4",
    "neat": VIDEO_DIR / "05-neat-实体血量条.mp4",
    "jade": VIDEO_DIR / "06-jade-准星目标信息.mp4",
    "appleskin": VIDEO_DIR / "02-appleskin-已安装.mp4",
}


@dataclass(frozen=True)
class Cue:
    start: float
    end: float
    text: str


def run(command: list[str], *, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, capture_output=True, text=True, timeout=timeout)


def media_info(path: Path) -> dict:
    return json.loads(
        run([FFPROBE, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]).stdout
    )


def duration(path: Path) -> float:
    return float(media_info(path)["format"]["duration"])


def format_srt_time(value: float) -> str:
    millis = round(value * 1000)
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    seconds, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def parse_srt_time(value: str) -> float:
    match = SRT_TIME.fullmatch(value.strip())
    if not match:
        raise RuntimeError(f"Invalid SRT timestamp: {value}")
    return int(match["h"]) * 3600 + int(match["m"]) * 60 + int(match["s"]) + int(match["ms"]) / 1000


def normalize_cues(cues: list[Cue]) -> list[Cue]:
    result: list[Cue] = []
    for cue in sorted(cues, key=lambda item: (item.start, item.end)):
        start = max(0.0, cue.start)
        end = cue.end
        if result:
            start = max(start, result[-1].end)
        if end - start >= 0.08:
            result.append(Cue(start, end, cue.text))
    return result


def parse_tts_srt(path: Path, clip_duration: float) -> list[Cue]:
    blocks = re.split(r"\n\s*\n", path.read_text(encoding="utf-8").strip())
    cues: list[Cue] = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        timing = next((line for line in lines if "-->" in line), None)
        if not timing:
            continue
        start_text, end_text = re.split(r"\s*-->\s*", timing)
        text = " ".join(lines[lines.index(timing) + 1 :]).strip()
        if text:
            start = parse_srt_time(start_text)
            end = min(parse_srt_time(end_text), clip_duration)
            if end > start:
                cues.append(Cue(start, end, text))
    return normalize_cues(cues)


def wrap_caption(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= CAPTION_WIDTH:
        return text
    mid = len(text) // 2
    punctuation = "，。！？；：、,.!?;:"
    candidates = [index for index, char in enumerate(text[:CAPTION_WIDTH], 1) if char in punctuation]
    split = min(candidates, key=lambda index: abs(index - mid)) if candidates else min(CAPTION_WIDTH, mid + 4)
    return text[:split].rstrip() + "\n" + text[split:].lstrip()


def cues_to_srt(cues: list[Cue]) -> str:
    return "\n\n".join(
        f"{index}\n{format_srt_time(cue.start)} --> {format_srt_time(cue.end)}\n{wrap_caption(cue.text)}"
        for index, cue in enumerate(normalize_cues(cues), 1)
    ) + "\n"


def locate_edge_tts() -> Path:
    candidates = (
        BUILD / ".venv/bin/edge-tts",
        ROOT / "build/modmenu-video/.venv/bin/edge-tts",
        ROOT / "build/chat-social-video/.venv/bin/edge-tts",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    system = shutil.which("edge-tts")
    if system:
        return Path(system)
    raise RuntimeError("edge-tts is required for zh-CN-YunxiNeural narration")


def build_slide_url(segment: Segment, *, state: str | None = None) -> str:
    query: dict[str, str | int] = {"export": 1, "slide": int(segment.slide or 1)}
    active_state = segment.state if state is None else state
    if active_state:
        query["state"] = active_state
    return f"{DECK.resolve().as_uri()}?{urlencode(query)}"


def capture_slide(segment: Segment, output: Path, *, state: str | None = None) -> Path:
    run(
        [
            CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
            "--hide-scrollbars", "--allow-file-access-from-files", "--force-device-scale-factor=1",
            "--run-all-compositor-stages-before-draw", "--virtual-time-budget=1200",
            "--window-size=1920,1080", f"--screenshot={output}", build_slide_url(segment, state=state),
        ],
        timeout=40,
    )
    stream = media_info(output)["streams"][0]
    if (stream.get("width"), stream.get("height")) != (1920, 1080):
        raise RuntimeError(f"Unexpected slide size: {output}")
    return output


def render_slides() -> tuple[Path, ...]:
    output_dir = BUILD / "slides"
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for segment in SEGMENTS:
        if segment.kind != "slide":
            continue
        output = output_dir / f"{segment.id}.png"
        outputs.append(capture_slide(segment, output))
        if segment.id == "durability_zoom":
            for stage, state in enumerate(("durability-zoom-start", "durability-zoom-1", "durability-zoom-2")):
                staged = output_dir / f"durability_zoom-stage-{stage}.png"
                outputs.append(capture_slide(segment, staged, state=state))
    return tuple(outputs)


def render_demos() -> tuple[Path, ...]:
    output_dir = BUILD / "demos"
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for segment in SEGMENTS:
        if segment.kind != "demo":
            continue
        assert segment.source_id is not None
        source = SOURCE_VIDEOS[segment.source_id]
        if segment.source_start + segment.seconds > duration(source) + 0.05:
            raise RuntimeError(f"Requested clip exceeds source: {segment.id}")
        output = output_dir / f"{segment.id}.mp4"
        visual_filter = (
            "scale=1920:1080:force_original_aspect_ratio=decrease,"
            "pad=1920:1080:(ow-iw)/2:(oh-ih):color=0x061019,setsar=1,fps=30,"
            f"trim=duration={segment.seconds:.3f},setpts=PTS-STARTPTS"
        )
        run(
            [
                FFMPEG, "-y", "-ss", f"{segment.source_start:.3f}", "-i", str(source),
                "-t", f"{segment.seconds:.3f}", "-vf", visual_filter, "-an",
                "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
                "-r", "30", "-movflags", "+faststart", str(output),
            ]
        )
        info = media_info(output)
        stream = next(item for item in info["streams"] if item.get("codec_type") == "video")
        if (stream.get("width"), stream.get("height")) != (1920, 1080):
            raise RuntimeError(f"Unexpected demo size: {output}")
        outputs.append(output)
    return tuple(outputs)


def tts_part(edge_tts: Path, segment: Segment, index: int, part: VoicePart) -> tuple[Path, Path]:
    raw = BUILD / "narration/parts/raw"
    raw.mkdir(parents=True, exist_ok=True)
    media = raw / f"{segment.id}-{index:02d}.mp3"
    subtitle = raw / f"{segment.id}-{index:02d}.srt"
    stamp = raw / f"{segment.id}-{index:02d}.txt"
    signature = "\n".join((VOICE, part.rate, part.pitch, part.text))
    if media.is_file() and subtitle.is_file() and stamp.is_file() and stamp.read_text(encoding="utf-8") == signature:
        return media, subtitle
    command = [
        str(edge_tts), "--voice", VOICE, f"--rate={part.rate}", f"--pitch={part.pitch}",
        "--text", part.text, "--write-media", str(media), "--write-subtitles", str(subtitle),
    ]
    for attempt in range(5):
        media.unlink(missing_ok=True)
        subtitle.unlink(missing_ok=True)
        try:
            run(command, timeout=80)
            stamp.write_text(signature, encoding="utf-8")
            time.sleep(0.8)
            return media, subtitle
        except subprocess.CalledProcessError:
            if attempt == 4:
                raise
            time.sleep(2 + attempt * 2)
    raise RuntimeError("TTS retry logic unexpectedly ended")


def trim_voice(source: Path, output: Path) -> None:
    run(
        [
            FFMPEG, "-y", "-i", str(source), "-af",
            "areverse,silenceremove=start_periods=1:start_duration=0.06:start_threshold=-45dB:start_silence=0.06,areverse",
            "-c:a", "libmp3lame", "-b:a", "192k", str(output),
        ]
    )


def compose_voice_segment(segment: Segment, edge_tts: Path) -> tuple[Path, list[Cue]]:
    narration = BUILD / "narration"
    parts_dir = narration / "parts"
    parts_dir.mkdir(parents=True, exist_ok=True)
    trimmed: list[Path] = []
    durations: list[float] = []
    cues: list[Cue] = []
    cursor = 0.0
    for index, part in enumerate(segment.voice, 1):
        source, source_srt = tts_part(edge_tts, segment, index, part)
        output = parts_dir / f"{segment.id}-{index:02d}.mp3"
        trim_voice(source, output)
        clip_duration = duration(output)
        part_cues = parse_tts_srt(source_srt, clip_duration)
        if not part_cues:
            part_cues = [Cue(0.0, clip_duration, part.text)]
        cues.extend(Cue(cue.start + cursor, cue.end + cursor, cue.text) for cue in part_cues)
        trimmed.append(output)
        durations.append(clip_duration)
        cursor += clip_duration + part.pause_ms / 1000

    output = narration / f"{segment.id}.mp3"
    command = [FFMPEG, "-y"]
    graph = []
    labels = []
    for index, (path, clip_duration, part) in enumerate(zip(trimmed, durations, segment.voice, strict=True)):
        command.extend(["-i", str(path)])
        pause = part.pause_ms / 1000
        graph.append(
            f"[{index}:a]aresample=48000,aformat=channel_layouts=mono,"
            f"apad=pad_dur={pause:.3f},atrim=0:{clip_duration + pause:.3f}[p{index}]"
        )
        labels.append(f"[p{index}]")
    graph.append("".join(labels) + f"concat=n={len(labels)}:v=0:a=1[a]")
    command.extend(["-filter_complex", ";".join(graph), "-map", "[a]", "-c:a", "libmp3lame", "-b:a", "192k", str(output)])
    run(command)

    maximum = segment.seconds if segment is SEGMENTS[-1] else segment.seconds - TRANSITION_SECONDS
    voice_duration = duration(output)
    if voice_duration > maximum + 0.04:
        raise RuntimeError(f"Narration {segment.id} is {voice_duration:.2f}s; maximum is {maximum:.2f}s")
    if maximum - voice_duration > 4.8:
        raise RuntimeError(f"Narration {segment.id} leaves too much silence ({maximum - voice_duration:.2f}s)")
    return output, normalize_cues(cues)


def generate_audio() -> tuple[Path, ...]:
    edge_tts = locate_edge_tts()
    narration = BUILD / "narration"
    narration.mkdir(parents=True, exist_ok=True)
    all_cues: list[Cue] = []
    outputs = []
    for item in timeline():
        output, cues = compose_voice_segment(item.segment, edge_tts)
        outputs.append(output)
        all_cues.extend(Cue(cue.start + item.start, cue.end + item.start, cue.text) for cue in cues)

    subtitle_dir = BUILD / "subtitles"
    subtitle_dir.mkdir(parents=True, exist_ok=True)
    srt = subtitle_dir / "info-hud.zh-CN.srt"
    srt.write_text(cues_to_srt(all_cues), encoding="utf-8")

    command = [FFMPEG, "-y"]
    graph = []
    labels = []
    for index, item in enumerate(timeline()):
        command.extend(["-i", str(narration / f"{item.segment.id}.mp3")])
        delay = round(item.start * 1000)
        graph.append(f"[{index}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={delay}|{delay}[a{index}]")
        labels.append(f"[a{index}]")
    graph.append(
        "".join(labels)
        + f"amix=inputs={len(labels)}:duration=longest:normalize=0,apad=pad_dur={encoded_seconds():.3f},"
        + f"atrim=0:{encoded_seconds():.3f}[out]"
    )
    narration_mp3 = BUILD / "info-hud-narration.mp3"
    command.extend(["-filter_complex", ";".join(graph), "-map", "[out]", "-c:a", "libmp3lame", "-b:a", "192k", str(narration_mp3)])
    run(command)

    preview_sources = [narration / f"{name}.mp3" for name in ("hook", "durability_zoom", "neat")]
    preview = BUILD / "voice-preview.mp3"
    run(
        [
            FFMPEG, "-y", *sum((["-i", str(path)] for path in preview_sources), []),
            "-filter_complex", "[0:a][1:a][2:a]concat=n=3:v=0:a=1[a]", "-map", "[a]",
            "-c:a", "libmp3lame", "-b:a", "192k", str(preview),
        ]
    )
    return (*outputs, srt, narration_mp3, preview)


def motion_filter(motion: str) -> str:
    if motion == "still":
        return "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30"
    if motion == "push":
        return (
            "scale=2200:1238:force_original_aspect_ratio=increase,"
            "zoompan=z='min(zoom+0.00017,1.045)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=30"
        )
    if motion == "pull":
        return (
            "scale=2200:1238:force_original_aspect_ratio=increase,"
            "zoompan=z='if(eq(on,0),1.045,max(1.0,zoom-0.00017))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=30"
        )
    raise ValueError(f"Unknown motion: {motion}")


def render_durability_zoom_segment(segment: Segment, audio: Path, output: Path) -> Path:
    """Turn staged deck screenshots into the lens pop-in requested for the video."""
    stages = (
        BUILD / "slides/durability_zoom-stage-0.png",
        BUILD / "slides/durability_zoom-stage-1.png",
        BUILD / "slides/durability_zoom-stage-2.png",
        BUILD / "slides/durability_zoom.png",
    )
    stage_durations = (1.0, 0.8, 0.8, 5.0)
    if abs(sum(stage_durations) - 0.6 - segment.seconds) > 0.001:
        raise RuntimeError("Durability lens stage timing no longer matches its segment")
    if any(not stage.is_file() for stage in stages):
        raise RuntimeError("Render slides before building the durability lens segment")
    command = [FFMPEG, "-y"]
    for stage, seconds in zip(stages, stage_durations, strict=True):
        command.extend(["-loop", "1", "-framerate", "30", "-t", f"{seconds:.3f}", "-i", str(stage)])
    command.extend(["-i", str(audio)])
    graph = [f"[{index}:v]fps=30,format=yuv420p,setsar=1[v{index}]" for index in range(len(stages))]
    graph.extend(
        (
            "[v0][v1]xfade=transition=fade:duration=0.20:offset=0.80[x1]",
            "[x1][v2]xfade=transition=fade:duration=0.20:offset=1.40[x2]",
            "[x2][v3]xfade=transition=fade:duration=0.20:offset=2.00[v]",
            f"[4:a]aresample=48000,aformat=channel_layouts=stereo,apad=pad_dur={segment.seconds:.3f},atrim=0:{segment.seconds:.3f}[a]",
        )
    )
    command.extend(
        [
            "-filter_complex", ";".join(graph), "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-r", "30",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", str(output),
        ]
    )
    run(command)
    return output


def render_segments() -> tuple[Path, ...]:
    output_dir = BUILD / "segments"
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for segment in SEGMENTS:
        visual = BUILD / ("slides" if segment.kind == "slide" else "demos") / f"{segment.id}.{'png' if segment.kind == 'slide' else 'mp4'}"
        audio = BUILD / "narration" / f"{segment.id}.mp3"
        output = output_dir / f"{segment.id}.mp4"
        if segment.id == "durability_zoom":
            outputs.append(render_durability_zoom_segment(segment, audio, output))
            continue
        command = [FFMPEG, "-y"]
        if segment.kind == "slide":
            command.extend(["-loop", "1", "-framerate", "30"])
        command.extend(["-i", str(visual), "-i", str(audio), "-t", f"{segment.seconds:.3f}"])
        if segment.kind == "slide":
            visual_filter = motion_filter(segment.motion)
        else:
            visual_filter = f"fps=30,tpad=stop_mode=clone:stop_duration={segment.seconds:.3f},trim=duration={segment.seconds:.3f},setpts=PTS-STARTPTS"
        audio_filter = f"aresample=48000,aformat=channel_layouts=stereo,apad=pad_dur={segment.seconds:.3f},atrim=0:{segment.seconds:.3f}"
        command.extend(
            [
                "-filter_complex", f"[0:v]{visual_filter}[v];[1:a]{audio_filter}[a]", "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-r", "30",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", str(output),
            ]
        )
        run(command)
        outputs.append(output)
    return tuple(outputs)


def loudness_measurement(path: Path) -> dict[str, str]:
    result = run(
        [FFMPEG, "-hide_banner", "-nostats", "-i", str(path), "-map", "0:a:0", "-af", "loudnorm=I=-16:TP=-2:LRA=11:print_format=json", "-f", "null", "-"]
    )
    start = result.stderr.rfind("{")
    end = result.stderr.rfind("}")
    if start < 0 or end < start:
        raise RuntimeError("Could not parse loudness measurement")
    return json.loads(result.stderr[start : end + 1])


def compose_master() -> tuple[Path, Path]:
    paths = [BUILD / "segments" / f"{segment.id}.mp4" for segment in SEGMENTS]
    command = [FFMPEG, "-y"]
    for path in paths:
        command.extend(["-i", str(path)])
    graph = []
    video_input = "[0:v]"
    audio_input = "[0:a]"
    elapsed = SEGMENTS[0].seconds
    for index, segment in enumerate(SEGMENTS[1:], 1):
        video_output = f"[v{index}]"
        audio_output = f"[a{index}]"
        offset = elapsed - TRANSITION_SECONDS * index
        graph.append(f"{video_input}[{index}:v]xfade=transition=fade:duration={TRANSITION_SECONDS}:offset={offset:.3f}{video_output}")
        graph.append(f"{audio_input}[{index}:a]acrossfade=d={TRANSITION_SECONDS}:c1=tri:c2=tri{audio_output}")
        video_input = video_output
        audio_input = audio_output
        elapsed += segment.seconds
    master = BUILD / "segments/info-hud-bilibili-master.mp4"
    command.extend(
        [
            "-filter_complex", ";".join(graph), "-map", video_input, "-map", audio_input,
            "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-r", "30",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", str(master),
        ]
    )
    run(command)
    measurements = loudness_measurement(master)
    measured_filter = ":".join(
        [
            "loudnorm=I=-16", "TP=-2", "LRA=11", f"measured_I={measurements['input_i']}",
            f"measured_TP={measurements['input_tp']}", f"measured_LRA={measurements['input_lra']}",
            f"measured_thresh={measurements['input_thresh']}", f"offset={measurements['target_offset']}", "linear=true",
        ]
    )
    clean = BUILD / "info-hud-bilibili-clean.mp4"
    run(
        [
            FFMPEG, "-y", "-i", str(master), "-c:v", "copy", "-af", measured_filter,
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", str(clean),
        ]
    )
    return master, clean


def burn_subtitles(clean: Path) -> Path:
    subtitle = BUILD / "subtitles/info-hud.zh-CN.srt"
    output = BUILD / "info-hud-bilibili.mp4"
    style = "FontName=Noto Sans CJK SC,FontSize=25,PrimaryColour=&H00FFFFFF,OutlineColour=&H0010182A,BorderStyle=1,Outline=1.7,Shadow=0,Alignment=2,MarginV=50"
    run(
        [
            FFMPEG, "-y", "-i", str(clean), "-vf", f"subtitles={subtitle.as_posix()}:force_style='{style}'",
            "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", str(output),
        ]
    )
    return output


def create_contact_sheet() -> Path:
    output = BUILD / "final-contact.png"
    run(
        [
            FFMPEG, "-y", "-i", str(BUILD / "info-hud-bilibili.mp4"),
            "-vf", f"fps=9/{encoded_seconds():.3f},scale=480:270,tile=3x3", "-frames:v", "1", "-update", "1", str(output),
        ]
    )
    return output


def render_cover() -> tuple[Path, Path]:
    BUILD.mkdir(parents=True, exist_ok=True)
    cover_source = BUILD / "cover-source"
    cover_source.mkdir(parents=True, exist_ok=True)
    game = cover_source / "cover-game.jpg"
    furnace = cover_source / "jade-furnaces.jpg"
    run([FFMPEG, "-y", "-ss", "39.5", "-i", str(SOURCE_VIDEOS["jade"]), "-frames:v", "1", "-update", "1", "-q:v", "2", str(game)])
    run([FFMPEG, "-y", "-ss", "46", "-i", str(SOURCE_VIDEOS["jade"]), "-frames:v", "1", "-update", "1", "-q:v", "2", str(furnace)])
    raw = BUILD / "info-hud-cover-raw.png"
    png = BUILD / "info-hud-cover-1600x1200.png"
    jpg = BUILD / "info-hud-cover-1600x1200.jpg"
    run(
        [
            CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
            "--force-device-scale-factor=1", "--virtual-time-budget=800", "--window-size=1600,1287",
            f"--screenshot={raw}", (ROOT / "scripts/info_hud_video/cover-4x3.html").resolve().as_uri(),
        ],
        timeout=35,
    )
    run([FFMPEG, "-y", "-i", str(raw), "-vf", "crop=1600:1200:0:0", "-frames:v", "1", "-update", "1", str(png)])
    run([FFMPEG, "-y", "-i", str(png), "-frames:v", "1", "-update", "1", "-q:v", "2", str(jpg)])
    raw.unlink(missing_ok=True)
    return png, jpg


def write_publishing() -> tuple[Path, ...]:
    BUILD.mkdir(parents=True, exist_ok=True)
    outputs = {
        BUILD / "bilibili-title.txt": TITLE + "\n",
        BUILD / "bilibili-description.txt": description_text() + "\n",
        BUILD / "bilibili-tags.txt": "、".join(TAGS) + "\n",
        BUILD / "chapters.txt": "\n".join(chapter_lines()) + "\n",
        BUILD / "bilibili-publish.md": build_publish_markdown(),
    }
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8")
    return tuple(outputs)


def stream_of(info: dict, kind: str) -> dict:
    return next(stream for stream in info["streams"] if stream.get("codec_type") == kind)


def verify() -> dict[str, object]:
    required = (
        BUILD / "info-hud-bilibili-clean.mp4", BUILD / "info-hud-bilibili.mp4", BUILD / "info-hud-narration.mp3",
        BUILD / "voice-preview.mp3", BUILD / "subtitles/info-hud.zh-CN.srt", BUILD / "info-hud-cover-1600x1200.png",
        BUILD / "info-hud-cover-1600x1200.jpg", BUILD / "chapters.txt", BUILD / "bilibili-publish.md", BUILD / "final-contact.png",
    )
    missing = [str(path) for path in required if not path.is_file() or path.stat().st_size == 0]
    if missing:
        raise RuntimeError("Missing delivery files: " + ", ".join(missing))
    result: dict[str, object] = {"source_audio_policy": "Original game audio is muted; Yunxi narration is the sole spoken track."}
    for label, path in (("clean", BUILD / "info-hud-bilibili-clean.mp4"), ("release", BUILD / "info-hud-bilibili.mp4")):
        info = media_info(path)
        video = stream_of(info, "video")
        audio = stream_of(info, "audio")
        video_duration = float(info["format"]["duration"])
        if (
            video.get("codec_name") != "h264" or (video.get("width"), video.get("height")) != (1920, 1080)
            or video.get("r_frame_rate") != "30/1" or video.get("pix_fmt") != "yuv420p"
            or audio.get("codec_name") != "aac" or audio.get("sample_rate") != "48000"
            or abs(video_duration - encoded_seconds()) > 0.8
        ):
            raise RuntimeError(f"Invalid {label} media: {info}")
        result[label] = {"duration": video_duration, "size": "1920x1080", "fps": "30/1", "audio": "aac"}
    loudness = loudness_measurement(BUILD / "info-hud-bilibili.mp4")
    integrated = float(loudness["input_i"])
    true_peak = float(loudness["input_tp"])
    if not -17 <= integrated <= -15 or true_peak > -1:
        raise RuntimeError(f"Loudness outside target: I={integrated}, TP={true_peak}")
    result["loudness"] = {"integrated_lufs": integrated, "true_peak_dbtp": true_peak}
    generic = run(
        [
            "python3", str(SKILL_VERIFIER), "--video", str(BUILD / "info-hud-bilibili.mp4"),
            "--subtitle", str(BUILD / "subtitles/info-hud.zh-CN.srt"), "--cover", str(BUILD / "info-hud-cover-1600x1200.png"),
            "--chapters", str(BUILD / "chapters.txt"), "--publish", str(BUILD / "bilibili-publish.md"),
        ]
    )
    result["skill_verifier"] = json.loads(generic.stdout)
    (BUILD / "build-report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def all_steps() -> dict[str, object]:
    render_slides()
    render_demos()
    generate_audio()
    render_segments()
    _, clean = compose_master()
    burn_subtitles(clean)
    create_contact_sheet()
    render_cover()
    write_publishing()
    return verify()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("slides", "demos", "audio", "video", "cover", "publish", "verify", "all"))
    args = parser.parse_args()
    actions = {
        "slides": render_slides,
        "demos": render_demos,
        "audio": generate_audio,
        "video": lambda: (render_segments(), compose_master(), burn_subtitles(BUILD / "info-hud-bilibili-clean.mp4"), create_contact_sheet()),
        "cover": render_cover,
        "publish": write_publishing,
        "verify": verify,
        "all": all_steps,
    }
    result = actions[args.command]()
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str) if isinstance(result, dict) else result)


if __name__ == "__main__":
    main()
