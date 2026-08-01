"""FFmpeg assembly for the Xaero delivery.

The final segment is the supplied recording. Its video is fitted to the B站
canvas, while its original audio stream is carried through untouched until the
final delivery encode; no TTS narration is mixed over it.
"""

import json
from pathlib import Path
import subprocess

from scripts.xaero_video.storyboard import INTRO_SEGMENTS, Segment, all_segments


FFMPEG = "/usr/bin/ffmpeg"
LOUDNESS = "loudnorm=I=-16:TP=-2:LRA=11:print_format=json"
FIELDS = (("input_i", "measured_I"), ("input_tp", "measured_TP"), ("input_lra", "measured_LRA"), ("input_thresh", "measured_thresh"), ("target_offset", "offset"))


def probe(path: Path) -> dict:
    result = subprocess.run(["/usr/bin/ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def measure_loudness(path: Path) -> dict[str, str]:
    result = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-i", str(path), "-map", "0:a:0", "-af", LOUDNESS, "-f", "null", "-"], check=True, capture_output=True, text=True)
    start, end = result.stderr.rfind("{"), result.stderr.rfind("}")
    if start < 0 or end < start:
        raise RuntimeError("No loudness JSON returned")
    values = json.loads(result.stderr[start:end + 1])
    for field, _ in FIELDS:
        float(values[field])
    return values


def second_pass_filter(values: dict[str, str]) -> str:
    options = ["loudnorm=I=-16", "TP=-2", "LRA=11"]
    options.extend(f"{target}={values[field]}" for field, target in FIELDS)
    options.append("linear=true")
    return ":".join(options)


def render_slides(build_dir: Path, deck_path: Path) -> tuple[Path, ...]:
    slide_dir = build_dir / "slides"
    slide_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for segment in INTRO_SEGMENTS:
        output = slide_dir / f"{segment.id}.png"
        url = deck_path.resolve().as_uri() + f"?export=1&slide={segment.slide}"
        subprocess.run([
            "/usr/bin/google-chrome", "--headless", "--no-sandbox", "--disable-gpu",
            "--disable-dev-shm-usage", "--hide-scrollbars", "--allow-file-access-from-files",
            "--force-device-scale-factor=1", "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=1200", "--window-size=1920,1080", f"--screenshot={output}", url,
        ], check=True, timeout=30, capture_output=True)
        media = probe(output)
        stream = media["streams"][0]
        if (stream.get("width"), stream.get("height")) != (1920, 1080):
            raise RuntimeError(f"Unexpected slide dimensions: {output}: {stream}")
        outputs.append(output)
    return tuple(outputs)


def render_segments(build_dir: Path, source_video: Path, source_seconds: float) -> tuple[Path, ...]:
    output_dir = build_dir / "segments"
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for segment in all_segments(source_seconds):
        output = output_dir / f"{segment.id}.mp4"
        if segment.kind == "source":
            if output.is_file() and output.stat().st_mtime >= source_video.stat().st_mtime:
                outputs.append(output)
                continue
            graph = (
                "[0:v]scale=1728:1080:force_original_aspect_ratio=decrease,"
                "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x070b12,"
                "fps=30,setpts=PTS-STARTPTS[v];"
                f"[0:a]aresample=48000,aformat=channel_layouts=stereo,"
                f"apad=pad_dur={source_seconds:.3f},atrim=duration={source_seconds:.3f}[a]"
            )
            command = [
                FFMPEG, "-y", "-i", str(source_video), "-filter_complex", graph,
                "-map", "[v]", "-map", "[a]", "-t", f"{source_seconds:.3f}",
                "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
                "-r", "30", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                "-movflags", "+faststart", str(output),
            ]
        else:
            image = build_dir / "slides" / f"{segment.id}.png"
            audio = build_dir / "narration" / f"{segment.id}.mp3"
            graph = (
                "[0:v]scale=1920:1080,fps=30,format=yuv420p[v];"
                f"[1:a]aresample=48000,aformat=channel_layouts=stereo,"
                f"apad=pad_dur={segment.seconds:.3f},atrim=duration={segment.seconds:.3f}[a]"
            )
            command = [
                FFMPEG, "-y", "-loop", "1", "-framerate", "30", "-i", str(image),
                "-i", str(audio), "-filter_complex", graph, "-map", "[v]", "-map", "[a]",
                "-t", f"{segment.seconds:.3f}", "-c:v", "libx264", "-preset", "medium",
                "-crf", "17", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k",
                "-ar", "48000", "-ac", "2", "-movflags", "+faststart", str(output),
            ]
        subprocess.run(command, check=True, capture_output=True)
        outputs.append(output)
    return tuple(outputs)


def compose_master(build_dir: Path, source_seconds: float) -> Path:
    paths = [build_dir / "segments" / f"{segment.id}.mp4" for segment in all_segments(source_seconds)]
    command = [FFMPEG, "-y"]
    for path in paths:
        command.extend(["-i", str(path)])
    command.extend([
        "-filter_complex", f"concat=n={len(paths)}:v=1:a=1[v][a]", "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart",
        str(build_dir / "segments/xaero-bilibili-master.mp4"),
    ])
    subprocess.run(command, check=True, capture_output=True)
    master = build_dir / "segments/xaero-bilibili-master.mp4"
    measurements = measure_loudness(master)
    clean = build_dir / "xaero-bilibili-clean.mp4"
    subprocess.run([
        FFMPEG, "-y", "-i", str(master), "-c:v", "copy", "-af", second_pass_filter(measurements),
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", str(clean),
    ], check=True, capture_output=True)
    return clean


def burn_subtitles(build_dir: Path, clean: Path) -> Path:
    subtitle = build_dir / "subtitles/xaero.zh-CN.srt"
    output = build_dir / "xaero-bilibili.mp4"
    style = "FontName=Noto Sans CJK SC,FontSize=25,PrimaryColour=&H00FFFFFF,OutlineColour=&H0010182A,BorderStyle=1,Outline=1.7,Shadow=0,Alignment=2,MarginV=48"
    subprocess.run([
        FFMPEG, "-y", "-i", str(clean), "-vf", f"subtitles={subtitle.as_posix()}:force_style='{style}'",
        "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "copy", "-movflags", "+faststart", str(output),
    ], check=True, capture_output=True)
    return output


def create_contact_sheet(build_dir: Path, duration: float) -> Path:
    output = build_dir / "final-contact.png"
    subprocess.run([
        FFMPEG, "-y", "-i", str(build_dir / "xaero-bilibili.mp4"),
        "-vf", f"fps=9/{duration:g},scale=480:270,tile=3x3", "-frames:v", "1", "-update", "1", str(output),
    ], check=True, capture_output=True)
    return output
