import fs from "node:fs/promises";
import path from "node:path";

const outputRoot = process.argv[2];
const cdpEndpoint = "http://127.0.0.1:9390/json/list";
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const responseMap = new Map();
const runtimeErrors = [];
let sequence = 0;

const targets = await fetch(cdpEndpoint).then((response) => response.json());
const pageTarget = targets.find((target) => target.type === "page");
if (!pageTarget) throw new Error("No Edge page target is available.");

const socket = new WebSocket(pageTarget.webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  socket.addEventListener("open", resolve, { once: true });
  socket.addEventListener("error", reject, { once: true });
});

socket.addEventListener("message", (event) => {
  const message = JSON.parse(event.data);
  if (message.method === "Runtime.exceptionThrown") {
    runtimeErrors.push(message.params.exceptionDetails?.text || "Runtime exception");
  }
  if (message.method === "Log.entryAdded" && message.params.entry.level === "error" && message.params.entry.source === "javascript") {
    runtimeErrors.push(message.params.entry.text || "Browser log error");
  }
  if (message.id && responseMap.has(message.id)) {
    const pending = responseMap.get(message.id);
    responseMap.delete(message.id);
    clearTimeout(pending.timer);
    if (message.error) pending.reject(new Error(message.error.message));
    else pending.resolve(message.result || {});
  }
});

function send(method, params = {}) {
  const id = ++sequence;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      responseMap.delete(id);
      reject(new Error("CDP timeout: " + method));
    }, 15000);
    responseMap.set(id, { resolve, reject, timer });
    socket.send(JSON.stringify({ id, method, params }));
  });
}

async function evaluate(expression, options = {}) {
  const result = await send("Runtime.evaluate", {
    expression,
    awaitPromise: true,
    returnByValue: true,
    ...options,
  });
  if (result.exceptionDetails) {
    throw new Error(result.exceptionDetails.text || "Page evaluation failed");
  }
  return result.result?.value;
}

await send("Runtime.enable");
await send("Log.enable");

async function waitForRender() {
  for (let attempt = 0; attempt < 50; attempt += 1) {
    const state = await evaluate("document.readyState");
    if (state === "complete") break;
    await delay(150);
  }
  await evaluate("(async()=>{await Promise.all(Array.from(document.images).map(i=>i.decode().catch(()=>{})));return true})()");
  await delay(500);
}

async function navigate(url) {
  await send("Page.navigate", { url });
  await waitForRender();
  await evaluate("(()=>{let s=document.getElementById('codex-capture-stable');if(!s){s=document.createElement('style');s.id='codex-capture-stable';s.textContent='*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}';document.head.appendChild(s)}if(location.hash==='#child-profiles'){document.getElementById('child-profiles')?.scrollIntoView({behavior:'instant',block:'start'})}else{window.scrollTo(0,0)}return true})()");
  await delay(url.includes("#child-profiles") ? 900 : 250);
}

async function capture(appKey, name, label, url, viewport, mobile, navigatePage = true) {
  await send("Emulation.setDeviceMetricsOverride", {
    width: viewport.width,
    height: viewport.height,
    deviceScaleFactor: 1,
    mobile,
  });
  if (navigatePage) await navigate(url);
  else await delay(350);
  const metrics = await send("Page.getLayoutMetrics");
  const screen = await evaluate("JSON.stringify({url:location.href,title:document.title,text:(document.body?.innerText||'').slice(0,260),bodyLength:(document.body?.innerText||'').length})");
  const filePath = path.join(outputRoot, appKey, name + ".png");
  const image = await send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: false,
  });
  await fs.writeFile(filePath, Buffer.from(image.data, "base64"));
  return {
    app: appKey,
    name,
    label,
    requestedUrl: url,
    finalUrl: JSON.parse(screen).url,
    title: JSON.parse(screen).title,
    bodyLength: JSON.parse(screen).bodyLength,
    visibleTextPreview: JSON.parse(screen).text,
    viewport: viewport.width + "x" + viewport.height,
    mobile,
    screenshot: path.relative(outputRoot, filePath).replaceAll(path.sep, "/"),
    documentSize: metrics.cssContentSize
      ? Math.round(metrics.cssContentSize.width) + "x" + Math.round(metrics.cssContentSize.height)
      : null,
  };
}

async function fillPreviewLogin() {
  return evaluate("(()=>{const set=(e,v)=>{const p=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value');p.set.call(e,v);e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}))};for(const e of document.querySelectorAll('input[type=email]'))set(e,'preview@example.test');for(const e of document.querySelectorAll('input[type=password]'))set(e,'preview-only');const f=document.querySelector('form');if(!f)return false;f.requestSubmit();return true})()");
}

const apps = [
  {
    key: "parent",
    port: 5271,
    viewport: { width: 430, height: 932 },
    mobile: true,
    routes: [
      ["P01-lesson-library", "P01 · Lesson library", "/p01-lesson-library"],
      ["P02-lesson-detail", "P02 · Lesson detail", "/p02-lesson-detail"],
      ["P03-drawing-guide", "P03 · Drawing guide", "/p03-drawing-line-guide"],
      ["P04-capture-subject", "P04 · Capture and subject confirmation", "/p04-capture-subject-confirmation"],
      ["P05-context-idea", "P05 · Context and idea confirmation", "/p05-context-idea-confirmation"],
      ["P05b-activity-selection", "P05b · Activity selection", "/p05b-activity-selection"],
      ["P06-story-review", "P06 · Story review", "/p06-story-review"],
      ["P07-video-job-status", "P07 · Video job status", "/p07-video-job-status"],
      ["P08-video-and-activities", "P08 · Video and activities", "/p08-video-and-activities"],
      ["P08b-outdoor-activity", "P08b · Outdoor activity", "/p08b-outdoor-activity"],
      ["P08c-session-feedback", "P08c · Session feedback", "/p08c-session-feedback"],
      ["P09-history-feedback", "P09 · History and feedback", "/p09-history-feedback"],
      ["P10-child-profile", "P10 · Child profile detail", "/p10-child-profiles/child-minh"],
      ["P12-video-quota", "P12 · Video quota", "/p12-video-quota"],
      ["P13-settings", "P13 · Settings", "/p13-settings"],
      ["P13-child-profiles", "P13 · Child profiles section", "/p13-settings#child-profiles"],
    ],
  },
  {
    key: "teacher",
    port: 5272,
    viewport: { width: 1440, height: 1000 },
    mobile: false,
    login: true,
    routes: [
      ["T01-workspace", "T01 · Lesson workspace", "/t01-lesson-workspace"],
      ["T02-lesson-authoring", "T02 · Lesson authoring", "/t02-lesson-authoring"],
      ["T03-document-import", "T03 · Document import review", "/t03-document-import-review"],
      ["T04-session-sketch-deck", "T04 · Session sketch deck", "/t04-session-sketch-deck"],
      ["T05-classes", "T05 · Classes and children", "/t05-classes-and-children"],
      ["T05-class-detail", "T05 · Class detail", "/t05-classes-and-children/cls-mam-2"],
      ["T06-sample-story-run", "T06 · Sample Story Run", "/t06-sample-story-run"],
      ["T07-video-confirmation", "T07 · Video presentation confirmation", "/t07-video-presentation-confirmation"],
      ["T08-settings", "T08 · Teacher settings", "/t08-settings"],
    ],
  },
  {
    key: "school-manager",
    port: 5273,
    viewport: { width: 1440, height: 1000 },
    mobile: false,
    login: true,
    routes: [
      ["M01-publication-review", "M01 · Publication review", "/m01-publication-review"],
      ["M02-organization-management", "M02 · Organization management", "/m02-organization-management"],
    ],
  },
  {
    key: "platform-admin",
    port: 5274,
    viewport: { width: 1440, height: 1000 },
    mobile: false,
    login: true,
    routes: [
      ["A01-content-moderation", "A01 · Content moderation", "/a01-content-moderation"],
      ["A02-platform-operations", "A02 · Platform operations", "/a02-platform-operations"],
    ],
  },
];

const manifest = {
  capturedAt: new Date().toISOString(),
  browser: "Google Chrome headless 157.0.8103.38 via Chrome DevTools Protocol",
  environment: "Local preview on 127.0.0.1; synthetic demo data; no provider credentials",
  screens: [],
  runtimeErrors,
};

const parentLoginUrl = "http://127.0.0.2:5271/p11-authentication";
const parentViewport = { width: 430, height: 932 };
manifest.screens.push(await capture(
  "parent",
  "P11-splash",
  "P11 · Welcome splash",
  parentLoginUrl,
  parentViewport,
  true,
));
await evaluate("(()=>{const b=Array.from(document.querySelectorAll('button')).find(x=>(x.innerText||'').includes('Bắt đầu thôi'));if(b)b.click();return !!b})()");
await delay(350);
manifest.screens.push(await capture("parent", "P11-onboarding-1", "P11 · Onboarding 1", parentLoginUrl, parentViewport, true, false));
await evaluate("(()=>{const b=Array.from(document.querySelectorAll('button')).find(x=>(x.innerText||'').includes('Tiếp theo'));if(b)b.click();return !!b})()");
await delay(350);
manifest.screens.push(await capture("parent", "P11-onboarding-2", "P11 · Onboarding 2", parentLoginUrl, parentViewport, true, false));
await evaluate("(()=>{const b=Array.from(document.querySelectorAll('button')).find(x=>(x.innerText||'').includes('Tiếp theo'));if(b)b.click();return !!b})()");
await delay(350);
manifest.screens.push(await capture("parent", "P11-onboarding-3", "P11 · Onboarding 3", parentLoginUrl, parentViewport, true, false));
await evaluate("(()=>{const b=Array.from(document.querySelectorAll('button')).find(x=>(x.innerText||'').includes('Bắt đầu hành trình'));if(b)b.click();return !!b})()");
await delay(350);
manifest.screens.push(await capture("parent", "P11-authentication", "P11 · Authentication", parentLoginUrl, parentViewport, true, false));

for (const app of apps) {
  if (app.login) {
    const loginUrl = "http://127.0.0.1:" + app.port + "/login";
    manifest.screens.push(await capture(
      app.key,
      "login",
      app.key === "teacher" ? "Teacher · Login" : app.key === "school-manager" ? "School Manager · Login" : "Platform Admin · Login",
      loginUrl,
      app.viewport,
      app.mobile,
    ));
    await fillPreviewLogin();
    await delay(900);
  }
  for (const [name, label, route] of app.routes) {
    manifest.screens.push(await capture(
      app.key,
      name,
      label,
      "http://127.0.0.1:" + app.port + route,
      app.viewport,
      app.mobile,
    ));
  }
}

await send("Browser.close");
await fs.writeFile(
  path.join(outputRoot, "capture-manifest.json"),
  JSON.stringify(manifest, null, 2),
  "utf8",
);
console.log("Captured " + manifest.screens.length + " screenshots.");
for (const screen of manifest.screens) {
  console.log(screen.app + "/" + screen.name + ".png | " + screen.bodyLength + " chars | " + screen.finalUrl);
}
if (manifest.runtimeErrors.length) {
  console.log("Runtime errors: " + manifest.runtimeErrors.join(" | "));
}
