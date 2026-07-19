# Tweakeroo Bilibili Video Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a verified 200-second Tweakeroo Bilibili package with a high-click cover, natural conversational Chinese narration, independent subtitles, a clean master, a captioned release, and complete publishing copy.

**Architecture:** Keep the approved `source/MOD介绍/tweakeroo/index.html` as the only slide source. Create an isolated `scripts/tweakeroo_video/` build package whose storyboard is the single source of truth for narration, slide states, timing, chapters, subtitles, audio, and video assembly; all generated media remains under ignored `build/tweakeroo-video/`.

**Tech Stack:** Python 3.12 standard library, `unittest`, Google Chrome headless, Edge TTS 7.2.8, FFmpeg/ffprobe 6.1, HTML/CSS, H.264/AAC.

## Global Constraints

- The feature order is fixed: 灵魂出窍 → 自动切换鞘翅与胸甲 → 自动补货 → 快速左右键 → Gamma.
- The encoded target is 200 seconds, with an accepted range of 196–205 seconds.
- Use only the ten supplied 2880×1800 PNG screenshots and the approved eight-slide deck; do not overwrite or downsample the source files.
- Default video frames preserve screenshots with `object-fit: contain`; only approved configuration states may zoom into a setting row.
- The title is `Tweakeroo 不只会灵魂出窍！自动补货、换胸甲这 5 个功能真省事`.
- The cover headline is `别再手动了！`, with `Tweakeroo · 5 个高频功能` visible at feed size.
- Narration prefers `zh-CN-YunxiNeural`, rate `-2%`, pitch `0Hz`; fallbacks are Yunyang and Yunjian.
- Generate and obtain user approval for `voice-preview.mp3` before rendering the complete narration.
- Captions are Simplified Chinese, at most two lines and about 18 characters per line; keep Latin product names intact.
- Video is 1920×1080, 30 fps, H.264; audio is AAC, about -16 LUFS, with true peak no higher than -1 dBTP.
- Do not add unlicensed music. Use clear voice and restrained generated click cues only.
- Do not modify or commit the existing dirty MiniHUD files, `.gitignore`, or unrelated user changes.
- Generated screenshots, audio, covers, and videos go only under `build/tweakeroo-video/` and remain untracked.

## File Structure

- Create `scripts/tweakeroo_video/__init__.py` — package marker.
- Create `scripts/tweakeroo_video/storyboard.py` — immutable segment data and timeline calculations.
- Create `scripts/tweakeroo_video/audio.py` — TTS, SRT parsing/wrapping, preview, merged captions, and narration-only export.
- Create `scripts/tweakeroo_video/video.py` — motion, segment encoding, transitions, loudness normalization, subtitle burn-in, and contact sheet.
- Create `scripts/tweakeroo_video/publishing.py` — synchronized Bilibili title, description, chapters, tags, and pinned comment.
- Create `scripts/tweakeroo_video/pipeline.py` — CLI orchestration and media probing.
- Create `scripts/tweakeroo_video/cover.html` — deterministic 1600×1000 cover.
- Create `scripts/tweakeroo_video/cover-4x3.html` — deterministic 1600×1200 cover.
- Create `tests/test_tweakeroo_video.py` — unit and static production-contract tests.
- Generate `build/tweakeroo-video/**` — ignored production artifacts.

---

### Task 1: Storyboard, conversational narration, and deterministic timeline

**Files:**
- Create: `scripts/tweakeroo_video/__init__.py`
- Create: `scripts/tweakeroo_video/storyboard.py`
- Create: `tests/test_tweakeroo_video.py`

**Interfaces:**
- Produces: `Segment`, `TimelineItem`, `SEGMENTS`, `TRANSITION_SECONDS`, `PREVIEW_SEGMENT_IDS`, `total_base_seconds()`, `encoded_seconds()`, `timeline()`, and `render_requests()`.
- Consumers: Tasks 2–6 import these exact names.

- [ ] **Step 1: Write the failing storyboard contract**

Create `tests/test_tweakeroo_video.py` with:

```python
from pathlib import Path
import unittest

from scripts.tweakeroo_video.storyboard import (
    PREVIEW_SEGMENT_IDS,
    SEGMENTS,
    encoded_seconds,
    render_requests,
    timeline,
    total_base_seconds,
)


ROOT = Path(__file__).resolve().parents[1]


class StoryboardTest(unittest.TestCase):
    def test_timeline_is_exactly_two_hundred_seconds(self):
        self.assertEqual(len(SEGMENTS), 20)
        self.assertAlmostEqual(total_base_seconds(), 204.75)
        self.assertAlmostEqual(encoded_seconds(), 200.0)
        self.assertAlmostEqual(timeline()[0].start, 0.0)
        self.assertAlmostEqual(timeline()[-1].end, 200.0)

    def test_hook_and_feature_order_are_fixed(self):
        self.assertEqual(
            [segment.id for segment in SEGMENTS[:3]],
            ["hook-soul", "hook-restock", "hook-gamma"],
        )
        chapters = []
        for segment in SEGMENTS:
            if segment.chapter not in chapters:
                chapters.append(segment.chapter)
        for expected in (
            "灵魂出窍",
            "鞘翅与胸甲",
            "自动补货",
            "快速左右键",
            "Gamma 亮度",
        ):
            self.assertIn(expected, chapters)
        feature_order = (
            "灵魂出窍",
            "鞘翅与胸甲",
            "自动补货",
            "快速左右键",
            "Gamma 亮度",
        )
        positions = [chapters.index(name) for name in feature_order]
        self.assertEqual(positions, sorted(positions))

    def test_copy_contains_conversion_and_safety_contract(self):
        copy = "".join(segment.narration for segment in SEGMENTS)
        for phrase in (
            "不念配置表",
            "翻译成人话",
            "快捷键",
            "服务器规则",
            "刷怪规则",
            "关注我",
        ):
            self.assertIn(phrase, copy)
        self.assertNotIn("三连", copy)
        self.assertNotIn("必装", copy)

    def test_preview_exercises_hook_explanation_and_joke(self):
        self.assertEqual(
            PREVIEW_SEGMENT_IDS,
            ("hook-soul", "soul-effect", "gamma-on"),
        )

    def test_render_requests_have_valid_deck_states(self):
        requests = render_requests()
        self.assertEqual(len(requests), len(SEGMENTS))
        required = {
            (2, "config"), (2, "effect"),
            (3, "auto"), (3, "chestplate"),
            (4, "config"), (4, "threshold"), (4, "done"),
            (5, "left"), (5, "right"),
            (6, "config"), (6, "off"), (6, "on"),
        }
        self.assertTrue(required.issubset(
            {(item["slide"], item["state"]) for item in requests}
        ))
```

- [ ] **Step 2: Run the targeted test and verify the import fails**

Run:

```bash
python -m unittest tests.test_tweakeroo_video.StoryboardTest -v
```

Expected: `ModuleNotFoundError: No module named 'scripts.tweakeroo_video'`.

- [ ] **Step 3: Implement the immutable storyboard**

Create an empty `scripts/tweakeroo_video/__init__.py`, then create `scripts/tweakeroo_video/storyboard.py` with this data and the same timeline math used by the tested MiniHUD pipeline:

```python
from dataclasses import dataclass


TRANSITION_SECONDS = 0.25
PREVIEW_SEGMENT_IDS = ("hook-soul", "soul-effect", "gamma-on")


@dataclass(frozen=True)
class Segment:
    id: str
    chapter: str
    seconds: float
    slide: int
    state: str
    motion: str
    narration: str


@dataclass(frozen=True)
class TimelineItem:
    segment: Segment
    start: float
    end: float


SEGMENTS = (
    Segment("hook-soul", "冷开场", 3.0, 2, "effect", "push",
            "灵魂出窍，视角先出去探路。"),
    Segment("hook-restock", "冷开场", 3.0, 4, "done", "pull",
            "方块见底？背包自动接班。"),
    Segment("hook-gamma", "冷开场", 3.0, 6, "on", "push",
            "矿洞太黑？一键看清。"),
    Segment("intro", "这期讲什么", 10.0, 1, "default", "still",
            "这就是 Tweakeroo。这里不念配置表，只挑真正能用上的场景，把几十页设置翻译成人话。"),
    Segment("soul-config", "灵魂出窍", 14.0, 2, "config", "still",
            "第一个，灵魂出窍。先给它配个顺手的快捷键。我这里是左 Alt 加 C。你用自己不冲突，又记得住的就行。"),
    Segment("soul-effect", "灵魂出窍", 11.0, 2, "effect", "push",
            "按下之后，人留在原地，视角出去转一圈。看建筑，查路线，都不用本人跑过去加班。"),
    Segment("elytra-auto", "鞘翅与胸甲", 11.0, 3, "auto", "still",
            "第二个，自动切换鞘翅。先打开自动鞘翅选项，飞行时让模组帮你处理装备切换。"),
    Segment("elytra-chest", "鞘翅与胸甲", 15.0, 3, "chestplate", "still",
            "再给胸甲交换设个快捷键。我这里是左 Alt 加 W。落地后按一下换回胸甲，至少苦力怕不会替你提醒。快捷键只是示例，按自己的键位改。"),
    Segment("restock-config", "自动补货", 10.0, 4, "config", "still",
            "第三个，自动补货。开启预先补货，再设置触发阈值。我这里用六，只是演示，不是标准答案。"),
    Segment("restock-threshold", "自动补货", 11.0, 4, "threshold", "push",
            "手里的同类方块接近阈值，模组就会去背包里找补给。连续建造时，不用等最后一个放完才开背包。"),
    Segment("restock-done", "自动补货", 10.0, 4, "done", "pull",
            "你看，数量从七补到十九，手里的建筑节奏没断。背包里的同类物品，终于知道主动来上班了。"),
    Segment("click-left", "快速左右键", 11.0, 5, "left", "still",
            "第四个，快速点击。左键和右键分开设置。快速左键适合重复挖掘或攻击测试，次数别一上来拉满。"),
    Segment("click-right", "快速左右键", 14.0, 5, "right", "still",
            "快速右键适合连续放置或交互。它只是重复输入，不是万能加速器。单人随你调。多人服先看规则，别把连点器当机关枪。"),
    Segment("gamma-config", "Gamma 亮度", 9.0, 6, "config", "still",
            "第五个，Gamma 亮度。打开覆盖并设置数值。我这里用十六，先从看得舒服开始。"),
    Segment("gamma-off", "Gamma 亮度", 10.0, 6, "off", "pull",
            "关闭时，夜里和矿洞保留原本的昏暗。氛围很到位，找路也确实有点费眼睛。"),
    Segment("gamma-on", "Gamma 亮度", 12.0, 6, "on", "push",
            "开启后，方块和道路立刻清楚很多。不过矿洞是亮了，刷怪规则并没有被你说服，该插的火把还是得插。"),
    Segment("setup", "快速上手", 16.0, 7, "default", "still",
            "想照着设置，只记住这条路线。X 加 C 进配置，搜索功能名，打开开关，再设置快捷键和参数。一次只改一个，回游戏确认效果。别在菜单里把自己调迷路。"),
    Segment("install", "安装与边界", 12.0, 8, "default", "still",
            "安装时，让游戏、Tweakeroo 和 MaLiLib 版本对应。它是客户端模组，但服务器规则优先。自动操作和连点，使用前先看说明。"),
    Segment("recap", "收藏与关注", 7.0, 1, "default", "pull",
            "灵魂出窍，换甲，补货，连点，Gamma。五项都在这里。先收藏，设置时回来对照。"),
    Segment("outro", "收藏与关注", 12.75, 8, "default", "push",
            "不想装完模组，还自己翻几十页菜单，就关注我。我继续把复杂配置翻译成人话。评论告诉我，这五个里你没用过哪一个。"),
)


def total_base_seconds() -> float:
    return sum(segment.seconds for segment in SEGMENTS)


def encoded_seconds() -> float:
    return total_base_seconds() - TRANSITION_SECONDS * (len(SEGMENTS) - 1)


def timeline() -> tuple[TimelineItem, ...]:
    items = []
    cursor = 0.0
    for index, segment in enumerate(SEGMENTS):
        start = cursor
        end = start + segment.seconds
        items.append(TimelineItem(segment, start, end))
        if index < len(SEGMENTS) - 1:
            cursor = end - TRANSITION_SECONDS
    return tuple(items)


def render_requests() -> list[dict[str, object]]:
    return [
        {"id": segment.id, "slide": segment.slide, "state": segment.state}
        for segment in SEGMENTS
    ]
```

- [ ] **Step 4: Run the storyboard test and verify it passes**

Run:

```bash
python -m unittest tests.test_tweakeroo_video.StoryboardTest -v
```

Expected: 5 tests pass.

- [ ] **Step 5: Commit the storyboard**

```bash
git add -- scripts/tweakeroo_video/__init__.py scripts/tweakeroo_video/storyboard.py tests/test_tweakeroo_video.py
git commit -m "feat: add Tweakeroo video storyboard"
```

---

### Task 2: Natural voice preview, complete narration, and subtitle timing

**Files:**
- Create: `scripts/tweakeroo_video/audio.py`
- Modify: `tests/test_tweakeroo_video.py`

**Interfaces:**
- Consumes: `SEGMENTS`, `PREVIEW_SEGMENT_IDS`, `timeline()`, and `encoded_seconds()`.
- Produces: `Cue`, `parse_srt()`, `split_cue()`, `merge_cues()`, `choose_voice()`, `generate_segment_voice()`, `generate_voice()`, `generate_voice_preview()`, and `compose_narration()`.

- [ ] **Step 1: Add failing audio and subtitle tests**

Append these imports and tests:

```python
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from scripts.tweakeroo_video import audio
from scripts.tweakeroo_video.audio import (
    Cue,
    choose_voice,
    format_srt_time,
    merge_cues,
    parse_srt,
    split_cue,
)


class AudioTest(unittest.TestCase):
    def test_voice_selection_prefers_conversational_male_voice(self):
        voices = (
            "zh-CN-YunyangNeural Male News\n"
            "zh-CN-YunxiNeural Male Novel\n"
            "zh-CN-YunjianNeural Male Sports\n"
        )
        with patch.object(
            audio.subprocess,
            "run",
            return_value=Mock(stdout=voices),
        ):
            self.assertEqual(choose_voice(Path("edge-tts")), "zh-CN-YunxiNeural")

    def test_srt_parser_and_time_formatter(self):
        cue = parse_srt(
            "1\n00:00:00,500 --> 00:00:02,000\n第一句字幕\n"
        )[0]
        self.assertEqual(cue, Cue(0.5, 2.0, "第一句字幕"))
        self.assertEqual(format_srt_time(62.345), "00:01:02,345")

    def test_caption_is_at_most_two_lines_of_eighteen_characters(self):
        cue = Cue(
            0.0,
            8.0,
            "安装时让游戏Tweakeroo和MaLiLib版本对应服务器规则优先",
        )
        captions = split_cue(cue)
        for caption in captions:
            lines = caption.text.splitlines()
            self.assertLessEqual(len(lines), 2)
            self.assertTrue(all(len(line) <= 18 for line in lines))
            self.assertFalse(any(line.endswith("Tweake") for line in lines))

    def test_merged_cues_follow_crossfade_timeline(self):
        merged = merge_cues(
            [[Cue(0.0, 1.0, "第一段")], [Cue(0.0, 1.0, "第二段")]],
            [0.0, 2.75],
        )
        self.assertEqual(merged[1], Cue(2.75, 3.75, "第二段"))

    def test_generate_voice_uses_approved_prosody(self):
        with TemporaryDirectory() as directory:
            build_dir = Path(directory)

            def fake_run(command, **kwargs):
                if "--list-voices" in command:
                    return Mock(stdout="zh-CN-YunxiNeural Male Novel\n")
                if "--write-media" in command:
                    Path(command[command.index("--write-media") + 1]).write_bytes(b"mp3")
                    Path(command[command.index("--write-subtitles") + 1]).write_text(
                        "1\n00:00:00,100 --> 00:00:01,000\n试听字幕\n",
                        encoding="utf-8",
                    )
                return Mock(stdout="")

            with (
                patch.object(audio, "SEGMENTS", SEGMENTS[:1]),
                patch.object(audio, "probe_duration", return_value=2.4),
                patch.object(audio.subprocess, "run", side_effect=fake_run) as run,
            ):
                audio.generate_voice(build_dir, Path("edge-tts"))

            command = next(
                call.args[0]
                for call in run.call_args_list
                if "--write-media" in call.args[0]
            )
            self.assertIn("--rate=-2%", command)
            self.assertIn("--pitch=+0Hz", command)
            self.assertIn("zh-CN-YunxiNeural", command)
```

- [ ] **Step 2: Run the audio tests and verify they fail**

Run:

```bash
python -m unittest tests.test_tweakeroo_video.AudioTest -v
```

Expected: import failure because `audio.py` does not exist.

- [ ] **Step 3: Implement caption parsing, semantic splitting, and TTS orchestration**

Create `scripts/tweakeroo_video/audio.py`. Use these exact public constants and orchestration rules:

```python
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess

from scripts.tweakeroo_video.storyboard import (
    PREVIEW_SEGMENT_IDS,
    SEGMENTS,
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
FFMPEG = "/usr/bin/ffmpeg"
FFPROBE = "/usr/bin/ffprobe"
TIME_PATTERN = re.compile(
    r"(?P<h>\d+):(?P<m>[0-5]\d):(?P<s>[0-5]\d),(?P<ms>\d{3})"
)
LATIN = re.compile(r"[A-Za-z0-9]")
BOUNDARIES = frozenset("，。！？；：、,.!?;: ")


@dataclass(frozen=True)
class Cue:
    start: float
    end: float
    text: str


def parse_srt_time(value: str) -> float:
    match = TIME_PATTERN.fullmatch(value.strip())
    if match is None:
        raise RuntimeError(f"invalid SRT timestamp: {value!r}")
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


def parse_srt(source: str) -> list[Cue]:
    if not source.strip():
        raise RuntimeError("SRT is empty")
    cues = []
    for block in re.split(r"\n\s*\n", source.strip()):
        lines = block.splitlines()
        timing = next((line for line in lines if "-->" in line), None)
        if timing is None:
            raise RuntimeError("SRT cue is missing timing")
        start_text, end_text = re.split(r"\s*-->\s*", timing)
        timing_index = lines.index(timing)
        text = " ".join(lines[timing_index + 1:]).strip()
        if not text:
            raise RuntimeError("SRT cue has empty text")
        cues.append(Cue(parse_srt_time(start_text), parse_srt_time(end_text), text))
    previous_end = -1.0
    for cue in cues:
        if cue.start < 0 or cue.end <= cue.start or cue.start < previous_end:
            raise RuntimeError("SRT cues must be positive and ordered")
        previous_end = cue.end
    return cues


def _safe_break(text: str, target: int, lower: int, upper: int) -> int:
    choices = [
        position
        for position in range(max(1, lower), min(len(text), upper + 1))
        if text[position - 1] in BOUNDARIES or text[position] in BOUNDARIES
    ]
    position = min(choices, key=lambda item: abs(item - target)) if choices else target
    if (
        0 < position < len(text)
        and LATIN.fullmatch(text[position - 1])
        and LATIN.fullmatch(text[position])
    ):
        left = position
        right = position
        while left > lower and LATIN.fullmatch(text[left - 1]):
            left -= 1
        while right < upper and LATIN.fullmatch(text[right]):
            right += 1
        position = left if left >= lower else right
    return position


def _chunks(text: str, limit: int) -> list[str]:
    remaining = re.sub(r"\s+", " ", text).strip()
    chunks = []
    while len(remaining) > limit:
        position = _safe_break(remaining, limit, 1, limit)
        chunks.append(remaining[:position].strip())
        remaining = remaining[position:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks


def _wrap(text: str) -> str:
    if len(text) <= CAPTION_WIDTH:
        return text
    lower = len(text) - CAPTION_WIDTH
    position = _safe_break(text, len(text) // 2, lower, CAPTION_WIDTH)
    return text[:position].rstrip() + "\n" + text[position:].lstrip()


def split_cue(cue: Cue) -> list[Cue]:
    chunks = _chunks(cue.text, CAPTION_WIDTH * MAX_CAPTION_LINES)
    weights = [len(chunk) for chunk in chunks]
    total = sum(weights)
    result = []
    consumed = 0
    for index, (chunk, weight) in enumerate(zip(chunks, weights, strict=True)):
        start = cue.start + (cue.end - cue.start) * consumed / total
        consumed += weight
        end = cue.end if index == len(chunks) - 1 else (
            cue.start + (cue.end - cue.start) * consumed / total
        )
        wrapped = _wrap(chunk)
        if len(wrapped.splitlines()) > 2 or max(map(len, wrapped.splitlines())) > 18:
            raise RuntimeError(f"caption cannot fit: {chunk}")
        result.append(Cue(start, end, wrapped))
    return result


def merge_cues(groups: list[list[Cue]], starts: list[float]) -> list[Cue]:
    merged = []
    for cues, offset in zip(groups, starts, strict=True):
        for cue in cues:
            shifted = Cue(cue.start + offset, cue.end + offset, cue.text)
            merged.extend(split_cue(shifted))
    for index in range(len(merged) - 1):
        current = merged[index]
        following = merged[index + 1]
        if current.end > following.start:
            merged[index] = Cue(current.start, following.start, current.text)
    if any(cue.end <= cue.start for cue in merged):
        raise RuntimeError("merged subtitle contains nonpositive cue")
    return merged


def cues_to_srt(cues: list[Cue]) -> str:
    return "\n\n".join(
        f"{index}\n{format_srt_time(cue.start)} --> {format_srt_time(cue.end)}\n{cue.text}"
        for index, cue in enumerate(cues, 1)
    ) + "\n"


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
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
```

Implement `generate_segment_voice(build_dir, edge_tts, segments)` so each supplied segment runs Edge TTS with `--voice`, `--rate=-2%`, `--pitch=+0Hz`, `--text`, `--write-media`, and `--write-subtitles`. Probe each MP3, reject audio longer than `segment.seconds - 0.25` except the final storyboard segment, and reject more than 1.5 seconds of unused tail. Return the generated MP3 paths.

Implement `generate_voice(build_dir, edge_tts)` by calling `generate_segment_voice()` with all `SEGMENTS`, parsing every segment SRT, merging cues at `[item.start for item in timeline()]`, asserting the final cue ends by `encoded_seconds()`, writing `subtitles/tweakeroo.zh-CN.srt`, and calling `compose_narration()`.

Implement `generate_voice_preview(build_dir, edge_tts)` by selecting the three `PREVIEW_SEGMENT_IDS`, calling `generate_segment_voice()` only for those segments, and using FFmpeg's concat filter over `hook-soul.mp3`, `soul-effect.mp3`, and `gamma-on.mp3` to write `voice-preview.mp3`. Implement `compose_narration()` by applying `adelay=<timeline start in ms>|<same>` to every segment MP3, `amix=inputs=20:duration=longest:normalize=0`, trimming to 200 seconds, and writing `tweakeroo-narration.mp3` with `libmp3lame -b:a 192k`.

- [ ] **Step 4: Run the audio tests and verify they pass**

Run:

```bash
python -m unittest tests.test_tweakeroo_video.AudioTest -v
```

Expected: 5 tests pass.

- [ ] **Step 5: Commit the audio layer**

```bash
git add -- scripts/tweakeroo_video/audio.py tests/test_tweakeroo_video.py
git commit -m "feat: add Tweakeroo narration and subtitle pipeline"
```

---

### Task 3: Deterministic slide capture and build CLI foundation

**Files:**
- Create: `scripts/tweakeroo_video/pipeline.py`
- Modify: `tests/test_tweakeroo_video.py`

**Interfaces:**
- Consumes: `render_requests()` and the approved deck query contract.
- Produces: `ROOT`, `DECK_PATH`, `BUILD_DIR`, `build_slide_url()`, `slide_path()`, `probe_media()`, `render_slides()`, and `locate_edge_tts()`.

- [ ] **Step 1: Add failing pipeline tests**

```python
from urllib.parse import parse_qs, urlparse

from scripts.tweakeroo_video.pipeline import (
    BUILD_DIR,
    DECK_PATH,
    build_slide_url,
    slide_path,
)


class PipelineTest(unittest.TestCase):
    def test_deck_and_build_paths_are_isolated(self):
        self.assertEqual(
            DECK_PATH,
            ROOT / "source/MOD介绍/tweakeroo/index.html",
        )
        self.assertEqual(BUILD_DIR, ROOT / "build/tweakeroo-video")
        self.assertNotIn("minihud", str(BUILD_DIR).lower())

    def test_slide_url_is_deterministic_and_exported(self):
        parsed = urlparse(build_slide_url(4, "done"))
        query = parse_qs(parsed.query)
        self.assertEqual(query, {
            "export": ["1"],
            "slide": ["4"],
            "state": ["done"],
        })

    def test_slide_output_uses_segment_id(self):
        self.assertEqual(
            slide_path("restock-done"),
            BUILD_DIR / "slides/restock-done.png",
        )
```

- [ ] **Step 2: Run the pipeline tests and verify they fail**

Run:

```bash
python -m unittest tests.test_tweakeroo_video.PipelineTest -v
```

Expected: import failure because `pipeline.py` does not exist.

- [ ] **Step 3: Implement deterministic 1920×1080 capture**

Create `scripts/tweakeroo_video/pipeline.py` with these constants and functions:

```python
import argparse
import json
from pathlib import Path
import shutil
import subprocess
from urllib.parse import urlencode

from scripts.tweakeroo_video.storyboard import render_requests


ROOT = Path(__file__).resolve().parents[2]
DECK_PATH = ROOT / "source/MOD介绍/tweakeroo/index.html"
BUILD_DIR = ROOT / "build/tweakeroo-video"
CHROME = "/usr/bin/google-chrome"
FFPROBE = "/usr/bin/ffprobe"


def build_slide_url(slide: int, state: str) -> str:
    query = urlencode({"export": 1, "slide": slide, "state": state})
    return f"{DECK_PATH.resolve().as_uri()}?{query}"


def slide_path(segment_id: str) -> Path:
    return BUILD_DIR / "slides" / f"{segment_id}.png"


def probe_media(path: Path) -> dict:
    result = subprocess.run(
        [FFPROBE, "-v", "error", "-show_streams", "-show_format",
         "-of", "json", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def locate_edge_tts() -> Path:
    candidates = (
        BUILD_DIR / ".venv/bin/edge-tts",
        Path(shutil.which("edge-tts") or ""),
    )
    for candidate in candidates:
        if str(candidate) and candidate.is_file():
            return candidate
    raise RuntimeError(
        "Missing edge-tts. Create build/tweakeroo-video/.venv and "
        "install edge-tts==7.2.8"
    )


def render_slides() -> tuple[Path, ...]:
    output_dir = BUILD_DIR / "slides"
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for request in render_requests():
        output = slide_path(str(request["id"]))
        subprocess.run(
            [CHROME, "--headless", "--no-sandbox", "--disable-gpu",
             "--disable-dev-shm-usage", "--hide-scrollbars",
             "--run-all-compositor-stages-before-draw",
             "--virtual-time-budget=1200", "--window-size=1920,1080",
             f"--screenshot={output}",
             build_slide_url(int(request["slide"]), str(request["state"]))],
            check=True,
        )
        media = probe_media(output)
        stream = media["streams"][0]
        if (stream["width"], stream["height"]) != (1920, 1080):
            raise RuntimeError(f"Unexpected slide size: {output}: {stream}")
        outputs.append(output)
    return tuple(outputs)
```

Do not add CLI actions beyond `slides` until Tasks 4 and 5 define their imports.

- [ ] **Step 4: Run the pipeline and storyboard tests**

Run:

```bash
python -m unittest tests.test_tweakeroo_video.StoryboardTest tests.test_tweakeroo_video.PipelineTest -v
```

Expected: 8 tests pass.

- [ ] **Step 5: Commit the capture foundation**

```bash
git add -- scripts/tweakeroo_video/pipeline.py tests/test_tweakeroo_video.py
git commit -m "feat: add Tweakeroo video slide capture"
```

---

### Task 4: High-click Bilibili cover and conversion-focused publishing copy

**Files:**
- Create: `scripts/tweakeroo_video/cover.html`
- Create: `scripts/tweakeroo_video/cover-4x3.html`
- Create: `scripts/tweakeroo_video/publishing.py`
- Modify: `scripts/tweakeroo_video/pipeline.py`
- Modify: `tests/test_tweakeroo_video.py`

**Interfaces:**
- Consumes: `timeline()` for exact chapter clocks and local source screenshots for cover visuals.
- Produces: `clock()`, `chapter_lines()`, `build_publish_markdown()`, `render_cover()`, and `write_publish_guide()`.

- [ ] **Step 1: Add failing cover and publishing tests**

```python
from scripts.tweakeroo_video.publishing import (
    build_publish_markdown,
    chapter_lines,
)


class PublishingTest(unittest.TestCase):
    def test_cover_sources_have_click_contract_and_exact_dimensions(self):
        cases = (
            ("cover.html", "width:1600px", "height:1000px"),
            ("cover-4x3.html", "width:1600px", "height:1200px"),
        )
        for filename, width, height in cases:
            source = (ROOT / "scripts/tweakeroo_video" / filename).read_text(
                encoding="utf-8"
            )
            for phrase in (
                width,
                height,
                "别再",
                "手动了",
                "Tweakeroo · 5 个高频功能",
                "自动补货",
                "快速换甲",
                "矿洞提亮",
            ):
                self.assertIn(phrase, source)
            self.assertLessEqual(source.count("<img"), 2)

    def test_publish_copy_is_searchable_specific_and_conversion_focused(self):
        copy = build_publish_markdown()
        for phrase in (
            "Tweakeroo 不只会灵魂出窍！自动补货、换胸甲这 5 个功能真省事",
            "Minecraft Java 版 26.2",
            "Tweakeroo 26.2-0.29.2",
            "MaLiLib 0.29.2",
            "不同版本",
            "服务器规则",
            "收藏",
            "关注",
            "你原来完全没用过的是哪一个",
        ):
            self.assertIn(phrase, copy)
        self.assertNotIn("必装", copy)
        self.assertNotIn("无敌", copy)

    def test_chapters_are_strictly_increasing(self):
        clocks = []
        for line in chapter_lines():
            clock, _ = line.split(" ", 1)
            minutes, seconds = map(int, clock.split(":"))
            self.assertLess(seconds, 60)
            clocks.append(minutes * 60 + seconds)
        self.assertTrue(all(a < b for a, b in zip(clocks, clocks[1:])))
```

- [ ] **Step 2: Run the publishing tests and verify they fail**

Run:

```bash
python -m unittest tests.test_tweakeroo_video.PublishingTest -v
```

Expected: file/import failures for the missing cover and publishing sources.

- [ ] **Step 3: Create the two deterministic cover sources**

Both covers use the same composition with ratio-specific sizing:

- A full-bleed, bright Gamma screenshot on the right 58%.
- A cropped, bordered soul-out-of-body screenshot card behind the copy, with the player kept visible.
- A dark navy-to-transparent gradient under the left copy.
- `Tweakeroo · 5 个高频功能` in a cyan pill.
- The two-line 112–136 px headline `别再` / `手动了！`, with the second line warm yellow.
- Three compact benefit chips: `自动补货`, `快速换甲`, `矿洞提亮`.
- No more than two `<img>` elements and no remote assets.

Use `../../source/MOD介绍/tweakeroo/启用ganam的.png` and `../../source/MOD介绍/tweakeroo/开启灵魂出窍.png`. Set the root canvas to exactly `1600×1000` and `1600×1200`, `overflow:hidden`, and `font-family:"Noto Sans CJK SC","Microsoft YaHei",sans-serif`. Add a dark 6 px outer border so feed crops do not remove text.

- [ ] **Step 4: Implement synchronized publishing copy**

Create `scripts/tweakeroo_video/publishing.py`:

```python
from scripts.tweakeroo_video.storyboard import timeline


TITLE = "Tweakeroo 不只会灵魂出窍！自动补货、换胸甲这 5 个功能真省事"
ALTERNATE_TITLES = (
    "装了 Tweakeroo 还在手动补方块？这 5 个功能真的能省事",
    "别把 Tweakeroo 只当配置菜单！5 个高频功能一次讲明白",
)


def clock(seconds: float) -> str:
    total = int(seconds)
    return f"{total // 60:02d}:{total % 60:02d}"


def chapter_lines() -> list[str]:
    lines = []
    seen = set()
    for item in timeline():
        if item.segment.chapter in seen:
            continue
        seen.add(item.segment.chapter)
        lines.append(f"{clock(item.start)} {item.segment.chapter}")
    return lines


def build_publish_markdown() -> str:
    alternatives = "\n".join(f"- {title}" for title in ALTERNATE_TITLES)
    chapters = "\n".join(chapter_lines())
    return f"""# B 站发布信息

## 推荐标题

{TITLE}

## 备选标题

{alternatives}

## 简介

还在手动补方块、换胸甲，进矿洞又被黑得找不到路？这期不念配置表，直接按使用场景讲 Tweakeroo 的五个高频功能：灵魂出窍、自动切换鞘翅与胸甲、自动补货、快速左右键和 Gamma 亮度。

本期演示基于 Minecraft Java 版 26.2、Tweakeroo 26.2-0.29.2 和 MaLiLib 0.29.2。不同版本的菜单、名称和行为可能变化，请使用与游戏版本匹配的文件。Tweakeroo 是客户端模组，但服务器规则始终优先；自动操作和快速点击在多人服使用前，请先阅读服务器说明。

这里不念几十页配置表，只把复杂模组翻译成能直接使用的场景。觉得这份清单有用，可以先收藏；想继续看这种不绕弯的模组用法，欢迎关注。

## 视频章节

{chapters}

## 推荐标签

Minecraft、我的世界、Tweakeroo、Fabric、MaLiLib、模组推荐、生存技巧、建筑辅助

## 置顶评论建议

五项功能速查已经放在章节里，建议先收藏，设置时回来对照。

这五个里面，你原来完全没用过的是哪一个？我先猜自动补货。评论区留一个名字就行。

关注我，后面继续把复杂配置翻译成人话，不用每次装完模组都自己翻几十页菜单。
"""
```

- [ ] **Step 5: Extend the pipeline with cover and publishing actions**

Add `COVER_PATH`, `COVER_4X3_PATH`, `render_cover_source(source, width, height, stem)`, `render_cover()`, and `write_publish_guide()`. For each cover, run Chrome with a window height 87 px taller than the target, crop the raw screenshot to the exact target with FFmpeg, then export PNG and JPG (`-q:v 2`). Always delete only the explicit `*-raw.png` temporary file in a `finally` block.

- [ ] **Step 6: Run the publishing tests and commit**

Run:

```bash
python -m unittest tests.test_tweakeroo_video.PublishingTest -v
```

Expected: 3 tests pass.

Then commit:

```bash
git add -- scripts/tweakeroo_video/cover.html scripts/tweakeroo_video/cover-4x3.html scripts/tweakeroo_video/publishing.py scripts/tweakeroo_video/pipeline.py tests/test_tweakeroo_video.py
git commit -m "feat: add Tweakeroo Bilibili packaging"
```

---

### Task 5: Video assembly, clean master, captioned release, and contact sheet

**Files:**
- Create: `scripts/tweakeroo_video/video.py`
- Modify: `scripts/tweakeroo_video/pipeline.py`
- Modify: `tests/test_tweakeroo_video.py`

**Interfaces:**
- Consumes: per-segment PNG and MP3 files, merged SRT, `SEGMENTS`, and `TRANSITION_SECONDS`.
- Produces: `motion_filter()`, `build_transition_filter()`, `render_segments()`, `compose_master()`, `burn_subtitles()`, `create_contact_sheet()`, and `verify_delivery()`.

- [ ] **Step 1: Add failing video filter and delivery tests**

```python
from scripts.tweakeroo_video.video import (
    build_transition_filter,
    motion_filter,
)


class VideoTest(unittest.TestCase):
    def test_motion_filters_preserve_1080p_and_thirty_fps(self):
        for name in ("still", "push", "pull"):
            source = motion_filter(name)
            self.assertIn("1920", source)
            self.assertIn("1080", source)
            self.assertIn("fps=30", source)
        with self.assertRaises(ValueError):
            motion_filter("spin")

    def test_transition_graph_has_video_and_audio_crossfades(self):
        graph, video_label, audio_label = build_transition_filter(
            [3.0, 3.0, 3.0],
            0.25,
        )
        self.assertEqual(graph.count("xfade=transition=fade:duration=0.25"), 2)
        self.assertEqual(graph.count("acrossfade=d=0.25"), 2)
        self.assertTrue(video_label.startswith("[v"))
        self.assertTrue(audio_label.startswith("[a"))

    def test_subtitle_style_is_pc_video_readable(self):
        source = (ROOT / "scripts/tweakeroo_video/video.py").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "Noto Sans CJK SC",
            "FontSize=20",
            "MarginV=30",
            "loudnorm=I=-16:TP=-1",
        ):
            self.assertIn(phrase, source)
```

- [ ] **Step 2: Run the video tests and verify they fail**

Run:

```bash
python -m unittest tests.test_tweakeroo_video.VideoTest -v
```

Expected: import failure because `video.py` does not exist.

- [ ] **Step 3: Implement motion and transition filters**

Create `scripts/tweakeroo_video/video.py`. Use the approved MiniHUD implementation as behavioral reference but keep Tweakeroo paths and names independent. `motion_filter()` must provide:

```python
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
```

`build_transition_filter()` must chain each input with `xfade=transition=fade:duration=0.25:offset=<cumulative encoded start>` and `acrossfade=d=0.25`, returning `(graph, final_video_label, final_audio_label)`.

- [ ] **Step 4: Implement segment and final encoding**

`render_segments()` loops over `SEGMENTS`, uses the matching slide PNG and narration MP3, pads/trims audio to the segment duration, adds a 760 Hz 80 ms click at chapter starts with volume 0.035, and encodes H.264 CRF 17 / AAC 192 kbps / 48 kHz stereo / 30 fps.

`compose_master()` applies the transition graph, writes a temporary `tweakeroo-bilibili-master.mp4`, measures loudness with:

```python
LOUDNESS_ANALYSIS_FILTER = "loudnorm=I=-16:TP=-1:LRA=11:print_format=json"
```

Parse `input_i`, `input_tp`, `input_lra`, `input_thresh`, and `target_offset`, then run the second linear loudnorm pass while copying the H.264 stream into `tweakeroo-bilibili-clean.mp4`.

`burn_subtitles()` uses:

```python
style = (
    "FontName=Noto Sans CJK SC,FontSize=20,"
    "PrimaryColour=&H00FFFFFF,OutlineColour=&H0010182A,"
    "BorderStyle=1,Outline=1.35,Shadow=0,Alignment=2,MarginV=30"
)
```

Write the captioned result to `tweakeroo-bilibili.mp4`. `create_contact_sheet()` samples one frame every 17 seconds, scales to 480×270, tiles 4×3, and writes `final-contact.png`.

- [ ] **Step 5: Extend the pipeline and implement delivery verification**

Add `render_video()` and `verify_delivery()` to `pipeline.py`. Verification must fail unless:

- clean and captioned videos are 1920×1080, H.264, 30 fps, and 196–205 seconds;
- the captioned video has AAC audio;
- standalone SRT, narration MP3, voice preview, four cover files, publishing markdown, and contact sheet exist and are nonempty;
- the ten source PNG files still report 2880×1800;
- FFmpeg loudnorm analysis of the captioned video reports integrated loudness between -17 and -15 LUFS and true peak at or below -1 dBTP.

- [ ] **Step 6: Run the video tests and commit**

Run:

```bash
python -m unittest tests.test_tweakeroo_video.VideoTest -v
```

Expected: 3 tests pass.

Then commit:

```bash
git add -- scripts/tweakeroo_video/video.py scripts/tweakeroo_video/pipeline.py tests/test_tweakeroo_video.py
git commit -m "feat: assemble Tweakeroo Bilibili video"
```

---

### Task 6: Complete CLI, static regression suite, and production dry run

**Files:**
- Modify: `scripts/tweakeroo_video/pipeline.py`
- Modify: `tests/test_tweakeroo_video.py`

**Interfaces:**
- Consumes: all task-level render functions.
- Produces: CLI commands `slides`, `voice-preview`, `voice`, `video`, `cover`, `publish`, `verify`, and `all`.

- [ ] **Step 1: Add a failing CLI action contract**

```python
class CliContractTest(unittest.TestCase):
    def test_pipeline_exposes_all_production_actions(self):
        source = (ROOT / "scripts/tweakeroo_video/pipeline.py").read_text(
            encoding="utf-8"
        )
        for action in (
            '"slides"',
            '"voice-preview"',
            '"voice"',
            '"video"',
            '"cover"',
            '"publish"',
            '"verify"',
            '"all"',
        ):
            self.assertIn(action, source)
```

- [ ] **Step 2: Run the CLI contract and verify it fails**

Run:

```bash
python -m unittest tests.test_tweakeroo_video.CliContractTest -v
```

Expected: failure because the full action map is absent.

- [ ] **Step 3: Implement the complete command dispatcher**

The `main()` function must use `argparse` with the eight exact choices and an explicit `--voice-approved` flag. `voice-preview` calls `generate_voice_preview(BUILD_DIR, locate_edge_tts())`. `voice` and `all` must stop with `parser.error("approve voice-preview.mp3 before full narration")` unless `--voice-approved` is present. With approval, `voice` calls `generate_voice(BUILD_DIR, locate_edge_tts())`; `all` runs slides, voice, video, cover, publish, and verify in that order. Each action prints every returned path. A failed subprocess or verification must propagate a nonzero exit status.

- [ ] **Step 4: Run all tracked tests before generating large media**

Run:

```bash
python -m unittest tests.test_tweakeroo_video -v
python -m unittest tests.test_tweakeroo_presentation -v
node tests/tweakeroo_presentation_browser_test.cjs
```

Expected: all Tweakeroo video unit tests pass, presentation static tests pass, and browser verification reports no overflow at 1920×1080 or 1280×720.

- [ ] **Step 5: Render deterministic slides, covers, and publishing copy**

Run:

```bash
python -m scripts.tweakeroo_video.pipeline slides
python -m scripts.tweakeroo_video.pipeline cover
python -m scripts.tweakeroo_video.pipeline publish
```

Expected: 20 slide PNGs, four cover files, and `bilibili-publish.md` under `build/tweakeroo-video/`.

- [ ] **Step 6: Inspect the generated visual assets**

Open the two cover PNGs and a contact sheet of the 20 slide PNGs. Confirm the cover remains readable at 320 px width, the player is visible, all slide images are complete by default, and the approved focus states magnify only the relevant settings.

- [ ] **Step 7: Commit the completed source pipeline**

```bash
git add -- scripts/tweakeroo_video/pipeline.py tests/test_tweakeroo_video.py
git commit -m "feat: complete Tweakeroo video build pipeline"
```

---

### Task 7: Voice audition checkpoint, final production, and evidence-based QA

**Files:**
- Generate only: `build/tweakeroo-video/**`

**Interfaces:**
- Consumes: approved source pipeline and Edge TTS 7.2.8.
- Produces: the complete delivery package and verification evidence.

- [ ] **Step 1: Create the isolated TTS environment**

Run:

```bash
python -m venv build/tweakeroo-video/.venv
build/tweakeroo-video/.venv/bin/pip install edge-tts==7.2.8
```

Expected: `build/tweakeroo-video/.venv/bin/edge-tts` exists and lists `zh-CN-YunxiNeural`.

- [ ] **Step 2: Generate only the 25-second voice audition**

Run:

```bash
python -m scripts.tweakeroo_video.pipeline voice-preview
```

Expected: `build/tweakeroo-video/voice-preview.mp3` exists, uses Yunxi at rate -2% and pitch 0 Hz, and contains the hook, ordinary explanation, and Gamma joke.

- [ ] **Step 3: Pause for user voice approval**

Give the user the clickable `voice-preview.mp3` path. Do not generate the full narration until the user confirms that the pace, emphasis, pauses, and joke sound like normal speech. If rejected, revise only narration punctuation/phrase boundaries first; generate the preview again. Change the voice only if rewriting and neutral pitch still sound synthetic.

- [ ] **Step 4: Generate narration, subtitles, and final video after approval**

Run:

```bash
python -m scripts.tweakeroo_video.pipeline voice --voice-approved
python -m scripts.tweakeroo_video.pipeline video
python -m scripts.tweakeroo_video.pipeline verify
```

Expected: clean and captioned videos, standalone narration, SRT, contact sheet, and verification success.

- [ ] **Step 5: Run ffprobe and loudness evidence checks**

Run:

```bash
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate -show_entries format=duration -of json build/tweakeroo-video/tweakeroo-bilibili.mp4
ffmpeg -hide_banner -i build/tweakeroo-video/tweakeroo-bilibili.mp4 -af loudnorm=I=-16:TP=-1:LRA=11:print_format=json -f null -
```

Expected: H.264 1920×1080 at 30/1 fps, AAC audio, 196–205 seconds, integrated loudness between -17 and -15 LUFS, and input true peak no higher than -1 dBTP.

- [ ] **Step 6: Inspect final visual evidence**

Open `final-contact.png` and representative frames near 00:03, 00:25, 00:55, 01:20, 01:50, 02:18, 02:42, and 03:10. Confirm no black frames, broken images, cropped source screenshots outside approved focus shots, subtitle overflow, or cover/style mismatch.

- [ ] **Step 7: Run final tracked regression verification**

Run:

```bash
python -m unittest tests.test_tweakeroo_video -v
python -m unittest tests.test_tweakeroo_presentation -v
node tests/tweakeroo_presentation_browser_test.cjs
git status --short
```

Expected: all relevant tests pass; generated build files remain ignored; the only working-tree changes are any pre-existing unrelated user edits.

- [ ] **Step 8: Deliver the package**

Provide clickable links to the captioned video, clean master, voice preview, standalone narration, SRT, both cover ratios, publishing markdown, and final contact sheet. State the verified duration, resolution, frame rate, codecs, loudness, and actual selected voice. Do not claim completion if any required artifact or verification is missing.
