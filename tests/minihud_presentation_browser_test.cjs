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
  const result = await send("Runtime.evaluate", {
    expression,
    returnByValue: true,
    awaitPromise: true,
  }, sessionId);
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.text);
  return result.result.value;
}

(async () => {
  const target = await send("Target.createTarget", { url: "about:blank" });
  const attached = await send("Target.attachToTarget", {
    targetId: target.targetId,
    flatten: true,
  });
  const sessionId = attached.sessionId;
  await send("Page.enable", {}, sessionId);
  await send("Runtime.enable", {}, sessionId);
  await send("Emulation.setDeviceMetricsOverride", {
    width: 1366,
    height: 768,
    deviceScaleFactor: 1,
    mobile: false,
    screenWidth: 1366,
    screenHeight: 768,
  }, sessionId);

  const url = pathToFileURL(
    path.resolve("source/extra/MOD介绍/minihud/index.html"),
  ).href;
  await send("Page.navigate", { url }, sessionId);
  await sleep(700);

  const initial = await evaluate(sessionId, `({
    slides: slides.length,
    cur,
    active: document.querySelector('.slide.active').id,
    dots: dots.length,
  })`);
  if (initial.slides !== 8 || initial.cur !== 0 || initial.active !== "s1" || initial.dots !== 8) {
    throw new Error(`Bad initial state: ${JSON.stringify(initial)}`);
  }

  await evaluate(sessionId, `document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight' }))`);
  await sleep(550);
  const afterKey = await evaluate(sessionId, `({
    cur,
    active: document.querySelector('.slide.active').id,
  })`);
  if (afterKey.cur !== 1 || afterKey.active !== "s2") {
    throw new Error(`Keyboard navigation failed: ${JSON.stringify(afterKey)}`);
  }

  await evaluate(sessionId, `go(2); document.querySelector('[data-scene="performance"]').click()`);
  const scene = await evaluate(sessionId, `({
    cur,
    selected: document.querySelector('[data-scene].selected').dataset.scene,
    hud: document.getElementById('hud-lines').textContent,
  })`);
  if (scene.cur !== 2 || scene.selected !== "performance" || !scene.hud.includes("TPS/MSPT")) {
    throw new Error(`Scene switch failed: ${JSON.stringify(scene)}`);
  }

  await evaluate(sessionId, `document.querySelector('[data-detail]').click()`);
  const opened = await evaluate(sessionId, `({
    hidden: detailModal.hidden,
    title: detailTitle.textContent,
    body: detailBody.textContent,
  })`);
  if (opened.hidden || !opened.title || opened.body.length < 40) {
    throw new Error(`Detail dialog failed: ${JSON.stringify(opened)}`);
  }
  await evaluate(sessionId, `document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))`);
  const closed = await evaluate(sessionId, `detailModal.hidden`);
  if (!closed) throw new Error("Detail dialog did not close with Escape");

  await send("Emulation.setDeviceMetricsOverride", {
    width: 390,
    height: 844,
    deviceScaleFactor: 1,
    mobile: true,
    screenWidth: 390,
    screenHeight: 844,
  }, sessionId);
  await evaluate(sessionId, `go(7)`);
  await sleep(250);
  const mobile = await evaluate(sessionId, `(() => {
    const slide = document.querySelector('.slide.active');
    return {
      width: document.documentElement.scrollWidth,
      viewport: innerWidth,
      scrollable: slide.scrollHeight >= slide.clientHeight,
    };
  })()`);
  if (mobile.width > mobile.viewport || !mobile.scrollable) {
    throw new Error(`Mobile layout failed: ${JSON.stringify(mobile)}`);
  }

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
