import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const origin = "http://127.0.0.1:5173";
const evidenceDir = fileURLToPath(new URL(".", import.meta.url));
const outputDir = join(evidenceDir, "screenshots", "school-manager-theme-final");
const targets = await fetch("http://127.0.0.1:9233/json/list").then((response) => response.json());
const page = targets.find((target) => target.type === "page" && target.url.startsWith(origin));
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
  });
}
const delay = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));
async function evaluate(expression) {
  const result = await cdp("Runtime.evaluate", { expression, returnByValue: true });
  return result.result?.result?.value;
}
async function key(key, code, virtualKey) {
  if (key === "Enter") {
    await cdp("Input.dispatchKeyEvent", { type: "rawKeyDown", key, code, windowsVirtualKeyCode: virtualKey, nativeVirtualKeyCode: virtualKey });
    await cdp("Input.dispatchKeyEvent", { type: "char", key, code, text: "\r", unmodifiedText: "\r", windowsVirtualKeyCode: virtualKey, nativeVirtualKeyCode: virtualKey });
    await cdp("Input.dispatchKeyEvent", { type: "keyUp", key, code, windowsVirtualKeyCode: virtualKey, nativeVirtualKeyCode: virtualKey });
  } else {
    await cdp("Input.dispatchKeyEvent", { type: "keyDown", key, code, windowsVirtualKeyCode: virtualKey });
    await cdp("Input.dispatchKeyEvent", { type: "keyUp", key, code, windowsVirtualKeyCode: virtualKey });
  }
  await delay(100);
}
await mkdir(outputDir, { recursive: true });
await cdp("Page.enable");
await cdp("Runtime.enable");
await cdp("Network.enable");
await cdp("Network.setBlockedURLs", { urls: ["https://*", "http://localhost:8000/*", "http://127.0.0.1:8000/*"] });
await cdp("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
await cdp("Page.navigate", { url: `${origin}/login` });
await delay(500);
await evaluate("sessionStorage.clear(); sessionStorage.setItem('s2l-web-role','MANAGER'); sessionStorage.setItem('s2l-web-authenticated','true')");
await cdp("Page.navigate", { url: `${origin}/m01-publication-review` });
await delay(700);
const preview = await evaluate("document.body.innerText.includes('Dữ liệu minh họa, không lưu')");
if (!preview) throw new Error("Stopped because the review route is not in local preview mode.");
const interaction = { route: "/m01-publication-review", localPreview: preview };
interaction.initialTabs = await evaluate(`(() => { const tabs=[...document.querySelectorAll('[role=tab]')]; tabs[0]?.focus(); return {tabs:tabs.map(x=>({id:x.id,controls:x.getAttribute('aria-controls'),selected:x.getAttribute('aria-selected'),tabIndex:x.tabIndex})),panels:[...document.querySelectorAll('[role=tabpanel]')].map(x=>({id:x.id,labelledby:x.getAttribute('aria-labelledby'),hidden:x.hidden})),activeId:document.activeElement?.id}; })()`);
await key("ArrowRight", "ArrowRight", 39);
interaction.afterArrowRight = await evaluate(`({activeId:document.activeElement?.id,selected:document.activeElement?.getAttribute('aria-selected'),tabIndex:document.activeElement?.tabIndex})`);
await key("Home", "Home", 36);
interaction.afterHome = await evaluate(`({activeId:document.activeElement?.id,selected:document.activeElement?.getAttribute('aria-selected')})`);
await key("End", "End", 35);
interaction.afterEnd = await evaluate(`({activeId:document.activeElement?.id,selected:document.activeElement?.getAttribute('aria-selected')})`);
await key("ArrowLeft", "ArrowLeft", 37);
interaction.afterArrowLeft = await evaluate(`({activeId:document.activeElement?.id,selected:document.activeElement?.getAttribute('aria-selected')})`);
await evaluate(`(() => { const field=document.querySelector('textarea'); const setter=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set; setter.call(field,'Vui lòng chỉnh sửa trước khi công khai.'); field.dispatchEvent(new Event('input',{bubbles:true})); })()`);
await evaluate(`[...document.querySelectorAll('button')].find(button=>button.innerText.includes('Yêu cầu chỉnh sửa'))?.click()`);
await delay(300);
interaction.afterRequestChanges = await evaluate(`({counts:[...document.querySelectorAll('.mg-pill')].map(x=>x.innerText.trim()),bodyText:document.body.innerText.slice(0,500),apiPreviewNotice:document.querySelector('[role=status]')?.innerText})`);
const changedShot = await cdp("Page.captureScreenshot", { format: "png", fromSurface: true, captureBeyondViewport: false });
await writeFile(join(outputDir, "m01-after-request-changes-desktop.png"), Buffer.from(changedShot.result.data, "base64"));
await cdp("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
await cdp("Page.navigate", { url: `${origin}/m02-organization-management` });
await delay(600);
interaction.narrowLogoutTarget = await evaluate(`(() => { const x=document.querySelector('.mg-logout-btn'); const r=x.getBoundingClientRect(); return {text:x.innerText.trim(),ariaLabel:x.getAttribute('aria-label'),width:Math.round(r.width),height:Math.round(r.height),insideViewport:r.left>=0&&r.right<=innerWidth}; })()`);
await cdp("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
await cdp("Page.navigate", { url: `${origin}/m02-organization-management` });
await delay(600);
await evaluate("document.querySelector('.mg-logout-btn')?.focus()");
await key("Enter", "Enter", 13);
interaction.afterKeyboardLogout = await evaluate(`({route:location.pathname,role:sessionStorage.getItem('s2l-web-role'),authenticated:sessionStorage.getItem('s2l-web-authenticated'),loginHeading:[...document.querySelectorAll('h1')].map(x=>x.innerText)})`);
await writeFile(join(outputDir, "interaction-observations.json"), JSON.stringify(interaction, null, 2), "utf8");
console.log(JSON.stringify(interaction, null, 2));
socket.close();
