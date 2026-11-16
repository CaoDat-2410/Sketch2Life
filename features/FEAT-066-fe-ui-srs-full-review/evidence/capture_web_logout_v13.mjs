import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const evidenceDir = dirname(fileURLToPath(import.meta.url));
const outputDir = join(evidenceDir, "screenshots", "web-logout-v13");
const targets = await fetch("http://127.0.0.1:9233/json/list").then((response) => response.json());
const initialTarget = targets.find((target) => target.type === "page" && target.url.startsWith("http://127.0.0.1:517"));
if (!initialTarget?.webSocketDebuggerUrl) throw new Error("No local role preview tab is available.");
const initialUrl = initialTarget.url;
const socket = new WebSocket(initialTarget.webSocketDebuggerUrl);
const runtimeErrors = [];
await new Promise((resolve, reject) => {
  socket.addEventListener("open", resolve, { once: true });
  socket.addEventListener("error", reject, { once: true });
});
let nextId = 0;
const pending = new Map();
socket.addEventListener("message", ({ data }) => {
  const message = JSON.parse(data);
  if (message.method === "Runtime.exceptionThrown") runtimeErrors.push(message.params.exceptionDetails?.text ?? "runtime exception");
  if (message.method === "Log.entryAdded" && message.params.entry?.level === "error") runtimeErrors.push(message.params.entry.text);
  if (message.id === undefined) return;
  const handler = pending.get(message.id);
  if (!handler) return;
  pending.delete(message.id);
  if (message.error) handler.reject(new Error(message.error.message));
  else handler.resolve(message);
});
function cdp(method, params = {}) {
  const id = ++nextId;
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    socket.send(JSON.stringify({ id, method, params }));
    setTimeout(() => {
      if (pending.has(id)) {
        pending.delete(id);
        reject(new Error("Timed out waiting for " + method));
      }
    }, 12000);
  });
}
const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const apps = [
  { name: "teacher", label: "Teacher", port: 5172, role: "TEACHER", route: "/t01-lesson-workspace", selector: ".tw-side-logout" },
  { name: "school-manager", label: "School Manager", port: 5173, role: "MANAGER", route: "/m02-organization-management", selector: ".mg-side .mg-logout-btn" },
  { name: "platform-admin", label: "Platform Admin", port: 5174, role: "ADMIN", route: "/a02-platform-operations", selector: ".mg-side .mg-logout-btn" },
];
const viewports = [
  { name: "desktop", width: 1440, height: 900, mobile: false },
  { name: "narrow", width: 390, height: 844, mobile: true },
];
const storageExpression = "JSON.stringify({local:Object.fromEntries(Array.from({length:localStorage.length},(_,i)=>{const k=localStorage.key(i);return [k,localStorage.getItem(k)]})),session:Object.fromEntries(Array.from({length:sessionStorage.length},(_,i)=>{const k=sessionStorage.key(i);return [k,sessionStorage.getItem(k)]}))})";
async function navigate(url) {
  await cdp("Page.navigate", { url });
  await pause(900);
}
async function readStorage() {
  const result = await cdp("Runtime.evaluate", { expression: storageExpression, returnByValue: true });
  return result.result?.result?.value ? JSON.parse(result.result.result.value) : { local: {}, session: {} };
}
async function writeStorage(storage) {
  const expression = "(()=>{const state=JSON.parse(" + JSON.stringify(JSON.stringify(storage)) + ");localStorage.clear();sessionStorage.clear();for(const [k,v] of Object.entries(state.local))localStorage.setItem(k,v);for(const [k,v] of Object.entries(state.session))sessionStorage.setItem(k,v);return true})()";
  await cdp("Runtime.evaluate", { expression, returnByValue: true });
}
const inspectExpression = (selector) => "(()=>{const e=document.querySelector(" + JSON.stringify(selector) + ");if(!e)return {found:false,route:location.pathname};const s=getComputedStyle(e);const r=e.getBoundingClientRect();return {found:true,route:location.pathname,viewport:{width:innerWidth,height:innerHeight},documentWidth:document.documentElement.scrollWidth,horizontalOverflow:document.documentElement.scrollWidth>innerWidth,text:e.innerText.trim(),accessibleName:e.getAttribute('aria-label')||e.innerText.trim(),title:e.title,visible:s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0,inViewport:r.right>0&&r.left<innerWidth&&r.bottom>0&&r.top<innerHeight,rect:{x:Math.round(r.x),y:Math.round(r.y),width:Math.round(r.width),height:Math.round(r.height)},focusable:e.tagName==='BUTTON'&&e.type==='button',viteError:!!document.querySelector('vite-error-overlay')}})()";
await mkdir(outputDir, { recursive: true });
await cdp("Page.enable");
await cdp("Runtime.enable");
await cdp("Log.enable");
const savedStorage = {};
const captures = [];
const logoutResults = [];
for (const app of apps) {
  const origin = "http://127.0.0.1:" + app.port;
  await navigate(origin + "/login");
  savedStorage[app.port] = await readStorage();
  const previewStorage = {
    local: { ...savedStorage[app.port].local, "s2l-web-theme": "light" },
    session: { ...savedStorage[app.port].session, "s2l-web-role": app.role, "s2l-web-authenticated": "true" },
  };
  await writeStorage(previewStorage);
  await cdp("Page.reload", { ignoreCache: true });
  await pause(800);
  for (const viewport of viewports) {
    await cdp("Emulation.setDeviceMetricsOverride", {
      width: viewport.width,
      height: viewport.height,
      deviceScaleFactor: 1,
      mobile: viewport.mobile,
    });
    await navigate(origin + app.route);
    const result = await cdp("Runtime.evaluate", { expression: inspectExpression(app.selector), returnByValue: true });
    const details = result.result?.result?.value ?? {};
    const shot = await cdp("Page.captureScreenshot", { format: "png", fromSurface: true, captureBeyondViewport: false });
    const file = app.name + "-dashboard-" + viewport.name + ".png";
    await writeFile(join(outputDir, file), Buffer.from(shot.result.data, "base64"));
    captures.push({ app: app.label, file, ...details });
  }
  await cdp("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
  await navigate(origin + app.route);
  const focusResult = await cdp("Runtime.evaluate", {
    expression: "(()=>{const e=document.querySelector(" + JSON.stringify(app.selector) + ");if(!e)return {found:false};e.focus();const s=getComputedStyle(e);const r=e.getBoundingClientRect();return {found:true,focused:document.activeElement===e,outlineWidth:s.outlineWidth,outlineStyle:s.outlineStyle,outlineColor:s.outlineColor,accessibleName:e.getAttribute('aria-label')||e.innerText.trim(),center:{x:r.x+r.width/2,y:r.y+r.height/2}}})()",
    returnByValue: true,
  });
  const focus = focusResult.result?.result?.value ?? {};
  const center = focus.center ?? { x: 24, y: 24 };
  await cdp("Input.dispatchMouseEvent", { type: "mouseMoved", x: center.x, y: center.y });
  await cdp("Input.dispatchMouseEvent", { type: "mousePressed", x: center.x, y: center.y, button: "left", clickCount: 1 });
  await cdp("Input.dispatchMouseEvent", { type: "mouseReleased", x: center.x, y: center.y, button: "left", clickCount: 1 });
  await pause(700);
  const logoutState = await cdp("Runtime.evaluate", {
    expression: "({route:location.pathname,roleCleared:sessionStorage.getItem('s2l-web-role')===null,authCleared:sessionStorage.getItem('s2l-web-authenticated')===null})",
    returnByValue: true,
  });
  logoutResults.push({ app: app.label, focus: { ...focus, center: undefined }, activation: "pointer", logout: logoutState.result?.result?.value ?? null });
  await navigate(origin + "/login");
  await writeStorage(savedStorage[app.port]);
  await cdp("Page.reload", { ignoreCache: true });
  await pause(600);
}
await cdp("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
await navigate(initialUrl);
await writeFile(join(outputDir, "observations.json"), JSON.stringify({
  note: "Manual loopback dashboard review; per-origin preview storage was restored after screenshots and logout button pointer interactions.",
  captures,
  logoutResults,
  runtimeErrors,
}, null, 2), "utf8");
console.log(JSON.stringify({ outputDir, captures, logoutResults, runtimeErrors }, null, 2));
socket.close();