import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const evidenceDir = dirname(fileURLToPath(import.meta.url));
const outputDir = join(evidenceDir, "screenshots", "auth-after");
const targets = await fetch("http://127.0.0.1:9233/json/list").then((response) => response.json());
const page = targets.find((target) => target.type === "page");
if (!page?.webSocketDebuggerUrl) throw new Error("Isolated local Edge page is unavailable.");
const socket = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  socket.addEventListener("open", resolve, { once: true });
  socket.addEventListener("error", reject, { once: true });
});
let nextId = 0;
const pending = new Map();
socket.addEventListener("message", ({ data }) => {
  const message = JSON.parse(data);
  if (message.id === undefined) return;
  const task = pending.get(message.id);
  if (!task) return;
  pending.delete(message.id);
  clearTimeout(task.timeout);
  if (message.error) task.reject(new Error(message.error.message));
  else task.resolve(message);
});
function cdp(method, params = {}) {
  const id = ++nextId;
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      pending.delete(id);
      reject(new Error("Timed out waiting for " + method));
    }, 12000);
    pending.set(id, { resolve, reject, timeout });
    socket.send(JSON.stringify({ id, method, params }));
  });
}
async function evaluate(expression) {
  const response = await cdp("Runtime.evaluate", { expression, returnByValue: true });
  if (response.result.exceptionDetails) throw new Error(response.result.exceptionDetails.text);
  return response.result.result.value;
}
async function key(keyName, code, keyCode) {
  await cdp("Input.dispatchKeyEvent", {
    type: "keyDown",
    key: keyName,
    code,
    windowsVirtualKeyCode: keyCode,
  });
  await cdp("Input.dispatchKeyEvent", {
    type: "keyUp",
    key: keyName,
    code,
    windowsVirtualKeyCode: keyCode,
  });
}
async function navigate(url) {
  await cdp("Page.navigate", { url });
  await new Promise((resolve) => setTimeout(resolve, 900));
}
await mkdir(outputDir, { recursive: true });
await cdp("Page.enable");
await cdp("Runtime.enable");

await cdp("Network.enable");
await cdp("Network.setBlockedURLs", { urls: ["https://*", "http://localhost:8000/*", "http://127.0.0.1:8000/*"] });
await cdp("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });

await navigate("http://127.0.0.1:5173/login");
await evaluate("document.activeElement.blur()");
await key("Tab", "Tab", 9);
await key("Tab", "Tab", 9);
const keyboardFocus = await evaluate("(() => ({tag:document.activeElement.tagName,text:document.activeElement.innerText.trim(),href:document.activeElement.href,outline:getComputedStyle(document.activeElement).outlineStyle}))()");
await key("Enter", "Enter", 13);
await new Promise((resolve) => setTimeout(resolve, 900));
const keyboardNavigation = await evaluate("({url:location.href,title:document.title,heading:document.querySelector('h1')?.innerText.trim()})");

await evaluate("document.querySelector('nav a[href*=\"5174\"]')?.click()");
await new Promise((resolve) => setTimeout(resolve, 900));
const platformAdminLink = await evaluate("({url:location.href,title:document.title,heading:document.querySelector('h1')?.innerText.trim()})");

await cdp("Emulation.setEmulatedMedia", {
  features: [{ name: "prefers-reduced-motion", value: "reduce" }],
});
await new Promise((resolve) => setTimeout(resolve, 120));
const reducedMotion = await evaluate("({preference:matchMedia('(prefers-reduced-motion: reduce)').matches,animationState:document.querySelector('.s2l-auth-scene-host')?.dataset.animation,webglReady:document.querySelector('.s2l-auth-webgl')?.classList.contains('is-ready')})");

const contextLossRequested = await evaluate("(() => { const canvas=document.querySelector('.s2l-auth-webgl'); const gl=canvas?.getContext('webgl2') || canvas?.getContext('webgl'); const extension=gl?.getExtension('WEBGL_lose_context'); if (!extension) return false; extension.loseContext(); return true; })()");
await new Promise((resolve) => setTimeout(resolve, 350));
const fallbackAfterContextLoss = await evaluate("({canvasReady:document.querySelector('.s2l-auth-webgl')?.classList.contains('is-ready') ?? false,sceneReady:document.querySelector('.s2l-auth-scene-host')?.dataset.webglReady ?? null,fallbackVisibility:getComputedStyle(document.querySelector('.s2l-auth-art-fallback')).visibility,documentWidth:document.documentElement.scrollWidth,viewportWidth:innerWidth})");

await navigate("http://127.0.0.1:5173/login");
let accessibilitySemantics;
try {
  const tree = await cdp("Accessibility.getFullAXTree");
  const roles = new Set(["main", "navigation", "link", "heading", "textbox", "button"]);
  accessibilitySemantics = tree.result.nodes
    .filter((node) => roles.has(node.role?.value))
    .map((node) => ({
      role: node.role?.value,
      name: node.name?.value,
      current: node.properties?.find((property) => property.name === "current")?.value?.value ?? null,
    }));
} catch (error) {
  accessibilitySemantics = { unavailable: error.message };
}

const observations = {
  scope: "Local-only UI interaction review; HTTPS blocked; no credentials or product API submitted.",
  accessibilitySemantics,
  keyboardFocus,
  keyboardEnterNavigation: keyboardNavigation,
  platformAdminRoleLink: platformAdminLink,
  reducedMotion,
  contextLossRequested,
  fallbackAfterContextLoss,
};
await writeFile(join(outputDir, "interactions.json"), JSON.stringify(observations, null, 2) + "\n");
await cdp("Emulation.setEmulatedMedia", { features: [] });
socket.close();
console.log(JSON.stringify(observations, null, 2));
