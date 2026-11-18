import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const evidenceDir = dirname(fileURLToPath(import.meta.url));
const outputDir = join(evidenceDir, "screenshots", "teacher-rev24");
const allowedPorts = new Set(["5172"]);
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
      reject(new Error(`Timed out waiting for ${method}`));
    }, 12000);
  });
}

const created = await browserCommand("Target.createTarget", { url: "http://127.0.0.1:5172/login" });
await wait(450);
const targets = await fetch("http://127.0.0.1:9233/json/list").then((r) => r.json());
const page = targets.find((target) => target.id === created.result.targetId && target.type === "page");
if (!page?.webSocketDebuggerUrl) throw new Error("Could not create an isolated local preview tab.");
const socket = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  socket.addEventListener("open", resolve, { once: true });
  socket.addEventListener("error", reject, { once: true });
});
let nextId = 0;
const pending = new Map();
const exceptions = [];
socket.addEventListener("message", ({ data }) => {
  const message = JSON.parse(data);
  if (message.method === "Fetch.requestPaused") {
    const requestId = ++nextId;
    const url = new URL(message.params.request.url);
    const localApp = url.protocol === "http:" && url.hostname === "127.0.0.1" && allowedPorts.has(url.port);
    socket.send(JSON.stringify(localApp
      ? { id: requestId, method: "Fetch.continueRequest", params: { requestId: message.params.requestId } }
      : { id: requestId, method: "Fetch.failRequest", params: { requestId: message.params.requestId, errorReason: "BlockedByClient" } }));
  }
  if (message.method === "Runtime.exceptionThrown") exceptions.push(message.params.exceptionDetails?.text || "Runtime exception");
  if (message.id === undefined || !pending.has(message.id)) return;
  const callback = pending.get(message.id);
  pending.delete(message.id);
  clearTimeout(callback.timer);
  if (message.error) callback.reject(new Error(message.error.message));
  else callback.resolve(message);
});
function command(method, params = {}) {
  const id = ++nextId;
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    socket.send(JSON.stringify({ id, method, params }));
    const timer = setTimeout(() => {
      if (!pending.has(id)) return;
      pending.delete(id);
      reject(new Error(`Timed out waiting for ${method}`));
    }, 15000);
    pending.get(id).timer = timer;
  });
}
async function evaluate(expression) {
  const response = await command("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  return response.result?.result?.value;
}
async function navigate(url) {
  await command("Page.navigate", { url });
  await wait(850);
}
async function setViewport(width, height) {
  await command("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: width < 600 });
}
async function capture(name, route, width, height) {
  await setViewport(width, height);
  await navigate(`http://127.0.0.1:5172${route}`);
  const observation = await evaluate(`(()=>({route:location.pathname,viewport:{width:innerWidth,height:innerHeight},documentWidth:document.documentElement.scrollWidth,horizontalOverflow:document.documentElement.scrollWidth>innerWidth,viteError:Boolean(document.querySelector("vite-error-overlay")),heading:document.querySelector("h1")?.innerText||"",previewLabel:document.body.innerText.includes("Bản xem thử · không lưu"),hasMockTeacherName:document.body.innerText.includes("Cô Thảo"),hasMockClassName:/Lớp Mầm|Mầm 2|Trường Ánh Dương/.test(document.body.innerText)}))()`);
  const image = await command("Page.captureScreenshot", { format: "png", fromSurface: true, captureBeyondViewport: false });
  const file = `${name}-${width}.png`;
  await writeFile(join(outputDir, file), Buffer.from(image.result.data, "base64"));
  return { file, ...observation };
}

await mkdir(outputDir, { recursive: true });
await command("Page.enable");
await command("Runtime.enable");
await command("Network.enable");
await command("Fetch.enable", { patterns: [{ urlPattern: "*" }] });
await setViewport(1440, 900);
await navigate("http://127.0.0.1:5172/login");
await evaluate('(()=>{sessionStorage.clear();sessionStorage.setItem("s2l-web-role","TEACHER");sessionStorage.setItem("s2l-web-authenticated","true")})()');
await command("Page.reload", { ignoreCache: true });
await wait(500);

const routes = [
  ["workbench", "/t01-lesson-workspace"],
  ["assigned-classes", "/t05-classes-and-children"],
  ["lesson-library", "/t02-lesson-authoring"],
  ["document-import", "/t03-document-import-review"],
  ["teaching-session", "/t04-session-sketch-deck"],
  ["sample-story-run", "/t06-sample-story-run"],
  ["video-projection", "/t07-video-presentation-confirmation"],
  ["settings", "/t08-settings"],
  ["history", "/t09-history"],
  ["inbox", "/t10-inbox"],
  ["profile", "/t11-profile"],
  ["activities", "/t12-activities"],
];
const captures = [];
for (const [name, route] of routes) {
  captures.push(await capture(name, route, 1440, 900));
  captures.push(await capture(name, route, 390, 844));
}

await setViewport(390, 844);
await navigate("http://127.0.0.1:5172/t01-lesson-workspace");
const pressKey = async (key, code, virtualKeyCode, text) => {
  const event = { key, code, windowsVirtualKeyCode: virtualKeyCode, nativeVirtualKeyCode: virtualKeyCode };
  await command("Input.dispatchKeyEvent", { type: "rawKeyDown", ...event });
  if (text) await command("Input.dispatchKeyEvent", { type: "char", ...event, text });
  await command("Input.dispatchKeyEvent", { type: "keyUp", ...event });
  await wait(120);
};
await pressKey("Tab", "Tab", 9);
const focusAfterTab = await evaluate('(()=>({className:document.activeElement?.className||"",label:document.activeElement?.getAttribute("aria-label")||""}))()');
await pressKey("Enter", "Enter", 13, "\r");
const menuAfterEnter = await evaluate('(()=>({expanded:document.querySelector(".teacher-mobile-menu")?.getAttribute("aria-expanded"),visible:getComputedStyle(document.querySelector(".teacher-rail")).visibility}))()');
const focusInsideMenu = await evaluate('(()=>({className:document.activeElement?.className||"",label:document.activeElement?.getAttribute("aria-label")||""}))()');
await pressKey("Escape", "Escape", 27);
await wait(260);
const menuAfterEscape = await evaluate('(()=>({expanded:document.querySelector(".teacher-mobile-menu")?.getAttribute("aria-expanded"),visible:getComputedStyle(document.querySelector(".teacher-rail")).visibility}))()');
const focusAfterEscape = await evaluate('(()=>({className:document.activeElement?.className||"",label:document.activeElement?.getAttribute("aria-label")||""}))()');
const activeNav = await evaluate('(()=>[...document.querySelectorAll(".teacher-nav-link")].filter(a=>a.getAttribute("aria-current")==="page").map(a=>a.getAttribute("aria-label")||a.innerText.trim()))()');

const observations = {
  browser: "isolated headless Chrome target; synthetic local TEACHER session flag only",
  networkPolicy: "Only HTTP requests to 127.0.0.1:5172 were allowed; other HTTP(S) requests were blocked.",
  captures,
  keyboard: { firstTabFocus: focusAfterTab, menuAfterEnter, focusInsideMenu, menuAfterEscape, focusAfterEscape, activeNav },
  runtimeExceptions: exceptions,
};
await writeFile(join(outputDir, "observations.json"), JSON.stringify(observations, null, 2), "utf8");
console.log(JSON.stringify({
  screenshotCount: captures.length,
  overflow: captures.filter((item) => item.horizontalOverflow).map((item) => item.file),
  viteErrors: captures.filter((item) => item.viteError).map((item) => item.file),
  mockMarkers: captures.filter((item) => item.hasMockTeacherName || item.hasMockClassName).map((item) => item.file),
  keyboard: observations.keyboard,
  runtimeExceptions: exceptions,
  evidencePath: outputDir,
}, null, 2));
socket.close();
await browserCommand("Target.closeTarget", { targetId: created.result.targetId });
browserSocket.close();
