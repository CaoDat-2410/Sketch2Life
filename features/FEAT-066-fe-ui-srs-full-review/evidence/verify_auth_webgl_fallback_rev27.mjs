import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(fileURLToPath(import.meta.url));
const outputDir = join(root, "screenshots", "auth-redesign-rev27");
const browserInfo = await fetch("http://127.0.0.1:9233/json/version").then((r) => r.json());
const browser = new WebSocket(browserInfo.webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  browser.addEventListener("open", resolve, { once: true });
  browser.addEventListener("error", reject, { once: true });
});
let browserId = 0;
const browserPending = new Map();
browser.addEventListener("message", ({ data }) => {
  const message = JSON.parse(data);
  const pending = browserPending.get(message.id);
  if (!pending) return;
  browserPending.delete(message.id);
  if (message.error) pending.reject(new Error(message.error.message));
  else pending.resolve(message);
});
function browserCommand(method, params = {}) {
  const id = ++browserId;
  return new Promise((resolve, reject) => {
    browserPending.set(id, { resolve, reject });
    browser.send(JSON.stringify({ id, method, params }));
    setTimeout(() => reject(new Error(`Timed out: ${method}`)), 12000);
  });
}
const target = await browserCommand("Target.createTarget", { url: "http://127.0.0.1:5172/login" });
await new Promise((resolve) => setTimeout(resolve, 450));
const pageInfo = (await fetch("http://127.0.0.1:9233/json/list").then((r) => r.json()))
  .find((entry) => entry.id === target.result.targetId && entry.type === "page");
if (!pageInfo?.webSocketDebuggerUrl) throw new Error("Local page target unavailable");
const page = new WebSocket(pageInfo.webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  page.addEventListener("open", resolve, { once: true });
  page.addEventListener("error", reject, { once: true });
});
let id = 0;
const pending = new Map();
const blocked = [];
const runtimeExceptions = [];
page.addEventListener("message", ({ data }) => {
  const message = JSON.parse(data);
  if (message.method === "Fetch.requestPaused") {
    const requestId = ++id;
    const url = new URL(message.params.request.url);
    const allowed = url.protocol === "http:" && url.hostname === "127.0.0.1" && ["5172", "5173", "5174"].includes(url.port);
    if (!allowed) blocked.push(url.toString());
    page.send(JSON.stringify(allowed
      ? { id: requestId, method: "Fetch.continueRequest", params: { requestId: message.params.requestId } }
      : { id: requestId, method: "Fetch.failRequest", params: { requestId: message.params.requestId, errorReason: "BlockedByClient" } }));
  }
  if (message.method === "Runtime.exceptionThrown") runtimeExceptions.push(message.params.exceptionDetails?.text || "Runtime exception");
  const callback = pending.get(message.id);
  if (!callback) return;
  pending.delete(message.id);
  if (message.error) callback.reject(new Error(message.error.message));
  else callback.resolve(message);
});
function command(method, params = {}) {
  const requestId = ++id;
  return new Promise((resolve, reject) => {
    pending.set(requestId, { resolve, reject });
    page.send(JSON.stringify({ id: requestId, method, params }));
    setTimeout(() => reject(new Error(`Timed out: ${method}`)), 15000);
  });
}
async function evaluate(expression) {
  const result = await command("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  return result.result?.result?.value;
}
await command("Page.enable");
await command("Runtime.enable");
await command("Network.enable");
await command("Fetch.enable", { patterns: [{ urlPattern: "*" }] });
await command("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
const injected = await command("Page.addScriptToEvaluateOnNewDocument", { source: `(() => {
  const prototype = WebGL2RenderingContext.prototype;
  const original = prototype.getProgramParameter;
  window.__forcedShaderLinkFailures = 0;
  prototype.getProgramParameter = function (program, parameter) {
    if (parameter === this.LINK_STATUS) {
      window.__forcedShaderLinkFailures += 1;
      return false;
    }
    return original.call(this, program, parameter);
  };
})();` });
await command("Page.navigate", { url: "http://127.0.0.1:5172/login" });
await new Promise((resolve) => setTimeout(resolve, 1600));
const state = await evaluate(`(() => {
  const host = document.querySelector(".s2l-auth-scene-host");
  const fallback = document.querySelector(".s2l-auth-art-fallback");
  const fallbackLayer = document.querySelector(".s2l-auth-art-fallback-layer");
  const canvas = document.querySelector(".s2l-auth-webgl");
  return {
    injectedFailureCount: window.__forcedShaderLinkFailures || 0,
    webglReady: host?.dataset.webglReady === "true",
    fallbackOpacity: fallbackLayer ? getComputedStyle(fallbackLayer).opacity : fallback ? getComputedStyle(fallback).opacity : "missing",
    fallbackVisible: Boolean(fallback && fallbackLayer && Number(getComputedStyle(fallbackLayer).opacity) > 0.01),
    canvasReady: Boolean(canvas?.classList.contains("is-ready")),
    viewport: { width: innerWidth, height: innerHeight },
  };
})()`);
const screenshot = await command("Page.captureScreenshot", { format: "png", fromSurface: true, captureBeyondViewport: false });
await mkdir(outputDir, { recursive: true });
const screenshotPath = join(outputDir, "webgl-failure-fallback-1440x900.png");
await writeFile(screenshotPath, Buffer.from(screenshot.result.data, "base64"));
const result = {
  method: "Isolated local browser injection forces WebGL2 program link checks to fail before the login module loads.",
  state,
  runtimeExceptions,
  blockedNonLoopbackRequests: blocked,
  screenshot: "screenshots/auth-redesign-rev27/webgl-failure-fallback-1440x900.png",
};
await writeFile(join(outputDir, "webgl-fallback-observation.json"), JSON.stringify(result, null, 2), "utf8");
console.log(JSON.stringify(result, null, 2));
page.close();
await browserCommand("Target.closeTarget", { targetId: target.result.targetId });
browser.close();