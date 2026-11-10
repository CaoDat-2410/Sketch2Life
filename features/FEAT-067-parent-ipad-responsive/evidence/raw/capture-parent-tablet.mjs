import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const baseUrl = "http://127.0.0.1:5171";
const outputDir = "F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation/features/FEAT-067-parent-ipad-responsive/evidence/screenshots";
await mkdir(outputDir, { recursive: true });

const targetResponse = await fetch("http://127.0.0.1:9222/json/new?about:blank", { method: "PUT" });
if (!targetResponse.ok) throw new Error(`Chrome target creation failed (${targetResponse.status}).`);
const target = await targetResponse.json();
const socket = new WebSocket(target.webSocketDebuggerUrl);
let nextId = 0;
const pending = new Map();

socket.addEventListener("message", (event) => {
  const message = JSON.parse(event.data);
  if (!message.id) return;
  const request = pending.get(message.id);
  if (!request) return;
  pending.delete(message.id);
  clearTimeout(request.timeout);
  if (message.error) request.reject(new Error(message.error.message));
  else request.resolve(message.result);
});
await new Promise((resolve, reject) => {
  socket.addEventListener("open", resolve, { once: true });
  socket.addEventListener("error", reject, { once: true });
});

function send(method, params = {}) {
  const id = ++nextId;
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      pending.delete(id);
      reject(new Error(`CDP timed out: ${method}`));
    }, 10000);
    pending.set(id, { resolve, reject, timeout });
    socket.send(JSON.stringify({ id, method, params }));
  });
}

const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
await send("Page.enable");
await send("Runtime.enable");

async function setViewport(width, height, touch = false) {
  await send("Emulation.setDeviceMetricsOverride", {
    width,
    height,
    deviceScaleFactor: 1,
    mobile: false,
  });
  await send("Emulation.setTouchEmulationEnabled", { enabled: touch, maxTouchPoints: touch ? 5 : 1 });
}

async function evaluate(expression) {
  const response = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  if (response.exceptionDetails) throw new Error(response.exceptionDetails.text);
  return response.result.value;
}

async function goTo(pathname) {
  await evaluate(`(() => { history.pushState({}, "", ${JSON.stringify(pathname)}); dispatchEvent(new PopStateEvent("popstate", { state: history.state })); })()`);
  await pause(550);
}

async function capture(name, width, height, touch = false) {
  await setViewport(width, height, touch);
  await pause(250);
  const metrics = await evaluate(`(() => {
    const phone = document.querySelector(".phone");
    const scroll = document.querySelector(".phone .scroll");
    const page = document.querySelector(".phone .page");
    const tabs = document.querySelector(".phone .tabbar");
    return {
      name: ${JSON.stringify(name)},
      viewport: { width: innerWidth, height: innerHeight, orientation: matchMedia("(orientation: landscape)").matches ? "landscape" : "portrait", coarsePointer: matchMedia("(pointer: coarse)").matches },
      route: phone?.dataset.route ?? null,
      shell: phone ? { width: Math.round(phone.getBoundingClientRect().width), height: Math.round(phone.getBoundingClientRect().height), columns: getComputedStyle(phone).gridTemplateColumns } : null,
      page: page ? { width: Math.round(page.getBoundingClientRect().width), scrollWidth: page.scrollWidth } : null,
      outdoorArt: (() => { const art = document.querySelector(".phone .outdoor-art"); if (!art) return null; const rect = art.getBoundingClientRect(); const style = getComputedStyle(art); return { x: Math.round(rect.x), y: Math.round(rect.y), width: Math.round(rect.width), height: Math.round(rect.height), naturalWidth: art.naturalWidth, naturalHeight: art.naturalHeight, display: style.display, visibility: style.visibility, opacity: style.opacity, objectFit: style.objectFit, gridRow: style.gridRow, gridColumn: style.gridColumn }; })(),
      outdoorLayout: phone?.dataset.route === "p08b-outdoor-activity" ? [...document.querySelector(".phone .page").children].map((element) => { const rect = element.getBoundingClientRect(); const style = getComputedStyle(element); return { tag: element.tagName, className: typeof element.className === "string" ? element.className : "", x: Math.round(rect.x), y: Math.round(rect.y), width: Math.round(rect.width), height: Math.round(rect.height), gridRow: style.gridRow, gridColumn: style.gridColumn }; }) : null,
      scroll: scroll ? { clientWidth: scroll.clientWidth, scrollWidth: scroll.scrollWidth } : null,
      tabs: tabs ? { display: getComputedStyle(tabs).display, width: Math.round(tabs.getBoundingClientRect().width), height: Math.round(tabs.getBoundingClientRect().height), count: tabs.dataset.tabCount ?? null } : null,
      documentScrollWidth: document.documentElement.scrollWidth
    };
  })()`);
  const image = await send("Page.captureScreenshot", { format: "png", fromSurface: true, captureBeyondViewport: false });
  await writeFile(path.join(outputDir, `${name}.png`), Buffer.from(image.data, "base64"));
  return metrics;
}

const metrics = [];
await setViewport(834, 1194, false);
await send("Page.navigate", { url: `${baseUrl}/p11-authentication` });
await pause(2700);
metrics.push(await capture("parent-auth-834x1194", 834, 1194, false));
await goTo("/p14-password-recovery");
metrics.push(await capture("parent-recovery-834x1194", 834, 1194, false));
await goTo("/p15-parent-registration");
metrics.push(await capture("parent-registration-834x1194", 834, 1194, false));
await goTo("/p11-authentication");
await pause(2300);
metrics.push(await capture("parent-auth-1194x834", 1194, 834, false));
await goTo("/p14-password-recovery");
metrics.push(await capture("parent-recovery-1194x834", 1194, 834, false));
await goTo("/p15-parent-registration");
metrics.push(await capture("parent-registration-1194x834", 1194, 834, false));

await goTo("/p11-authentication");
await pause(2300);
const openedPreview = await evaluate(`(() => { const button = document.querySelector(".login-preview-action"); if (!button) return false; button.click(); return true; })()`);
if (!openedPreview) throw new Error("Local preview button was not available on Parent auth screen.");
await pause(800);

const routes = [
  ["home", "/p01-lesson-library"],
  ["lesson-detail", "/p02-lesson-detail"],
  ["drawing-guide", "/p03-drawing-line-guide"],
  ["capture", "/p04-capture-subject-confirmation"],
  ["story-context", "/p05-context-idea-confirmation"],
  ["story-review", "/p06-story-review"],
  ["video-status", "/p07-video-job-status"],
  ["video", "/p08-video-and-activities"],
  ["outdoor-activities", "/p08b-outdoor-activity"],
  ["session-feedback", "/p08c-session-feedback"],
  ["history", "/p09-history-feedback"],
  ["quota", "/p12-video-quota"],
  ["settings", "/p13-settings"],
  ["child-profile", "/p10-child-profiles/child-minh"],
];

for (const [name, route] of routes) {
  await goTo(route);
  metrics.push(await capture(`parent-${name}-834x1194`, 834, 1194, false));
  metrics.push(await capture(`parent-${name}-1194x834`, 1194, 834, false));
}

for (const [width, height] of [[744, 1133], [768, 1024], [810, 1080], [820, 1180], [1024, 768], [1080, 810], [1180, 820], [1133, 744], [1032, 1376], [1376, 1032]]) {
  await goTo("/p01-lesson-library");
  const name = `parent-home-${width}x${height}`;
  metrics.push(await capture(name, width, height, false));
}
await goTo("/p01-lesson-library");
metrics.push(await capture("parent-home-1194x834-ipad-touch", 1194, 834, true));
await goTo("/p01-lesson-library");
metrics.push(await capture("parent-home-1280x800-tablet-touch", 1280, 800, true));

for (const [width, height] of [[1366, 768], [1440, 900]]) {
  await goTo("/p01-lesson-library");
  metrics.push(await capture(`parent-desktop-${width}x${height}`, width, height, false));
}

await writeFile(path.join(outputDir, "viewport-metrics.json"), `${JSON.stringify(metrics, null, 2)}\n`);
console.log(JSON.stringify(metrics, null, 2));
socket.close();
