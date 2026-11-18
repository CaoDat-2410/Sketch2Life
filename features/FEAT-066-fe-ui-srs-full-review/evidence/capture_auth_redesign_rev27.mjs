import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const evidenceDir = dirname(fileURLToPath(import.meta.url));
const outputDir = join(evidenceDir, "screenshots", "auth-redesign-rev27");
const allowedPorts = new Set(["5172", "5173", "5174"]);
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const browserInfo = await fetch("http://127.0.0.1:9233/json/version").then((r) => r.json());
const browserSocket = new WebSocket(browserInfo.webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  browserSocket.addEventListener("open", resolve, { once: true });
  browserSocket.addEventListener("error", reject, { once: true });
});
let browserId = 0;
const browserPending = new Map();
browserSocket.addEventListener("message", ({ data }) => {
  const message = JSON.parse(data);
  if (message.id === undefined || !browserPending.has(message.id)) return;
  const pending = browserPending.get(message.id);
  browserPending.delete(message.id);
  if (message.error) pending.reject(new Error(message.error.message));
  else pending.resolve(message);
});
function browserCommand(method, params = {}) {
  const id = ++browserId;
  return new Promise((resolve, reject) => {
    browserPending.set(id, { resolve, reject });
    browserSocket.send(JSON.stringify({ id, method, params }));
    setTimeout(() => {
      if (!browserPending.has(id)) return;
      browserPending.delete(id);
      reject(new Error("Timed out waiting for " + method));
    }, 12000);
  });
}

const targetCreated = await browserCommand("Target.createTarget", { url: "http://127.0.0.1:5172/login" });
await wait(450);
const targets = await fetch("http://127.0.0.1:9233/json/list").then((r) => r.json());
const page = targets.find((target) => target.id === targetCreated.result.targetId && target.type === "page");
if (!page?.webSocketDebuggerUrl) throw new Error("Could not create an isolated local preview tab.");
const socket = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  socket.addEventListener("open", resolve, { once: true });
  socket.addEventListener("error", reject, { once: true });
});
let nextId = 0;
const pending = new Map();
const runtimeExceptions = [];
const consoleErrors = [];
const networkResponses = [];
const failedRequests = [];
const blockedRequests = [];
const requestUrls = new Map();
socket.addEventListener("message", ({ data }) => {
  const message = JSON.parse(data);
  if (message.method === "Fetch.requestPaused") {
    const requestId = ++nextId;
    const url = new URL(message.params.request.url);
    const localApp = url.protocol === "http:" && url.hostname === "127.0.0.1" && allowedPorts.has(url.port);
    if (!localApp) blockedRequests.push({ url: url.toString(), resourceType: message.params.resourceType });
    socket.send(JSON.stringify(localApp
      ? { id: requestId, method: "Fetch.continueRequest", params: { requestId: message.params.requestId } }
      : { id: requestId, method: "Fetch.failRequest", params: { requestId: message.params.requestId, errorReason: "BlockedByClient" } }));
  }
  if (message.method === "Network.requestWillBeSent") requestUrls.set(message.params.requestId, message.params.request.url);
  if (message.method === "Network.responseReceived" && message.params.response.status >= 400) {
    networkResponses.push({ url: message.params.response.url, status: message.params.response.status, statusText: message.params.response.statusText });
  }
  if (message.method === "Network.loadingFailed") {
    failedRequests.push({ url: requestUrls.get(message.params.requestId) || "unknown", error: message.params.errorText, canceled: message.params.canceled });
  }
  if (message.method === "Runtime.exceptionThrown") runtimeExceptions.push(message.params.exceptionDetails?.text || "Runtime exception");
  if (message.method === "Log.entryAdded" && message.params.entry?.level === "error") {
    const entry = message.params.entry;
    const text = entry.text || "Console error";
    if (!text.includes("ERR_BLOCKED_BY_CLIENT.Inspector")) consoleErrors.push({ text, url: entry.url || "", source: entry.source || "" });
  }
  if (message.id === undefined || !pending.has(message.id)) return;
  const callbacks = pending.get(message.id);
  pending.delete(message.id);
  if (message.error) callbacks.reject(new Error(message.error.message));
  else callbacks.resolve(message);
});
function command(method, params = {}) {
  const id = ++nextId;
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    socket.send(JSON.stringify({ id, method, params }));
    setTimeout(() => {
      if (!pending.has(id)) return;
      pending.delete(id);
      reject(new Error("Timed out waiting for " + method));
    }, 15000);
  });
}
async function evaluate(expression) {
  const result = await command("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  return result.result?.result?.value;
}
async function navigate(url) {
  await command("Page.navigate", { url });
  await wait(900);
}
async function setViewport(width, height) {
  await command("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: width < 600 });
}
async function waitForScene(width) {
  if (width < 901) return;
  for (let attempt = 0; attempt < 20; attempt += 1) {
    const ready = await evaluate('Boolean(document.querySelector(".s2l-auth-scene-host[data-webgl-ready=\\\"true\\\"]"))');
    if (ready) return;
    await wait(200);
  }
}
async function capture(role, origin, width, height) {
  await setViewport(width, height);
  await navigate(origin + "/login");
  await waitForScene(width);
  if (width >= 901) await wait(300);
  const detail = await evaluate(`(()=>({
    url: location.href,
    viewport: { width: innerWidth, height: innerHeight },
    documentWidth: document.documentElement.scrollWidth,
    horizontalOverflow: document.documentElement.scrollWidth > innerWidth,
    viteError: Boolean(document.querySelector("vite-error-overlay")),
    heading: document.querySelector("h1")?.innerText || "",
    roleLabel: document.querySelector(".s2l-auth-panel-role")?.innerText || "",
    activePortal: document.querySelector(".s2l-auth-portal[aria-current=page]")?.innerText || "",
    ariaCurrentCount: document.querySelectorAll(".s2l-auth-portal[aria-current=page]").length,
    portalLinks: [...document.querySelectorAll(".s2l-auth-portal")].map((item) => ({
      label: item.querySelector(".s2l-auth-portal-label")?.innerText || "",
      href: item.href || "",
      current: item.getAttribute("aria-current"),
      disabled: item.getAttribute("aria-disabled") === "true"
    })),
    fieldLabels: [...document.querySelectorAll(".s2l-auth-field span")].map((item) => item.innerText),
    submitText: document.querySelector(".s2l-auth-submit")?.innerText || "",
    submitInFirstViewport: (() => { const button = document.querySelector(".s2l-auth-submit"); return Boolean(button && button.getBoundingClientRect().bottom <= innerHeight); })(),
    previewNotice: document.querySelector("#s2l-auth-preview-note")?.innerText || "",
    artworkFallbackVisible: (() => { const art = document.querySelector(".s2l-auth-art-fallback-layer") || document.querySelector(".s2l-auth-art-fallback"); return Boolean(art && Number(getComputedStyle(art).opacity) > 0.01); })(),
    artworkFallbackOpacity: (() => { const art = document.querySelector(".s2l-auth-art-fallback-layer") || document.querySelector(".s2l-auth-art-fallback"); return art ? getComputedStyle(art).opacity : "missing"; })(),
    artworkFallbackParent: document.querySelector(".s2l-auth-art-fallback")?.parentElement?.className || "",
    artworkFallbackInsideScene: Boolean(document.querySelector(".s2l-auth-scene-host")?.contains(document.querySelector(".s2l-auth-art-fallback"))),
    webglCanvasOpacity: document.querySelector(".s2l-auth-webgl") ? getComputedStyle(document.querySelector(".s2l-auth-webgl")).opacity : "missing",
    webglReady: Boolean(document.querySelector(".s2l-auth-scene-host[data-webgl-ready=\\\"true\\\"]")),
    keyboardFocusVisibleRule: Boolean(document.querySelector(".s2l-auth-portal:focus-visible, .s2l-auth-field input:focus-visible, .s2l-auth-submit:focus-visible"))
  }))()`);
  const image = await command("Page.captureScreenshot", { format: "png", fromSurface: true, captureBeyondViewport: false });
  const file = `${role}-${width}x${height}.png`;
  await writeFile(join(outputDir, file), Buffer.from(image.result.data, "base64"));
  return { file, ...detail };
}

await mkdir(outputDir, { recursive: true });
await command("Page.enable");
await command("Runtime.enable");
await command("Log.enable");
await command("Network.enable");
await command("Fetch.enable", { patterns: [{ urlPattern: "*" }] });
const viewports = [
  { width: 1440, height: 900 },
  { width: 1024, height: 768 },
  { width: 768, height: 1024 },
  { width: 390, height: 844 },
];
const captures = [];
for (const app of [
  { role: "teacher", origin: "http://127.0.0.1:5172" },
  { role: "school-manager", origin: "http://127.0.0.1:5173" },
  { role: "platform-admin", origin: "http://127.0.0.1:5174" },
]) {
  for (const viewport of viewports) {
    captures.push(await capture(app.role, app.origin, viewport.width, viewport.height));
  }
}
async function inspectKeyboard(role, origin) {
  await navigate(origin + "/login");
  await evaluate('(()=>{const active=document.activeElement;if(active instanceof HTMLElement) active.blur();window.focus()})()');
  const focusOrder = [];
  const tab = { type: "keyDown", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9, nativeVirtualKeyCode: 9 };
  for (let index = 0; index < 6; index += 1) {
    await command("Input.dispatchKeyEvent", tab);
    await command("Input.dispatchKeyEvent", { ...tab, type: "keyUp" });
    focusOrder.push(await evaluate(`(()=>{const el=document.activeElement;return {tag:el?.tagName||"",text:(el?.innerText||el?.getAttribute("aria-label")||"").trim(),href:el?.href||"",current:el?.getAttribute("aria-current"),focusVisible:el instanceof HTMLElement&&el.matches(":focus-visible"),outline:getComputedStyle(el).outlineStyle,outlineWidth:getComputedStyle(el).outlineWidth}})()`));
  }
  await command("Input.dispatchKeyEvent", { ...tab, type: "keyDown", modifiers: 8 });
  await command("Input.dispatchKeyEvent", { ...tab, type: "keyUp", modifiers: 8 });
  const reverseFocus = await evaluate('(()=>{const el=document.activeElement;return {tag:el?.tagName||"",text:(el?.innerText||el?.getAttribute("aria-label")||"").trim(),href:el?.href||"",current:el?.getAttribute("aria-current"),focusVisible:el instanceof HTMLElement&&el.matches(":focus-visible"),outline:getComputedStyle(el).outlineStyle}})()');
  return { role, focusOrder, reverseFocus };
}

const keyboard = [];
for (const app of [
  { role: "teacher", origin: "http://127.0.0.1:5172" },
  { role: "school-manager", origin: "http://127.0.0.1:5173" },
  { role: "platform-admin", origin: "http://127.0.0.1:5174" },
]) keyboard.push(await inspectKeyboard(app.role, app.origin));

const observations = {
  browser: "isolated local Chrome target; no auth credentials or product API calls",
  networkPolicy: "Only HTTP requests to 127.0.0.1 ports 5172, 5173 and 5174 were allowed; other requests were blocked.",
  roles: ["Teacher", "School Manager", "Platform Admin"],
  captures,
  keyboard,
  networkResponses,
  failedRequests,
  blockedRequests,
  runtimeExceptions,
  consoleErrors,
};
await writeFile(join(outputDir, "observations.json"), JSON.stringify(observations, null, 2), "utf8");
console.log(JSON.stringify({
  screenshotCount: captures.length,
  horizontalOverflow: captures.filter((item) => item.horizontalOverflow).map((item) => item.file),
  viteErrors: captures.filter((item) => item.viteError).map((item) => item.file),
  wrongActivePortalCount: captures.filter((item) => item.ariaCurrentCount !== 1).map((item) => item.file),
  roleMappings: captures.map((item) => ({ file: item.file, roleLabel: item.roleLabel, activePortal: item.activePortal })),
  firstViewportSubmitMissing: captures.filter((item) => !item.submitInFirstViewport).map((item) => item.file),
  keyboard: keyboard.map((item) => ({ role: item.role, focusOrder: item.focusOrder.map((step) => ({ tag: step.tag, text: step.text, focusVisible: step.focusVisible, outline: step.outline, href: step.href, current: step.current })), reverseFocus: item.reverseFocus })),
  networkResponses,
  failedRequests: failedRequests.length,
  blockedRequestCount: blockedRequests.length,
  runtimeExceptions,
  consoleErrors,
  evidencePath: outputDir,
}, null, 2));
socket.close();
await browserCommand("Target.closeTarget", { targetId: targetCreated.result.targetId });
browserSocket.close();
