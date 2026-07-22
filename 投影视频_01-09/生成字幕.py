from pathlib import Path
from faster_whisper import WhisperModel

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "原始视频"
OUT = ROOT / "字幕"
OUT.mkdir(exist_ok=True)

files = sorted(SRC.glob("*.mp4"))
LOCAL_MODEL = ROOT.parent / "build" / "itemscroller-video" / "models" / "models--Systran--faster-whisper-small" / "snapshots" / "536b0662742c02347bc0e980a01041f333bce120"
model = WhisperModel(str(LOCAL_MODEL) if LOCAL_MODEL.exists() else "small", device="cpu", compute_type="int8", cpu_threads=4)

def srt_time(seconds: float) -> str:
    ms = max(0, int(round(seconds * 1000)))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

all_segments = []
offset = 0.0
for path in files:
    print(f"Transcribing {path.name} at offset {offset:.3f}s", flush=True)
    if path.name.startswith("09"):
        # The supplied ninth clip has no audio; keep a chapter caption for it.
        all_segments.append((offset, offset + 6.0, "09｜配置投影公共目录"))
    else:
        segments, info = model.transcribe(
            str(path),
            language="zh",
            task="transcribe",
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=350),
            condition_on_previous_text=True,
            temperature=0.0,
        )
        for seg in segments:
            text = seg.text.strip()
            if text:
                all_segments.append((offset + seg.start, offset + seg.end, text))
    import av
    container = av.open(str(path))
    duration = float(container.duration / av.time_base) if container.duration else 0.0
    container.close()
    offset += duration

with (OUT / "投影教程_中文字幕.srt").open("w", encoding="utf-8") as f:
    for idx, (start, end, text) in enumerate(all_segments, 1):
        f.write(f"{idx}\n{srt_time(start)} --> {srt_time(max(end, start + 0.2))}\n{text}\n\n")
print(f"Wrote {len(all_segments)} subtitle entries")
