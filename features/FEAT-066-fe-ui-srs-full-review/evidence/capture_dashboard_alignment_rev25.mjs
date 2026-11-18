import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const evidenceDir = dirname(fileURLToPath(import.meta.url));
const outputDir = join(evidenceDir, "screenshots", "dashboard-alignment-rev25");
const targets = {
  teacher: { port: "5172", role: "TEACHER", route: "/t01-lesson-workspace", menu: ".teacher-mobile-menu", rail: ".teacher-rail", nav: ".teacher-nav-link" },
  manager: { port: "5173", role: "MANAGER", route: "/m02-organization-management", menu: ".manager-mobile-menu", rail: ".manager-rail", nav: ".manager-nav-link" },
  admin: { port: "5174", role: "ADMIN", route: "/a02-platform-operations", menu: ".admin-mobile-menu", rail: ".admin-rail", nav: ".admin-nav-link" },
};
const requested = process.argv.slice(2).filter((name) => name in targets);
const selected = requested.length ? requested : Object.keys(targets);
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
await mkdir(outputDir, { recursive: true });
const results = [];
for (const roleName of selected) {
  const target = targets[roleName];
  const created = await browserCommand("Target.createTarget", { url: `http://127.0.0.1:${target.port}/login` });
  await wait(350);
  const pages = await fetch("http://127.0.0.1:9233/json/list").then((response) => response.json());
  const page = pages.find((item) => item.id === created.result.targetId && item.type === "page");
  if (!page?.webSocketDebuggerUrl) throw new Error(`Could not create isolated local preview for ${roleName}.`);
  const socket = new WebSocket(page.webSocketDebuggerUrl);
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
      const allowed = url.protocol === "http:" && url.hostname === "127.0.0.1" && url.port === target.port;
      socket.send(JSON.stringify(allowed
        ? { id: requestId, method: "Fetch.continueRequest", params: { requestId: message.params.requestId } }
        : { id: requestId, method: "Fetch.failRequest", params: { requestId: message.params.requestId, errorReason: "BlockedByClient" } }));
    }
    if (message.method === "Runtime.exceptionThrown") exceptions.push(message.params.exceptionDetails?.text || "Runtime exception");
    if (message.method === "Runtime.consoleAPICalled" && message.params.type === "error") {
      consoleErrors.push((message.params.args || []).map((item) => item.value || item.description || "").join(" "));
    }
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
    if (response.result?.exceptionDetails) throw new Error(response.result.exceptionDetails.text || "Browser evaluation failed");
    return response.result?.result?.value;
  }
  async function navigate(url) {
    await command("Page.navigate", { url });
    await wait(900);
  }
  async function setViewport(width, height) {
    await command("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: width < 600 });
  }
  async function press(key, code, virtualKeyCode) {
    const event = { key, code, windowsVirtualKeyCode: virtualKeyCode, nativeVirtualKeyCode: virtualKeyCode };
    await command("Input.dispatchKeyEvent", { type: "rawKeyDown", ...event });
    if (key === "Enter") await command("Input.dispatchKeyEvent", { type: "char", ...event, text: "\r" });
    await command("Input.dispatchKeyEvent", { type: "keyUp", ...event });
    await wait(180);
  }
  await command("Page.enable");
  await command("Runtime.enable");
  await command("Network.enable");
  await command("Fetch.enable", { patterns: [{ urlPattern: "*" }] });
  await setViewport(1440, 900);
  await navigate(`http://127.0.0.1:${target.port}/login`);
  await evaluate(`(()=>{sessionStorage.clear();sessionStorage.setItem("s2l-web-role",${JSON.stringify(target.role)});sessionStorage.setItem("s2l-web-authenticated","true")})()`);
  await command("Page.reload", { ignoreCache: true });
  await wait(650);
  async function capture(width, height) {
    await setViewport(width, height);
    await navigate(`http://127.0.0.1:${target.port}${target.route}`);
    const observation = await evaluate(`(()=>{const text=document.body.innerText;return{route:location.pathname,viewport:{width:innerWidth,height:innerHeight},documentWidth:document.documentElement.scrollWidth,horizontalOverflow:document.documentElement.scrollWidth>innerWidth,viteError:Boolean(document.querySelector("vite-error-overlay")),heading:document.querySelector("h1")?.innerText||"",previewLabel:text.includes("Bản xem thử · không lưu"),previewMentions:(text.match(/Bản xem thử/g)||[]).length,logoutControlPresent:Boolean(document.querySelector(".teacher-logout-button,.manager-logout-button,.admin-logout-button")),logoutControlVisible:(()=>{const item=document.querySelector(".teacher-logout-button,.manager-logout-button,.admin-logout-button");if(!item)return false;const rect=item.getBoundingClientRect();return rect.width>0&&rect.height>0&&getComputedStyle(item).visibility!=="hidden"})(),activeNav:[...document.querySelectorAll(${JSON.stringify(target.nav)})].filter(item=>item.classList.contains("is-active")).map(item=>item.innerText.trim()),ariaCurrentCount:[...document.querySelectorAll(${JSON.stringify(target.nav)})].filter(item=>item.getAttribute("aria-current")==="page").length}})()`);
    const image = await command("Page.captureScreenshot", { format: "png", fromSurface: true, captureBeyondViewport: false });
    const file = `${roleName}-overview-${width}.png`;
    await writeFile(join(outputDir, file), Buffer.from(image.result.data, "base64"));
    return { file, ...observation };
  }
  const captures = [await capture(1440, 900), await capture(390, 844)];
  await setViewport(390, 844);
  await navigate(`http://127.0.0.1:${target.port}${target.route}`);
  const menuSelector = JSON.stringify(target.menu);
  await evaluate(`document.querySelector(${menuSelector})?.focus()`);
  await press("Enter", "Enter", 13);
  const menuAfterEnter = await evaluate(`(()=>({expanded:document.querySelector(${menuSelector})?.getAttribute("aria-expanded"),railVisibility:getComputedStyle(document.querySelector(${JSON.stringify(target.rail)})).visibility,focusClass:document.activeElement?.className||"",logoutVisible:(()=>{const item=document.querySelector(".teacher-logout-button,.manager-logout-button,.admin-logout-button");if(!item)return false;const rect=item.getBoundingClientRect();return rect.width>0&&rect.height>0&&rect.left<innerWidth&&rect.right>0&&getComputedStyle(item).visibility!=="hidden"})()}))()`);
  await press("Escape", "Escape", 27);
  await wait(260);
  const menuAfterEscape = await evaluate(`(()=>({expanded:document.querySelector(${menuSelector})?.getAttribute("aria-expanded"),railVisibility:getComputedStyle(document.querySelector(${JSON.stringify(target.rail)})).visibility,focusReturned:document.activeElement===document.querySelector(${menuSelector})}))()`);
  results.push({ role: roleName, networkPolicy: `Only HTTP requests to 127.0.0.1:${target.port} were allowed; all other requests were blocked.`, captures, keyboard: { menuAfterEnter, menuAfterEscape }, runtimeExceptions: exceptions, consoleErrors });
  socket.close();
  await browserCommand("Target.closeTarget", { targetId: created.result.targetId });
}
const observations = { browser: "isolated local Chrome preview; synthetic sessionStorage role flag only", results };
await writeFile(join(outputDir, "observations.json"), JSON.stringify(observations, null, 2), "utf8");
console.log(JSON.stringify({
  roles: results.map((result) => result.role),
  screenshots: results.flatMap((result) => result.captures.map((capture) => capture.file)),
  overflow: results.flatMap((result) => result.captures.filter((capture) => capture.horizontalOverflow).map((capture) => capture.file)),
  viteErrors: results.flatMap((result) => result.captures.filter((capture) => capture.viteError).map((capture) => capture.file)),
  runtimeExceptions: results.flatMap((result) => result.runtimeExceptions.map((error) => ({ role: result.role, error }))),
  consoleErrors: results.flatMap((result) => result.consoleErrors.map((error) => ({ role: result.role, error }))),
  keyboard: results.map((result) => ({ role: result.role, ...result.keyboard })),
  evidencePath: outputDir,
}, null, 2));
await browserSocket.close();
