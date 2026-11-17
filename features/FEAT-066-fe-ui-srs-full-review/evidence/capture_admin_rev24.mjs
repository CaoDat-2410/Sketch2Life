import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const evidenceDir = dirname(fileURLToPath(import.meta.url));
const outputDir = join(evidenceDir, "screenshots", "admin-rev24");
const appPort = "5174";
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const browserInfo = await fetch("http://127.0.0.1:9233/json/version").then((response) => response.json());
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
  clearTimeout(pending.timer);
  if (message.error) pending.reject(new Error(message.error.message));
  else pending.resolve(message);
});
function browserCommand(method, params = {}) {
  const id = ++browserId;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      if (!browserPending.has(id)) return;
      browserPending.delete(id);
      reject(new Error(`Timed out waiting for ${method}`));
    }, 12000);
    browserPending.set(id, { resolve, reject, timer });
    browserSocket.send(JSON.stringify({ id, method, params }));
  });
}

const target = await browserCommand("Target.createTarget", { url: `http://127.0.0.1:${appPort}/login` });
await wait(500);
const targetList = await fetch("http://127.0.0.1:9233/json/list").then((response) => response.json());
const pageTarget = targetList.find((item) => item.id === target.result.targetId && item.type === "page");
if (!pageTarget?.webSocketDebuggerUrl) throw new Error("Could not open an isolated Platform Admin preview tab.");
const socket = new WebSocket(pageTarget.webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  socket.addEventListener("open", resolve, { once: true });
  socket.addEventListener("error", reject, { once: true });
});

let nextId = 0;
const pending = new Map();
const exceptions = [];
const consoleErrors = [];
socket.addEventListener("message", ({ data }) => {
  const message = JSON.parse(data);
  if (message.method === "Fetch.requestPaused") {
    const requestId = ++nextId;
    const url = new URL(message.params.request.url);
    const localApp = url.protocol === "http:" && url.hostname === "127.0.0.1" && url.port === appPort;
    socket.send(JSON.stringify(localApp
      ? { id: requestId, method: "Fetch.continueRequest", params: { requestId: message.params.requestId } }
      : { id: requestId, method: "Fetch.failRequest", params: { requestId: message.params.requestId, errorReason: "BlockedByClient" } }));
  }
  if (message.method === "Runtime.exceptionThrown") exceptions.push(message.params.exceptionDetails?.text || "Runtime exception");
  if (message.method === "Runtime.consoleAPICalled" && message.params.type === "error") consoleErrors.push(message.params.args?.map((item) => item.value ?? item.description ?? "").join(" ") || "Console error");
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
    const timer = setTimeout(() => {
      if (!pending.has(id)) return;
      pending.delete(id);
      reject(new Error(`Timed out waiting for ${method}`));
    }, 15000);
    pending.set(id, { resolve, reject, timer });
    socket.send(JSON.stringify({ id, method, params }));
  });
}
async function evaluate(expression) {
  const result = await command("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  return result.result?.result?.value;
}
async function setViewport(width, height) {
  await command("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: width < 600 });
}
async function navigate(route) {
  await command("Page.navigate", { url: `http://127.0.0.1:${appPort}${route}` });
  await wait(1100);
}
async function capture(name, route, width, height) {
  await setViewport(width, height);
  await navigate(route);
  const observation = await evaluate(`(()=>({
    route:location.pathname+location.search,
    viewport:{width:innerWidth,height:innerHeight},
    documentWidth:Math.max(document.documentElement.scrollWidth,document.body.scrollWidth),
    horizontalOverflow:Math.max(document.documentElement.scrollWidth,document.body.scrollWidth)>innerWidth,
    viteError:Boolean(document.querySelector("vite-error-overlay")),
    heading:document.querySelector("h1")?.innerText||"",
    activeNav:[...document.querySelectorAll(".admin-nav-link[aria-current='page']")].map((node)=>node.innerText.trim()),
    fakeOrganization:/Ánh Dương|Hiệu trưởng Minh|Quản trị viên\\b/.test(document.body.innerText),
    fakeAmount:/₫|VND|\\b\\d+\\s*(lượt|quota|slot|trường)\\b/.test(document.body.innerText),
    unreadDot:Boolean(document.querySelector(".admin-unread-dot,.admin-notification-dot,.mg-dot")),
    unavailableVisible:document.body.innerText.includes("Chưa khả dụng")||document.body.innerText.includes("Chưa kiểm tra")||document.body.innerText.includes("chưa có API"),
  }))()`);
  const screenshot = await command("Page.captureScreenshot", { format: "png", fromSurface: true, captureBeyondViewport: false });
  const file = `${name}-${width}.png`;
  await writeFile(join(outputDir, file), Buffer.from(screenshot.result.data, "base64"));
  return { file, ...observation };
}

await mkdir(outputDir, { recursive: true });
await command("Page.enable");
await command("Runtime.enable");
await command("Network.enable");
await command("Fetch.enable", { patterns: [{ urlPattern: "*" }] });
await setViewport(1440, 900);
await navigate("/login");
await evaluate('(()=>{sessionStorage.clear();sessionStorage.setItem("s2l-web-role","ADMIN");sessionStorage.setItem("s2l-web-authenticated","true")})()');
await command("Page.reload", { ignoreCache: true });
await wait(600);

const routes = [
  ["overview", "/a02-platform-operations"],
  ["organizations", "/a02-platform-operations?panel=orgs"],
  ["queues-jobs", "/a02-platform-operations?panel=queues"],
  ["lifecycle", "/a02-platform-operations?panel=lifecycle"],
  ["audit", "/a02-platform-operations?panel=audit"],
  ["content-moderation", "/a01-content-moderation"],
  ["activity-catalog", "/a02-platform-operations?panel=catalog"],
  ["permissions", "/a02-platform-operations?panel=permissions"],
  ["quota-policy", "/a02-platform-operations?panel=quota"],
  ["billing-reconciliation", "/a02-platform-operations?panel=billing"],
  ["feedback", "/a02-platform-operations?panel=feedback"],
  ["inbox", "/a02-platform-operations?panel=inbox"],
];
const captures = [];
for (const [name, route] of routes) {
  captures.push(await capture(name, route, 1440, 900));
  captures.push(await capture(name, route, 390, 844));
}

await setViewport(390, 844);
await navigate("/a02-platform-operations");
const pressKey = async (key, code, keyCode, text) => {
  const event = { key, code, windowsVirtualKeyCode: keyCode, nativeVirtualKeyCode: keyCode };
  await command("Input.dispatchKeyEvent", { type: "rawKeyDown", ...event });
  if (text) await command("Input.dispatchKeyEvent", { type: "char", ...event, text });
  await command("Input.dispatchKeyEvent", { type: "keyUp", ...event });
  await wait(180);
};
await pressKey("Tab", "Tab", 9);
const focusAfterTab = await evaluate('(()=>({className:document.activeElement?.className||"",label:document.activeElement?.getAttribute("aria-label")||""}))()');
await pressKey("Enter", "Enter", 13, "\r");
const menuAfterEnter = await evaluate('(()=>({expanded:document.querySelector(".admin-mobile-menu")?.getAttribute("aria-expanded"),visibility:getComputedStyle(document.querySelector(".admin-rail")).visibility}))()');
const focusInsideMenu = await evaluate('(()=>({className:document.activeElement?.className||"",label:document.activeElement?.getAttribute("aria-label")||""}))()');
await pressKey("Escape", "Escape", 27);
await wait(230);
const menuAfterEscape = await evaluate('(()=>({expanded:document.querySelector(".admin-mobile-menu")?.getAttribute("aria-expanded"),visibility:getComputedStyle(document.querySelector(".admin-rail")).visibility}))()');
const focusAfterEscape = await evaluate('(()=>({className:document.activeElement?.className||"",label:document.activeElement?.getAttribute("aria-label")||""}))()');
await setViewport(1440, 900);
await navigate("/a02-platform-operations");
const logoutPoint = await evaluate('(()=>{const r=document.querySelector(".admin-logout-button").getBoundingClientRect();return{x:r.left+r.width/2,y:r.top+r.height/2}})()');
await command("Input.dispatchMouseEvent", { type: "mouseMoved", x: logoutPoint.x, y: logoutPoint.y });
await command("Input.dispatchMouseEvent", { type: "mousePressed", x: logoutPoint.x, y: logoutPoint.y, button: "left", clickCount: 1 });
await command("Input.dispatchMouseEvent", { type: "mouseReleased", x: logoutPoint.x, y: logoutPoint.y, button: "left", clickCount: 1 });
await wait(450);
const logoutCheck = await evaluate('(()=>({path:location.pathname,role:sessionStorage.getItem("s2l-web-role"),authenticated:sessionStorage.getItem("s2l-web-authenticated")}))()');
const observations = {
  browser: "isolated local Chrome tab with synthetic ADMIN sessionStorage only",
  networkPolicy: `Only HTTP requests to 127.0.0.1:${appPort} were allowed; other requests were blocked.`,
  captures,
  keyboard: { firstTabFocus: focusAfterTab, menuAfterEnter, focusInsideMenu, menuAfterEscape, focusAfterEscape },
  logout: logoutCheck,
  runtimeExceptions: exceptions,
  consoleErrors,
};
await writeFile(join(outputDir, "observations.json"), JSON.stringify(observations, null, 2), "utf8");
console.log(JSON.stringify({
  screenshotCount: captures.length,
  overflow: captures.filter((item) => item.horizontalOverflow).map((item) => item.file),
  viteErrors: captures.filter((item) => item.viteError).map((item) => item.file),
  fakeOrganizations: captures.filter((item) => item.fakeOrganization).map((item) => item.file),
  fakeAmounts: captures.filter((item) => item.fakeAmount).map((item) => item.file),
  unreadIndicators: captures.filter((item) => item.unreadDot).map((item) => item.file),
  unavailableStates: captures.filter((item) => item.unavailableVisible).length,
  keyboard: observations.keyboard,
  logout: logoutCheck,
  runtimeExceptions: exceptions,
  consoleErrors,
  evidencePath: outputDir,
}, null, 2));
socket.close();
await browserCommand("Target.closeTarget", { targetId: target.result.targetId });
browserSocket.close();
