"""FFmpeg composition for the Tweakeroo Bilibili release."""

import json
from pathlib import Path
import subprocess

from scripts.tweakeroo_video.storyboard import SEGMENTS, TRANSITION_SECONDS


FFMPEG = "/usr/bin/ffmpeg"
LOUDNESS_ANALYSIS_FILTER = (
    "loudnorm=I=-16:TP=-2:LRA=11:print_format=json"
)
_LOUDNESS_FIELDS = (
    ("input_i", "measured_I"),
    ("input_tp", "measured_TP"),
    ("input_lra", "measured_LRA"),
    ("input_thresh", "measured_thresh"),
    ("target_offset", "offset"),
)


def motion_filter(motion: str) -> str:
    filters = {
        "still": (
            "scale=1920:1080:force_original_aspect_ratio=increase,"
            "crop=1920:1080,fps=30"
        ),
        "push": (
            "scale=2200:1238:force_original_aspect_ratio=increase,"
            "zoompan=z='min(zoom+0.00018,1.045)':"
            "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            "d=1:s=1920x1080:fps=30"
        ),
        "pull": (
            "scale=2200:1238:force_original_aspect_ratio=increase,"
            "zoompan=z='if(eq(on,0),1.045,max(1.0,zoom-0.00018))':"
            "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            "d=1:s=1920x1080:fps=30"
        ),
    }
    try:
        return filters[motion]
    except KeyError as error:
        raise ValueError(f"Unknown motion: {motion}") from error


def build_transition_filter(
    durations: list[float],
    transition: float,
) -> tuple[str, str, str]:
    if len(durations) < 2:
        return "", "[0:v]", "[0:a]"

    transition_text = f"{transition:g}"
    parts = []
    video_in = "[0:v]"
    audio_in = "[0:a]"
    elapsed = durations[0]
    for index in range(1, len(durations)):
        video_out = f"[v{index}]"
        audio_out = f"[a{index}]"
        offset = elapsed - transition * index
        parts.append(
            f"{video_in}[{index}:v]"
            f"xfade=transition=fade:duration={transition_text}:"
            f"offset={offset:.3f}{video_out}"
        )
        parts.append(
            f"{audio_in}[{index}:a]"
            f"acrossfade=d={transition_text}:c1=tri:c2=tri{audio_out}"
        )
        video_in = video_out
        audio_in = audio_out
        elapsed += durations[index]
    return ";".join(parts), video_in, audio_in


def measure_loudness(path: Path) -> dict[str, str]:
    result = subprocess.run(
        [
            FFMPEG,
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-af",
            LOUDNESS_ANALYSIS_FILTER,
            "-f",
            "null",
            "-",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    start = result.stderr.rfind("{")
    end = result.stderr.rfind("}")
    if start < 0 or end < start:
        raise RuntimeError("FFmpeg loudness analysis did not return JSON")
    try:
        measurements = json.loads(result.stderr[start : end + 1])
        for field, _option in _LOUDNESS_FIELDS:
            float(measurements[field])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise RuntimeError(
            "FFmpeg loudness analysis returned invalid measurements"
        ) from error
    return measurements


def measured_loudnorm_filter(measurements: dict[str, str]) -> str:
    options = ["loudnorm=I=-16", "TP=-2", "LRA=11"]
    options.extend(
        f"{option}={measurements[field]}"
        for field, option in _LOUDNESS_FIELDS
    )
    options.append("linear=true")
    return ":".join(options)


def render_segments(build_dir: Path) -> tuple[Path, ...]:
    output_dir = build_dir / "segments"
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for index, segment in enumerate(SEGMENTS):
        image = build_dir / "slides" / f"{segment.id}.png"
        audio = build_dir / "narration" / f"{segment.id}.mp3"
        output = output_dir / f"{segment.id}.mp4"
        voice_filter = (
            f"aresample=48000,apad=pad_dur={segment.seconds},"
            f"atrim=0:{segment.seconds}"
        )
        chapter_start = (
            index == 0 or segment.chapter != SEGMENTS[index - 1].chapter
        )
        if chapter_start:
            audio_graph = (
                f"[1:a]{voice_filter}[voice];"
                "sine=frequency=760:sample_rate=48000:duration=0.08,"
                "volume=0.035[click];"
                "[voice][click]amix=inputs=2:duration=longest[a]"
            )
        else:
            audio_graph = f"[1:a]{voice_filter}[a]"
        subprocess.run(
            [
                FFMPEG,
                "-y",
                "-loop",
                "1",
                "-framerate",
                "30",
                "-i",
                str(image),
                "-i",
                str(audio),
                "-t",
                str(segment.seconds),
                "-filter_complex",
                f"[0:v]{motion_filter(segment.motion)}[v];{audio_graph}",
                "-map",
                "[v]",
                "-map",
                "[a]",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "17",
                "-pix_fmt",
                "yuv420p",
                "-r",
                "30",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-ar",
                "48000",
                "-ac",
                "2",
                "-movflags",
                "+faststart",
                str(output),
            ],
            check=True,
        )
        outputs.append(output)
    return tuple(outputs)


def compose_master(build_dir: Path) -> Path:
    paths = [
        build_dir / "segments" / f"{segment.id}.mp4"
        for segment in SEGMENTS
    ]
    graph, video_label, audio_label = build_transition_filter(
        [segment.seconds for segment in SEGMENTS],
        TRANSITION_SECONDS,
    )
    master = build_dir / "tweakeroo-bilibili-master.mp4"
    command = [FFMPEG, "-y"]
    for path in paths:
        command.extend(["-i", str(path)])
    command.extend(
        [
            "-filter_complex",
            graph,
            "-map",
            video_label,
            "-map",
            audio_label,
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "17",
            "-pix_fmt",
            "yuv420p",
            "-r",
            "30",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-movflags",
            "+faststart",
            str(master),
        ]
    )
    subprocess.run(command, check=True)

    measurements = measure_loudness(master)
    clean = build_dir / "tweakeroo-bilibili-clean.mp4"
    subprocess.run(
        [
            FFMPEG,
            "-y",
            "-i",
            str(master),
            "-c:v",
            "copy",
            "-af",
            measured_loudnorm_filter(measurements),
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-movflags",
            "+faststart",
            str(clean),
        ],
        check=True,
    )
    return clean


def burn_subtitles(build_dir: Path, clean: Path) -> Path:
    srt = build_dir / "subtitles/tweakeroo.zh-CN.srt"
    output = build_dir / "tweakeroo-bilibili.mp4"
    style = (
        "FontName=Noto Sans CJK SC,FontSize=20,"
        "PrimaryColour=&H00FFFFFF,OutlineColour=&H0010182A,"
        "BorderStyle=1,Outline=1.35,Shadow=0,Alignment=2,MarginV=30"
    )
    subprocess.run(
        [
            FFMPEG,
            "-y",
            "-i",
            str(clean),
            "-vf",
            f"subtitles={srt.as_posix()}:force_style='{style}'",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "17",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "copy",
            "-movflags",
            "+faststart",
            str(output),
        ],
        check=True,
    )
    return output


def create_contact_sheet(build_dir: Path) -> Path:
    output = build_dir / "final-contact.png"
    subprocess.run(
        [
            FFMPEG,
            "-y",
            "-i",
            str(build_dir / "tweakeroo-bilibili.mp4"),
            "-vf",
            "fps=1/17,scale=480:270,tile=4x3",
            "-frames:v",
            "1",
            "-update",
            "1",
            str(output),
        ],
        check=True,
    )
    return output
