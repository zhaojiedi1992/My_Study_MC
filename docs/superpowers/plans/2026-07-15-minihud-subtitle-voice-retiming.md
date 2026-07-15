# MiniHUD Subtitle, Voice, and Retiming Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the MiniHUD Bilibili video with compact subtitles, a mature conversational male voice, and a tight timeline with no awkward post-speech pauses.

**Architecture:** Keep the existing storyboard-driven pipeline and eight-slide visual source. Change the immutable narration/timing data, voice profile, and subtitle ASS style in tracked code; add a production guard that rejects more than one second of tail silence; then regenerate only voice, video, chapters, subtitles, and contact-sheet artifacts under the ignored build directory.

**Tech Stack:** Python 3.11+ standard library, unittest, edge-tts 7.2.8, FFmpeg/ffprobe 6.x with libass 0.17.1, Google Chrome browser test, Sphinx.

## Global Constraints

- Preserve the six-scenario “遇到的问题 → 开什么功能 → 得到什么效果” structure and all existing Minecraft Java 26.2, MiniHUD, MaLiLib, Fabric Loader, Servux, TPS/MSPT, and Mob Cap accuracy constraints.
- Use a single `zh-CN-YunjianNeural` male voice at `rate=-2%` and `pitch=-2Hz`; use `zh-CN-YunxiNeural` only as an unavailable-voice fallback, never mixed into the same release.
- Keep every segment's audible tail silence between 0 and 1.0 seconds after accounting for the 0.25-second crossfade.
- Final encoded duration must be 180–195 seconds.
- Embedded subtitle style is exactly `FontName=Noto Sans CJK SC`, `FontSize=20`, `Outline=1.2`, `Alignment=2`, and `MarginV=26`.
- SRT cues remain non-overlapping, at most two lines, and at most 18 characters per line.
- Do not add background music, tease 15 shapes, change the cover, or introduce new screenshots.
- Generated voice, SRT, segment, MP4, contact-sheet, and publishing artifacts remain under ignored `build/minihud-video/`.

## File Structure

- Modify `scripts/minihud_video/audio.py` — conversational voice preference, prosody, and maximum-tail-silence production guard.
- Modify `scripts/minihud_video/storyboard.py` — exact conversational narration and 192.9-second encoded timeline.
- Modify `scripts/minihud_video/video.py` — compact libass subtitle style.
- Modify `tests/test_minihud_video.py` — TDD contracts for voice fallback, timings, tail silence, copy, and exact subtitle style.
- Regenerate `build/minihud-video/narration/**`, `segments/**`, `subtitles/**`, release MP4s, `final-contact.png`, and `bilibili-publish.md`.

---

### Task 1: Naturalize narration and eliminate padded dead air

**Files:**
- Modify: `tests/test_minihud_video.py`
- Modify: `scripts/minihud_video/audio.py`
- Modify: `scripts/minihud_video/storyboard.py`

**Interfaces:**
- Consumes: `Segment`, `TRANSITION_SECONDS`, `probe_duration()`, and the existing edge-tts CLI contract.
- Produces: `VOICES`, `RATE`, `PITCH`, `MAX_TAIL_SILENCE_SECONDS`, and the exact 19-item `SEGMENTS` tuple consumed by subtitle merging, video rendering, and publishing chapters.

- [ ] **Step 1: Write failing voice, timing, copy, and tail-silence tests**

Replace the current voice-choice test with:

```python
def test_choose_voice_prefers_yunjian_then_falls_back_to_yunxi(self):
    edge_tts = Path("edge-tts")
    cases = (
        (
            "zh-CN-YunxiNeural Male\nzh-CN-YunjianNeural Male\n",
            "zh-CN-YunjianNeural",
        ),
        ("zh-CN-YunxiNeural Male\n", "zh-CN-YunxiNeural"),
    )

    for voices, expected in cases:
        with self.subTest(expected=expected):
            with patch.object(
                audio.subprocess,
                "run",
                return_value=Mock(stdout=voices),
            ):
                self.assertEqual(audio.choose_voice(edge_tts), expected)
```

Add this focused production-guard test to `AudioTest`:

```python
def test_generate_voice_rejects_more_than_one_second_of_tail_silence(self):
    with TemporaryDirectory() as directory:
        with (
            patch.object(audio, "SEGMENTS", SEGMENTS[:1]),
            patch.object(audio, "choose_voice", return_value=audio.VOICES[0]),
            patch.object(audio, "probe_duration", return_value=3.1),
            patch.object(audio.subprocess, "run", return_value=Mock()),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                r"hook-structure.*1\.20s.*1\.00s",
            ):
                audio.generate_voice(Path(directory), Path("edge-tts"))
```

Update the command assertions in `test_generate_voice_creates_all_artifacts_with_fixed_prosody`:

```python
self.assertIn("--rate=-2%", command)
self.assertIn("--pitch=-2Hz", command)
```

Update the three duration-boundary fixtures so they still exercise the new first-segment and encoded limits:

```python
# test_generate_voice_rejects_segment_srt_past_crossfade_budget
"1\n00:00:00,100 --> 00:00:04,100\n越界字幕\n"
# expected allowed end in regex: r"hook-structure.*4\.05"

# test_generate_voice_rejects_narration_past_crossfade_budget
patch.object(audio, "probe_duration", return_value=4.06)
# expected regex: r"hook-structure.*4\.06s.*4\.05s"

# test_generate_voice_rejects_merged_srt_past_encoded_timeline
patch.object(audio, "timeline", return_value=(Mock(start=192.8),))
# expected regex: r"Merged subtitles.*193\.00"
```

Because the new guard runs before reading the generated SRT, replace the old
`probe_duration(..., return_value=0.2)` mocks in the downstream SRT tests with
durations that leave a valid tail:

```python
# test_generate_voice_rejects_empty_segment_srt
patch.object(audio, "probe_duration", return_value=3.5)

# test_generate_voice_rejects_segment_srt_past_crossfade_budget
patch.object(audio, "probe_duration", return_value=3.5)

# test_generate_voice_rejects_merged_srt_past_encoded_timeline
patch.object(audio, "probe_duration", return_value=12.5)

# test_generate_voice_creates_all_artifacts_with_fixed_prosody
mock_durations = [
    segment.seconds
    - (TRANSITION_SECONDS if index < len(SEGMENTS) - 1 else 0)
    - 0.5
    for index, segment in enumerate(SEGMENTS)
]
# use patch.object(audio, "probe_duration", side_effect=mock_durations)
```

Replace `StoryboardTest.test_storyboard_has_exact_timing_and_unique_ids` and its timing-sensitive assertions with:

```python
def test_storyboard_has_exact_timing_and_unique_ids(self):
    self.assertEqual(len(SEGMENTS), 19)
    self.assertEqual(len({segment.id for segment in SEGMENTS}), 19)
    self.assertEqual(
        tuple(segment.seconds for segment in SEGMENTS),
        (
            4.3, 4.1, 4.5, 11.6, 12.4, 10.5, 13.9, 20.0, 8.3,
            13.7, 6.3, 5.6, 11.4, 9.3, 10.6, 12.9, 11.8, 13.2, 13.0,
        ),
    )
    self.assertAlmostEqual(total_base_seconds(), 197.4, places=3)
    self.assertAlmostEqual(encoded_seconds(), 192.9, places=3)
    self.assertTrue(180 <= encoded_seconds() <= 195)
    self.assertEqual(TRANSITION_SECONDS, 0.25)

def test_narration_matches_approved_scope(self):
    copy = "".join(segment.narration for segment in SEGMENTS)
    timing_sensitive_copy = {
        segment.id: segment.narration
        for segment in SEGMENTS
        if segment.id in {"hook-structure", "hook-shape", "range-spawn"}
    }
    self.assertEqual(
        timing_sensitive_copy,
        {
            "hook-structure": "结构被挡，看不清范围？",
            "hook-shape": "圆心半径，还靠目测？",
            "range-spawn": "刷怪距离看球形范围，挂机点会直观很多。",
        },
    )
    self.assertEqual(len(copy), 847)
    for phrase in (
        "问题", "Servux", "按住 Shift", "Mob Cap 是数量上限",
        "先收藏", "实用的 Minecraft 模组和生存技巧",
    ):
        self.assertIn(phrase, copy)
    for forbidden in ("15 种", "下一期", "自动建造", "服务器许可"):
        self.assertNotIn(forbidden, copy)

def test_timeline_accounts_for_crossfades(self):
    items = timeline()
    self.assertEqual(items[0].start, 0)
    self.assertAlmostEqual(items[1].start, 4.05, places=3)
    self.assertAlmostEqual(items[-1].end, 192.9, places=3)
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```bash
python3 -m unittest \
  tests.test_minihud_video.AudioTest.test_choose_voice_prefers_yunjian_then_falls_back_to_yunxi \
  tests.test_minihud_video.AudioTest.test_generate_voice_rejects_more_than_one_second_of_tail_silence \
  tests.test_minihud_video.AudioTest.test_generate_voice_creates_all_artifacts_with_fixed_prosody \
  tests.test_minihud_video.StoryboardTest -v
```

Expected: FAIL because the preferred voices/prosody, tail-silence guard, narration, and 192.9-second timeline are not implemented.

- [ ] **Step 3: Implement the voice profile and tail-silence guard**

At the top of `scripts/minihud_video/audio.py`, use:

```python
VOICES = ("zh-CN-YunjianNeural", "zh-CN-YunxiNeural")
RATE = "-2%"
PITCH = "-2Hz"
MAX_TAIL_SILENCE_SECONDS = 1.0
CAPTION_WIDTH = 18
MAX_CAPTION_LINES = 2
```

Immediately after the existing `duration > allowed` rejection in `generate_voice()`, add:

```python
tail_silence = allowed - duration
if tail_silence > MAX_TAIL_SILENCE_SECONDS + 1e-9:
    raise RuntimeError(
        f"Narration {segment.id} leaves {tail_silence:.2f}s of tail "
        f"silence; maximum is {MAX_TAIL_SILENCE_SECONDS:.2f}s"
    )
```

- [ ] **Step 4: Replace the storyboard with the measured conversational copy and durations**

Keep `Segment`, `TimelineItem`, and all helper functions unchanged. Replace only `SEGMENTS` with:

```python
SEGMENTS = (
    Segment("hook-structure", "冷开场", 4.3, 4, "structure:on", "push", "结构被挡，看不清范围？"),
    Segment("hook-shape", "冷开场", 4.1, 7, "shape:basic", "pull", "圆心半径，还靠目测？"),
    Segment("hook-preview", "冷开场", 4.5, 8, "base:shulker", "push", "潜影盒，还要挨个打开确认？"),
    Segment("intro", "MiniHUD 是什么", 11.6, 1, "default", "push", "这就是 MiniHUD。它不替你建造，也不帮你找结构，只把原本看不见的信息、边界和范围，直接画进游戏画面。"),
    Segment("problem-map", "使用方法", 12.4, 2, "default", "still", "不用背菜单。遇到什么问题，就开对应功能。默认按 H 控制总渲染，按 H 加 C 进入配置；快捷键也可以改。"),
    Segment("info-explore", "日常信息", 10.5, 3, "info:explore", "push", "出门怕迷路，就开坐标、朝向、群系和时间。要回基地时，先设个参考点，再看距离。"),
    Segment("info-performance", "日常信息", 13.9, 3, "info:performance", "pull", "游戏卡顿时，别把所有数字都堆上去。FPS 看客户端；延迟、TPS 和 MSPT 看联机状态。精确数据，还得看服务器支持。"),
    Segment("structure", "结构边界", 20.0, 4, "structure:on", "push", "结构被海水或山体挡住时，打开结构主边界和组成部分，就能看清整体和内部。注意，它只显示已有数据，不会远程找结构，也不会调用 locate。单人读取本地数据；多人服需要 Servux 提供结构数据。"),
    Segment("site-biome", "工程选址", 8.3, 5, "site:biome", "pull", "准备建基地或农场，先看群系和区块边界，确认工程有没有跨过关键区域。"),
    Segment("site-guide", "工程选址", 13.7, 5, "site:guide", "push", "担心刷怪，就按需要检查光照。一次只开一层：看见问题，现场处理，关闭复查。低光照只是条件之一，不代表一定刷怪。"),
    Segment("range-device", "机制范围", 6.3, 6, "range:beacon", "push", "信标、潮涌核心这类装置，适合看盒状覆盖边界。"),
    Segment("range-spawn", "机制范围", 5.6, 6, "range:spawn", "pull", "刷怪距离看球形范围，挂机点会直观很多。"),
    Segment("range-chunk", "机制范围", 11.4, 6, "range:chunk", "still", "随机刻和出生区块看网格。二十四、三十二、一百二十八格只是常见参考，具体规则还要看版本和生物。"),
    Segment("build-basic", "施工规划", 9.3, 7, "shape:basic", "push", "圆心、半径和占地不好确定，就用圆形、圆柱或方框，先把施工参考线画进世界。"),
    Segment("build-spawn", "施工规划", 10.6, 7, "shape:spawn", "pull", "需要判断高度或生成空间，再切换球体和生成球。它们只帮助检查，不会自动放置或拆除方块。"),
    Segment("base-preview", "基地管理", 12.9, 8, "base:shulker", "push", "回到基地，默认按住 Shift 悬停，就能预览潜影盒、收纳袋、地图或支持的容器内容，少开很多界面。触发方式也能改。"),
    Segment("base-efficiency", "基地管理", 11.8, 8, "base:efficiency", "pull", "机器效率不对，再查看光照、生成距离、Mob Cap、实体数量、延迟和 TPS。Mob Cap 是数量上限，不是空间范围。"),
    Segment("install", "安装与限制", 13.2, 2, "video:install", "still", "安装记住三样：Fabric Loader，加上版本匹配的 MiniHUD 和 MaLiLib。两个模组都装客户端；多人服的结构数据，需要服务器端 Servux 支持。"),
    Segment("outro", "收藏与关注", 13.0, 8, "video:outro", "push", "遇到这六类问题，就回来按清单找功能。觉得有用，先收藏；也欢迎关注我，继续分享实用的 Minecraft 模组和生存技巧。"),
)
```

- [ ] **Step 5: Run the focused and full Python tests**

Run:

```bash
python3 -m unittest tests.test_minihud_video.AudioTest tests.test_minihud_video.StoryboardTest -v
python3 -m unittest tests.test_minihud_video -v
```

Expected: all tests PASS, including the updated duration-boundary cases and new tail-silence guard.

- [ ] **Step 6: Commit Task 1**

```bash
git add -- scripts/minihud_video/audio.py scripts/minihud_video/storyboard.py tests/test_minihud_video.py
git commit -m "feat: naturalize MiniHUD narration timing"
```

---

### Task 2: Shrink the embedded subtitles without weakening readability

**Files:**
- Modify: `tests/test_minihud_video.py`
- Modify: `scripts/minihud_video/video.py`

**Interfaces:**
- Consumes: the merged SRT at `build/minihud-video/subtitles/minihud-bilibili.zh-CN.srt`.
- Produces: `burn_subtitles(build_dir: Path, clean: Path) -> Path` with an exact compact libass style and unchanged clean audio.

- [ ] **Step 1: Write an exact failing subtitle-style test**

In `test_subtitle_release_uses_readable_style_and_clean_audio`, replace substring-only style checks with:

```python
self.assertIn("subtitles=", subtitle_filter)
style_source = subtitle_filter.split("force_style='", 1)[1].rsplit("'", 1)[0]
style = dict(item.split("=", 1) for item in style_source.split(","))
self.assertEqual(style["FontName"], "Noto Sans CJK SC")
self.assertEqual(style["FontSize"], "20")
self.assertEqual(style["Outline"], "1.2")
self.assertEqual(style["Alignment"], "2")
self.assertEqual(style["MarginV"], "26")
self.assertEqual(command[command.index("-c:a") + 1], "copy")
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
python3 -m unittest tests.test_minihud_video.VideoFilterTest.test_subtitle_release_uses_readable_style_and_clean_audio -v
```

Expected: FAIL because the current style is still `FontSize=30`, `Outline=1.5`, and `MarginV=44` after the first insufficient reduction.

- [ ] **Step 3: Implement the compact style**

In `burn_subtitles()`, set:

```python
style = (
    "FontName=Noto Sans CJK SC,FontSize=20,"
    "PrimaryColour=&H00FFFFFF,OutlineColour=&H0010182A,"
    "BorderStyle=1,Outline=1.2,Shadow=0,Alignment=2,MarginV=26"
)
```

Do not add a background box or change the `-c:a copy` audio path.

- [ ] **Step 4: Run the focused and full Python tests**

Run:

```bash
python3 -m unittest tests.test_minihud_video.VideoFilterTest.test_subtitle_release_uses_readable_style_and_clean_audio -v
python3 -m unittest tests.test_minihud_video -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit Task 2**

```bash
git add -- scripts/minihud_video/video.py tests/test_minihud_video.py
git commit -m "fix: reduce MiniHUD subtitle obstruction"
```

---

### Task 3: Regenerate the voice, releases, subtitles, chapters, and contact sheet

**Files:**
- Regenerate: `build/minihud-video/narration/**`
- Regenerate: `build/minihud-video/segments/**`
- Regenerate: `build/minihud-video/subtitles/minihud-bilibili.zh-CN.srt`
- Regenerate: `build/minihud-video/minihud-bilibili-master.mp4`
- Regenerate: `build/minihud-video/minihud-bilibili-clean.mp4`
- Regenerate: `build/minihud-video/minihud-bilibili.mp4`
- Regenerate: `build/minihud-video/final-contact.png`
- Regenerate: `build/minihud-video/bilibili-publish.md`
- Preserve: `build/minihud-video/minihud-cover-1600x1000.png`
- Preserve: `build/minihud-video/minihud-cover-1600x1000.jpg`

**Interfaces:**
- Consumes: committed `SEGMENTS`, `VOICES`, `RATE`, `PITCH`, and subtitle style.
- Produces: the final ignored Bilibili delivery artifacts and updated chapter clocks.

- [ ] **Step 1: Record the unchanged cover hashes and confirm voice/font availability**

Run:

```bash
sha256sum \
  build/minihud-video/minihud-cover-1600x1000.png \
  build/minihud-video/minihud-cover-1600x1000.jpg \
  > /tmp/minihud-cover-before.sha256
build/minihud-video/.venv/bin/edge-tts --list-voices | rg 'zh-CN-(Yunjian|Yunxi)Neural'
fc-match 'Noto Sans CJK SC'
```

Expected: both male voices are listed, the font resolves to a Noto Sans CJK file, and the cover hashes are recorded.

- [ ] **Step 2: Generate the new voice and SRT**

Run:

```bash
python3 -m scripts.minihud_video.pipeline voice
```

Expected: 19 MP3 and 19 segment SRT paths are printed; no duration or tail-silence exception occurs.

- [ ] **Step 3: Audit every generated tail before encoding video**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
from scripts.minihud_video.audio import MAX_TAIL_SILENCE_SECONDS, probe_duration
from scripts.minihud_video.storyboard import SEGMENTS, TRANSITION_SECONDS

for index, segment in enumerate(SEGMENTS):
    duration = probe_duration(
        Path("build/minihud-video/narration") / f"{segment.id}.mp3"
    )
    allowed = (
        segment.seconds
        if index == len(SEGMENTS) - 1
        else segment.seconds - TRANSITION_SECONDS
    )
    tail = allowed - duration
    assert 0 <= tail <= MAX_TAIL_SILENCE_SECONDS, (segment.id, duration, tail)
    print(f"{segment.id:20} voice={duration:6.3f}s tail={tail:5.3f}s")
PY
```

Expected: every printed tail is between `0.000s` and `1.000s`.

- [ ] **Step 4: Rebuild all video variants and publishing chapters**

Run:

```bash
python3 -m scripts.minihud_video.pipeline video
python3 -m scripts.minihud_video.pipeline publish
```

Expected: 19 segments, the master, normalized clean release, compact-subtitle release, contact sheet, and publishing Markdown are regenerated. The video step may take several minutes.

- [ ] **Step 5: Prove the cover was not changed**

Run:

```bash
sha256sum -c /tmp/minihud-cover-before.sha256
```

Expected: both cover files report `OK`.

---

### Task 4: Perform full technical and visual acceptance

**Files:**
- Verify: all tracked sources and tests
- Verify: all eight required files under `build/minihud-video/`

**Interfaces:**
- Consumes: the regenerated Task 3 package.
- Produces: evidence that the revised package is ready for the user.

- [ ] **Step 1: Run all source verification**

Run:

```bash
python3 -m unittest discover -s tests -v
node tests/minihud_presentation_browser_test.cjs
python3 -m sphinx -b html source build/html
git diff --check
```

Expected: all Python tests pass; browser JSON ends with `errors: []`; Sphinx exits 0 with `build succeeded`; `git diff --check` prints nothing.

- [ ] **Step 2: Probe both release streams and duration**

Run separately for `minihud-bilibili.mp4` and `minihud-bilibili-clean.mp4`:

```bash
ffprobe -v error \
  -show_entries format=duration:stream=codec_name,width,height,r_frame_rate,sample_rate,channels \
  -of json build/minihud-video/minihud-bilibili.mp4
ffprobe -v error \
  -show_entries format=duration:stream=codec_name,width,height,r_frame_rate,sample_rate,channels \
  -of json build/minihud-video/minihud-bilibili-clean.mp4
```

Expected for both: H.264 `1920x1080`, `30/1`; AAC `48000`, two channels; duration between 180 and 195 seconds and approximately 192.9 seconds.

- [ ] **Step 3: Verify loudness and subtitles**

Run:

```bash
ffmpeg -hide_banner -i build/minihud-video/minihud-bilibili.mp4 \
  -filter_complex ebur128=peak=true -f null -
python3 - <<'PY'
from pathlib import Path
import re
from scripts.minihud_video.audio import parse_srt

path = Path("build/minihud-video/subtitles/minihud-bilibili.zh-CN.srt")
source = path.read_text(encoding="utf-8")
cues = parse_srt(source, "production SRT")
assert all(left.end <= right.start for left, right in zip(cues, cues[1:]))
# parse_srt() intentionally normalizes cue lines for semantic parsing; inspect
# the raw blocks for the display-layout contract instead.
for block in re.split(r"\n\s*\n", source.strip()):
    lines = block.splitlines()
    timing_index = next(i for i, line in enumerate(lines) if "-->" in line)
    caption_lines = lines[timing_index + 1 :]
    assert 1 <= len(caption_lines) <= 2
    assert all(len(line) <= 18 for line in caption_lines)
assert "按住 Shift" in source
print(f"cues={len(cues)} max_end={cues[-1].end:.3f}s")
PY
```

Expected: integrated loudness within one LU of `-16 LUFS`, true peak no higher than `-1 dBFS`, parsed cues are chronological/non-overlapping, and every raw SRT block is at most two lines of 18 characters.

- [ ] **Step 4: Inspect compact subtitles on representative full-resolution frames**

Generate ten frames that cover every chapter after the hook:

```bash
mkdir -p /tmp/minihud-subtitle-audit
ffmpeg -hide_banner -loglevel error -y -ss 13.5  -i build/minihud-video/minihud-bilibili.mp4 -frames:v 1 /tmp/minihud-subtitle-audit/01-intro.png
ffmpeg -hide_banner -loglevel error -y -ss 25.0  -i build/minihud-video/minihud-bilibili.mp4 -frames:v 1 /tmp/minihud-subtitle-audit/02-method.png
ffmpeg -hide_banner -loglevel error -y -ss 37.5  -i build/minihud-video/minihud-bilibili.mp4 -frames:v 1 /tmp/minihud-subtitle-audit/03-info.png
ffmpeg -hide_banner -loglevel error -y -ss 61.0  -i build/minihud-video/minihud-bilibili.mp4 -frames:v 1 /tmp/minihud-subtitle-audit/04-structure.png
ffmpeg -hide_banner -loglevel error -y -ss 81.5  -i build/minihud-video/minihud-bilibili.mp4 -frames:v 1 /tmp/minihud-subtitle-audit/05-site.png
ffmpeg -hide_banner -loglevel error -y -ss 104.0 -i build/minihud-video/minihud-bilibili.mp4 -frames:v 1 /tmp/minihud-subtitle-audit/06-range.png
ffmpeg -hide_banner -loglevel error -y -ss 127.0 -i build/minihud-video/minihud-bilibili.mp4 -frames:v 1 /tmp/minihud-subtitle-audit/07-build.png
ffmpeg -hide_banner -loglevel error -y -ss 145.5 -i build/minihud-video/minihud-bilibili.mp4 -frames:v 1 /tmp/minihud-subtitle-audit/08-base.png
ffmpeg -hide_banner -loglevel error -y -ss 169.0 -i build/minihud-video/minihud-bilibili.mp4 -frames:v 1 /tmp/minihud-subtitle-audit/09-install.png
ffmpeg -hide_banner -loglevel error -y -ss 181.5 -i build/minihud-video/minihud-bilibili.mp4 -frames:v 1 /tmp/minihud-subtitle-audit/10-outro.png
```

Inspect these ten images and `build/minihud-video/final-contact.png` at original resolution. Accept only if subtitles remain in the lower band, do not enter the central title area, and do not cover the highlighted boundary, crosshair, key settings text, or primary screenshot focal point.

- [ ] **Step 5: Verify chapters, deliverables, and repository state**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
from scripts.minihud_video.publishing import build_publish_markdown

root = Path("build/minihud-video")
required = (
    root / "minihud-bilibili.mp4",
    root / "minihud-bilibili-clean.mp4",
    root / "minihud-bilibili-master.mp4",
    root / "subtitles/minihud-bilibili.zh-CN.srt",
    root / "minihud-cover-1600x1000.png",
    root / "minihud-cover-1600x1000.jpg",
    root / "bilibili-publish.md",
    root / "final-contact.png",
)
assert all(path.is_file() and path.stat().st_size > 0 for path in required)
assert (root / "bilibili-publish.md").read_text(encoding="utf-8") == build_publish_markdown()
print("delivery-files=8/8")
PY
git status --short --branch
git log --oneline -n 5
```

Expected: `delivery-files=8/8`; publishing chapters include the revised starts near `00:12`, `00:23`, `00:59`, `01:40`, `02:22`, `02:46`, and `02:59`; no tracked working-tree changes remain.

- [ ] **Step 6: Request final read-only review and hand off the revised package**

Generate a review package from commit `1d0da3f` to the final source HEAD, dispatch a whole-change reviewer against the approved design, resolve any Critical or Important findings, and report the final MP4, clean MP4, cover, publishing guide, and SRT paths to the user.
