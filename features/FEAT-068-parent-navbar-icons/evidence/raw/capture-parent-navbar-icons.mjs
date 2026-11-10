import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const baseUrl = "http://127.0.0.1:5171";
const outputDir = "F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation/features/FEAT-068-parent-navbar-icons/evidence/screenshots";
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

async function evaluate(expression) {
  const response = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  if (response.exceptionDetails) throw new Error(response.exceptionDetails.text);
  return response.result.value;
}

async function setViewport(width, height) {
  await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: false });
  await send("Emulation.setTouchEmulationEnabled", { enabled: false, maxTouchPoints: 1 });
}

await setViewport(390, 844);
await send("Page.navigate", { url: `${baseUrl}/p11-authentication` });
await pause(2200);
const openedPreview = await evaluate(`(() => { const button = document.querySelector(".login-preview-action"); if (!button) return false; button.click(); return true; })()`);
if (!openedPreview) throw new Error("Local preview button is missing from the Parent auth screen.");
await pause(600);

const captures = [];
for (const [name, width, height] of [
  ["phone-390x844", 390, 844],
  ["ipad-portrait-834x1194", 834, 1194],
  ["ipad-landscape-1194x834", 1194, 834],
]) {
  await setViewport(width, height);
  await evaluate(`(() => { history.pushState({}, "", "/p01-lesson-library"); dispatchEvent(new PopStateEvent("popstate", { state: history.state })); })()`);
  await pause(600);
  const metrics = await evaluate(`(() => {
    const nav = document.querySelector(".phone .tabbar");
    const phone = document.querySelector(".phone");
    return {
      name: ${JSON.stringify(name)},
      viewport: { width: innerWidth, height: innerHeight, coarsePointer: matchMedia("(pointer: coarse)").matches },
      shell: phone ? { width: Math.round(phone.getBoundingClientRect().width), columns: getComputedStyle(phone).gridTemplateColumns } : null,
      nav: nav ? {
        width: Math.round(nav.getBoundingClientRect().width),
        scrollWidth: nav.scrollWidth,
        labels: [...nav.querySelectorAll(":scope > .tab")].map((tab) => tab.textContent.trim()),
        icons: [...nav.querySelectorAll("svg")].map((svg) => ({ viewBox: svg.getAttribute("viewBox"), pathCount: svg.querySelectorAll("path").length, circleCount: svg.querySelectorAll("circle").length, ellipseCount: svg.querySelectorAll("ellipse").length, strokeWidth: getComputedStyle(svg).strokeWidth })),
        createLabel: nav.querySelector(".tab-create-action")?.getAttribute("aria-label")
      } : null,
      documentScrollWidth: document.documentElement.scrollWidth
    };
  })()`);
  const image = await send("Page.captureScreenshot", { format: "png", fromSurface: true, captureBeyondViewport: false });
  await writeFile(path.join(outputDir, `${name}.png`), Buffer.from(image.data, "base64"));
  captures.push(metrics);
}

await writeFile(path.join(outputDir, "navbar-icon-metrics.json"), `${JSON.stringify(captures, null, 2)}\n`);
console.log(JSON.stringify(captures));
socket.close();
