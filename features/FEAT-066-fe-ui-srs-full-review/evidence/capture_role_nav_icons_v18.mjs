import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const evidenceDir = dirname(fileURLToPath(import.meta.url));
const outputDir = join(evidenceDir, "screenshots", "role-nav-icons-v18");
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
  await wait(750);
}
async function setViewport(width, height) {
  await command("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: width < 600 });
}
async function capture(name, url, width, height) {
  await setViewport(width, height);
  await navigate(url);
  const detail = await evaluate('(()=>({url:location.href,viewport:{width:innerWidth,height:innerHeight},documentWidth:document.documentElement.scrollWidth,horizontalOverflow:document.documentElement.scrollWidth>innerWidth,viteError:Boolean(document.querySelector("vite-error-overlay")),heading:document.querySelector("h1")?.innerText||"",emojiIcons:[...document.querySelectorAll(".s2l-icon-emoji")].map(x=>x.innerText),notificationIcon:document.querySelector(".s2l-icon-emoji--notification")?.innerText||"",visibleRole:document.body.innerText.slice(0,350)}))()');
  const image = await command("Page.captureScreenshot", { format: "png", fromSurface: true, captureBeyondViewport: false });
  const file = `${name}-${width}.png`;
  await writeFile(join(outputDir, file), Buffer.from(image.result.data, "base64"));
  return { file, ...detail };
}

await mkdir(outputDir, { recursive: true });
await command("Page.enable");
await command("Runtime.enable");
await command("Network.enable");
await command("Fetch.enable", { patterns: [{ urlPattern: "*" }] });
const viewports = [{ width: 1440, height: 900 }, { width: 390, height: 844 }];
const captures = [];
for (const app of [
  { name: "teacher", origin: "http://127.0.0.1:5172", role: "TEACHER", dashboard: "/t01-lesson-workspace" },
  { name: "school-manager", origin: "http://127.0.0.1:5173", role: "MANAGER", dashboard: "/m02-organization-management" },
  { name: "platform-admin", origin: "http://127.0.0.1:5174", role: "ADMIN", dashboard: "/a02-platform-operations" },
]) {
  await navigate(app.origin + "/login");
  const savedStorage = await evaluate('(()=>({local:Object.fromEntries(Object.keys(localStorage).map(k=>[k,localStorage.getItem(k)])),session:Object.fromEntries(Object.keys(sessionStorage).map(k=>[k,sessionStorage.getItem(k)]))}))()');
  await evaluate(`(()=>{localStorage.clear();sessionStorage.clear();localStorage.setItem("s2l-web-theme","light");sessionStorage.setItem("s2l-web-role",${JSON.stringify(app.role)});sessionStorage.setItem("s2l-web-authenticated","true")})()`);
  await command("Page.reload", { ignoreCache: true });
  await wait(650);
  for (const viewport of viewports) {
    captures.push(await capture(`${app.name}-dashboard`, app.origin + app.dashboard, viewport.width, viewport.height));
  }
  await evaluate('localStorage.setItem("s2l-web-theme","dark")');
  await command("Page.reload", { ignoreCache: true });
  await wait(650);
  captures.push(await capture(`${app.name}-dashboard-dark`, app.origin + app.dashboard, 1440, 900));
  await evaluate(`(()=>{localStorage.clear();for(const [k,v] of Object.entries(${JSON.stringify(savedStorage.local)}))localStorage.setItem(k,v);sessionStorage.clear();for(const [k,v] of Object.entries(${JSON.stringify(savedStorage.session)}))sessionStorage.setItem(k,v)})()`);
  await command("Page.reload", { ignoreCache: true });
  await wait(350);
}

const observations = {
  browser: "isolated headless Chrome target",
  networkPolicy: "Only HTTP requests to 127.0.0.1 ports 5172, 5173, and 5174 were allowed; all other HTTP(S) requests were blocked.",
  captures,
  runtimeExceptions: exceptions,
};
await writeFile(join(outputDir, "observations.json"), JSON.stringify(observations, null, 2), "utf8");
console.log(JSON.stringify({
  screenshotCount: captures.length,
  horizontalOverflow: captures.filter((x) => x.horizontalOverflow).map((x) => x.file),
  viteErrors: captures.filter((x) => x.viteError).map((x) => x.file),
  runtimeExceptions: exceptions,
  screenshots: captures.map((x) => x.file),
  evidencePath: outputDir,
}, null, 2));
socket.close();
await browserCommand("Target.closeTarget", { targetId: targetCreated.result.targetId });
browserSocket.close();
