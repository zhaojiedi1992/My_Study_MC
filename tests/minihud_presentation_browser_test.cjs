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
    if (message.method === "Runtime.consoleAPICalled" && ["error", "assert"].includes(message.params.type)) {
      errors.push(message.params.args.map((arg) => arg.value || arg.description || "console error").join(" "));
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

  const initialAccessibility = await evaluate(sessionId, `({
    activeExposed: !slides[0].inert && slides[0].getAttribute('aria-hidden') === 'false',
    inactiveHidden: slides.slice(1).every((slide) => slide.inert && slide.getAttribute('aria-hidden') === 'true'),
  })`);
  if (!initialAccessibility.activeExposed || !initialAccessibility.inactiveHidden) {
    throw new Error(`Inactive slides remain focusable: ${JSON.stringify(initialAccessibility)}`);
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

  const spaceOnButton = await evaluate(sessionId, `(() => {
    const button = document.querySelector('[data-scene="performance"]');
    button.focus();
    button.dispatchEvent(new KeyboardEvent('keydown', { key: ' ', bubbles: true, cancelable: true }));
    return { cur, activeId: document.activeElement.dataset.scene };
  })()`);
  if (spaceOnButton.cur !== 2 || spaceOnButton.activeId !== "performance") {
    throw new Error(`Space on a button changed slides: ${JSON.stringify(spaceOnButton)}`);
  }

  const arrowOnButton = await evaluate(sessionId, `(() => {
    const button = document.querySelector('[data-scene="performance"]');
    button.focus();
    button.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true, cancelable: true }));
    const result = { cur, active: document.querySelector('.slide.active').id };
    go(2);
    return result;
  })()`);
  if (arrowOnButton.cur !== 3 || arrowOnButton.active !== "s4") {
    throw new Error(`Arrow key on a button did not change slides: ${JSON.stringify(arrowOnButton)}`);
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
  const modalFocus = await evaluate(sessionId, `(() => {
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true, cancelable: true }));
    return {
      deckInert: document.getElementById('deck').inert,
      navInert: document.getElementById('nav').inert,
      activeId: document.activeElement.id,
    };
  })()`);
  if (!modalFocus.deckInert || !modalFocus.navInert || modalFocus.activeId !== "detail-close") {
    throw new Error(`Modal focus escaped: ${JSON.stringify(modalFocus)}`);
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
  const verticalTouch = await evaluate(sessionId, `(() => {
    go(6);
    const start = new Event('touchstart', { bubbles: true, cancelable: true });
    Object.defineProperty(start, 'touches', { value: [{ clientX: 200, clientY: 700 }] });
    document.dispatchEvent(start);
    const end = new Event('touchend', { bubbles: true, cancelable: true });
    Object.defineProperty(end, 'changedTouches', { value: [{ clientX: 204, clientY: 300 }] });
    document.dispatchEvent(end);
    return { cur, active: document.querySelector('.slide.active').id };
  })()`);
  if (verticalTouch.cur !== 6 || verticalTouch.active !== "s7") {
    throw new Error(`Vertical touch blocked page scrolling: ${JSON.stringify(verticalTouch)}`);
  }
  const horizontalTouch = await evaluate(sessionId, `(() => {
    const start = new Event('touchstart', { bubbles: true, cancelable: true });
    Object.defineProperty(start, 'touches', { value: [{ clientX: 330, clientY: 500 }] });
    document.dispatchEvent(start);
    const end = new Event('touchend', { bubbles: true, cancelable: true });
    Object.defineProperty(end, 'changedTouches', { value: [{ clientX: 70, clientY: 505 }] });
    document.dispatchEvent(end);
    return { cur, active: document.querySelector('.slide.active').id };
  })()`);
  if (horizontalTouch.cur !== 7 || horizontalTouch.active !== "s8") {
    throw new Error(`Horizontal touch did not change slides: ${JSON.stringify(horizontalTouch)}`);
  }
  await sleep(250);
  const mobile = await evaluate(sessionId, `(() => {
    const slide = document.querySelector('.slide.active');
    return {
      width: document.documentElement.scrollWidth,
      viewport: innerWidth,
      scrollable: slide.scrollHeight > slide.clientHeight,
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
