const assert = require("assert");
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
const browserErrors = [];

chrome.stdio[4].on("data", (chunk) => {
  input += chunk.toString();
  let boundary;
  while ((boundary = input.indexOf("\0")) >= 0) {
    const raw = input.slice(0, boundary);
    input = input.slice(boundary + 1);
    if (!raw) continue;
    const message = JSON.parse(raw);
    if (message.method === "Runtime.exceptionThrown") {
      browserErrors.push(message.params.exceptionDetails.text);
    }
    if (message.method === "Runtime.consoleAPICalled"
        && ["error", "assert"].includes(message.params.type)) {
      browserErrors.push(
        message.params.args.map((arg) => arg.value || arg.description || "console error").join(" "),
      );
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
    chrome.stdio[3].write(`${JSON.stringify(message)}\0`);
  });
}

const sleep = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

async function evaluate(sessionId, expression) {
  const result = await send("Runtime.evaluate", {
    expression,
    returnByValue: true,
    awaitPromise: true,
  }, sessionId);
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.text);
  return result.result.value;
}

async function navigate(sessionId, url) {
  await send("Page.navigate", { url }, sessionId);
  await sleep(500);
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

  const url = pathToFileURL(
    path.resolve("source/MOD介绍/tweakeroo/index.html"),
  ).href;
  await navigate(sessionId, url);

  await evaluate(sessionId, `go(1); document.querySelector('#s2 [data-state="config"]').click()`);
  const multiImage = await evaluate(sessionId, `(() => {
    const slide=document.getElementById('s2');
    const active=[...slide.querySelectorAll('[data-media-state].active')];
    const params=new URLSearchParams(location.search);
    return {
      slide:document.querySelector('.slide.active').id,
      view:slide.dataset.view,
      activeLayers:active.map((layer)=>layer.dataset.mediaState),
      selected:slide.querySelector('[data-state].selected').dataset.state,
      urlSlide:params.get('slide'),
      urlState:params.get('state'),
    };
  })()`);
  assert.deepStrictEqual(multiImage, {
    slide: "s2",
    view: "config",
    activeLayers: ["config"],
    selected: "config",
    urlSlide: "2",
    urlState: "config",
  });

  await send("Page.reload", {}, sessionId);
  await sleep(500);
  const refreshedMultiImage = await evaluate(sessionId, `(() => {
    const slide=document.getElementById('s2');
    return {
      slide:document.querySelector('.slide.active').id,
      view:slide.dataset.view,
      active:slide.querySelector('[data-media-state].active').dataset.mediaState,
    };
  })()`);
  assert.deepStrictEqual(refreshedMultiImage, {
    slide: "s2",
    view: "config",
    active: "config",
  });

  await evaluate(sessionId, `go(2); document.querySelector('#s3 [data-state="chestplate"]').click()`);
  const focused = await evaluate(sessionId, `(() => {
    const slide=document.getElementById('s3');
    const stage=slide.querySelector('.media-stage');
    const params=new URLSearchParams(location.search);
    return {
      imageCount:slide.querySelectorAll('img.media-layer').length,
      view:slide.dataset.view,
      focus:slide.dataset.focus,
      focused:stage.classList.contains('focused'),
      focusX:stage.style.getPropertyValue('--focus-x'),
      focusY:stage.style.getPropertyValue('--focus-y'),
      selected:slide.querySelector('[data-state].selected').dataset.state,
      urlState:params.get('state'),
    };
  })()`);
  assert.deepStrictEqual(focused, {
    imageCount: 1,
    view: "chestplate",
    focus: "chestplate",
    focused: true,
    focusX: "50%",
    focusY: "61%",
    selected: "chestplate",
    urlState: "chestplate",
  });

  await evaluate(sessionId, `document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))`);
  const reset = await evaluate(sessionId, `(() => {
    const slide=document.getElementById('s3');
    const stage=slide.querySelector('.media-stage');
    const params=new URLSearchParams(location.search);
    return {
      view:slide.dataset.view,
      focus:slide.dataset.focus,
      focusX:stage.style.getPropertyValue('--focus-x'),
      focusY:stage.style.getPropertyValue('--focus-y'),
      selected:slide.querySelector('[data-state].selected').dataset.state,
      urlState:params.get('state'),
    };
  })()`);
  assert.deepStrictEqual(reset, {
    view: "auto",
    focus: "auto",
    focusX: "46%",
    focusY: "38%",
    selected: "auto",
    urlState: "auto",
  });

  await navigate(sessionId, `${url}?slide=4&state=done`);
  const queryRestore = await evaluate(sessionId, `(() => {
    const slide=document.getElementById('s4');
    return {
      slide:document.querySelector('.slide.active').id,
      view:slide.dataset.view,
      active:slide.querySelector('[data-media-state].active').dataset.mediaState,
      selected:slide.querySelector('[data-state].selected').dataset.state,
    };
  })()`);
  assert.deepStrictEqual(queryRestore, {
    slide: "s4",
    view: "done",
    active: "done",
    selected: "done",
  });

  await navigate(sessionId, `${url}?slide=2.5&state=config`);
  const fractionalSlide = await evaluate(sessionId, `({
    cur,
    active:document.querySelector('.slide.active').id,
    view:document.getElementById('s2').dataset.view,
  })`);
  assert.deepStrictEqual(fractionalSlide, { cur: 1, active: "s2", view: "config" });

  assert.deepStrictEqual(browserErrors, []);
  console.log(JSON.stringify({
    multiImage,
    refreshedMultiImage,
    focused,
    reset,
    queryRestore,
    fractionalSlide,
  }, null, 2));
  await send("Target.closeTarget", { targetId: target.targetId });
  chrome.kill("SIGKILL");
  setTimeout(() => process.exit(0), 100);
})().catch((error) => {
  console.error(error.stack || error.message);
  chrome.kill("SIGKILL");
  setTimeout(() => process.exit(1), 100);
});
