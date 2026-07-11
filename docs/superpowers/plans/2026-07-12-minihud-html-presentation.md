# MiniHUD HTML PPT Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an eight-slide, self-guided Chinese MiniHUD HTML presentation that comprehensively groups user-facing features and teaches their use through player scenarios.

**Architecture:** Keep the existing repository pattern: one standalone HTML deck under `source/extra/` and one Sphinx RST landing page under `source/MOD介绍/`. The deck owns its CSS, semantic slide markup, keyboard/mouse/touch navigation, scene switches, and one reusable detail dialog; standard-library static tests and a Chrome DevTools Protocol smoke test verify content and behavior without adding package dependencies.

**Tech Stack:** HTML5, CSS3, vanilla JavaScript, Python `unittest`, Node.js standard library, headless Google Chrome CDP, Sphinx/reStructuredText.

## Global Constraints

- Audience is 8–21 years old; Chinese copy starts with plain-language conclusions and adds depth through judgment, scenarios, and limitations.
- The deck contains exactly 8 slides.
- User guidance starts from player problems and tasks, not source code, Java classes, internal implementation, or raw config fields.
- Feature coverage includes five groups: information HUD, environment/grid, ranges/boundaries, building/shapes, and previews/inspection.
- Content is based on official MiniHUD branch `pre-rewrite/fabric/1.21.1-masa`, commit `faebd93e39e4464294d55d3e18c248397c2ca0eb`, while acknowledging version differences.
- Preserve the Item Scroller series language: dark high-contrast full-screen slides, colored chapters, cards, keyboard/mouse/touch navigation, responsive layout, and export mode.
- Do not show broken video controls; use inline HTML/CSS visual demonstrations while MiniHUD videos do not exist.
- Do not use CDN fonts, remote scripts, or remote media; external official project/download links are allowed as anchors.
- Preserve unrelated working-tree changes and stage only files named by each task.

## File Map

- `tests/test_minihud_presentation.py`: parses the HTML and RST, enforcing slide count, feature/scenario coverage, semantic controls, and offline assets.
- `tests/minihud_presentation_browser_test.cjs`: opens the local deck in headless Chrome and checks navigation, detail-dialog behavior, scene switches, mobile layout, and console errors.
- `source/extra/MOD介绍/minihud/index.html`: standalone eight-slide presentation and all visual/interaction behavior.
- `source/MOD介绍/minihud/minihud.rst`: Sphinx landing page with the deck link, scenario-first summary, data limitations, installation, and official links.
- `source/MOD介绍/index.rst`: contains the MiniHUD toctree entry; preserve the existing line and include it in the documentation commit.

---

### Task 1: Lock the presentation contract with failing tests

**Files:**
- Create: `tests/test_minihud_presentation.py`
- Create: `tests/minihud_presentation_browser_test.cjs`
- Read: `.tmp-itemscroller-modal-test.cjs`
- Test: `source/extra/MOD介绍/minihud/index.html`
- Test: `source/MOD介绍/minihud/minihud.rst`

**Interfaces:**
- Consumes: current MiniHUD draft and the Item Scroller Chrome CDP testing pattern.
- Produces: the required DOM contract: eight `.slide` elements, `go(index)`, `openDetail(key, trigger)`, `closeDetail()`, `[data-scene]` switches, `#detail-modal`, `#nav`, and scenario/feature copy.

- [ ] **Step 1: Create the static contract test**

Create `tests/test_minihud_presentation.py` with this complete content:

```python
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "source/extra/MOD介绍/minihud/index.html"
RST_PATH = ROOT / "source/MOD介绍/minihud/minihud.rst"


class DeckParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.slide_ids = []
        self.assets = []
        self.detail_keys = []
        self.scene_keys = []
        self.ids = set()
        self.text = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        classes = values.get("class", "").split()
        element_id = values.get("id")
        if element_id:
            self.ids.add(element_id)
        if "slide" in classes:
            self.slide_ids.append(element_id)
        if tag in {"script", "link", "img", "video", "audio", "source", "iframe"}:
            target = values.get("src") or values.get("href")
            if target:
                self.assets.append(target)
        if "data-detail" in values:
            self.detail_keys.append(values["data-detail"])
        if "data-scene" in values:
            self.scene_keys.append(values["data-scene"])

    def handle_data(self, data):
        self.text.append(data)


class MiniHudPresentationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = HTML_PATH.read_text(encoding="utf-8")
        cls.rst = RST_PATH.read_text(encoding="utf-8")
        cls.parser = DeckParser()
        cls.parser.feed(cls.html)
        cls.copy = re.sub(r"\s+", " ", " ".join(cls.parser.text))

    def test_deck_has_exactly_eight_unique_slides(self):
        self.assertEqual(cls_count := len(self.parser.slide_ids), 8, cls_count)
        self.assertEqual(len(set(self.parser.slide_ids)), 8)
        self.assertNotIn(None, self.parser.slide_ids)

    def test_all_feature_groups_are_present(self):
        for phrase in ("信息 HUD", "环境与网格", "范围与边界", "建筑与形状", "预览与检查"):
            self.assertIn(phrase, self.copy)

    def test_scenario_copy_is_comprehensive(self):
        required = (
            "探索", "性能排查", "光照", "群系边界", "信标", "潮涌核心",
            "随机刻", "史莱姆区块", "结构边界", "村民交易", "生成球",
            "方框", "圆柱", "方块线", "地图预览", "潜影盒", "物品栏预览",
            "Servux", "Carpet", "MaLiLib", "TPS/MSPT", "Mob Cap",
        )
        missing = [phrase for phrase in required if phrase not in self.copy]
        self.assertEqual(missing, [])

    def test_interaction_contract_is_semantic(self):
        self.assertTrue({"deck", "nav", "detail-modal", "detail-title", "detail-body", "detail-close"}.issubset(self.parser.ids))
        self.assertGreaterEqual(len(set(self.parser.detail_keys)), 5)
        self.assertTrue({"explore", "build", "performance"}.issubset(self.parser.scene_keys))
        for token in ("function go", "function openDetail", "function closeDetail", "ArrowRight", "touchstart", "prefers-reduced-motion"):
            self.assertIn(token, self.html)

    def test_media_and_code_are_offline_and_audience_safe(self):
        remote_assets = [asset for asset in self.parser.assets if asset.startswith(("http://", "https://", "//"))]
        self.assertEqual(remote_assets, [])
        for forbidden in ("InfoToggle.java", "RendererToggle.java", "ShapeType.java", "src/main/java"):
            self.assertNotIn(forbidden, self.html)
        self.assertNotRegex(self.html, r"<button[^>]+disabled[^>]*class=[\"'][^\"']*video")

    def test_rst_links_and_summarizes_the_deck(self):
        for phrase in ("index.html", "信息 HUD", "环境与网格", "范围与边界", "建筑与形状", "预览与检查", "Servux", "MaLiLib"):
            self.assertIn(phrase, self.rst)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Create the browser behavior test**

Create `tests/minihud_presentation_browser_test.cjs`. Reuse the null-delimited CDP transport from `.tmp-itemscroller-modal-test.cjs`, but use these exact assertions after navigating to the MiniHUD file URL:

```javascript
const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
const { spawn } = require("child_process");

const chrome = spawn("google-chrome", [
  "--headless", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
  "--hide-scrollbars", "--remote-debugging-pipe", "about:blank",
], { stdio: ["ignore", "ignore", "pipe", "pipe", "pipe"] });

let nextId = 0;
let input = "";
const pending = new Map();
const errors = [];

chrome.stdio[4].on("data", (chunk) => {
  input += chunk.toString();
  let boundary;
  while ((boundary = input.indexOf("\0")) >= 0) {
    const raw = input.slice(0, boundary);
    input = input.slice(boundary + 1);
    if (!raw) continue;
    const message = JSON.parse(raw);
    if (message.method === "Runtime.exceptionThrown") errors.push(message.params.exceptionDetails.text);
    if (!message.id || !pending.has(message.id)) continue;
    const request = pending.get(message.id);
    pending.delete(message.id);
    clearTimeout(request.timer);
    if (message.error) request.reject(new Error(message.error.message));
    else request.resolve(message.result || {});
  }
});

function send(method, params = {}, sessionId) {
  return new Promise((resolve, reject) => {
    const id = ++nextId;
    const timer = setTimeout(() => {
      pending.delete(id);
      reject(new Error(`CDP timeout: ${method}`));
    }, 10000);
    pending.set(id, { resolve, reject, timer });
    const message = { id, method, params };
    if (sessionId) message.sessionId = sessionId;
    chrome.stdio[3].write(JSON.stringify(message) + "\0");
  });
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function evaluate(sessionId, expression) {
  const result = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true }, sessionId);
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.text);
  return result.result.value;
}

(async () => {
  const target = await send("Target.createTarget", { url: "about:blank" });
  const attached = await send("Target.attachToTarget", { targetId: target.targetId, flatten: true });
  const sessionId = attached.sessionId;
  await send("Page.enable", {}, sessionId);
  await send("Runtime.enable", {}, sessionId);
  await send("Emulation.setDeviceMetricsOverride", {
    width: 1366, height: 768, deviceScaleFactor: 1, mobile: false,
    screenWidth: 1366, screenHeight: 768,
  }, sessionId);
  const url = pathToFileURL(path.resolve("source/extra/MOD介绍/minihud/index.html")).href;
  await send("Page.navigate", { url }, sessionId);
  await sleep(700);

  const initial = await evaluate(sessionId, `({ slides: slides.length, cur, active: document.querySelector('.slide.active').id, dots: dots.length })`);
  if (initial.slides !== 8 || initial.cur !== 0 || initial.active !== "s1" || initial.dots !== 8) throw new Error(`Bad initial state: ${JSON.stringify(initial)}`);

  await evaluate(sessionId, `document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight' }))`);
  await sleep(550);
  const afterKey = await evaluate(sessionId, `({ cur, active: document.querySelector('.slide.active').id })`);
  if (afterKey.cur !== 1 || afterKey.active !== "s2") throw new Error(`Keyboard navigation failed: ${JSON.stringify(afterKey)}`);

  await evaluate(sessionId, `go(2); document.querySelector('[data-scene="performance"]').click()`);
  const scene = await evaluate(sessionId, `({ cur, selected: document.querySelector('[data-scene].selected').dataset.scene, hud: document.getElementById('hud-lines').textContent })`);
  if (scene.cur !== 2 || scene.selected !== "performance" || !scene.hud.includes("TPS/MSPT")) throw new Error(`Scene switch failed: ${JSON.stringify(scene)}`);

  await evaluate(sessionId, `document.querySelector('[data-detail]').click()`);
  const opened = await evaluate(sessionId, `({ hidden: detailModal.hidden, title: detailTitle.textContent, body: detailBody.textContent })`);
  if (opened.hidden || !opened.title || opened.body.length < 40) throw new Error(`Detail dialog failed: ${JSON.stringify(opened)}`);
  await evaluate(sessionId, `document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))`);
  const closed = await evaluate(sessionId, `detailModal.hidden`);
  if (!closed) throw new Error("Detail dialog did not close with Escape");

  await send("Emulation.setDeviceMetricsOverride", {
    width: 390, height: 844, deviceScaleFactor: 1, mobile: true,
    screenWidth: 390, screenHeight: 844,
  }, sessionId);
  await evaluate(sessionId, `go(7)`);
  await sleep(250);
  const mobile = await evaluate(sessionId, `(() => {
    const slide = document.querySelector('.slide.active');
    return { width: document.documentElement.scrollWidth, viewport: innerWidth, scrollable: slide.scrollHeight >= slide.clientHeight };
  })()`);
  if (mobile.width > mobile.viewport || !mobile.scrollable) throw new Error(`Mobile layout failed: ${JSON.stringify(mobile)}`);

  const shot = await send("Page.captureScreenshot", { format: "png" }, sessionId);
  fs.writeFileSync("/tmp/minihud-mobile.png", Buffer.from(shot.data, "base64"));
  console.log(JSON.stringify({ initial, afterKey, scene, opened, mobile, errors }, null, 2));
  await send("Target.closeTarget", { targetId: target.targetId });
  chrome.kill("SIGKILL");
  setTimeout(() => process.exit(errors.length ? 1 : 0), 100);
})().catch((error) => {
  console.error(error.stack || error.message);
  chrome.kill("SIGKILL");
  setTimeout(() => process.exit(1), 100);
});
```

- [ ] **Step 3: Run both tests to prove the current draft violates the contract**

Run:

```bash
python -m unittest tests/test_minihud_presentation.py -v
node tests/minihud_presentation_browser_test.cjs
```

Expected: the static test fails because the draft has 10 slides and lacks the complete five-group/scenario copy; the browser test fails its initial eight-slide assertion.

- [ ] **Step 4: Commit the contract tests**

```bash
git add tests/test_minihud_presentation.py tests/minihud_presentation_browser_test.cjs
git commit -m "test: define MiniHUD presentation contract"
```

---

### Task 2: Replace the draft with the eight-slide scenario deck

**Files:**
- Modify: `source/extra/MOD介绍/minihud/index.html`
- Test: `tests/test_minihud_presentation.py`
- Test: `tests/minihud_presentation_browser_test.cjs`

**Interfaces:**
- Consumes: Task 1 DOM contract and the approved five-group feature matrix.
- Produces: eight sections `#s1` through `#s8`; global `slides`, `dots`, `cur`, `go(index)`, `openDetail(key, trigger)`, `closeDetail()`; scene keys `explore`, `build`, `performance`; reusable details keyed by the five feature groups and multiplayer data.

- [ ] **Step 1: Replace the page body with exactly eight scenario-first slides**

Use this exact semantic outline; fill each card with the approved copy shown here, not raw configuration names:

```html
<main id="deck">
  <section class="slide s1 active" id="s1" aria-labelledby="title-s1">
    <span class="snum">01 / 08</span><span class="pill">MINECRAFT MOD 介绍</span>
    <h1 class="hero-title" id="title-s1">MiniHUD</h1>
    <p class="hero-sub">把看不见的信息、边界与范围画出来</p>
    <div class="badge-row"><span>信息 HUD</span><span>环境与网格</span><span>范围与边界</span><span>建筑与形状</span><span>预览与检查</span></div>
  </section>
  <section class="slide s2" id="s2" aria-labelledby="title-s2">
    <span class="snum">02 / 08</span><span class="pill">从问题出发</span>
    <h2 id="title-s2">你现在想解决什么？</h2>
    <div class="problem-grid">
      <button data-detail="info">我在哪里、朝哪走？</button><button data-detail="environment">哪里太暗、边界在哪？</button>
      <button data-detail="range">农场为什么效率不对？</button><button data-detail="shape">中心、半径和高度怎么定？</button>
      <button data-detail="preview">地图、潜影盒或实体里有什么？</button><button data-detail="multiplayer">服务器为什么看不到某些数据？</button>
    </div>
  </section>
  <section class="slide s3" id="s3" aria-labelledby="title-s3">
    <span class="snum">03 / 08</span><span class="pill">场景 1 · 探索与排查</span>
    <h2 id="title-s3">只显示当前真正需要的信息</h2>
    <div class="scene-tabs"><button class="selected" data-scene="explore">探索</button><button data-scene="build">建筑</button><button data-scene="performance">性能排查</button></div>
    <div class="hud-demo" id="hud-lines" aria-live="polite">坐标 · 朝向 · 群系 · 时间 · 参考点距离</div>
    <p>信息 HUD 还能按需查看移动、世界、区块、目标方块、目标实体、光照、天气、FPS、内存、延迟、TPS/MSPT 与 Mob Cap。</p>
  </section>
  <section class="slide s4" id="s4" aria-labelledby="title-s4">
    <span class="snum">04 / 08</span><span class="pill">场景 2 · 照明与边界</span>
    <h2 id="title-s4">哪里需要处理，直接标在世界里</h2>
    <div class="layer-demo" aria-label="光照、方块网格、区块和群系边界示意"></div>
    <div class="category-grid"><article>光照等级</article><article>方块与区块网格</article><article>群系边界</article><article>区域文件与高级诊断</article></div>
    <p>发现问题 → 选择覆盖层 → 观察颜色或线框 → 现场处理 → 关闭覆盖层复查。刷怪和光照规则要结合当前游戏版本。</p>
  </section>
  <section class="slide s5" id="s5" aria-labelledby="title-s5">
    <span class="snum">05 / 08</span><span class="pill">场景 3 · 农场与结构</span>
    <h2 id="title-s5">把效率相关的范围一次看懂</h2>
    <div class="task-grid"><article>史莱姆农场：史莱姆区块</article><article>挂机点：生成球、32 格与 128 格范围</article><article>作物与机器：随机刻区域</article><article>结构农场：结构边界</article><article>装置覆盖：信标与潮涌核心</article><article>村民筛选：村民交易信息</article></div>
    <div class="data-legend"><span>本地可用</span><span>需要种子</span><span>需要服务器数据</span></div>
  </section>
  <section class="slide s6" id="s6" aria-labelledby="title-s6">
    <span class="snum">06 / 08</span><span class="pill">场景 4 · 规划与查看</span>
    <h2 id="title-s6">先画再建，先看再开</h2>
    <div class="split"><article><h3>建筑与形状</h3><p>方框 · 圆 / 圆柱 · 方块线 · 方块球体 · 可调生成球</p><div class="shape-demo"></div></article><article><h3>预览与检查</h3><p>地图预览 · 潜影盒 · 物品栏预览 · 蜜蜂和六角恐龙等提示</p><div class="inventory-demo"></div></article></div>
    <p>形状只是视觉参考，不会自动放置或拆除方块。</p>
  </section>
  <section class="slide s7" id="s7" aria-labelledby="title-s7">
    <span class="snum">07 / 08</span><span class="pill">多人游戏与正确配置</span>
    <h2 id="title-s7">看不到，不一定是坏了</h2>
    <div class="source-flow"><article>单人世界<br>本地数据最完整</article><article>知道世界种子<br>可判断种子相关区域</article><article>Servux / Carpet<br>同步结构、Mob Cap、精确 TPS/MSPT 等数据</article></div>
    <ol><li>检查主开关与单项开关</li><li>确认数据来源和服务器规则</li><li>检查距离、维度和快捷键冲突</li></ol>
    <p>安装匹配版本的 MiniHUD 与 MaLiLib；具体支持范围以对应下载页为准。</p>
  </section>
  <section class="slide s8" id="s8" aria-labelledby="title-s8">
    <span class="snum">08 / 08</span><span class="pill">按场景速查</span>
    <h2 id="title-s8">遇到问题，就开对应的一组</h2>
    <div class="quick-grid"><article>日常探索 → 信息 HUD</article><article>照明与建筑 → 光照、网格、区块边界、形状</article><article>技术生存 → 史莱姆区块、生成球、随机刻、结构、Mob Cap</article><article>交易和物品 → 村民交易、目标实体、地图/潜影盒/物品栏预览</article><article>性能排查 → FPS、内存、实体、区块更新、延迟、TPS/MSPT</article></div>
    <p><kbd>H</kbd> 主渲染开关 · <kbd>H + C</kbd> 配置入口 · 快捷键均可修改</p>
  </section>
</main>
<nav id="nav" aria-label="幻灯片导航"></nav>
<div class="detail-modal" id="detail-modal" hidden><section role="dialog" aria-modal="true" aria-labelledby="detail-title"><header><h2 id="detail-title"></h2><button id="detail-close" type="button" aria-label="关闭详情">×</button></header><div id="detail-body"></div></section></div>
```

- [ ] **Step 2: Implement the Item Scroller-compatible visual system and MiniHUD-specific diagrams**

In the same file, define these selectors and behaviors with concrete CSS values:

```css
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:100%;height:100%;overflow:hidden;background:#030712;color:#f8fafc}
body{font-family:Inter,"Noto Sans SC","Microsoft YaHei",system-ui,sans-serif}
#deck{position:fixed;inset:0}.slide{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:5vh 6vw 10vh;opacity:0;pointer-events:none;transform:translateY(48px) scale(.98);transition:.45s ease;overflow:hidden}.slide.active{opacity:1;pointer-events:auto;transform:none}
.slide::before{content:"";position:absolute;inset:0;z-index:-2;background:radial-gradient(circle at 78% 18%,rgba(34,211,238,.18),transparent 34%),#030712}.slide::after{content:"";position:absolute;inset:0;z-index:-1;background-image:linear-gradient(rgba(96,165,250,.055) 1px,transparent 1px),linear-gradient(90deg,rgba(96,165,250,.055) 1px,transparent 1px);background-size:48px 48px;mask-image:linear-gradient(#000,transparent 92%)}
.snum{position:absolute;left:4vw;top:3vh;color:#ffffff99;font-weight:900;letter-spacing:.16em}.pill{margin-bottom:2vh;padding:.38em 1.1em;border:1px solid #67e8f988;border-radius:999px;color:#67e8f9;font-weight:900}.hero-title{font-size:clamp(4rem,9vw,9rem);line-height:.9}.hero-title,h2{background:linear-gradient(135deg,#fff,#67e8f9,#60a5fa);background-clip:text;-webkit-background-clip:text;color:transparent;text-align:center;font-weight:1000}.hero-sub{margin-top:2vh;font-size:clamp(1rem,2vw,1.8rem);font-weight:750;text-align:center}h2{font-size:clamp(2.1rem,5vw,5rem);line-height:1;margin-bottom:2vh}
.badge-row,.scene-tabs,.data-legend{display:flex;flex-wrap:wrap;justify-content:center;gap:12px;margin-top:3vh}.badge-row span,.data-legend span,.scene-tabs button{padding:.55em 1em;border:1px solid #ffffff33;border-radius:999px;background:#ffffff12;color:#fff;font-weight:850}.scene-tabs button.selected{border-color:#67e8f9;background:#0891b233}
.problem-grid,.category-grid,.task-grid,.quick-grid,.split,.source-flow{display:grid;width:min(1200px,100%);gap:clamp(10px,1.4vw,18px)}.problem-grid,.category-grid,.task-grid,.quick-grid{grid-template-columns:repeat(3,minmax(0,1fr))}.split{grid-template-columns:1fr 1fr}.source-flow{grid-template-columns:repeat(3,1fr)}article,.problem-grid button{padding:clamp(14px,2vw,26px);border:1px solid #ffffff29;border-radius:18px;background:#ffffff12;color:#f8fafc;box-shadow:0 18px 45px #0004;font:inherit;text-align:left}.problem-grid button{cursor:pointer;font-weight:900}
.hud-demo,.layer-demo,.shape-demo,.inventory-demo{position:relative;width:min(1050px,100%);min-height:220px;margin:1vh auto 2vh;border:1px solid #ffffff29;border-radius:18px;background:#07111fd9;overflow:hidden}.hud-demo{padding:24px;border-left:4px solid #67e8f9;color:#cffafe;font:800 clamp(.85rem,1.4vw,1.1rem)/1.8 ui-monospace,monospace}.layer-demo{background-image:radial-gradient(circle at 30% 60%,#ef444466 0 10%,transparent 11%),linear-gradient(#22d3ee55 2px,transparent 2px),linear-gradient(90deg,#22d3ee55 2px,transparent 2px);background-size:auto,64px 64px,64px 64px}.shape-demo::before{content:"";position:absolute;inset:18% 22%;border:4px solid #c084fc;border-radius:50%;box-shadow:0 0 32px #a855f766}.inventory-demo{display:grid;grid-template-columns:repeat(9,34px);place-content:center;gap:5px}.inventory-demo::before{content:"🗺️  📦  🐝  🪣";grid-column:1/-1;text-align:center;font-size:2rem;letter-spacing:.7em}
#nav{position:fixed;left:50%;bottom:3vh;z-index:50;display:flex;gap:8px;transform:translateX(-50%);padding:.65em 1em;border:1px solid #ffffff1f;border-radius:999px;background:#0008}.dot{width:9px;height:9px;border:0;border-radius:9px;background:#ffffff44}.dot.on{width:28px;background:#67e8f9}
.detail-modal{position:fixed;inset:0;z-index:100;display:grid;place-items:center;padding:24px;background:#01040aeb}.detail-modal[hidden]{display:none}.detail-modal>section{width:min(820px,96vw);max-height:84vh;overflow:auto;border:1px solid #ffffff33;border-radius:18px;background:#07111f}.detail-modal header{display:flex;justify-content:space-between;align-items:center;padding:16px 20px;border-bottom:1px solid #ffffff20}.detail-modal header h2{font-size:1.35rem;margin:0}.detail-modal header button{width:38px;height:38px;border:1px solid #ffffff33;border-radius:8px;background:#ffffff12;color:#fff;font-size:1.4rem}.detail-modal #detail-body{padding:20px;line-height:1.75;color:#ffffffd8}
body.export .slide{transition:none;padding:3vh 4vw 4vh}body.export #nav{display:none}@media(max-width:900px){.slide{justify-content:flex-start;padding:7vh 5vw 13vh;overflow-y:auto}.problem-grid,.category-grid,.task-grid,.quick-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.split,.source-flow{grid-template-columns:1fr}}@media(max-width:600px){.problem-grid,.category-grid,.task-grid,.quick-grid{grid-template-columns:1fr}.detail-modal{padding:0}.detail-modal>section{width:100%;max-height:100vh;border-radius:0}}@media(prefers-reduced-motion:reduce){*,*::before,*::after{scroll-behavior:auto!important;animation-duration:.01ms!important;transition-duration:.01ms!important}}
```

- [ ] **Step 3: Implement navigation, details, and scenario switches**

Add this complete interaction contract at the end of the HTML:

```javascript
const slides=[...document.querySelectorAll('.slide')];
const nav=document.getElementById('nav');
let cur=0,detailOpen=false,lastDetailTrigger=null,wheelAt=0,tx=0,ty=0;
slides.forEach((slide,index)=>{const dot=document.createElement('button');dot.className='dot'+(index===0?' on':'');dot.type='button';dot.title=slide.querySelector('.pill')?.textContent||`第 ${index+1} 页`;dot.addEventListener('click',e=>{e.stopPropagation();go(index)});nav.appendChild(dot)});
const dots=[...document.querySelectorAll('.dot')];
function go(index){if(index<0||index>=slides.length||index===cur)return;slides[cur].classList.remove('active');slides[index].classList.add('active');dots[cur].classList.remove('on');dots[index].classList.add('on');cur=index}
const sceneCopy={explore:'坐标 · 朝向 · 群系 · 时间 · 参考点距离',build:'方块坐标 · 区块坐标 · 区块内坐标 · 目标方块属性',performance:'FPS · 内存 · 实体数量 · 区块更新 · 延迟 · TPS/MSPT'};
document.querySelectorAll('[data-scene]').forEach(button=>button.addEventListener('click',()=>{document.querySelectorAll('[data-scene]').forEach(item=>item.classList.toggle('selected',item===button));document.getElementById('hud-lines').textContent=sceneCopy[button.dataset.scene]}));
const detailCopy={
  info:{title:'信息 HUD',body:'从导航定位、行动状态、世界环境、目标方块和实体，到 FPS、内存、延迟与 TPS/MSPT，都可以按当前任务选择。推荐一次保留 4–6 行。'},
  environment:{title:'环境与网格',body:'光照覆盖层负责发现暗区；方块、区块、群系和区域文件边界负责定位。颜色和线框只是提示，处理完成后应关闭覆盖层复查。'},
  range:{title:'范围与边界',body:'史莱姆区块、随机刻、结构边界、信标和潮涌核心范围，以及生成和消失距离适合技术生存规划。多人服要先确认数据来源。'},
  shape:{title:'建筑与形状',body:'方框、圆柱、方块线、球体与生成球用于标中心、半径、高度、路线和施工边界。它们不会自动放置或拆除方块。'},
  preview:{title:'预览与检查',body:'地图、潜影盒和支持的物品栏可以快速预览；目标方块、目标实体、蜜蜂与六角恐龙等信息可减少反复打开界面。'},
  multiplayer:{title:'多人服务器的数据限制',body:'单人世界能直接读取本地数据；史莱姆区块可能需要种子；结构、Mob Cap、精确 TPS/MSPT 或实体数据可能需要 Servux、Carpet 和服务器许可。'}
};
const detailModal=document.getElementById('detail-modal'),detailTitle=document.getElementById('detail-title'),detailBody=document.getElementById('detail-body'),detailClose=document.getElementById('detail-close');
function openDetail(key,trigger){const copy=detailCopy[key];if(!copy)return;lastDetailTrigger=trigger;detailTitle.textContent=copy.title;detailBody.textContent=copy.body;detailModal.hidden=false;detailOpen=true;detailClose.focus()}
function closeDetail(){if(!detailOpen)return;detailModal.hidden=true;detailOpen=false;lastDetailTrigger?.focus()}
document.querySelectorAll('[data-detail]').forEach(button=>button.addEventListener('click',()=>openDetail(button.dataset.detail,button)));detailClose.addEventListener('click',closeDetail);detailModal.addEventListener('click',e=>{if(e.target===detailModal)closeDetail()});
document.addEventListener('keydown',e=>{if(detailOpen){if(e.key==='Escape')closeDetail();return}if(['ArrowRight','ArrowDown',' '].includes(e.key)){e.preventDefault();go(cur+1)}else if(['ArrowLeft','ArrowUp'].includes(e.key)){e.preventDefault();go(cur-1)}else if(e.key==='Home')go(0);else if(e.key==='End')go(slides.length-1)});
document.getElementById('deck').addEventListener('click',e=>{if(!e.target.closest('button,a'))go(cur+1)});document.addEventListener('wheel',e=>{if(detailOpen)return;const now=Date.now();if(now-wheelAt<550)return;wheelAt=now;go(cur+(e.deltaY>0?1:-1))},{passive:true});document.addEventListener('touchstart',e=>{tx=e.touches[0].clientX;ty=e.touches[0].clientY},{passive:true});document.addEventListener('touchend',e=>{if(detailOpen)return;const dx=e.changedTouches[0].clientX-tx,dy=e.changedTouches[0].clientY-ty;if(Math.max(Math.abs(dx),Math.abs(dy))<35)return;go(cur+((Math.abs(dx)>Math.abs(dy)?dx:dy)<0?1:-1))},{passive:true});
const params=new URLSearchParams(location.search);if(params.get('export')==='1')document.body.classList.add('export');const requested=Number(params.get('slide'));if(Number.isInteger(requested)&&requested>=1&&requested<=slides.length)go(requested-1);
```

- [ ] **Step 4: Run the static and browser tests**

Run the HTML-specific static checks and browser test:

```bash
python -m unittest \
  tests.test_minihud_presentation.MiniHudPresentationTest.test_deck_has_exactly_eight_unique_slides \
  tests.test_minihud_presentation.MiniHudPresentationTest.test_all_feature_groups_are_present \
  tests.test_minihud_presentation.MiniHudPresentationTest.test_scenario_copy_is_comprehensive \
  tests.test_minihud_presentation.MiniHudPresentationTest.test_interaction_contract_is_semantic \
  tests.test_minihud_presentation.MiniHudPresentationTest.test_media_and_code_are_offline_and_audience_safe \
  -v
node tests/minihud_presentation_browser_test.cjs
```

Expected: all five HTML-specific static tests pass; the browser test exits `0` with successful navigation, scene-switch, dialog, and mobile-layout states.

- [ ] **Step 5: Commit the completed deck**

```bash
git add source/extra/MOD介绍/minihud/index.html
git commit -m "feat: rebuild MiniHUD presentation by user scenarios"
```

---

### Task 3: Align the Sphinx landing page with the scenario deck

**Files:**
- Modify: `source/MOD介绍/minihud/minihud.rst`
- Modify: `source/MOD介绍/index.rst`
- Test: `tests/test_minihud_presentation.py`

**Interfaces:**
- Consumes: the eight-slide deck and five feature group names from Task 2.
- Produces: a discoverable Sphinx entry whose link resolves through `html_extra_path = ['extra']` and whose summary matches the deck.

- [ ] **Step 1: Replace the RST page with the scenario-first summary**

Use this complete document:

```rst
MiniHUD - 信息、边界与范围可视化
====================================

.. raw:: html

   <p style="margin:0 0 24px;">
     <a href="index.html" target="_blank" style="display:inline-block;padding:10px 20px;background:#0891b2;color:#fff;border-radius:6px;text-decoration:none;font-weight:bold;">
       🎮 打开 MiniHUD PPT 风格演示
     </a>
   </p>

MiniHUD 是 maruohon（Masa）开发的客户端信息与覆盖层 MOD。它把玩家关心的信息、网格、范围和边界直接显示在游戏画面中，帮助玩家少开完整 F3、少做手工测量，并在建造前先看清空间规则。

按使用场景选择
------------------------

.. list-table::
   :header-rows: 1
   :widths: 22 34 44

   * - 我现在要做什么
     - 推荐功能分类
     - 可以解决什么问题
   * - 探索、定位或排查性能
     - 信息 HUD
     - 查看坐标、朝向、群系、光照、目标方块、FPS、内存、延迟和可获得的 TPS/MSPT、Mob Cap 等信息
   * - 检查照明和空间位置
     - 环境与网格
     - 显示光照、方块网格、区块边界、群系边界和区域文件边界
   * - 规划农场和装置
     - 范围与边界
     - 查看史莱姆区块、随机刻、生成与消失范围、结构边界、信标和潮涌核心范围
   * - 规划大型建筑
     - 建筑与形状
     - 创建方框、圆柱、方块线、球体与可调生成球，标记中心、半径、高度和施工范围
   * - 快速确认物品或实体内容
     - 预览与检查
     - 预览地图、潜影盒和支持的物品栏，并查看村民交易或目标实体信息

推荐使用方法
------------------------

#. 按默认 ``H + C`` 打开配置，先说明自己要解决的问题。
#. 只启用当前场景需要的信息行或覆盖层，不要一次全部打开。
#. 根据颜色、数字和线框判断范围，回到现场处理。
#. 按默认 ``H`` 临时关闭主渲染，检查结果并保持画面清楚。

多人游戏限制
------------------------

MiniHUD 是客户端 MOD，但客户端并不总能得到世界的全部数据：

- 单人世界通常可以直接读取本地数据。
- 史莱姆区块等种子相关功能需要正确的世界种子。
- 结构边界、Mob Cap、精确 TPS/MSPT 或部分实体数据在多人服上可能需要 **Servux**、**Carpet** 或服务器许可。
- 服务器没有提供数据时，功能可能不显示、不完整或只能估算；应遵守服务器规则。

安装与官方项目
------------------------

- 安装与当前 Minecraft 版本匹配的 **MiniHUD** 和 **MaLiLib**。
- 默认 ``H`` 控制主渲染，``H + C`` 打开配置；快捷键可以修改。
- 作者：maruohon（Masa）
- GitHub：https://github.com/maruohon/minihud/
- CurseForge：https://www.curseforge.com/minecraft/mc-mods/minihud
- Modrinth：https://modrinth.com/mod/minihud
```

- [ ] **Step 2: Preserve the existing MiniHUD toctree entry**

Ensure `source/MOD介绍/index.rst` contains this line once under its existing `.. toctree::` block, without reformatting unrelated entries:

```rst
   minihud/minihud
```

- [ ] **Step 3: Run the static contract test**

Run:

```bash
python -m unittest tests/test_minihud_presentation.py -v
```

Expected: all tests pass, including RST link/summary coverage.

- [ ] **Step 4: Commit the Sphinx content**

```bash
git add source/MOD介绍/minihud/minihud.rst source/MOD介绍/index.rst
git commit -m "docs: add MiniHUD scenario guide"
```

---

### Task 4: Verify build, layouts, and final feature coverage

**Files:**
- Verify: `source/extra/MOD介绍/minihud/index.html`
- Verify: `source/MOD介绍/minihud/minihud.rst`
- Verify: `source/MOD介绍/index.rst`
- Verify: `tests/test_minihud_presentation.py`
- Verify: `tests/minihud_presentation_browser_test.cjs`

**Interfaces:**
- Consumes: completed deck, RST page, and automated tests.
- Produces: evidence that the deck is functional at desktop/mobile sizes, copied by Sphinx, and complete against the approved feature matrix.

- [ ] **Step 1: Run the complete automated test set**

```bash
python -m unittest tests/test_minihud_presentation.py -v
node tests/minihud_presentation_browser_test.cjs
```

Expected: Python reports all tests `OK`; Node exits `0`, prints eight slides, successful navigation/dialog/scene states, and `errors: []`.

- [ ] **Step 2: Build the Sphinx site from a clean output directory**

```bash
.venv/bin/sphinx-build -E -a -b html source build/html
```

Expected: exit code `0`; warnings unrelated to MiniHUD may be recorded separately, but there are no missing-document or broken-path errors for `minihud/minihud`.

- [ ] **Step 3: Verify the generated paths and links**

```bash
test -f build/html/MOD介绍/minihud/minihud.html
test -f build/html/MOD介绍/minihud/index.html
rg -n 'MiniHUD|index.html' build/html/MOD介绍/minihud/minihud.html
```

Expected: both files exist and the generated RST page contains the independent presentation link.

- [ ] **Step 4: Capture and inspect representative slides**

Run these exact local-file captures after resolving the absolute HTML path with `pwd`:

```bash
google-chrome --headless --no-sandbox --disable-gpu --hide-scrollbars --window-size=1366,768 --screenshot=/tmp/minihud-slide-1.png "file:///home/zhaojd5/codes/github/My_Study_MC/source/extra/MOD%E4%BB%8B%E7%BB%8D/minihud/index.html?slide=1&export=1"
google-chrome --headless --no-sandbox --disable-gpu --hide-scrollbars --window-size=1366,768 --screenshot=/tmp/minihud-slide-4.png "file:///home/zhaojd5/codes/github/My_Study_MC/source/extra/MOD%E4%BB%8B%E7%BB%8D/minihud/index.html?slide=4&export=1"
google-chrome --headless --no-sandbox --disable-gpu --hide-scrollbars --window-size=1366,768 --screenshot=/tmp/minihud-slide-5.png "file:///home/zhaojd5/codes/github/My_Study_MC/source/extra/MOD%E4%BB%8B%E7%BB%8D/minihud/index.html?slide=5&export=1"
google-chrome --headless --no-sandbox --disable-gpu --hide-scrollbars --window-size=1366,768 --screenshot=/tmp/minihud-slide-6.png "file:///home/zhaojd5/codes/github/My_Study_MC/source/extra/MOD%E4%BB%8B%E7%BB%8D/minihud/index.html?slide=6&export=1"
google-chrome --headless --no-sandbox --disable-gpu --hide-scrollbars --window-size=1366,768 --screenshot=/tmp/minihud-slide-8.png "file:///home/zhaojd5/codes/github/My_Study_MC/source/extra/MOD%E4%BB%8B%E7%BB%8D/minihud/index.html?slide=8&export=1"
```

Open the five PNG files with the workspace image viewer, then inspect `/tmp/minihud-mobile.png` produced by the browser test at 390×844.

Expected: titles, cards, diagrams, bottom navigation, and detail controls do not overlap or clip; mobile has no horizontal overflow.

- [ ] **Step 5: Check feature coverage and working-tree scope**

```bash
git diff --check HEAD~3..HEAD
git status --short
rg -n '信息 HUD|群系边界|潮涌核心|随机刻|史莱姆区块|村民交易|方块线|地图预览|潜影盒|Servux|Carpet' source/extra/MOD介绍/minihud/index.html source/MOD介绍/minihud/minihud.rst
```

Expected: no whitespace errors; every named feature is present; only intentional MiniHUD/test changes remain, and no Item Scroller file changed.

## Plan Coverage Map

- Exact eight-page structure: Task 1 static/browser assertions; Task 2 markup.
- Complete five-group classification: Task 1 phrase matrix; Task 2 slides 3–6; Task 3 RST table.
- Scenario-first usage: Task 2 slides 2–8; Task 3 recommended method.
- Multiplayer/data limits: Task 2 slides 5 and 7 plus detail dialog; Task 3 limitations.
- Item Scroller family style and interactions: Task 2 CSS/JS; Task 4 desktop/mobile validation.
- Offline and accessibility requirements: Task 1 asset/semantic assertions; Task 2 dialog/focus/reduced-motion/mobile CSS.
- Sphinx integration: Task 3 toctree/RST; Task 4 clean build and generated-path checks.
