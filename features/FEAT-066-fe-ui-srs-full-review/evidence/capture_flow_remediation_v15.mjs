import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const evidenceDir = dirname(fileURLToPath(import.meta.url));
const outputDir = join(evidenceDir, "screenshots", "flow-remediation-v15");
const targets = await fetch("http://127.0.0.1:9233/json/list").then((response) => response.json());
const page = targets.find((target) => target.type === "page" && target.url.startsWith("http://127.0.0.1:5173"));
if (!page?.webSocketDebuggerUrl) throw new Error("Loopback review browser page is unavailable.");
const socket = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  socket.addEventListener("open", resolve, { once: true });
  socket.addEventListener("error", reject, { once: true });
});
let nextId = 0;
const pending = new Map();
socket.addEventListener("message", ({ data }) => {
  const message = JSON.parse(data);
  if (message.method === "Fetch.requestPaused") {
    const requestId = ++nextId;
    const url = message.params.request.url;
    const localApp = [5172, 5173, 5174].some((port) => url.startsWith(`http://127.0.0.1:${port}/`));
    socket.send(JSON.stringify(localApp
      ? { id: requestId, method: "Fetch.continueRequest", params: { requestId: message.params.requestId } }
      : { id: requestId, method: "Fetch.failRequest", params: { requestId: message.params.requestId, errorReason: "BlockedByClient" } }));
  }
  if (message.id === undefined || !pending.has(message.id)) return;
  const callbacks = pending.get(message.id);
  pending.delete(message.id);
  if (message.error) callbacks.reject(new Error(message.error.message));
  else callbacks.resolve(message);
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
    }, 15000);
  });
}
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
async function evaluate(expression) {
  const result = await cdp("Runtime.evaluate", { expression, returnByValue: true });
  return result.result?.result?.value;
}
async function navigate(url) {
  await cdp("Page.navigate", { url });
  await wait(700);
}
async function setViewport(width, height) {
  await cdp("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: width < 600 });
}
async function seedPreview(origin, role, route) {
  await navigate(origin + "/login");
  await evaluate(`(()=>{localStorage.clear();sessionStorage.clear();localStorage.setItem("s2l-web-theme","light");sessionStorage.setItem("s2l-web-role",${JSON.stringify(role)});sessionStorage.setItem("s2l-web-authenticated","true")})()`);
  await cdp("Page.reload", { ignoreCache: true });
  await wait(600);
  await navigate(origin + route);
}
async function capture(app, route, width, height) {
  await setViewport(width, height);
  await navigate(app.origin + route);
  const detail = await evaluate(`(()=>({route:location.pathname+location.search,viewport:{width:innerWidth,height:innerHeight},documentWidth:document.documentElement.scrollWidth,horizontalOverflow:document.documentElement.scrollWidth>innerWidth,viteError:Boolean(document.querySelector('vite-error-overlay')),heading:document.querySelector('h1')?.innerText||'',visibleText:document.body.innerText.slice(0,700)}))()`);
  const image = await cdp("Page.captureScreenshot", { format: "png", fromSurface: true, captureBeyondViewport: false });
  const routeName = (route.replace(/^\//, "") || "dashboard").replace(/[^a-zA-Z0-9-]+/g, "-").replace(/-+$/g, "") || "dashboard";
  const file = `${app.name}-${routeName}-${width}.png`;
  await writeFile(join(outputDir, file), Buffer.from(image.result.data, "base64"));
  return { app: app.name, file, ...detail };
}

await mkdir(outputDir, { recursive: true });
await cdp("Page.enable");
await cdp("Runtime.enable");
await cdp("Network.enable");
await cdp("Fetch.enable", { patterns: [{ urlPattern: "*" }] });
const viewports = [{ width: 1440, height: 900 }, { width: 390, height: 844 }];
const apps = [
  { name: "school-manager", origin: "http://127.0.0.1:5173", role: "MANAGER", routes: [
    "/m01-publication-review", "/m02-organization-management", "/m02-organization-management?section=teachers", "/m02-organization-management?section=classes", "/m02-organization-management?section=quota", "/m02-organization-management?section=settings",
  ] },
  { name: "teacher", origin: "http://127.0.0.1:5172", role: "TEACHER", routes: [
    "/t01-lesson-workspace", "/t02-lesson-authoring", "/t03-document-import-review", "/t04-session-sketch-deck", "/t05-classes-and-children", "/t05-classes-and-children/local-preview-class", "/t06-sample-story-run", "/t07-video-presentation-confirmation",
  ] },
  { name: "platform-admin", origin: "http://127.0.0.1:5174", role: "ADMIN", routes: [
    "/a01-content-moderation", "/a02-platform-operations", "/a02-platform-operations?panel=catalog",
  ] },
];
const observations = { networkPolicy: "Only HTTP requests to the three 127.0.0.1 Vite ports were continued; all other HTTP(S) requests were blocked.", captures: [], m01RequestChanges: null };
for (const app of apps) {
  await seedPreview(app.origin, app.role, app.routes[0]);
  for (const route of app.routes) {
    for (const viewport of viewports) observations.captures.push(await capture(app, route, viewport.width, viewport.height));
  }
}

const manager = apps[0];
await setViewport(1440, 900);
await navigate(manager.origin + "/m01-publication-review");
await evaluate(`(()=>{const field=document.querySelector('textarea');if(field){const setter=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set;setter.call(field,'Nội dung cần chỉnh sửa trước khi gửi duyệt.');field.dispatchEvent(new Event('input',{bubbles:true}));field.dispatchEvent(new Event('change',{bubbles:true}));} })()`);
await evaluate(`(()=>{const b=[...document.querySelectorAll('button')].find(x=>x.innerText.includes('Yêu cầu chỉnh sửa'));b?.click()})()`);
await wait(250);
observations.m01RequestChanges = await evaluate(`({localPreview:document.body.innerText.includes('Dữ liệu minh họa, không lưu'),counts:document.body.innerText.split('\\n').filter(x=>x.includes('Đã duyệt')||x.includes('Yêu cầu chỉnh sửa')),requestButtons:[...document.querySelectorAll('button')].filter(x=>x.innerText.includes('Yêu cầu chỉnh sửa')).length,visibleHeadings:[...document.querySelectorAll('h1,h2')].slice(0,8).map(x=>x.innerText)})`);
const changed = await cdp("Page.captureScreenshot", { format: "png", fromSurface: true, captureBeyondViewport: false });
await writeFile(join(outputDir, "school-manager-m01-after-request-changes-1440.png"), Buffer.from(changed.result.data, "base64"));
await writeFile(join(outputDir, "interaction-observations.json"), JSON.stringify(observations, null, 2), "utf8");
console.log(JSON.stringify({captureCount:observations.captures.length,overflowPages:observations.captures.filter(x=>x.horizontalOverflow).map(x=>x.file),viteErrors:observations.captures.filter(x=>x.viteError).map(x=>x.file),m01RequestChanges:observations.m01RequestChanges}, null, 2));
socket.close();
