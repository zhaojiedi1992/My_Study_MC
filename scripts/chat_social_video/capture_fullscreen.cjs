/* Record the fifth PPT screen, click its visible maximize control, and keep
 * the native HTML video in fullscreen for the remainder of the segment. */
const { spawn } = require("child_process");
const process = require("process");

const chromePath = "/usr/bin/google-chrome";
const ffmpegPath = "/usr/bin/ffmpeg";
const url = process.argv[2];
const output = process.argv[3];
const seconds = Number(process.argv[4] || 21);
const clickDelaySeconds = Number(process.argv[5] || 1.2);
if (!url || !output || !Number.isFinite(seconds) || !Number.isFinite(clickDelaySeconds)) {
  throw new Error("usage: capture_fullscreen.cjs URL OUTPUT SECONDS CLICK_DELAY_SECONDS");
}

let nextId = 0;
let input = "";
const pending = new Map();
const eventWaiters = new Map();

function send(chrome, method, params = {}, sessionId) {
  return new Promise((resolve, reject) => {
    const id = ++nextId;
    const timer = setTimeout(() => {
      pending.delete(id);
      reject(new Error(`CDP timeout: ${method}`));
    }, 15000);
    pending.set(id, { resolve, reject, timer });
    const message = { id, method, params };
    if (sessionId) message.sessionId = sessionId;
    chrome.stdio[3].write(`${JSON.stringify(message)}\0`);
  });
}

function waitForEvent(method, sessionId) {
  return new Promise((resolve, reject) => {
    const key = `${sessionId || ""}:${method}`;
    const list = eventWaiters.get(key) || [];
    const waiter = {
      resolve,
      reject,
      timer: setTimeout(() => reject(new Error(`CDP event timeout: ${method}`)), 15000),
    };
    list.push(waiter);
    eventWaiters.set(key, list);
  });
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function evaluate(chrome, sessionId, expression) {
  const result = await send(chrome, "Runtime.evaluate", {
    expression,
    returnByValue: true,
    awaitPromise: true,
  }, sessionId);
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.text);
  return result.result?.value;
}

async function main() {
  const chrome = spawn(chromePath, [
    "--no-sandbox",
    "--disable-gpu",
    "--disable-dev-shm-usage",
    // Avoid attaching to an already-running desktop Chrome instance.  When
    // that happens Chromium forwards the URL and exits before opening the
    // remote-debugging pipe (which presents as ECONNRESET on fd 4).
    `--user-data-dir=/tmp/chat-social-video-chrome-${process.pid}`,
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-features=FullscreenNotification,FullscreenOverlay",
    "--allow-file-access-from-files",
    "--autoplay-policy=no-user-gesture-required",
    "--remote-debugging-pipe",
    "--window-size=1920,1080",
    "--kiosk",
    "about:blank",
  ], { stdio: ["ignore", "ignore", "pipe", "pipe", "pipe"] });

  chrome.stdio[4].on("data", (chunk) => {
    input += chunk.toString();
    let boundary;
    while ((boundary = input.indexOf("\0")) >= 0) {
      const raw = input.slice(0, boundary);
      input = input.slice(boundary + 1);
      if (!raw) continue;
      const message = JSON.parse(raw);
      const key = `${message.sessionId || ""}:${message.method || ""}`;
      const waiters = eventWaiters.get(key);
      if (waiters?.length) {
        const waiter = waiters.shift();
        clearTimeout(waiter.timer);
        waiter.resolve(message.params || {});
        if (!waiters.length) eventWaiters.delete(key);
      }
      if (!message.id || !pending.has(message.id)) continue;
      const request = pending.get(message.id);
      pending.delete(message.id);
      clearTimeout(request.timer);
      if (message.error) request.reject(new Error(message.error.message));
      else request.resolve(message.result || {});
    }
  });

  try {
    const target = await send(chrome, "Target.createTarget", { url: "about:blank" });
    const attached = await send(chrome, "Target.attachToTarget", {
      targetId: target.targetId,
      flatten: true,
    });
    const sessionId = attached.sessionId;
    await send(chrome, "Page.enable", {}, sessionId);
    await send(chrome, "Runtime.enable", {}, sessionId);
    const loaded = waitForEvent("Page.loadEventFired", sessionId);
    await send(chrome, "Page.navigate", { url }, sessionId);
    await loaded;
    await sleep(2200);

    const display = process.env.DISPLAY || ":99";
    const displayInput = display.includes(".") ? display : `${display}.0`;
    const recorder = spawn(ffmpegPath, [
      "-hide_banner", "-loglevel", "error", "-y",
      "-f", "x11grab", "-video_size", "1920x1080", "-framerate", "30",
      "-i", displayInput,
      "-t", String(seconds),
      "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
      "-pix_fmt", "yuv420p", "-r", "30", "-movflags", "+faststart", output,
    ], { stdio: ["ignore", "ignore", "pipe"] });

    await sleep(clickDelaySeconds * 1000);
    const rect = await evaluate(chrome, sessionId, `(() => {
      const button = document.querySelector('[data-video-maximize]');
      if (!button) throw new Error('maximize button not found');
      const box = button.getBoundingClientRect();
      return {x: box.left + box.width / 2, y: box.top + box.height / 2};
    })()`);
    await send(chrome, "Input.dispatchMouseEvent", {
      type: "mouseMoved", x: rect.x, y: rect.y,
    }, sessionId);
    await send(chrome, "Input.dispatchMouseEvent", {
      type: "mousePressed", button: "left", clickCount: 1, x: rect.x, y: rect.y,
    }, sessionId);
    await send(chrome, "Input.dispatchMouseEvent", {
      type: "mouseReleased", button: "left", clickCount: 1, x: rect.x, y: rect.y,
    }, sessionId);
    await sleep(900);
    const state = await evaluate(chrome, sessionId, `(() => {
      const video = document.querySelector('.slide-emote video');
      return {fullscreen: document.fullscreenElement === video, playing: !video.paused};
    })()`);
    if (!state.fullscreen || !state.playing) {
      throw new Error(`maximize click did not start fullscreen video: ${JSON.stringify(state)}`);
    }
    await new Promise((resolve) => recorder.once("close", resolve));
  } finally {
    chrome.kill("SIGTERM");
  }
}

main().catch((error) => {
  console.error(error.stack || error.message || error);
  process.exitCode = 1;
});
