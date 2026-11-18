import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const evidenceDir = dirname(fileURLToPath(import.meta.url));
const outputDir = join(evidenceDir, "screenshots", "auth-teacher-v16");
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
  const detail = await evaluate('(()=>({url:location.href,viewport:{width:innerWidth,height:innerHeight},documentWidth:document.documentElement.scrollWidth,horizontalOverflow:document.documentElement.scrollWidth>innerWidth,viteError:Boolean(document.querySelector("vite-error-overlay")),heading:document.querySelector("h1")?.innerText||"",activeRole:[...document.querySelectorAll(".s2l-auth-portal.is-current .s2l-auth-portal-label")].map(x=>x.innerText),portalLinks:[...document.querySelectorAll(".s2l-auth-portal")].map(a=>({label:a.querySelector(".s2l-auth-portal-label")?.innerText,href:a.href,current:a.getAttribute("aria-current")})),authSubmitInFirstViewport:(()=>{const b=document.querySelector(".s2l-auth-submit");return !!b&&b.getBoundingClientRect().bottom<=innerHeight})(),previewNotice:document.body.innerText.includes("Xem thử cục bộ")}))()');
  const image = await command("Page.captureScreenshot", { format: "png", fromSurface: true, captureBeyondViewport: false });
  const file = name + "-" + width + ".png";
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
  { name: "auth-teacher", origin: "http://127.0.0.1:5172" },
  { name: "auth-school-manager", origin: "http://127.0.0.1:5173" },
  { name: "auth-platform-admin", origin: "http://127.0.0.1:5174" },
]) {
  for (const viewport of viewports) captures.push(await capture(app.name, app.origin + "/login", viewport.width, viewport.height));
}

await navigate("http://127.0.0.1:5172/login");
await evaluate('(()=>{localStorage.clear();sessionStorage.clear();localStorage.setItem("s2l-web-theme","light");sessionStorage.setItem("s2l-web-role","TEACHER");sessionStorage.setItem("s2l-web-authenticated","true")})()');
await command("Page.reload", { ignoreCache: true });
await wait(750);
for (const route of [
  { name: "teacher-dashboard", path: "/t01-lesson-workspace" },
  { name: "teacher-classes", path: "/t05-classes-and-children" },
  { name: "teacher-lessons", path: "/t02-lesson-authoring" },
  { name: "teacher-sketch-deck", path: "/t04-session-sketch-deck" },
]) {
  for (const viewport of viewports) captures.push(await capture(route.name, "http://127.0.0.1:5172" + route.path, viewport.width, viewport.height));
}
await setViewport(390, 844);
await navigate("http://127.0.0.1:5172/login");
await evaluate('(()=>{const input=document.querySelector("input[type=email]");if(input){const setter=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,"value").set;setter.call(input,"preview@example.invalid");input.dispatchEvent(new Event("input",{bubbles:true}));}})()');
await command("Runtime.evaluate", { expression: 'document.querySelector(".s2l-auth-submit")?.click()', returnByValue: true });
await wait(550);
const loginPreviewFlow = await evaluate('(()=>({route:location.pathname,role:sessionStorage.getItem("s2l-web-role"),authenticated:sessionStorage.getItem("s2l-web-authenticated"),previewLabel:document.body.innerText.includes("Xem thử · không lưu")}))()');
const observations = {
  browser: "isolated headless Chrome target",
  networkPolicy: "Only HTTP requests to 127.0.0.1 ports 5172, 5173, and 5174 were allowed; other HTTP(S) requests were blocked.",
  captures,
  loginPreviewFlow,
  runtimeExceptions: exceptions,
};
await writeFile(join(outputDir, "observations.json"), JSON.stringify(observations, null, 2), "utf8");
console.log(JSON.stringify({
  screenshotCount: captures.length,
  horizontalOverflow: captures.filter((x) => x.horizontalOverflow).map((x) => x.file),
  viteErrors: captures.filter((x) => x.viteError).map((x) => x.file),
  headings: captures.map((x) => ({ file: x.file, heading: x.heading })),
  runtimeExceptions: exceptions,
  loginPreviewFlow,
  evidencePath: outputDir,
}, null, 2));
socket.close();
await browserCommand("Target.closeTarget", { targetId: targetCreated.result.targetId });
browserSocket.close();