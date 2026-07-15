# MiniHUD Bilibili Video Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Revise the MiniHUD deck around six problem-driven scenarios and produce a verified 3 minute 30 second Bilibili package with a magnetic male narration, readable subtitles, cover, and publishing copy.

**Architecture:** Keep the existing eight-page HTML deck as the visual source of truth. Add a small tracked Python build package whose storyboard is the single source of truth for narration, timing, slide state, subtitles, video assembly, cover, and publishing chapters; all large generated files stay under the ignored build/minihud-video directory.

**Tech Stack:** HTML/CSS/JavaScript, Python 3.11+ standard library, unittest, Google Chrome headless screenshots, edge-tts 7.2.8, FFmpeg/ffprobe 6.x, Sphinx.

## Global Constraints

- Public feature baseline is Minecraft Java Edition 26.2 with matching current MiniHUD and MaLiLib.
- Say that core usage ideas are broadly reusable, but never promise identical features or rules across versions.
- Every content block follows problem → feature → visible result.
- Final base timeline is exactly 210 seconds; crossfades may reduce the encoded result to 205–215 seconds.
- Use only the existing MiniHUD screenshots; crop, dim, highlight, and annotate them non-destructively.
- Do not sell, enumerate in narration, or tease a future video about all 15 shapes.
- Do not describe Mob Cap as a spatial range.
- Multiplayer structure boundaries require compatible server-side Servux data; Carpet is not a substitute for structure data.
- Default preview copy says to hold Shift while hovering and says the binding is configurable.
- Cover copy is “一个 MOD / 看清隐藏规则” with “MiniHUD · 6 个实用场景”.
- Narration is a natural low-pitched adult Chinese male voice, preferring zh-CN-YunyangNeural at rate -4% and pitch -4Hz.
- No unlicensed background music; use clear narration and restrained generated transition sounds only.
- Generated video, audio, screenshots, cover, and publishing files go under build/minihud-video.

## File Structure

- Modify source/extra/MOD介绍/minihud/index.html — deck copy, responsive layout, deterministic video export states, install card, and outro card.
- Modify source/MOD介绍/minihud/minihud.rst — 26.2 baseline, Fabric relationship, Shift preview wording, and multiplayer data limits.
- Modify tests/test_minihud_presentation.py — static copy and technical-accuracy contract.
- Modify tests/minihud_presentation_browser_test.cjs — active-slide horizontal-boundary checks at 390×844.
- Create scripts/minihud_video/__init__.py — package marker.
- Create scripts/minihud_video/storyboard.py — immutable segment data, narration, duration, state, and timeline calculations.
- Create scripts/minihud_video/audio.py — edge-tts invocation, SRT parsing/wrapping/offset merging, and audio probing.
- Create scripts/minihud_video/video.py — still-frame motion, fixed-duration segments, crossfades, normalization, subtitle burn-in, and contact sheet.
- Create scripts/minihud_video/publishing.py — chapter timestamps and complete Bilibili publishing guide.
- Create scripts/minihud_video/pipeline.py — CLI orchestration for slides, voice, video, cover, publishing, and all.
- Create scripts/minihud_video/cover.html — deterministic 1600×1000 Bilibili cover.
- Create tests/test_minihud_video.py — storyboard, audio, filter-graph, cover, and publishing tests.
- Generate build/minihud-video/** — ignored production artifacts.

---

### Task 1: Revise and harden the eight-page MiniHUD deck

**Files:**
- Modify: tests/test_minihud_presentation.py
- Modify: tests/minihud_presentation_browser_test.cjs
- Modify: source/extra/MOD介绍/minihud/index.html
- Modify: source/MOD介绍/minihud/minihud.rst

**Interfaces:**
- Consumes: Existing slide IDs s1–s8 and existing scene control data attributes.
- Produces: Query interface ?export=1&slide=N&state=group:value, plus video:install and video:outro states used by Task 3.

- [ ] **Step 1: Add failing static content tests**

Add these methods to MiniHudPresentationTest:

~~~python
def test_video_copy_is_problem_driven_and_versioned(self):
    required = (
        "一个 MOD", "看清隐藏规则", "遇到什么问题，就开什么功能",
        "Minecraft Java 版 26.2", "Fabric Loader", "按住 Shift",
        "收藏这份问题清单", "实用 Minecraft 模组和生存技巧",
    )
    for phrase in required:
        self.assertIn(phrase, self.copy + " " + self.rst)

def test_multiplayer_data_copy_is_precise(self):
    for phrase in (
        "多人服需要服务器端 Servux 提供结构数据",
        "精确 TPS/MSPT",
        "Mob Cap 是数量上限，不是空间范围",
    ):
        self.assertIn(phrase, self.copy + " " + self.rst)
    for misleading in (
        "Carpet 或服务器许可",
        "Mob Cap：看玩家周围空间",
        "悬停即可预览",
    ):
        self.assertNotIn(misleading, self.copy + " " + self.rst)

def test_video_export_states_exist_without_adding_slides(self):
    for token in (
        'data-video-card="install"',
        'data-video-card="outro"',
        'data-range="chunk"',
        "applyRequestedState",
        "video-install",
        "video-outro",
    ):
        self.assertIn(token, self.html)
~~~

Keep test_all_fifteen_shape_types_are_present because the self-guided web deck may retain the detailed reference. Change the visible button label so “15 种形状” is not a video selling point.

Also update test_six_player_scenarios_drive_the_deck so its title assertions use the new problem-driven phrases “总在按 F3”, “结构藏进地形”, “选址怕踩坑”, “范围全靠估”, “圆心半径难确定”, and “整理和排查太慢”. In test_examples_support_scenes_without_becoming_scene_titles, replace the required “圆形刷怪塔” example with “圆形 / 圆柱体”; the available image shows a planning ring rather than a completed mob farm.

- [ ] **Step 2: Add a failing mobile element-boundary test**

In tests/minihud_presentation_browser_test.cjs, after switching to 390×844, inspect every active slide:

~~~javascript
const mobileBounds = [];
for (let index = 0; index < 8; index += 1) {
  await evaluate(sessionId, "go(" + index + ")");
  await sleep(80);
  const expression = [
    "(() => {",
    "const slide=document.querySelector('.slide.active');",
    "const selectors=['.hero-title','.sec-title','.hero-sub','.scene-lead','.badge-row','.task-route','.scene-layout'];",
    "const failures=selectors.flatMap((selector)=>[...slide.querySelectorAll(selector)].flatMap((element)=>{",
    "const rect=element.getBoundingClientRect();",
    "if(rect.width===0||rect.height===0)return [];",
    "return rect.left < -1 || rect.right > innerWidth + 1 ? [{selector,left:rect.left,right:rect.right,viewport:innerWidth}] : [];",
    "}));",
    "return {id:slide.id,ownOverflow:slide.scrollWidth > slide.clientWidth + 1,failures};",
    "})()",
  ].join("");
  mobileBounds.push(await evaluate(sessionId, expression));
}
if (mobileBounds.some((item) => item.ownOverflow || item.failures.length)) {
  throw new Error("Mobile content clipped: " + JSON.stringify(mobileBounds));
}
~~~

Include mobileBounds in the final JSON diagnostic output.

- [ ] **Step 3: Run tests and verify failure**

~~~bash
python3 -m unittest tests.test_minihud_presentation -v
node tests/minihud_presentation_browser_test.cjs
~~~

Expected: static tests fail because the copy and export states are absent; browser test reports clipped mobile elements.

- [ ] **Step 4: Replace visible titles and concise scenario copy**

Use these exact titles:

~~~html
<h1 class="hero-title" id="title-s1"><span>一个 MOD</span><span>看清隐藏规则</span></h1>
<p class="hero-sub">信息、结构、范围、施工和预览，直接画进游戏画面</p>

<h2 class="sec-title" id="title-s2">遇到什么问题，就开什么功能</h2>
<h2 class="sec-title" id="title-s3">总在按 F3？把常用信息留在眼前</h2>
<h2 class="sec-title" id="title-s4">结构藏进地形？打开已有数据的边界</h2>
<h2 class="sec-title" id="title-s5">选址怕踩坑？一次只开一层覆盖</h2>
<h2 class="sec-title" id="title-s6">范围全靠估？先分清盒子、球和网格</h2>
<h2 class="sec-title" id="title-s7">圆心半径难确定？先画进世界再动手</h2>
<h2 class="sec-title" id="title-s8">整理和排查太慢？少开界面先确认</h2>
~~~

Shorten each side-card to at most three bullets. Use this structure warning:

~~~html
<p class="tip"><strong>数据来源：</strong>单人读取本地数据；多人服需要服务器端 Servux 提供结构数据。它不会远程找结构，也不调用 /locate。</p>
~~~

Use these range bullets:

~~~html
<ul>
  <li><strong>盒子：</strong>信标、潮涌核心等装置覆盖。</li>
  <li><strong>球：</strong>生成与消失距离的空间参考。</li>
  <li><strong>网格：</strong>随机刻、出生区块等区块机制。</li>
</ul>
<p class="tip"><strong>别混淆：</strong>Mob Cap 是数量上限，不是空间范围。</p>
~~~

Change the base label to “默认按住 Shift 悬停预览，触发方式可以修改”. Change the shape detail button to “更多形状参考 →”.

Keep these exact compact decision points in the six side cards:

~~~html
<!-- s3 uses the existing three tabs; replace only the performance warning -->
<p class="tip" id="scene-warning"><strong>判断方法：</strong>坐标和朝向是本地信息；精确 TPS/MSPT 要看服务器支持。</p>

<!-- s4 -->
<ul><li>先到达附近，让所需结构数据可用。</li><li>主边界看整体，组成部分看内部。</li><li>结果只解释已有数据，不负责寻找结构。</li></ul>

<!-- s5 -->
<ul><li>担心刷怪：按需要检查光照条件。</li><li>担心跨界：查看方块、区块和区域边界。</li><li>担心选错环境：查看群系和种子相关覆盖。</li></ul>

<!-- s7 -->
<ul><li><strong>占地：</strong>圆形、圆柱和方框。</li><li><strong>路线：</strong>直线和中心参考。</li><li><strong>空间：</strong>球体、生成球和高度参考。</li></ul>

<!-- s8 -->
<ul><li><strong>快速预览：</strong>默认按住 Shift 悬停确认内容。</li><li><strong>目标检查：</strong>查看实体、方块和交易信息。</li><li><strong>效率排查：</strong>区分现场、客户端和服务器状态。</li></ul>
~~~

- [ ] **Step 5: Add chunk, install, and outro render states**

Add a fourth range button and scene:

~~~html
<button type="button" data-range="chunk">区块机制</button>
<div class="range-scene chunk-scene">
  <div class="chunk-grid" aria-hidden="true"></div>
  <div class="player-dot">👤</div>
  <div class="range-labels">随机刻 · 出生区块<br>看网格，不和球形距离混用</div>
</div>
~~~

Add this card inside s2:

~~~html
<div class="video-card install-card" data-video-card="install" aria-hidden="true">
  <span class="video-kicker">安装关系 · 26.2 基线</span>
  <h3>Fabric Loader + MiniHUD + MaLiLib</h3>
  <p>三者都要匹配 Minecraft Java 版 26.2；不同版本的菜单和功能可能不同。</p>
  <div class="install-flow">
    <span>客户端：MiniHUD + MaLiLib</span>
    <span>多人服按需：Servux 数据支持</span>
  </div>
</div>
~~~

Add this card inside s8:

~~~html
<div class="video-card outro-card" data-video-card="outro" aria-hidden="true">
  <span class="video-kicker">遇到问题，按场景找功能</span>
  <h3>收藏这份问题清单</h3>
  <div class="outro-grid">
    <span>迷路 → 信息 HUD</span><span>遮挡 → 结构边界</span>
    <span>选址 → 环境覆盖</span><span>估算 → 范围参考</span>
    <span>施工 → 形状参考</span><span>整理 → 预览与检查</span>
  </div>
  <p>关注我，继续分享实用 Minecraft 模组和生存技巧。</p>
</div>
~~~

Add deterministic state CSS:

~~~css
.video-card{display:none;width:min(1120px,100%);padding:34px;border:1px solid rgba(255,255,255,.18);border-radius:24px;background:rgba(5,13,27,.92)}
.video-card h3{margin:.25em 0;font-size:clamp(2rem,4vw,4rem);color:#fff}
.video-kicker{color:var(--accent);font-weight:950;letter-spacing:.08em}
.install-flow,.outro-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:24px}
.install-flow span,.outro-grid span{padding:16px;border:1px solid rgba(255,255,255,.15);border-radius:14px;background:rgba(255,255,255,.06);font-weight:850}
body.video-install .s2 .task-route,
body.video-install .s2 .shortcut,
body.video-install .s2 > .pill,
body.video-install .s2 > .sec-title,
body.video-install .s2 > .scene-lead{display:none}
body.video-install .s2 [data-video-card="install"]{display:block}
body.video-outro .s8 .scene-layout,
body.video-outro .s8 > .pill,
body.video-outro .s8 > .sec-title,
body.video-outro .s8 > .scene-lead{display:none}
body.video-outro .s8 [data-video-card="outro"]{display:block}
.range-stage[data-range="chunk"] .chunk-scene{display:block}
.chunk-grid{position:absolute;inset:8%;background-image:linear-gradient(#c084fc66 2px,transparent 2px),linear-gradient(90deg,#c084fc66 2px,transparent 2px);background-size:25% 25%;border:3px solid #c084fc}
~~~

- [ ] **Step 6: Add deterministic query-state handling**

Replace the final URLSearchParams block with:

~~~javascript
const params = new URLSearchParams(location.search);
if (params.get('export') === '1') document.body.classList.add('export');
const requested = Number(params.get('slide'));
if (Number.isInteger(requested) && requested >= 1 && requested <= slides.length) go(requested - 1);

function applyRequestedState(rawState) {
  if (!rawState || rawState === 'default') return;
  const [group, value] = rawState.split(':', 2);
  if (group === 'video' && ['install', 'outro'].includes(value)) {
    document.body.classList.add('video-' + value);
    return;
  }
  const attributes = {
    info: 'data-scene',
    structure: 'data-structure-view',
    site: 'data-site-layer',
    range: 'data-range',
    shape: 'data-shape-group',
    base: 'data-base-view',
  };
  const attribute = attributes[group];
  const selector = attribute ? '[' + attribute + '="' + value + '"]' : '';
  const button = selector && document.querySelector(selector);
  if (!button) throw new Error('Unknown export state: ' + rawState);
  button.click();
}
applyRequestedState(params.get('state'));
~~~

- [ ] **Step 7: Fix mobile sizing and improve video text**

~~~css
.hero-title{display:flex;flex-direction:column;width:100%;max-width:15ch}
.task-route,.scene-layout,.visual-stage,.side-card,.badge-row{min-width:0;max-width:100%}
.side-card p,.side-card li{font-size:clamp(.86rem,1vw,1rem)}
.side-card h3{font-size:clamp(1.1rem,1.5vw,1.38rem)}
body.export .side-card p,body.export .side-card li{font-size:1rem}
body.export .detail-button{font-size:.86rem}

@media(max-width:900px){
  .slide{align-items:stretch}
  .hero-title,.sec-title,.hero-sub,.scene-lead{align-self:center;width:100%;overflow-wrap:anywhere;word-break:break-word}
  .task-route{grid-template-columns:repeat(2,minmax(0,1fr))}
  .scene-layout{grid-template-columns:minmax(0,1fr)}
  .visual-stage,.side-card{width:100%}
}
@media(max-width:600px){
  .task-route{grid-template-columns:minmax(0,1fr)}
  .install-flow,.outro-grid{grid-template-columns:minmax(0,1fr)}
  .hero-title{font-size:clamp(3.2rem,17vw,5.2rem)}
  .sec-title{font-size:clamp(1.8rem,9.4vw,3rem)}
}
~~~

Keep source screenshots unchanged. Enlarge hud-focus and darken the full paused screenshot. Add a CSS callout around the visible beacon boundary rather than fabricating a new screenshot.

- [ ] **Step 8: Correct the RST version and install section**

~~~rst
版本与安装
------------------------

本文和演示以 **Minecraft Java 版 26.2** 及其匹配的最新 MiniHUD、MaLiLib 为功能基线。核心使用思路在多个版本中相通，但具体菜单、功能数量和游戏规则可能不同，请以对应版本的下载页为准。

- 使用与游戏版本匹配的 **Fabric Loader、MiniHUD 和 MaLiLib**；不要把 Fabric API 写成 MiniHUD 的固定硬依赖。
- MiniHUD 与 MaLiLib 安装在客户端。
- 单人世界通常直接读取本地数据；多人服的真实结构边界需要服务器端 **Servux** 提供结构数据。
- 精确 TPS/MSPT 可由 Servux、Carpet 等服务器支持提供；没有同步时可能只能估算或不可用。
- 潜影盒、收纳袋等预览默认按住 **Shift** 悬停触发，按键和触发方式可以在配置中修改。
~~~

In the range section, add “Mob Cap 是数量上限，不是空间范围.” Remove wording that treats Carpet or generic permission as a substitute for structure data.

- [ ] **Step 9: Run all deck tests**

~~~bash
python3 -m unittest tests.test_minihud_presentation -v
node tests/minihud_presentation_browser_test.cjs
python3 -m sphinx -b html source build/html
~~~

Expected: at least 19 static tests pass, browser diagnostics show no mobile clipping, and Sphinx exits 0.

- [ ] **Step 10: Commit**

~~~bash
git add -- tests/test_minihud_presentation.py tests/minihud_presentation_browser_test.cjs source/extra/MOD介绍/minihud/index.html source/MOD介绍/minihud/minihud.rst
git commit -m "feat: refocus MiniHUD deck for Bilibili video"
~~~

---

### Task 2: Create the timed problem-driven storyboard

**Files:**
- Create: scripts/minihud_video/__init__.py
- Create: scripts/minihud_video/storyboard.py
- Create: tests/test_minihud_video.py

**Interfaces:**
- Produces: Segment, SEGMENTS, TRANSITION_SECONDS, total_base_seconds(), encoded_seconds(), timeline(), and render_requests().
- Consumed by: Tasks 3–7.

- [ ] **Step 1: Write failing storyboard tests**

~~~python
from pathlib import Path
import unittest

from scripts.minihud_video.storyboard import (
    SEGMENTS, TRANSITION_SECONDS, encoded_seconds,
    render_requests, timeline, total_base_seconds,
)

ROOT = Path(__file__).resolve().parents[1]

class StoryboardTest(unittest.TestCase):
    def test_storyboard_has_exact_timing_and_unique_ids(self):
        self.assertEqual(len(SEGMENTS), 19)
        self.assertEqual(len({segment.id for segment in SEGMENTS}), 19)
        self.assertAlmostEqual(total_base_seconds(), 210.0, places=3)
        self.assertAlmostEqual(encoded_seconds(), 205.5, places=3)
        self.assertEqual(TRANSITION_SECONDS, 0.25)

    def test_narration_matches_approved_scope(self):
        copy = "".join(segment.narration for segment in SEGMENTS)
        self.assertEqual(len(copy), 819)
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
        self.assertAlmostEqual(items[1].start, 3.05, places=3)
        self.assertAlmostEqual(items[-1].end, 205.5, places=3)

    def test_every_render_request_has_a_supported_slide(self):
        requests = render_requests()
        self.assertEqual(len(requests), 19)
        self.assertTrue(all(1 <= item["slide"] <= 8 for item in requests))
        self.assertEqual(requests[-2]["state"], "video:install")
        self.assertEqual(requests[-1]["state"], "video:outro")
~~~

- [ ] **Step 2: Run and verify import failure**

~~~bash
python3 -m unittest tests.test_minihud_video -v
~~~

Expected: ModuleNotFoundError for scripts.minihud_video.

- [ ] **Step 3: Implement the complete storyboard**

Create an empty scripts/minihud_video/__init__.py and:

~~~python
from dataclasses import dataclass

TRANSITION_SECONDS = 0.25

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
    Segment("hook-structure", "冷开场", 3.3, 4, "structure:on", "push", "结构被挡，看不清范围？"),
    Segment("hook-shape", "冷开场", 3.3, 7, "shape:basic", "pull", "圆心半径，还靠目测？"),
    Segment("hook-preview", "冷开场", 3.4, 8, "base:shulker", "push", "潜影盒，也要一个个打开确认？"),
    Segment("intro", "MiniHUD 是什么", 13, 1, "default", "push", "这就是 MiniHUD。它不会替你建造或找结构，只把原本看不见的信息、边界和范围，直接画进游戏画面。"),
    Segment("problem-map", "使用方法", 13, 2, "default", "still", "不用背菜单。遇到什么问题，就开对应功能。默认 H 控制总渲染，H 加 C 进入配置，快捷键可以修改。"),
    Segment("info-explore", "日常信息", 11, 3, "info:explore", "push", "出门怕迷路，就开启坐标、朝向、群系和时间。需要回基地时，可以先设置参考点，再查看距离。"),
    Segment("info-performance", "日常信息", 14, 3, "info:performance", "pull", "游戏卡顿时，别把所有数字都堆上去。FPS 看客户端，延迟和 TPS、MSPT 看联机状态；精确数据还要看服务器支持。"),
    Segment("structure", "结构边界", 23, 4, "structure:on", "push", "结构被海水或山体挡住时，打开结构主边界和组成部分，就能看清整体与内部。它只显示已有数据，不会远程找结构，也不会调用 locate。单人读取本地数据，多人服需要 Servux 提供结构数据。"),
    Segment("site-biome", "工程选址", 8, 5, "site:biome", "pull", "准备建基地或农场，先看群系和区块边界，确认工程有没有跨过关键区域。"),
    Segment("site-guide", "工程选址", 14, 5, "site:guide", "push", "担心刷怪，再按需要检查光照。一次只开一层，看见问题、现场处理、关闭复查。低光照只是条件之一，不代表一定刷怪。"),
    Segment("range-device", "机制范围", 6, 6, "range:beacon", "push", "信标、潮涌核心这类装置，适合看盒状覆盖边界。"),
    Segment("range-spawn", "机制范围", 6, 6, "range:spawn", "pull", "刷怪距离看球，挂机点更直观。"),
    Segment("range-chunk", "机制范围", 12, 6, "range:chunk", "still", "随机刻和出生区块看网格。二十四、三十二、一百二十八格只是常见参考，具体规则仍要看版本和生物。"),
    Segment("build-basic", "施工规划", 9, 7, "shape:basic", "push", "圆心、半径和占地不好确定，就用圆形、圆柱或方框，先把施工参考线画进世界。"),
    Segment("build-spawn", "施工规划", 11, 7, "shape:spawn", "pull", "需要判断高度或生成空间，再切换球体和生成球。它们只帮助检查，不会自动放置或拆除方块。"),
    Segment("base-preview", "基地管理", 12, 8, "base:shulker", "push", "回到基地，默认按住 Shift 悬停，就能预览潜影盒、收纳袋、地图或支持的容器内容，少开很多界面。"),
    Segment("base-efficiency", "基地管理", 15, 8, "base:efficiency", "pull", "机器效率不对，再查看光照、生成距离、Mob Cap、实体数量、延迟和 TPS。Mob Cap 是数量上限，不是空间范围。"),
    Segment("install", "安装与限制", 18, 2, "video:install", "still", "安装只要记住：Fabric Loader，加上版本匹配的 MiniHUD 和 MaLiLib。MiniHUD 装客户端；多人结构数据还要服务器支持。"),
    Segment("outro", "收藏与关注", 15, 8, "video:outro", "push", "遇到这六类问题，就回来按清单找功能。觉得有用先收藏，也欢迎关注我，继续分享实用的 Minecraft 模组和生存技巧。"),
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
        cursor = end - (TRANSITION_SECONDS if index < len(SEGMENTS) - 1 else 0)
    return tuple(items)

def render_requests() -> list[dict[str, object]]:
    return [{"id": s.id, "slide": s.slide, "state": s.state} for s in SEGMENTS]
~~~

- [ ] **Step 4: Run tests**

~~~bash
python3 -m unittest tests.test_minihud_video.StoryboardTest -v
~~~

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

~~~bash
git add -- scripts/minihud_video/__init__.py scripts/minihud_video/storyboard.py tests/test_minihud_video.py
git commit -m "feat: define MiniHUD video storyboard"
~~~

---

### Task 3: Render deterministic 1080p slide states

**Files:**
- Create: scripts/minihud_video/pipeline.py
- Modify: tests/test_minihud_video.py

**Interfaces:**
- Consumes: render_requests() and deck query states.
- Produces: build_slide_url(), slide_path(), render_slides(), and 19 PNGs.

- [ ] **Step 1: Write failing URL tests**

~~~python
from scripts.minihud_video.pipeline import BUILD_DIR, DECK_PATH, build_slide_url, slide_path

class SlidePipelineTest(unittest.TestCase):
    def test_slide_url_is_local_and_encodes_export_state(self):
        url = build_slide_url(6, "range:chunk")
        self.assertTrue(url.startswith("file:"))
        self.assertIn("export=1", url)
        self.assertIn("slide=6", url)
        self.assertIn("state=range%3Achunk", url)

    def test_slide_path_is_stable(self):
        self.assertEqual(slide_path("range-chunk"), BUILD_DIR / "slides/range-chunk.png")
        self.assertTrue(DECK_PATH.is_file())
~~~

- [ ] **Step 2: Run and verify import failure**

~~~bash
python3 -m unittest tests.test_minihud_video.SlidePipelineTest -v
~~~

Expected: FAIL because pipeline.py does not exist.

- [ ] **Step 3: Implement headless Chrome rendering**

~~~python
import argparse
import json
from pathlib import Path
import subprocess
from urllib.parse import urlencode

from scripts.minihud_video.storyboard import render_requests

ROOT = Path(__file__).resolve().parents[2]
DECK_PATH = ROOT / "source/extra/MOD介绍/minihud/index.html"
BUILD_DIR = ROOT / "build/minihud-video"
CHROME = "/usr/bin/google-chrome"
FFPROBE = "/usr/bin/ffprobe"

def build_slide_url(slide: int, state: str) -> str:
    return f"{DECK_PATH.resolve().as_uri()}?{urlencode({'export': 1, 'slide': slide, 'state': state})}"

def slide_path(segment_id: str) -> Path:
    return BUILD_DIR / "slides" / f"{segment_id}.png"

def probe_video(path: Path) -> dict:
    result = subprocess.run(
        [FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height", "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)["streams"][0]

def render_slides() -> tuple[Path, ...]:
    (BUILD_DIR / "slides").mkdir(parents=True, exist_ok=True)
    outputs = []
    for request in render_requests():
        output = slide_path(str(request["id"]))
        subprocess.run(
            [CHROME, "--headless", "--no-sandbox", "--disable-gpu",
             "--disable-dev-shm-usage", "--hide-scrollbars",
             "--run-all-compositor-stages-before-draw", "--virtual-time-budget=1200",
             "--window-size=1920,1080", f"--screenshot={output}",
             build_slide_url(int(request["slide"]), str(request["state"]))],
            check=True,
        )
        dimensions = probe_video(output)
        if (dimensions["width"], dimensions["height"]) != (1920, 1080):
            raise RuntimeError(f"Unexpected slide size for {output}: {dimensions}")
        outputs.append(output)
    return tuple(outputs)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("slides",))
    args = parser.parse_args()
    if args.command == "slides":
        for path in render_slides():
            print(path)

if __name__ == "__main__":
    main()
~~~

- [ ] **Step 4: Run tests and render**

~~~bash
python3 -m unittest tests.test_minihud_video.SlidePipelineTest -v
python3 -m scripts.minihud_video.pipeline slides
find build/minihud-video/slides -maxdepth 1 -name '*.png' | wc -l
ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 build/minihud-video/slides/range-chunk.png
~~~

Expected: tests PASS; count is 19; probe prints 1920,1080.

- [ ] **Step 5: Commit**

~~~bash
git add -- scripts/minihud_video/pipeline.py tests/test_minihud_video.py
git commit -m "feat: render MiniHUD video slide states"
~~~

---

### Task 4: Generate magnetic male narration and synchronized subtitles

**Files:**
- Create: scripts/minihud_video/audio.py
- Modify: scripts/minihud_video/pipeline.py
- Modify: tests/test_minihud_video.py

**Interfaces:**
- Consumes: SEGMENTS and timeline().
- Produces: Cue, parse_srt(), wrap_caption(), merge_cues(), probe_duration(), generate_voice(); 19 MP3/SRT pairs and one merged SRT.

- [ ] **Step 1: Write failing subtitle timing tests**

~~~python
from scripts.minihud_video.audio import (
    Cue, format_srt_time, merge_cues, parse_srt, split_cue, wrap_caption,
)

class AudioTest(unittest.TestCase):
    def test_srt_parser_and_formatter(self):
        source = "1\n00:00:00,500 --> 00:00:02,000\n第一句字幕\n"
        cue = parse_srt(source)[0]
        self.assertEqual(cue, Cue(0.5, 2.0, "第一句字幕"))
        self.assertEqual(format_srt_time(62.345), "00:01:02,345")

    def test_chinese_caption_wraps_to_two_lines(self):
        wrapped = wrap_caption("一次只开一层看见问题现场处理关闭复查", width=10)
        self.assertEqual(wrapped.count("\n"), 1)
        self.assertLessEqual(max(map(len, wrapped.splitlines())), 10)

    def test_merge_cues_uses_crossfade_timeline(self):
        merged = merge_cues(
            [[Cue(0.0, 1.0, "第一段")], [Cue(0.0, 1.0, "第二段")]],
            starts=[0.0, 3.05],
        )
        self.assertEqual(merged[1], Cue(3.05, 4.05, "第二段"))

    def test_long_cue_splits_before_wrapping(self):
        source = Cue(0.0, 4.0, "一二三四五六七八九十一二三四五六七八九十一二三四五六七八九十一二三四五六七八九十")
        parts = split_cue(source, width=10)
        self.assertEqual(len(parts), 2)
        self.assertTrue(all(part.text.count("\n") <= 1 for part in parts))
        self.assertTrue(all(max(map(len, part.text.splitlines())) <= 10 for part in parts))
~~~

- [ ] **Step 2: Run and verify import failure**

~~~bash
python3 -m unittest tests.test_minihud_video.AudioTest -v
~~~

Expected: FAIL because audio.py does not exist.

- [ ] **Step 3: Implement SRT parsing and merging**

Create scripts/minihud_video/audio.py:

~~~python
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess

from scripts.minihud_video.storyboard import SEGMENTS, TRANSITION_SECONDS, timeline

VOICES = ("zh-CN-YunyangNeural", "zh-CN-YunjianNeural")
RATE = "-4%"
PITCH = "-4Hz"

@dataclass(frozen=True)
class Cue:
    start: float
    end: float
    text: str

def parse_srt_time(value: str) -> float:
    hours, minutes, rest = value.split(":")
    seconds, millis = rest.split(",")
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000

def format_srt_time(value: float) -> str:
    millis = round(value * 1000)
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    seconds, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"

def parse_srt(source: str) -> list[Cue]:
    cues = []
    for block in re.split(r"\n\s*\n", source.strip()):
        lines = block.splitlines()
        timing_index = next(i for i, line in enumerate(lines) if " --> " in line)
        start, end = lines[timing_index].split(" --> ")
        text = " ".join(lines[timing_index + 1:]).strip()
        cues.append(Cue(parse_srt_time(start), parse_srt_time(end), text))
    return cues

def wrap_caption(text: str, width: int = 18) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= width:
        return compact
    split = min(width, max(1, len(compact) // 2))
    punctuation = "，。！？；：、 "
    candidates = [
        i for i in range(max(1, split - 5), min(len(compact), split + 6))
        if compact[i - 1] in punctuation
    ]
    if candidates:
        split = min(candidates, key=lambda item: abs(item - len(compact) / 2))
    return compact[:split].rstrip() + "\n" + compact[split:].lstrip()

def split_cue(cue: Cue, width: int = 18) -> list[Cue]:
    compact = re.sub(r"\s+", " ", cue.text).strip()
    chunk_size = width * 2
    chunks = [compact[index:index + chunk_size] for index in range(0, len(compact), chunk_size)]
    part_duration = (cue.end - cue.start) / len(chunks)
    return [
        Cue(
            cue.start + index * part_duration,
            cue.start + (index + 1) * part_duration,
            wrap_caption(chunk, width),
        )
        for index, chunk in enumerate(chunks)
    ]

def merge_cues(groups: list[list[Cue]], starts: list[float]) -> list[Cue]:
    merged = []
    for cues, offset in zip(groups, starts, strict=True):
        for cue in cues:
            shifted = Cue(cue.start + offset, cue.end + offset, cue.text)
            merged.extend(split_cue(shifted))
    return merged

def cues_to_srt(cues: list[Cue]) -> str:
    blocks = []
    for index, cue in enumerate(cues, 1):
        blocks.append(
            f"{index}\n{format_srt_time(cue.start)} --> {format_srt_time(cue.end)}\n{cue.text}"
        )
    return "\n\n".join(blocks) + "\n"

def probe_duration(path: Path, ffprobe: str = "/usr/bin/ffprobe") -> float:
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        check=True, capture_output=True, text=True,
    )
    return float(result.stdout.strip())

def choose_voice(edge_tts: Path) -> str:
    result = subprocess.run(
        [str(edge_tts), "--list-voices"],
        check=True, capture_output=True, text=True,
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
    for segment in SEGMENTS:
        media = narration_dir / f"{segment.id}.mp3"
        srt = narration_dir / f"{segment.id}.srt"
        subprocess.run(
            [str(edge_tts), "--voice", voice, f"--rate={RATE}", f"--pitch={PITCH}",
             "--text", segment.narration, "--write-media", str(media),
             "--write-subtitles", str(srt)],
            check=True,
        )
        duration = probe_duration(media)
        allowed = (
            segment.seconds
            if segment is SEGMENTS[-1]
            else segment.seconds - TRANSITION_SECONDS
        )
        if duration > allowed:
            raise RuntimeError(
                f"Narration {segment.id} is {duration:.2f}s, longer than {allowed:.2f}s"
            )
        outputs.append(media)
        segment_srts.append(parse_srt(srt.read_text(encoding="utf-8")))
    starts = [item.start for item in timeline()]
    merged = merge_cues(segment_srts, starts)
    merged_path = subtitle_dir / "minihud-bilibili.zh-CN.srt"
    merged_path.write_text(cues_to_srt(merged), encoding="utf-8")
    return tuple(outputs)
~~~

- [ ] **Step 4: Wire the voice command**

Add to pipeline.py:

~~~python
from scripts.minihud_video.audio import generate_voice

EDGE_TTS = BUILD_DIR / ".venv/bin/edge-tts"

def render_voice() -> tuple[Path, ...]:
    if not EDGE_TTS.is_file():
        raise RuntimeError(
            "Missing edge-tts environment. Create build/minihud-video/.venv "
            "and install edge-tts==7.2.8"
        )
    return generate_voice(BUILD_DIR, EDGE_TTS)
~~~

Extend argparse choices with voice and call render_voice().

- [ ] **Step 5: Run unit tests**

~~~bash
python3 -m unittest tests.test_minihud_video.AudioTest -v
~~~

Expected: 3 tests PASS.

- [ ] **Step 6: Create the TTS environment and generate voice**

~~~bash
python3 -m venv build/minihud-video/.venv
build/minihud-video/.venv/bin/pip install edge-tts==7.2.8
python3 -m scripts.minihud_video.pipeline voice
find build/minihud-video/narration -maxdepth 1 -name '*.mp3' | wc -l
~~~

Expected: 19 MP3 files and 19 segment SRT files; no duration error.

- [ ] **Step 7: Verify the merged subtitle**

~~~bash
sed -n '1,80p' build/minihud-video/subtitles/minihud-bilibili.zh-CN.srt
~~~

Expected: monotonic timestamps, readable Chinese, and no cue over two lines.

- [ ] **Step 8: Commit**

~~~bash
git add -- scripts/minihud_video/audio.py scripts/minihud_video/pipeline.py tests/test_minihud_video.py
git commit -m "feat: generate MiniHUD narration and subtitles"
~~~

---

### Task 5: Compose the 1080p master and subtitle release

**Files:**
- Create: scripts/minihud_video/video.py
- Modify: scripts/minihud_video/pipeline.py
- Modify: tests/test_minihud_video.py

**Interfaces:**
- Consumes: slide PNGs, narration MP3s, SEGMENTS, TRANSITION_SECONDS, and merged SRT.
- Produces: motion_filter(), build_transition_filter(), render_segments(), compose_master(), burn_subtitles(), create_contact_sheet(), and final MP4s.

- [ ] **Step 1: Write failing filter tests**

~~~python
from scripts.minihud_video.video import build_transition_filter, motion_filter

class VideoFilterTest(unittest.TestCase):
    def test_motion_filters_are_deterministic(self):
        self.assertIn("zoompan", motion_filter("push"))
        self.assertIn("zoompan", motion_filter("pull"))
        self.assertIn("scale=1920:1080", motion_filter("still"))
        with self.assertRaises(ValueError):
            motion_filter("spin")

    def test_transition_offsets_account_for_crossfades(self):
        graph, video_label, audio_label = build_transition_filter([3.3, 3.3, 3.4], 0.25)
        self.assertIn("offset=3.050", graph)
        self.assertIn("offset=6.100", graph)
        self.assertEqual(video_label, "[v2]")
        self.assertEqual(audio_label, "[a2]")
~~~

- [ ] **Step 2: Run and verify import failure**

~~~bash
python3 -m unittest tests.test_minihud_video.VideoFilterTest -v
~~~

Expected: FAIL because video.py does not exist.

- [ ] **Step 3: Implement motion and transitions**

Create scripts/minihud_video/video.py:

~~~python
from pathlib import Path
import subprocess

from scripts.minihud_video.storyboard import SEGMENTS, TRANSITION_SECONDS

FFMPEG = "/usr/bin/ffmpeg"

def motion_filter(motion: str) -> str:
    filters = {
        "still": "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30",
        "push": (
            "scale=2200:1238:force_original_aspect_ratio=increase,"
            "zoompan=z='min(zoom+0.00025,1.06)':"
            "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=30"
        ),
        "pull": (
            "scale=2200:1238:force_original_aspect_ratio=increase,"
            "zoompan=z='if(eq(on,0),1.06,max(1.0,zoom-0.00025))':"
            "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=30"
        ),
    }
    try:
        return filters[motion]
    except KeyError as error:
        raise ValueError(f"Unknown motion: {motion}") from error

def build_transition_filter(
    durations: list[float], transition: float
) -> tuple[str, str, str]:
    if len(durations) < 2:
        return "", "[0:v]", "[0:a]"
    parts = []
    video_in = "[0:v]"
    audio_in = "[0:a]"
    elapsed = durations[0]
    for index in range(1, len(durations)):
        video_out = f"[v{index}]"
        audio_out = f"[a{index}]"
        offset = elapsed - transition * index
        parts.append(
            f"{video_in}[{index}:v]xfade=transition=fade:duration={transition:.3f}:"
            f"offset={offset:.3f}{video_out}"
        )
        parts.append(
            f"{audio_in}[{index}:a]acrossfade=d={transition:.3f}:c1=tri:c2=tri{audio_out}"
        )
        video_in = video_out
        audio_in = audio_out
        elapsed += durations[index]
    return ";".join(parts), video_in, audio_in
~~~

- [ ] **Step 4: Implement fixed-duration segment rendering**

~~~python
def render_segments(build_dir: Path) -> tuple[Path, ...]:
    output_dir = build_dir / "segments"
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for index, segment in enumerate(SEGMENTS):
        image = build_dir / "slides" / f"{segment.id}.png"
        audio = build_dir / "narration" / f"{segment.id}.mp3"
        output = output_dir / f"{segment.id}.mp4"
        video_filter = motion_filter(segment.motion)
        voice_filter = f"aresample=48000,apad=pad_dur={segment.seconds},atrim=0:{segment.seconds}"
        chapter_start = index == 0 or segment.chapter != SEGMENTS[index - 1].chapter
        if chapter_start:
            audio_graph = (
                f"[1:a]{voice_filter}[voice];"
                "sine=frequency=760:sample_rate=48000:duration=0.08,volume=0.045[click];"
                "[voice][click]amix=inputs=2:duration=longest[a]"
            )
        else:
            audio_graph = f"[1:a]{voice_filter}[a]"
        subprocess.run(
            [FFMPEG, "-y", "-loop", "1", "-framerate", "30", "-i", str(image),
             "-i", str(audio), "-t", str(segment.seconds),
             "-filter_complex", f"[0:v]{video_filter}[v];{audio_graph}",
             "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium",
             "-crf", "17", "-pix_fmt", "yuv420p", "-r", "30",
             "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
             "-movflags", "+faststart", str(output)],
            check=True,
        )
        outputs.append(output)
    return tuple(outputs)
~~~

- [ ] **Step 5: Implement master, subtitle burn, and contact sheet**

~~~python
def compose_master(build_dir: Path) -> Path:
    paths = [build_dir / "segments" / f"{s.id}.mp4" for s in SEGMENTS]
    graph, video_label, audio_label = build_transition_filter(
        [s.seconds for s in SEGMENTS], TRANSITION_SECONDS
    )
    master = build_dir / "minihud-bilibili-master.mp4"
    command = [FFMPEG, "-y"]
    for path in paths:
        command.extend(["-i", str(path)])
    command.extend([
        "-filter_complex", graph, "-map", video_label, "-map", audio_label,
        "-c:v", "libx264", "-preset", "medium", "-crf", "17",
        "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart", str(master),
    ])
    subprocess.run(command, check=True)
    clean = build_dir / "minihud-bilibili-clean.mp4"
    subprocess.run(
        [FFMPEG, "-y", "-i", str(master), "-c:v", "copy",
         "-af", "loudnorm=I=-16:TP=-1:LRA=11",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
         "-movflags", "+faststart", str(clean)],
        check=True,
    )
    return clean

def burn_subtitles(build_dir: Path, clean: Path) -> Path:
    srt = build_dir / "subtitles/minihud-bilibili.zh-CN.srt"
    output = build_dir / "minihud-bilibili.mp4"
    style = (
        "FontName=Noto Sans CJK SC,FontSize=42,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H0010182A,BorderStyle=1,Outline=2,Shadow=0,"
        "Alignment=2,MarginV=72"
    )
    subprocess.run(
        [FFMPEG, "-y", "-i", str(clean),
         "-vf", f"subtitles={srt.as_posix()}:force_style='{style}'",
         "-c:v", "libx264", "-preset", "medium", "-crf", "17",
         "-pix_fmt", "yuv420p", "-c:a", "copy",
         "-movflags", "+faststart", str(output)],
        check=True,
    )
    return output

def create_contact_sheet(build_dir: Path) -> Path:
    output = build_dir / "final-contact.png"
    subprocess.run(
        [FFMPEG, "-y", "-i", str(build_dir / "minihud-bilibili.mp4"),
         "-vf", "fps=1/18,scale=480:270,tile=4x3", "-frames:v", "1",
         "-update", "1", str(output)],
        check=True,
    )
    return output
~~~

- [ ] **Step 6: Wire the video command**

~~~python
from scripts.minihud_video.video import (
    burn_subtitles, compose_master, create_contact_sheet, render_segments,
)

def render_video() -> tuple[Path, Path, Path]:
    render_segments(BUILD_DIR)
    clean = compose_master(BUILD_DIR)
    captioned = burn_subtitles(BUILD_DIR, clean)
    contact = create_contact_sheet(BUILD_DIR)
    return clean, captioned, contact
~~~

Extend argparse choices with video.

- [ ] **Step 7: Run tests and build**

~~~bash
python3 -m unittest tests.test_minihud_video.VideoFilterTest -v
python3 -m scripts.minihud_video.pipeline video
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,r_frame_rate,sample_rate,channels -of json build/minihud-video/minihud-bilibili.mp4
~~~

Expected: tests PASS; probe reports approximately 205.5 seconds, H.264 1920×1080 at 30 fps, and AAC 48 kHz stereo.

- [ ] **Step 8: Commit**

~~~bash
git add -- scripts/minihud_video/video.py scripts/minihud_video/pipeline.py tests/test_minihud_video.py
git commit -m "feat: compose MiniHUD Bilibili video"
~~~

---

### Task 6: Build the cover and publishing package

**Files:**
- Create: scripts/minihud_video/cover.html
- Create: scripts/minihud_video/publishing.py
- Modify: scripts/minihud_video/pipeline.py
- Modify: tests/test_minihud_video.py

**Interfaces:**
- Consumes: shape.webp, timeline(), and chapter names.
- Produces: 1600×1000 PNG/JPG cover and bilibili-publish.md.

- [ ] **Step 1: Write failing cover and publishing tests**

~~~python
from scripts.minihud_video.publishing import build_publish_markdown, chapter_lines

class PublishingTest(unittest.TestCase):
    def test_cover_source_has_approved_copy_and_dimensions(self):
        source = (ROOT / "scripts/minihud_video/cover.html").read_text(encoding="utf-8")
        for phrase in ("width:1600px", "height:1000px", "一个 MOD", "看清隐藏规则", "6 个实用场景"):
            self.assertIn(phrase, source)
        self.assertLessEqual(source.count("<img"), 2)

    def test_publish_copy_is_complete_and_honest(self):
        copy = build_publish_markdown()
        for phrase in (
            "MiniHUD", "Minecraft Java 版 26.2", "Fabric Loader",
            "MaLiLib", "Servux", "不同版本", "收藏", "置顶评论",
        ):
            self.assertIn(phrase, copy)
        self.assertNotIn("下一期", copy)
        self.assertNotIn("15 种", copy)

    def test_chapters_are_monotonic(self):
        lines = chapter_lines()
        self.assertEqual(lines[0], "00:00 冷开场")
        self.assertTrue(any("结构边界" in line for line in lines))
        self.assertTrue(lines[-1].endswith("收藏与关注"))
~~~

- [ ] **Step 2: Run and verify failures**

~~~bash
python3 -m unittest tests.test_minihud_video.PublishingTest -v
~~~

Expected: FAIL because cover.html and publishing.py do not exist.

- [ ] **Step 3: Create the cover**

Create scripts/minihud_video/cover.html:

~~~html
<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<style>
*{box-sizing:border-box}html,body{margin:0;width:1600px;height:1000px;overflow:hidden;background:#030712}
body{position:relative;font-family:"Noto Sans CJK SC","Microsoft YaHei",sans-serif;color:#fff}
.bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:42% 50%;filter:saturate(1.25) contrast(1.08) brightness(.72);transform:scale(1.04)}
.shade{position:absolute;inset:0;background:linear-gradient(90deg,rgba(3,7,18,.08),rgba(3,7,18,.48) 52%,rgba(3,7,18,.96)),linear-gradient(0deg,rgba(3,7,18,.78),transparent 52%)}
.ring{position:absolute;left:92px;top:110px;width:860px;height:640px;border:8px solid #67e8f9;border-radius:50%;filter:drop-shadow(0 0 22px #22d3ee);transform:rotate(-8deg)}
.copy{position:absolute;right:72px;top:108px;width:700px;text-align:right}
.tag{display:inline-block;padding:14px 24px;border:2px solid #67e8f9;border-radius:99px;background:#06172bd9;color:#67e8f9;font-size:28px;font-weight:900}
h1{margin:28px 0 18px;font-size:112px;line-height:.98;letter-spacing:-.06em;text-shadow:0 8px 35px #000}
h1 span{display:block}h1 span:last-child{color:#facc15}
.sub{font-size:38px;font-weight:900;color:#e2e8f0}
.features{position:absolute;left:86px;bottom:72px;display:flex;gap:16px}
.features span{padding:14px 20px;border:1px solid #ffffff55;border-radius:12px;background:#030712d9;font-size:26px;font-weight:850}
.name{position:absolute;right:74px;bottom:66px;color:#67e8f9;font-size:34px;font-weight:1000}
</style>
</head>
<body>
  <img class="bg" src="../../source/extra/MOD介绍/minihud/assets/screenshots/shape.webp" alt="">
  <div class="shade"></div><div class="ring"></div>
  <div class="copy">
    <span class="tag">MiniHUD · 6 个实用场景</span>
    <h1><span>一个 MOD</span><span>看清隐藏规则</span></h1>
    <div class="sub">遇到问题，就开对应功能</div>
  </div>
  <div class="features"><span>结构</span><span>范围</span><span>施工</span><span>预览</span></div>
  <div class="name">MINECRAFT JAVA</div>
</body>
</html>
~~~

- [ ] **Step 4: Implement publishing copy**

Create scripts/minihud_video/publishing.py:

~~~python
from scripts.minihud_video.storyboard import timeline

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
    chapters = "\n".join(chapter_lines())
    return f"""# B 站发布信息

## 推荐标题

一个 MOD 看清 Minecraft 隐藏规则｜MiniHUD 6 个实用场景

## 简介

结构藏进地形、装置范围只能靠估、圆心半径不好确定、潜影盒还要逐个打开？本期不背菜单，直接按六类常见问题介绍 MiniHUD：遇到什么问题，开启什么功能，以及画面会得到什么结果。

本视频以 **Minecraft Java 版 26.2** 和与其匹配的最新 MiniHUD、MaLiLib 为功能基线。核心思路在多个版本中相通，但具体菜单、功能数量和规则可能不同，请以对应版本下载页为准。

安装关系：Fabric Loader + MiniHUD + MaLiLib。MiniHUD 安装在客户端；多人服真实结构边界需要服务器端 Servux 提供数据，精确性能信息也取决于服务器支持。

官方项目：
- MiniHUD：https://github.com/maruohon/minihud
- Modrinth：https://modrinth.com/mod/minihud
- CurseForge：https://www.curseforge.com/minecraft/mc-mods/minihud

## 视频章节

{chapters}

## 推荐标签

Minecraft、我的世界、MiniHUD、Fabric、MaLiLib、模组推荐、生存技巧、技术生存、建筑辅助

## 置顶评论建议

六类问题速查：迷路看信息 HUD；遮挡看结构边界；选址看环境覆盖；估算看范围参考；施工看形状参考；整理和排查看预览与性能信息。建议先收藏，需要时按问题回来找功能。
"""
~~~

- [ ] **Step 5: Wire cover and publishing commands**

~~~python
from scripts.minihud_video.publishing import build_publish_markdown

COVER_PATH = ROOT / "scripts/minihud_video/cover.html"

def render_cover() -> tuple[Path, Path]:
    png = BUILD_DIR / "minihud-cover-1600x1000.png"
    jpg = BUILD_DIR / "minihud-cover-1600x1000.jpg"
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [CHROME, "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
         "--run-all-compositor-stages-before-draw", "--virtual-time-budget=1000",
         "--window-size=1600,1000", f"--screenshot={png}", COVER_PATH.resolve().as_uri()],
        check=True,
    )
    subprocess.run(
        ["/usr/bin/ffmpeg", "-y", "-i", str(png), "-q:v", "2", str(jpg)],
        check=True,
    )
    return png, jpg

def write_publish_guide() -> Path:
    output = BUILD_DIR / "bilibili-publish.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_publish_markdown(), encoding="utf-8")
    return output
~~~

Replace main() with the complete final dispatcher:

~~~python
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=("slides", "voice", "video", "cover", "publish", "all"),
    )
    args = parser.parse_args()
    actions = {
        "slides": render_slides,
        "voice": render_voice,
        "video": render_video,
        "cover": render_cover,
        "publish": write_publish_guide,
    }
    if args.command == "all":
        for name in ("slides", "voice", "video", "cover", "publish"):
            result = actions[name]()
            print(name, result)
        return
    print(actions[args.command]())

if __name__ == "__main__":
    main()
~~~

- [ ] **Step 6: Run tests and generate assets**

~~~bash
python3 -m unittest tests.test_minihud_video.PublishingTest -v
python3 -m scripts.minihud_video.pipeline cover
python3 -m scripts.minihud_video.pipeline publish
ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 build/minihud-video/minihud-cover-1600x1000.png
~~~

Expected: tests PASS; probe prints 1600,1000; PNG, JPG, and publishing guide exist.

- [ ] **Step 7: Commit**

~~~bash
git add -- scripts/minihud_video/cover.html scripts/minihud_video/publishing.py scripts/minihud_video/pipeline.py tests/test_minihud_video.py
git commit -m "feat: add MiniHUD cover and publishing package"
~~~

---

### Task 7: Run the complete build and final verification

**Files:**
- Verify: all tracked files from Tasks 1–6.
- Generate: build/minihud-video/**.

**Interfaces:**
- Consumes: pipeline.py all.
- Produces: complete delivery package and completion evidence.

- [ ] **Step 1: Run every source test**

~~~bash
python3 -m unittest tests.test_minihud_presentation tests.test_minihud_video -v
node tests/minihud_presentation_browser_test.cjs
python3 -m sphinx -b html source build/html
~~~

Expected: all Python tests PASS, browser output contains errors: [], and Sphinx exits 0.

- [ ] **Step 2: Run the full production command**

~~~bash
python3 -m scripts.minihud_video.pipeline all
~~~

Expected: no narration-duration error and all slides, narration, segments, subtitles, videos, cover, and publishing outputs are created.

- [ ] **Step 3: Verify streams and duration**

~~~bash
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,r_frame_rate,sample_rate,channels -of json build/minihud-video/minihud-bilibili.mp4
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,r_frame_rate,sample_rate,channels -of json build/minihud-video/minihud-bilibili-clean.mp4
~~~

Expected: duration 205–215 seconds; H.264 1920×1080 at 30/1; AAC 48000 Hz stereo.

- [ ] **Step 4: Verify loudness**

~~~bash
ffmpeg -hide_banner -i build/minihud-video/minihud-bilibili.mp4 -filter_complex ebur128=peak=true -f null -
~~~

Expected: integrated loudness near -16 LUFS and true peak no higher than -1 dBFS. If integrated loudness differs by more than 1 LU, rerun the existing loudnorm output stage without changing narration speed.

- [ ] **Step 5: Verify subtitles and cover**

~~~bash
python3 -c "from pathlib import Path; p=Path('build/minihud-video/subtitles/minihud-bilibili.zh-CN.srt'); assert p.is_file() and '按住 Shift' in p.read_text(encoding='utf-8')"
ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 build/minihud-video/minihud-cover-1600x1000.jpg
~~~

Expected: subtitle assertion passes; cover reports 1600,1000.

- [ ] **Step 6: Inspect visual evidence**

Open build/minihud-video/final-contact.png and build/minihud-video/minihud-cover-1600x1000.png. Confirm:

- opening contains structure, shape, and preview results;
- no paused-menu button is the primary focus of HUD shots;
- beacon boundary and chunk grid are legible;
- subtitles fit in two lines above player controls;
- outro says 收藏 and 关注 with no 15-shape promise;
- cover stays readable at 400×250.

- [ ] **Step 7: Check package and repository**

~~~bash
find build/minihud-video -maxdepth 2 -type f | sort
git status --short
git log -n 7 --oneline
~~~

Expected package:

~~~text
build/minihud-video/bilibili-publish.md
build/minihud-video/final-contact.png
build/minihud-video/minihud-bilibili-clean.mp4
build/minihud-video/minihud-bilibili-master.mp4
build/minihud-video/minihud-bilibili.mp4
build/minihud-video/minihud-cover-1600x1000.jpg
build/minihud-video/minihud-cover-1600x1000.png
build/minihud-video/subtitles/minihud-bilibili.zh-CN.srt
~~~

Expected git status is clean because build/ is ignored and all source changes were committed task by task.
