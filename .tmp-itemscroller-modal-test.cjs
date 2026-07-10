const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
const { spawn } = require("child_process");

const chrome = spawn("google-chrome", [
  "--headless",
  "--no-sandbox",
  "--disable-gpu",
  "--disable-dev-shm-usage",
  "--hide-scrollbars",
  "--remote-debugging-pipe",
  "about:blank",
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
    if (message.method === "Runtime.exceptionThrown") {
      errors.push(message.params.exceptionDetails.text);
    }
    if (!message.id) continue;
    const request = pending.get(message.id);
    if (!request) continue;
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

async function evaluate(sessionId, expression, contextId) {
  const params = { expression, returnByValue: true, awaitPromise: true };
  if (contextId) params.contextId = contextId;
  const result = await send("Runtime.evaluate", params, sessionId);
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.text);
  return result.result.value;
}

async function waitForAnimationFrame(sessionId) {
  for (let attempt = 0; attempt < 50; attempt++) {
    const tree = await send("Page.getFrameTree", {}, sessionId);
    const child = tree.frameTree.childFrames && tree.frameTree.childFrames[0];
    if (child && child.frame.url.includes("/animations/") && child.frame.url.includes("autoplay=1")) {
      return child.frame.id;
    }
    await sleep(100);
  }
  throw new Error("Animation iframe did not load");
}

async function waitUntilDone(sessionId, frameId) {
  const world = await send("Page.createIsolatedWorld", { frameId, worldName: `test-${Date.now()}` }, sessionId);
  for (let attempt = 0; attempt < 80; attempt++) {
    const state = await evaluate(sessionId, `(() => {
      const status = document.getElementById("status");
      return status ? { text: status.textContent, done: status.classList.contains("done") } : null;
    })()`, world.executionContextId);
    if (state && state.done) return state;
    await sleep(150);
  }
  throw new Error("Animation did not finish");
}

(async () => {
  const target = await send("Target.createTarget", { url: "about:blank" });
  const attached = await send("Target.attachToTarget", { targetId: target.targetId, flatten: true });
  const sessionId = attached.sessionId;
  await send("Page.enable", {}, sessionId);
  await send("Runtime.enable", {}, sessionId);
  await send("Emulation.setDeviceMetricsOverride", {
    width: 1440,
    height: 1000,
    deviceScaleFactor: 1,
    mobile: false,
    screenWidth: 1440,
    screenHeight: 1000,
  }, sessionId);

  const url = pathToFileURL(path.resolve("source/extra/MOD介绍/itemscroller/index.html")).href;
  await send("Page.navigate", { url }, sessionId);
  await sleep(800);

  await evaluate(sessionId, `go(6, 1)`);
  await sleep(650);
  const entries = await evaluate(sessionId, `[...document.querySelectorAll(".animation-trigger")].map((el) => ({ title: el.dataset.title, file: el.dataset.animation }))`);
  const results = [];

  for (let index = 0; index < entries.length; index++) {
    await evaluate(sessionId, `document.querySelectorAll(".animation-trigger")[${index}].click()`);
    const openState = await evaluate(sessionId, `({ hidden: animationModal.hidden, title: animationTitle.textContent, src: animationFrame.src, cur })`);
    const frameId = await waitForAnimationFrame(sessionId);
    const done = await waitUntilDone(sessionId, frameId);
    results.push({ entry: entries[index], openState, done });
    if (index === 3) {
      const shot = await send("Page.captureScreenshot", { format: "png" }, sessionId);
      fs.writeFileSync("/tmp/itemscroller-context-player-desktop.png", Buffer.from(shot.data, "base64"));
    }
    await evaluate(sessionId, `animationClose.click()`);
    const closed = await evaluate(sessionId, `({ hidden: animationModal.hidden, src: animationFrame.getAttribute("src"), cur })`);
    if (!closed.hidden || closed.cur !== 6) throw new Error(`Player did not close cleanly for ${entries[index].title}`);
  }

  await send("Emulation.setDeviceMetricsOverride", {
    width: 390,
    height: 900,
    deviceScaleFactor: 1,
    mobile: true,
    screenWidth: 390,
    screenHeight: 900,
  }, sessionId);
  await sleep(250);
  await evaluate(sessionId, `document.querySelectorAll(".animation-trigger")[6].click()`);
  await waitForAnimationFrame(sessionId);
  await sleep(900);
  const mobileLayout = await evaluate(sessionId, `(() => {
    const modal = animationModal.getBoundingClientRect();
    const player = document.querySelector(".animation-player").getBoundingClientRect();
    return { innerWidth, innerHeight, modal: { width: modal.width, height: modal.height }, player: { width: player.width, height: player.height }, title: animationTitle.textContent };
  })()`);
  const mobileShot = await send("Page.captureScreenshot", { format: "png" }, sessionId);
  fs.writeFileSync("/tmp/itemscroller-context-player-mobile.png", Buffer.from(mobileShot.data, "base64"));

  console.log(JSON.stringify({ entries, results, mobileLayout, errors }, null, 2));
  const failed = errors.length || results.length !== 7 || results.some((item) => item.openState.hidden || !item.done.done || !item.openState.src.includes(item.entry.file));
  await send("Target.closeTarget", { targetId: target.targetId });
  chrome.kill("SIGKILL");
  setTimeout(() => process.exit(failed ? 1 : 0), 100);
})().catch((error) => {
  console.error(error.stack || error.message);
  chrome.kill("SIGKILL");
  setTimeout(() => process.exit(1), 100);
});
