const assert = require("assert");
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
const eventWaiters = new Map();
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
    const eventKey = `${message.sessionId || ""}:${message.method || ""}`;
    const waiters = eventWaiters.get(eventKey);
    if (waiters && waiters.length) {
      const waiter = waiters.shift();
      clearTimeout(waiter.timer);
      waiter.resolve(message.params || {});
      if (!waiters.length) eventWaiters.delete(eventKey);
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

function waitForEvent(method, sessionId) {
  return new Promise((resolve, reject) => {
    const eventKey = `${sessionId || ""}:${method}`;
    const waiters = eventWaiters.get(eventKey) || [];
    const waiter = {
      resolve,
      reject,
      timer: setTimeout(() => {
        const current = eventWaiters.get(eventKey) || [];
        const index = current.indexOf(waiter);
        if (index >= 0) current.splice(index, 1);
        if (!current.length) eventWaiters.delete(eventKey);
        reject(new Error(`CDP event timeout: ${method}`));
      }, 10000),
    };
    waiters.push(waiter);
    eventWaiters.set(eventKey, waiters);
  });
}

async function evaluate(sessionId, expression) {
  const result = await send("Runtime.evaluate", {
    expression,
    returnByValue: true,
    awaitPromise: true,
  }, sessionId);
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.text);
  return result.result.value;
}

async function waitForAnimations(sessionId) {
  await evaluate(sessionId, `Promise.all(
    document.getAnimations().map(animation=>animation.finished.catch(()=>undefined))
  ).then(()=>true)`);
}

async function navigate(sessionId, url) {
  const loaded = waitForEvent("Page.loadEventFired", sessionId);
  const result = await send("Page.navigate", { url }, sessionId);
  if (result.errorText) throw new Error(`Navigation failed: ${result.errorText}`);
  await loaded;
}

async function reload(sessionId) {
  const loaded = waitForEvent("Page.loadEventFired", sessionId);
  await send("Page.reload", {}, sessionId);
  await loaded;
}

async function setViewport(sessionId, width, height) {
  await send("Emulation.setDeviceMetricsOverride", {
    width,
    height,
    deviceScaleFactor: 1,
    mobile: false,
  }, sessionId);
}

async function pressKey(sessionId, key, code, virtualKeyCode) {
  const params = {
    key,
    code,
    windowsVirtualKeyCode: virtualKeyCode,
    nativeVirtualKeyCode: virtualKeyCode,
  };
  await send("Input.dispatchKeyEvent", { type: "rawKeyDown", ...params }, sessionId);
  await send("Input.dispatchKeyEvent", { type: "keyUp", ...params }, sessionId);
}

async function capture(sessionId, outputPath) {
  const shot = await send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: false,
  }, sessionId);
  fs.writeFileSync(outputPath, Buffer.from(shot.data, "base64"));
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
    path.resolve("source/extra/MOD介绍/masa/tweakeroo/index.html"),
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

  await reload(sessionId);
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
      focus:slide.dataset.focus || null,
      focusX:stage.style.getPropertyValue('--focus-x'),
      focusY:stage.style.getPropertyValue('--focus-y'),
      selected:slide.querySelector('[data-state].selected').dataset.state,
      urlState:params.get('state'),
    };
  })()`);
  assert.deepStrictEqual(reset, {
    view: "auto",
    focus: null,
    focusX: "",
    focusY: "",
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

  await navigate(sessionId, `${url}?slide=1`);
  const keySequence = [];
  for (const [key, code, virtualKeyCode] of [
    ["ArrowRight", "ArrowRight", 39],
    ["PageDown", "PageDown", 34],
    ["ArrowLeft", "ArrowLeft", 37],
    ["PageUp", "PageUp", 33],
  ]) {
    await pressKey(sessionId, key, code, virtualKeyCode);
    keySequence.push(await evaluate(sessionId, `({
      cur,
      active:document.querySelector('.slide.active').id,
      urlSlide:new URLSearchParams(location.search).get('slide'),
    })`));
  }
  assert.deepStrictEqual(keySequence, [
    { cur: 1, active: "s2", urlSlide: "2" },
    { cur: 2, active: "s3", urlSlide: "3" },
    { cur: 1, active: "s2", urlSlide: "2" },
    { cur: 0, active: "s1", urlSlide: "1" },
  ]);

  const requiredStates = [
    { slide: 2, state: "config" },
    { slide: 3, state: "chestplate" },
    { slide: 4, state: "done" },
    { slide: 5, state: "right" },
    { slide: 6, state: "on" },
  ];
  const restoredStates = [];
  for (const { slide, state } of requiredStates) {
    await navigate(sessionId, `${url}?slide=${slide}&state=${state}`);
    const restored = await evaluate(sessionId, `(() => {
      const slide=document.getElementById('s${slide}');
      const images=[...document.images];
      const uniqueImages=[...new Map(images.map(image=>[image.src,image])).values()];
      return {
        cur,
        active:document.querySelector('.slide.active').id,
        view:slide.dataset.view,
        focus:slide.dataset.focus || null,
        selected:slide.querySelector('[data-state].selected').dataset.state,
        activeMedia:[...slide.querySelectorAll('[data-media-state].active')]
          .map(layer=>layer.dataset.mediaState),
        imageCount:images.length,
        uniqueImageCount:uniqueImages.length,
        naturalWidths:images.map(image=>image.naturalWidth),
      };
    })()`);
    assert.strictEqual(restored.cur, slide - 1);
    assert.strictEqual(restored.active, `s${slide}`);
    assert.strictEqual(restored.view, state);
    assert.strictEqual(restored.selected, state);
    if ([3, 5].includes(slide)) assert.strictEqual(restored.focus, state);
    else assert.deepStrictEqual(restored.activeMedia, [state]);
    assert.strictEqual(restored.imageCount, 11);
    assert.strictEqual(restored.uniqueImageCount, 10);
    assert.strictEqual(restored.naturalWidths.length, 11);
    assert(restored.naturalWidths.every((width) => width === 2880));
    restoredStates.push({ slide, state, uniqueImageCount: restored.uniqueImageCount });
  }

  const focusInteractions = [];
  for (const [slideNumber, states, defaultState] of [
    [3, ["auto", "chestplate"], "auto"],
    [5, ["left", "right"], "left"],
  ]) {
    await navigate(sessionId, `${url}?slide=${slideNumber}`);
    const initialFocus = await evaluate(sessionId, `(() => {
      const slide=document.getElementById('s${slideNumber}');
      return {
        focused:slide.querySelector('.media-stage').classList.contains('focused'),
        focus:slide.dataset.focus || null,
      };
    })()`);
    assert.deepStrictEqual(initialFocus, { focused: false, focus: null });
    for (const state of states) {
      await evaluate(sessionId,
        `document.querySelector('#s${slideNumber} [data-state="${state}"]').click()`);
      await waitForAnimations(sessionId);
      const clickedFocus = await evaluate(sessionId, `(() => {
        const slide=document.getElementById('s${slideNumber}');
        const stage=slide.querySelector('.media-stage');
        const image=slide.querySelector('.media-layer.active');
        const frame=stage.getBoundingClientRect();
        const imageRect=image.getBoundingClientRect();
        const style=getComputedStyle(image);
        const scaleX=imageRect.width/image.clientWidth;
        const scaleY=imageRect.height/image.clientHeight;
        const fitScale=Math.min(
          image.clientWidth/image.naturalWidth,
          image.clientHeight/image.naturalHeight
        );
        const paintedWidth=image.naturalWidth*fitScale*scaleX;
        const paintedHeight=image.naturalHeight*fitScale*scaleY;
        const painted={
          left:imageRect.left+(imageRect.width-paintedWidth)/2,
          top:imageRect.top+(imageRect.height-paintedHeight)/2,
          right:imageRect.right-(imageRect.width-paintedWidth)/2,
          bottom:imageRect.bottom-(imageRect.height-paintedHeight)/2,
        };
        return {
          view:slide.dataset.view,
          focused:stage.classList.contains('focused'),
          focus:slide.dataset.focus || null,
          objectFit:style.objectFit,
          complete:painted.left>=frame.left-.5 && painted.top>=frame.top-.5 &&
            painted.right<=frame.right+.5 && painted.bottom<=frame.bottom+.5,
        };
      })()`);
      assert.deepStrictEqual(clickedFocus, {
        view: state,
        focused: true,
        focus: state,
        objectFit: "contain",
        complete: true,
      });
    }
    await pressKey(sessionId, "Escape", "Escape", 27);
    const escapedFocus = await evaluate(sessionId, `(() => {
      const slide=document.getElementById('s${slideNumber}');
      return {
        view:slide.dataset.view,
        focused:slide.querySelector('.media-stage').classList.contains('focused'),
        focus:slide.dataset.focus || null,
      };
    })()`);
    assert.deepStrictEqual(escapedFocus, {
      view: defaultState,
      focused: false,
      focus: null,
    });
    focusInteractions.push({ slide: slideNumber, states, escapedFocus });
  }

  await setViewport(sessionId, 1920, 1080);
  await navigate(sessionId, `${url}?slide=1`);
  await waitForAnimations(sessionId);
  const coverIntro = await evaluate(sessionId, `(() => {
    const cover=document.getElementById('s1');
    const layout=cover.querySelector('.cover-layout');
    const copy=cover.querySelector('.cover-copy');
    const frame=cover.querySelector('.cover-frame');
    const image=cover.querySelector('.cover-media');
    const title=cover.querySelector('.cover-title');
    const titleUnit=cover.querySelector('.cover-title .keep-together');
    const brand=cover.querySelector('.cover-brand');
    if(!layout||!copy||!frame||!image||!title||!brand){
      return {present:false};
    }
    const rgbBrightness=value=>{
      const channels=value.match(/[0-9.]+/g)?.slice(0,3).map(Number) || [0,0,0];
      return channels.reduce((sum,channel)=>sum+channel,0)/3;
    };
    const coverStyle=getComputedStyle(cover);
    const layoutRect=layout.getBoundingClientRect();
    const copyRect=copy.getBoundingClientRect();
    const frameRect=frame.getBoundingClientRect();
    const imageRect=image.getBoundingClientRect();
    return {
      present:true,
      display:getComputedStyle(layout).display,
      backgroundBrightness:rgbBrightness(coverStyle.backgroundColor),
      backgroundColor:coverStyle.backgroundColor,
      backgroundImage:coverStyle.backgroundImage,
      textBrightness:rgbBrightness(getComputedStyle(copy).color),
      titleBrightness:rgbBrightness(getComputedStyle(title).color),
      titleColor:getComputedStyle(title).color,
      brandColor:getComputedStyle(brand).color,
      tagBackground:getComputedStyle(cover.querySelector('.cover-tag')).backgroundColor,
      lastTagColor:getComputedStyle(cover.querySelector('.cover-tag:last-child')).color,
      frameBackground:getComputedStyle(frame).backgroundColor,
      overlayContent:getComputedStyle(cover,'::after').content,
      split:copyRect.right < frameRect.left,
      layout:{x:layoutRect.x,y:layoutRect.y,width:layoutRect.width,height:layoutRect.height},
      frame:{x:frameRect.x,y:frameRect.y,width:frameRect.width,height:frameRect.height},
      imageInsideFrame:imageRect.left>=frameRect.left && imageRect.top>=frameRect.top &&
        imageRect.right<=frameRect.right && imageRect.bottom<=frameRect.bottom,
      objectFit:getComputedStyle(image).objectFit,
      imageFilter:getComputedStyle(image).filter,
      imageOpacity:getComputedStyle(image).opacity,
      titleFontSize:parseFloat(getComputedStyle(title).fontSize),
      titleUnitPresent:Boolean(titleUnit),
      titleUnitOneLine:titleUnit ? titleUnit.getBoundingClientRect().height <=
        parseFloat(getComputedStyle(titleUnit).lineHeight)+1 : false,
      brandFontSize:parseFloat(getComputedStyle(brand).fontSize),
      tags:[...cover.querySelectorAll('.cover-tag')].map(tag=>tag.textContent.trim()),
    };
  })()`);
  assert.strictEqual(coverIntro.present, true);
  assert.strictEqual(coverIntro.display, "grid");
  assert.strictEqual(coverIntro.backgroundColor, "rgb(2, 7, 17)");
  assert(coverIntro.backgroundBrightness < 20, JSON.stringify(coverIntro));
  assert(coverIntro.backgroundImage.includes("rgb(18, 51, 81)"), coverIntro.backgroundImage);
  assert(coverIntro.backgroundImage.includes("rgb(13, 74, 75)"), coverIntro.backgroundImage);
  assert.strictEqual(coverIntro.titleColor, "rgb(255, 255, 255)");
  assert(coverIntro.titleBrightness-coverIntro.backgroundBrightness > 230,
    JSON.stringify(coverIntro));
  assert.strictEqual(coverIntro.brandColor, "rgb(86, 224, 196)");
  assert.strictEqual(coverIntro.lastTagColor, "rgb(249, 199, 79)");
  assert(coverIntro.tagBackground.startsWith("rgba(8, 19, 33,"), coverIntro.tagBackground);
  assert(coverIntro.frameBackground.startsWith("rgba(8, 19, 33,"), coverIntro.frameBackground);
  assert.strictEqual(coverIntro.overlayContent, "none");
  assert.strictEqual(coverIntro.split, true);
  assert.strictEqual(coverIntro.imageInsideFrame, true);
  assert.strictEqual(coverIntro.objectFit, "contain");
  assert.strictEqual(coverIntro.imageFilter, "none");
  assert.strictEqual(coverIntro.imageOpacity, "1");
  assert(coverIntro.titleFontSize <= 58, JSON.stringify(coverIntro));
  assert.strictEqual(coverIntro.titleUnitPresent, true);
  assert.strictEqual(coverIntro.titleUnitOneLine, true);
  assert(coverIntro.brandFontSize <= 32, JSON.stringify(coverIntro));
  assert.deepStrictEqual(coverIntro.tags, [
    "灵魂出窍", "自动鞘翅", "自动补货", "快速点击", "Gamma 亮度",
  ]);
  await navigate(sessionId, `${url}?export=1&slide=1`);
  const coverExport = await evaluate(sessionId, `(() => {
    const layout=document.querySelector('#s1 .cover-layout').getBoundingClientRect();
    const frame=document.querySelector('#s1 .cover-frame').getBoundingClientRect();
    return {
      layout:{x:layout.x,y:layout.y,width:layout.width,height:layout.height},
      frame:{x:frame.x,y:frame.y,width:frame.width,height:frame.height},
    };
  })()`);
  assert.deepStrictEqual(coverExport, { layout: coverIntro.layout, frame: coverIntro.frame });

  const completeImageResults = [];
  for (let slideNumber = 1; slideNumber <= 6; slideNumber += 1) {
    await navigate(sessionId, `${url}?slide=${slideNumber}`);
    await waitForAnimations(sessionId);
    const imageLayout = await evaluate(sessionId, `(() => {
      const slide=document.querySelector('.slide.active');
      const stage=slide.querySelector('.media-stage,.cover-frame');
      const image=slide.querySelector(slide.id==='s1' ? '.cover-media' : '.media-layer.active');
      const frame=stage ? stage.getBoundingClientRect() :
        {left:0,top:0,right:innerWidth,bottom:innerHeight};
      const imageRect=image.getBoundingClientRect();
      const style=getComputedStyle(image);
      const boxWidth=image.clientWidth;
      const boxHeight=image.clientHeight;
      const scaleX=imageRect.width / boxWidth;
      const scaleY=imageRect.height / boxHeight;
      const fitScale=style.objectFit==='cover'
        ? Math.max(boxWidth/image.naturalWidth,boxHeight/image.naturalHeight)
        : Math.min(boxWidth/image.naturalWidth,boxHeight/image.naturalHeight);
      const paintedWidth=image.naturalWidth * fitScale * scaleX;
      const paintedHeight=image.naturalHeight * fitScale * scaleY;
      const painted={
        left:imageRect.left+(imageRect.width-paintedWidth)/2,
        top:imageRect.top+(imageRect.height-paintedHeight)/2,
        right:imageRect.right-(imageRect.width-paintedWidth)/2,
        bottom:imageRect.bottom-(imageRect.height-paintedHeight)/2,
      };
      return {
        slide:slide.id,
        objectFit:style.objectFit,
        focused:stage ? stage.classList.contains('focused') : false,
        painted,
        frame:{left:frame.left,top:frame.top,right:frame.right,bottom:frame.bottom},
        complete:painted.left >= frame.left-.5 && painted.top >= frame.top-.5 &&
          painted.right <= frame.right+.5 && painted.bottom <= frame.bottom+.5,
      };
    })()`);
    assert.strictEqual(imageLayout.objectFit, "contain", JSON.stringify(imageLayout));
    assert.strictEqual(imageLayout.focused, false, JSON.stringify(imageLayout));
    assert.strictEqual(imageLayout.complete, true, JSON.stringify(imageLayout));
    completeImageResults.push(imageLayout);
  }

  const viewportResults = [];
  for (const [width, height] of [[1920, 1080], [1280, 720]]) {
    await setViewport(sessionId, width, height);
    for (let slideNumber = 1; slideNumber <= 8; slideNumber += 1) {
      await navigate(sessionId, `${url}?slide=${slideNumber}`);
      const layout = await evaluate(sessionId, `(() => {
        const active=document.querySelector('.slide.active');
        const critical=[...active.querySelectorAll([
          '.feature-layout','.summary-layout','.cover-layout','.cover-copy','.cover-frame',
          '.cover-title','.cover-intro','.cover-tags','.media-stage',
          '.feature-copy','.summary-card','h1','h2','.lead','.feature-list',
          '.state-controls','.hint','.steps','.boundary p'
        ].join(','))];
        const criticalOverflow=critical.flatMap(element=>{
          const rect=element.getBoundingClientRect();
          const outside=rect.left < -.5 || rect.top < -.5 ||
            rect.right > innerWidth + .5 || rect.bottom > innerHeight + .5;
          const internal=!element.matches('.media-stage') &&
            (element.scrollWidth > element.clientWidth + 1 ||
            (element.matches('.feature-layout,.summary-layout,.cover-layout,.cover-copy,'+
              '.cover-frame,.cover-tags,'+
              '.feature-copy,.summary-card,.state-controls') &&
              element.scrollHeight > element.clientHeight + 1));
          return outside || internal ? [{
            selector:element.className || element.tagName,
            rect:{left:rect.left,top:rect.top,right:rect.right,bottom:rect.bottom},
            client:[element.clientWidth,element.clientHeight],
            scroll:[element.scrollWidth,element.scrollHeight],
          }] : [];
        });
        return {
          viewport:[innerWidth,innerHeight],
          active:active.id,
          documentOverflow:document.documentElement.scrollWidth > innerWidth ||
            document.documentElement.scrollHeight > innerHeight,
          slideOverflow:active.scrollWidth > innerWidth || active.scrollHeight > innerHeight,
          criticalOverflow,
        };
      })()`);
      assert.deepStrictEqual(layout.viewport, [width, height]);
      assert.strictEqual(layout.active, `s${slideNumber}`);
      assert.strictEqual(layout.documentOverflow, false, JSON.stringify(layout));
      assert.strictEqual(layout.slideOverflow, false, JSON.stringify(layout));
      assert.deepStrictEqual(layout.criticalOverflow, [], JSON.stringify(layout));
      viewportResults.push({ width, height, slide: slideNumber });
    }
  }

  await setViewport(sessionId, 1920, 1080);
  await navigate(sessionId, `${url}?slide=6&state=on`);
  await waitForAnimations(sessionId);
  const groupedTitle = await evaluate(sessionId, `(() => {
    const unit=document.querySelector('#s6 h2 .keep-together');
    if(!unit)return {present:false,oneLine:false};
    const style=getComputedStyle(unit);
    return {
      present:true,
      oneLine:unit.getBoundingClientRect().height <= parseFloat(style.lineHeight)+1,
    };
  })()`);
  assert.deepStrictEqual(groupedTitle, { present: true, oneLine: true });
  const regularGeometry = await evaluate(sessionId, `(() => {
    const active=document.querySelector('.slide.active').getBoundingClientRect();
    const main=document.querySelector('.slide.active .feature-layout').getBoundingClientRect();
    return {
      active:{x:active.x,y:active.y,width:active.width,height:active.height},
      main:{x:main.x,y:main.y,width:main.width,height:main.height},
    };
  })()`);
  await navigate(sessionId, `${url}?export=1&slide=6&state=on`);
  const exportMode = await evaluate(sessionId, `(() => {
    const active=document.querySelector('.slide.active');
    const activeRect=active.getBoundingClientRect();
    const mainRect=active.querySelector('.feature-layout').getBoundingClientRect();
    const layer=active.querySelector('.media-layer');
    return {
      bodyExport:document.body.classList.contains('export'),
      navVisibility:getComputedStyle(document.getElementById('nav')).visibility,
      animationName:getComputedStyle(active).animationName,
      transitionDuration:getComputedStyle(layer).transitionDuration,
      active:{x:activeRect.x,y:activeRect.y,width:activeRect.width,height:activeRect.height},
      main:{x:mainRect.x,y:mainRect.y,width:mainRect.width,height:mainRect.height},
    };
  })()`);
  assert.strictEqual(exportMode.bodyExport, true);
  assert.strictEqual(exportMode.navVisibility, "hidden");
  assert.strictEqual(exportMode.animationName, "none");
  assert(exportMode.transitionDuration.split(", ").every((duration) => duration === "0s"));
  assert.deepStrictEqual(exportMode.active, regularGeometry.active);
  assert.deepStrictEqual(exportMode.main, regularGeometry.main);

  const screenshots = [
    { slide: 1, state: "", output: "/tmp/tweakeroo-slide-1-cover.png" },
    { slide: 2, state: "effect", output: "/tmp/tweakeroo-slide-2-effect.png" },
    { slide: 3, state: "chestplate", output: "/tmp/tweakeroo-slide-3-chestplate.png" },
    { slide: 4, state: "done", output: "/tmp/tweakeroo-slide-4-done.png" },
    { slide: 6, state: "on", output: "/tmp/tweakeroo-slide-6-on.png" },
  ];
  for (const { slide, state, output } of screenshots) {
    await navigate(sessionId, `${url}?export=1&slide=${slide}&state=${state}`);
    await capture(sessionId, output);
    assert(fs.statSync(output).size > 0, output);
  }

  assert.deepStrictEqual(browserErrors, []);
  console.log(JSON.stringify({
    multiImage,
    refreshedMultiImage,
    focused,
    reset,
    queryRestore,
    fractionalSlide,
    keySequence,
    restoredStates,
    completeImageResults,
    focusInteractions,
    coverIntro,
    coverExport,
    viewportResults,
    exportMode,
    groupedTitle,
    screenshots: screenshots.map(({ output }) => output),
  }, null, 2));
  await send("Target.closeTarget", { targetId: target.targetId });
  chrome.kill("SIGKILL");
  setTimeout(() => process.exit(0), 100);
})().catch((error) => {
  console.error(error.stack || error.message);
  chrome.kill("SIGKILL");
  setTimeout(() => process.exit(1), 100);
});
