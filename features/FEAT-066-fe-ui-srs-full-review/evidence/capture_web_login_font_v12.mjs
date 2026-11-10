import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
const evidenceDir = dirname(fileURLToPath(import.meta.url));
const outputDir = join(evidenceDir, "screenshots", "web-login-font-v12");
const targets = await fetch("http://127.0.0.1:9233/json/list").then((r) => r.json());
const page = targets.find((target) => target.type === "page" && /127\.0.0.1:517[234]/.test(target.url));
if (!page?.webSocketDebuggerUrl) throw new Error("No local role preview tab is available.");
const socket = new WebSocket(page.webSocketDebuggerUrl);
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
  { name: "teacher", label: "Teacher", port: 5172 },
  { name: "school-manager", label: "School Manager", port: 5173 },
  { name: "platform-admin", label: "Platform Admin", port: 5174 },
];
const viewports = [
  { name: "desktop", width: 1440, height: 900, mobile: false },
  { name: "narrow", width: 390, height: 844, mobile: true },
];
const expression = "(()=>{const e=document.querySelector('.s2l-auth-title');const s=e?getComputedStyle(e):null;const r=e?.getBoundingClientRect();return {route:location.pathname,width:innerWidth,docWidth:document.documentElement.scrollWidth,overflow:document.documentElement.scrollWidth>innerWidth,role:document.querySelector('.s2l-auth-role')?.innerText?.trim()||null,title:e?.innerText?.trim()||null,fontFamily:s?.fontFamily||null,fontWeight:s?.fontWeight||null,fontStyle:s?.fontStyle||null,lineHeight:s?.lineHeight||null,letterSpacing:s?.letterSpacing||null,rect:r?{x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)}:null,accentStyle:(()=>{const a=e?.querySelector('em');if(!a)return null;const x=getComputedStyle(a);return {fontFamily:x.fontFamily,fontWeight:x.fontWeight,fontStyle:x.fontStyle,letterSpacing:x.letterSpacing}})(),viteError:!!document.querySelector('vite-error-overlay')}})()";
const storageExpression = "JSON.stringify({local:Object.fromEntries(Array.from({length:localStorage.length},(_,i)=>{const k=localStorage.key(i);return [k,localStorage.getItem(k)]})),session:Object.fromEntries(Array.from({length:sessionStorage.length},(_,i)=>{const k=sessionStorage.key(i);return [k,sessionStorage.getItem(k)]}))})";
async function navigate(url) {
  await cdp("Page.navigate", { url });
  await pause(1000);
}
async function readStorage() {
  const result = await cdp("Runtime.evaluate", { expression: storageExpression, returnByValue: true });
  return result.result?.result?.value ? JSON.parse(result.result.result.value) : { local: {}, session: {} };
}
async function writeStorage(storage) {
  const expression = "(()=>{const state=JSON.parse(" + JSON.stringify(JSON.stringify(storage)) + ");localStorage.clear();sessionStorage.clear();for(const [k,v] of Object.entries(state.local))localStorage.setItem(k,v);for(const [k,v] of Object.entries(state.session))sessionStorage.setItem(k,v);return true})()";
  await cdp("Runtime.evaluate", { expression, returnByValue: true });
}
await mkdir(outputDir, { recursive: true });
await cdp("Page.enable");
await cdp("Runtime.enable");
await cdp("Log.enable");
const savedStorage = {};
const captures = [];
for (const app of apps) {
  const origin = "http://127.0.0.1:" + app.port;
  await navigate(origin + "/login");
  savedStorage[app.port] = await readStorage();
  await writeStorage({ local: { "s2l-web-theme": "light" }, session: {} });
  await cdp("Page.reload", { ignoreCache: true });
  await pause(900);
  for (const viewport of viewports) {
    await cdp("Emulation.setDeviceMetricsOverride", { width: viewport.width, height: viewport.height, deviceScaleFactor: 1, mobile: viewport.mobile });
    await navigate(origin + "/login");
    const result = await cdp("Runtime.evaluate", { expression, returnByValue: true });
    const details = result.result?.result?.value ?? {};
    const shot = await cdp("Page.captureScreenshot", { format: "png", fromSurface: true, captureBeyondViewport: false });
    const file = app.name + "-login-" + viewport.name + ".png";
    await writeFile(join(outputDir, file), Buffer.from(shot.result.data, "base64"));
    captures.push({ app: app.label, file, ...details });
  }
  await navigate(origin + "/login");
  await writeStorage(savedStorage[app.port]);
  await cdp("Page.reload", { ignoreCache: true });
  await pause(700);
}
await cdp("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
await navigate("http://127.0.0.1:5172/login");
await writeFile(join(outputDir, "observations.json"), JSON.stringify({
  note: "Manual loopback login screenshots after the shared typography fix. Existing per-origin preview storage was restored after capture.",
  captures,
  runtimeErrors,
}, null, 2), "utf8");
console.log(JSON.stringify({ outputDir, captures, runtimeErrors }, null, 2));
socket.close();