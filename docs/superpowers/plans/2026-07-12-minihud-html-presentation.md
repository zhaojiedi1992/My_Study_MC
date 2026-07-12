# MiniHUD Six-Scenario HTML Presentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rework the existing eight-slide MiniHUD deck into a polished, task-led presentation for 8–18-year-old players, using six player scenarios and the user's exported `minihud.json` as a behind-the-scenes visual reference.

**Architecture:** Keep the established standalone HTML deck, vanilla JavaScript interactions, reusable detail dialog, Sphinx landing page, Python static contract tests, and Node/Chrome browser smoke test. The eight slides become one cover, one clickable task map, and six scenario slides; configuration names never appear in student-facing copy, while the exported colors and shortcuts remain accurate.

**Tech Stack:** HTML5, CSS3, vanilla JavaScript, Python 3 `unittest`, Node.js standard library, headless Google Chrome CDP, Sphinx/reStructuredText.

## Global Constraints

- Audience is 8–18 years old; each slide uses one short task sentence, one dominant visual, and no more than three primary judgment steps.
- The deck contains exactly eight slides: cover, task map, and six player scenarios.
- Scenario order is fixed: 日常游玩 → 外出探索 → 工程选址 → 机制规划 → 开始施工 → 完工排查.
- Concrete examples such as 林地府邸, 信标, and 圆形刷怪塔 appear inside scenes, never as scene titles.
- Structure copy must state that MiniHUD does not remotely scan for structures and does not use `/locate`; usable local/server structure data is required.
- `C:\Users\zhaojd5\AppData\Roaming\PrismLauncher\instances\26.2\minecraft\config\minihud.json` is the source for visual colors, available feature examples, `H`, and `H + C`; raw field names stay out of the deck.
- Preserve keyboard, wheel, pointer, touch navigation, focus management, reduced-motion support, offline operation, and responsive mobile scrolling.
- Do not touch the user's untracked `source/extra/MOD介绍/minihud/videos/` files.

## File Map

- `tests/test_minihud_presentation.py`: static eight-slide, six-scenario, configuration-derived visual, copy, and offline contract.
- `tests/minihud_presentation_browser_test.cjs`: browser navigation, scenario switch, structure reveal, building view, dialog, focus, and mobile behavior.
- `source/extra/MOD介绍/minihud/index.html`: complete presentation, CSS visuals, and vanilla JavaScript interactions.
- `source/MOD介绍/minihud/minihud.rst`: website entry and six-scenario summary.

---

### Task 1: Lock the six-scenario contract with failing tests

**Files:**
- Modify: `tests/test_minihud_presentation.py`
- Modify: `tests/minihud_presentation_browser_test.cjs`
- Test: `source/extra/MOD介绍/minihud/index.html`

**Interfaces:**
- Consumes: existing `DeckParser`, global `slides`, `dots`, `cur`, `go(index)`, and detail dialog functions.
- Produces: required scene copy; interaction keys `data-scene`, `data-structure-view`, `data-site-layer`, `data-range`, `data-build-view`, and `data-check`.

- [ ] **Step 1: Replace the static scenario assertions**

Add these exact tests and remove the old regex that requires the previous range-task card markup:

```python
def test_six_player_scenarios_drive_the_deck(self):
    scenarios = (
        "日常游玩", "外出探索", "工程选址",
        "机制规划", "开始施工", "完工排查",
    )
    positions = [self.copy.index(scene) for scene in scenarios]
    self.assertEqual(positions, sorted(positions))
    for task in (
        "随时掌握信息", "看清结构", "检查周围环境",
        "确认影响范围", "把设计画进世界", "快速找到问题",
    ):
        self.assertIn(task, self.copy)

def test_examples_support_scenes_without_becoming_scene_titles(self):
    for example in ("林地府邸", "信标", "潮涌核心", "圆形刷怪塔"):
        self.assertIn(example, self.copy)
    for slide_title in re.findall(r'<h2[^>]*class="sec-title"[^>]*>(.*?)</h2>', self.html, re.S):
        plain = re.sub(r"<[^>]+>", "", slide_title)
        self.assertNotIn("林地府邸", plain)
        self.assertNotIn("信标", plain)

def test_structure_scene_states_ability_boundary(self):
    for phrase in ("不是远程搜索", "不使用 /locate", "结构主边界", "组成部分"):
        self.assertIn(phrase, self.copy)

def test_exported_config_informs_visuals_not_student_copy(self):
    for color in ("#ff6500", "#e060ff", "#ffb040", "#fff040", "#60ff40", "#30b0b0"):
        self.assertIn(color, self.html.lower())
    for raw_name in (
        "overlayBeaconRange", "overlayStructureMainToggle",
        "shapeRenderer", "StructureToggles", "InfoTypeToggles",
    ):
        self.assertNotIn(raw_name, self.html)
    self.assertIn("H + C", self.copy)

def test_scenario_controls_are_present(self):
    for attribute in (
        "data-structure-view", "data-site-layer", "data-range",
        "data-build-view", "data-check",
    ):
        self.assertIn(attribute, self.html)
```

- [ ] **Step 2: Extend the browser behavior test**

After the existing information-HUD scene assertion, add exact checks for structure reveal and construction view:

```javascript
await evaluate(sessionId, `go(3); document.querySelector('[data-structure-view="on"]').click()`);
const structure = await evaluate(sessionId, `({
  cur,
  selected: document.querySelector('[data-structure-view].selected').dataset.structureView,
  revealed: document.getElementById('structure-stage').classList.contains('revealed'),
})`);
if (structure.cur !== 3 || structure.selected !== "on" || !structure.revealed) {
  throw new Error(`Structure reveal failed: ${JSON.stringify(structure)}`);
}

await evaluate(sessionId, `go(6); document.querySelector('[data-build-view="elevation"]').click()`);
const building = await evaluate(sessionId, `({
  cur,
  selected: document.querySelector('[data-build-view].selected').dataset.buildView,
  mode: document.getElementById('build-stage').dataset.view,
})`);
if (building.cur !== 6 || building.selected !== "elevation" || building.mode !== "elevation") {
  throw new Error(`Building view failed: ${JSON.stringify(building)}`);
}
```

Include `{ structure, building }` in the final printed result.

- [ ] **Step 3: Run the focused tests and confirm RED**

Run:

```bash
python3 -m unittest tests/test_minihud_presentation.py -v
node tests/minihud_presentation_browser_test.cjs
```

Expected: static failures for missing six-scenario copy and data attributes; browser failure because `data-structure-view="on"` does not exist.

- [ ] **Step 4: Commit the failing contract**

```bash
git add tests/test_minihud_presentation.py tests/minihud_presentation_browser_test.cjs
git commit -m "test: define MiniHUD six-scenario deck contract"
```

---

### Task 2: Rebuild the deck around six player tasks

**Files:**
- Modify: `source/extra/MOD介绍/minihud/index.html`
- Test: `tests/test_minihud_presentation.py`
- Test: `tests/minihud_presentation_browser_test.cjs`

**Interfaces:**
- Consumes: Task 1 data attributes and the existing navigation/dialog globals.
- Produces: slides `#s1` through `#s8`; interactive stages `#hud-lines`, `#structure-stage`, `#site-stage`, `#range-stage`, `#build-stage`, and `#check-stage`.

- [ ] **Step 1: Replace slide content with the approved semantic outline**

Use exactly this slide/title mapping, with concrete examples placed in supporting cards or visual captions:

```html
<section class="slide s1 active" id="s1"><h1>MiniHUD</h1><p>把看不见的信息、边界与范围画出来</p></section>
<section class="slide s2" id="s2"><h2 class="sec-title">今天，你准备完成什么任务？</h2><!-- six-node task route --></section>
<section class="slide s3" id="s3"><span>场景 1 · 日常游玩</span><h2 class="sec-title">随时掌握真正有用的信息</h2><!-- HUD stage --></section>
<section class="slide s4" id="s4"><span>场景 2 · 外出探索</span><h2 class="sec-title">让藏在地形里的结构变清楚</h2><!-- structure stage --></section>
<section class="slide s5" id="s5"><span>场景 3 · 工程选址</span><h2 class="sec-title">开工前，先检查周围环境</h2><!-- site stage --></section>
<section class="slide s6" id="s6"><span>场景 4 · 机制规划</span><h2 class="sec-title">把看不见的影响范围画出来</h2><!-- range stage --></section>
<section class="slide s7" id="s7"><span>场景 5 · 开始施工</span><h2 class="sec-title">先把设计画进世界，再动手</h2><!-- build stage --></section>
<section class="slide s8" id="s8"><span>场景 6 · 完工排查</span><h2 class="sec-title">沿着线索，快速找到问题</h2><!-- check stage --></section>
```

The task map contains six numbered buttons with a short question and calls `go(2)` through `go(7)`. Keep five feature-group labels only as small capability tags, not navigation headings.

- [ ] **Step 2: Build configuration-informed visual stages**

Define these exact color tokens and use them in the relevant visuals:

```css
:root{
  --mansion:#ff6500;
  --beacon-1:#e060ff;
  --beacon-2:#ffb040;
  --beacon-3:#fff040;
  --beacon-4:#60ff40;
  --conduit:#30ffff;
  --shape:#30b0b0;
  --shape-box:#50a0a0;
  --spawn:#a04050;
}
```

Implement each stage with one dominant diagram and at most three visible instruction steps:

- `#structure-stage`: forest/terrain silhouettes, a mansion silhouette, orange main/component boxes, and off/on controls. Its copy says “不是远程搜索，也不使用 /locate；需要先探索到附近并获得可用数据。”
- `#site-stage`: plain terrain that switches between light markers, block/chunk grid, and biome/slime overlays.
- `#range-stage`: beacon four-level range as the default; conduit and spawn/range modes replace the main diagram instead of adding more cards.
- `#build-stage`: top-down circle/box plan and elevation view with a center axis, tower levels, AFK point, and translucent sphere.
- `#check-stage`: a three-step diagnostic path and a compact strip explicitly labeled 地图预览、潜影盒、物品栏预览、村民交易.

- [ ] **Step 3: Add the scenario switch data and handlers**

Retain `sceneCopy` for the HUD scene and add these complete mode maps and handlers:

```javascript
const stageBindings = [
  ['data-structure-view', 'structureView', 'structure-stage', 'view'],
  ['data-site-layer', 'siteLayer', 'site-stage', 'layer'],
  ['data-range', 'range', 'range-stage', 'range'],
  ['data-build-view', 'buildView', 'build-stage', 'view'],
  ['data-check', 'check', 'check-stage', 'check'],
];

stageBindings.forEach(([attribute, datasetKey, stageId, stateKey]) => {
  document.querySelectorAll(`[${attribute}]`).forEach(button => {
    button.addEventListener('click', () => {
      const group = button.parentElement.querySelectorAll(`[${attribute}]`);
      group.forEach(item => item.classList.toggle('selected', item === button));
      const stage = document.getElementById(stageId);
      const value = button.dataset[datasetKey];
      stage.dataset[stateKey] = value;
      if (stageId === 'structure-stage') stage.classList.toggle('revealed', value === 'on');
    });
  });
});
```

Use matching HTML attributes: `data-structure-view`, `data-site-layer`, `data-range`, `data-build-view`, and `data-check`. Preserve existing `go`, modal focus trap, wheel, pointer, keyboard, and touch behavior unchanged unless the browser test identifies a regression.

- [ ] **Step 4: Polish for 8–18-year-old readers and responsive layouts**

Apply these measurable layout rules:

```css
.sec-title{max-width:18ch;font-size:clamp(2rem,4.5vw,4rem);line-height:1.02}
.scene-lead{max-width:54ch;font-size:clamp(.92rem,1.35vw,1.12rem)}
.task-route{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.scene-layout{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(260px,.65fr);gap:18px}
@media(max-width:760px){
  .task-route,.scene-layout{grid-template-columns:1fr}
  .slide{overflow-y:auto;padding:58px 18px 96px}
  .visual-stage{min-height:300px}
}
```

Use large scene numbers, concise verb-led labels, Minecraft-like grid/terrain motifs, short state transitions, visible focus rings, and text labels in addition to color. Ensure all interactive buttons are `type="button"` and have meaningful `aria-label` text.

- [ ] **Step 5: Run tests and confirm GREEN**

Run:

```bash
python3 -m unittest tests/test_minihud_presentation.py -v
node tests/minihud_presentation_browser_test.cjs
```

Expected: all static tests pass; browser output reports eight slides, successful structure/building switches, no console errors, and a scrollable 390×844 layout.

- [ ] **Step 6: Commit the rebuilt deck**

```bash
git add source/extra/MOD介绍/minihud/index.html
git commit -m "feat: retell MiniHUD through six player scenarios"
```

---

### Task 3: Align the Sphinx landing page

**Files:**
- Modify: `source/MOD介绍/minihud/minihud.rst`
- Test: `tests/test_minihud_presentation.py`

**Interfaces:**
- Consumes: the final six scenario names and feature coverage from Task 2.
- Produces: a concise website entry using the same scenario order and ability limits.

- [ ] **Step 1: Replace the five-category table with six player tasks**

Use these exact row labels and summaries:

```rst
   * - 日常游玩：随时掌握信息
     - 坐标、方向、群系、时间与性能信息
   * - 外出探索：看清结构
     - 在可用数据范围内显示结构主边界和组成部分，不进行远程搜索
   * - 工程选址：检查环境
     - 光照、网格、区块、群系和可生成区域
   * - 机制规划：确认范围
     - 信标、潮涌核心、随机刻与生物生成或消失范围
   * - 开始施工：画出设计
     - 方框、圆柱、方块线和球体辅助占地、半径与高度规划
   * - 完工排查：找到问题
     - Mob Cap、TPS/MSPT、目标信息与快速预览
```

Keep the installation, MaLiLib, Servux/Carpet, `H`, and `H + C` guidance. Change the introductory audience language to “适合第一次接触 MiniHUD 的同学按任务了解功能”.

- [ ] **Step 2: Run the static contract**

Run:

```bash
python3 -m unittest tests/test_minihud_presentation.py -v
```

Expected: all tests pass and the RST link/feature assertions remain green.

- [ ] **Step 3: Commit the landing-page update**

```bash
git add source/MOD介绍/minihud/minihud.rst
git commit -m "docs: align MiniHUD guide with player scenarios"
```

---

### Task 4: Verify the final presentation

**Files:**
- Verify: `source/extra/MOD介绍/minihud/index.html`
- Verify: `source/MOD介绍/minihud/minihud.rst`
- Verify: `tests/test_minihud_presentation.py`
- Verify: `tests/minihud_presentation_browser_test.cjs`

**Interfaces:**
- Consumes: Tasks 1–3.
- Produces: fresh verification evidence and screenshots at desktop/mobile sizes.

- [ ] **Step 1: Run the full MiniHUD test set**

```bash
python3 -m unittest tests/test_minihud_presentation.py -v
node tests/minihud_presentation_browser_test.cjs
```

Expected: all assertions pass and browser `errors` is `[]`.

- [ ] **Step 2: Build the documentation**

```bash
python3 -m sphinx -W --keep-going -b html source /tmp/my-study-mc-minihud-html
```

Expected: exit code 0; `/tmp/my-study-mc-minihud-html/MOD介绍/minihud/index.html` exists.

- [ ] **Step 3: Inspect repository state and scope**

```bash
git diff --check
git status --short
git log -4 --oneline
```

Expected: no whitespace errors; only the user's pre-existing untracked `source/extra/MOD介绍/minihud/videos/` remains outside the committed work.

- [ ] **Step 4: Record verification evidence in the handoff**

Report the Python test count, browser interaction results, Sphinx build result, changed files, and the untouched untracked videos directory. Do not claim completion without current command output.
