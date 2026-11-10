import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const origin = "http://127.0.0.1:5173";
const evidenceDir = dirname(fileURLToPath(import.meta.url));
const capturePhase = process.env.S2L_CAPTURE_PHASE ?? "after";
const outputDir = process.env.S2L_SCREENSHOT_DIR ?? join(evidenceDir, "screenshots", capturePhase);
const targets = await fetch("http://127.0.0.1:9233/json/list").then((response) => response.json());
const page = targets.find((target) => target.type === "page" && target.url.startsWith(origin));
if (!page?.webSocketDebuggerUrl) throw new Error("Headless local browser page is not available.");

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
  const callbacks = pending.get(message.id);
  if (!callbacks) return;
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
        reject(new Error(`Timed out waiting for ${method}`));
      }
    }, 10000);
  });
}

await mkdir(outputDir, { recursive: true });
await cdp("Page.enable");
await cdp("Runtime.enable");
await cdp("Network.enable");
await cdp("Network.setBlockedURLs", {
  urls: ["https://*", "http://localhost:8000/*", "http://127.0.0.1:8000/*"],
});
await cdp("Runtime.evaluate", { expression: "sessionStorage.clear()" });

const evidence = [];
for (const viewport of [
  { label: "desktop", width: 1440, height: 900, mobile: false },
  { label: "narrow", width: 390, height: 844, mobile: true },
]) {
  await cdp("Emulation.setDeviceMetricsOverride", {
    width: viewport.width,
    height: viewport.height,
    deviceScaleFactor: 1,
    mobile: viewport.mobile,
  });
  await cdp("Page.navigate", { url: `${origin}/login` });
  await new Promise((resolve) => setTimeout(resolve, 700));
  const inspection = await cdp("Runtime.evaluate", {
    expression: `({title:document.title, route:location.pathname+location.search, viewportWidth:innerWidth, documentWidth:document.documentElement.scrollWidth, documentHeight:document.documentElement.scrollHeight, horizontalOverflow:document.documentElement.scrollWidth>innerWidth, heading:[...document.querySelectorAll('h1,h2')].map(x=>x.innerText).slice(0,8), inputLabels:[...document.querySelectorAll('input')].map(x=>({type:x.type,autocomplete:x.autocomplete,required:x.required})), text:document.body.innerText.slice(0,500)})`,
    returnByValue: true,
  });
  const details = inspection.result?.result?.value ?? null;
  const shot = await cdp("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: false,
  });
  const fileName = `school-manager-login-${viewport.label}.png`;
  await writeFile(join(outputDir, fileName), Buffer.from(shot.result.data, "base64"));
  evidence.push({ file: fileName, ...details });
}

await cdp("Runtime.evaluate", {
  expression: "sessionStorage.setItem('s2l-web-role','MANAGER'); sessionStorage.setItem('s2l-web-authenticated','true')",
});

const captures = [
  { name: "m02-dashboard", route: "/m02-organization-management", desktop: true, narrow: true },
  { name: "m02-teachers", route: "/m02-organization-management?section=teachers", desktop: true, narrow: true },
  { name: "m02-classes", route: "/m02-organization-management?section=classes", desktop: true, narrow: true },
  { name: "m02-quota", route: "/m02-organization-management?section=quota", desktop: true, narrow: true },
  { name: "m02-settings", route: "/m02-organization-management?section=settings", desktop: true, narrow: true },
  { name: "m01-publication-review", route: "/m01-publication-review", desktop: true, narrow: true },
];

for (const capture of captures) {
  for (const viewport of [
    ...(capture.desktop ? [{ label: "desktop", width: 1440, height: 900, mobile: false }] : []),
    ...(capture.narrow ? [{ label: "narrow", width: 390, height: 844, mobile: true }] : []),
  ]) {
    await cdp("Emulation.setDeviceMetricsOverride", {
      width: viewport.width,
      height: viewport.height,
      deviceScaleFactor: 1,
      mobile: viewport.mobile,
    });
    await cdp("Page.navigate", { url: `${origin}${capture.route}` });
    await new Promise((resolve) => setTimeout(resolve, 700));

    const inspection = await cdp("Runtime.evaluate", {
      expression: `({title:document.title, route:location.pathname+location.search, viewportWidth:innerWidth, documentWidth:document.documentElement.scrollWidth, documentHeight:document.documentElement.scrollHeight, horizontalOverflow:document.documentElement.scrollWidth>innerWidth, heading:[...document.querySelectorAll('h1,h2')].map(x=>x.innerText).slice(0,8), buttonCount:document.querySelectorAll('button').length, unnamedButtons:[...document.querySelectorAll('button')].filter(x=>!(x.innerText.trim()||x.getAttribute('aria-label'))).length, tabs:[...document.querySelectorAll('[role=tab]')].map(x=>({id:x.id,controls:x.getAttribute('aria-controls'),selected:x.getAttribute('aria-selected'),tabIndex:x.tabIndex})), panels:[...document.querySelectorAll('[role=tabpanel]')].map(x=>({id:x.id,labelledby:x.getAttribute('aria-labelledby'),hidden:x.hidden,tabIndex:x.tabIndex})), inboxStatus:document.querySelector('.mg-inbox-unavailable')?.innerText, scrollRegions:[...document.querySelectorAll('.mg-table-wrap')].map(x=>({clientWidth:x.clientWidth,scrollWidth:x.scrollWidth,overflowX:getComputedStyle(x).overflowX,scrollable:x.scrollWidth>x.clientWidth})), unavailableActions:[...document.querySelectorAll('button')].filter(x=>/Tạo lớp|Thêm suất|Mua lượt/.test(x.innerText)).map(x=>({text:x.innerText.trim(),disabled:x.disabled,left:Math.round(x.getBoundingClientRect().left),right:Math.round(x.getBoundingClientRect().right),insideViewport:x.getBoundingClientRect().left>=0&&x.getBoundingClientRect().right<=innerWidth})), organizationContextTag:document.querySelector('.mg-org-context')?.tagName, text:document.body.innerText.slice(0,500)})`,
      returnByValue: true,
    });
    const details = inspection.result?.result?.value ?? null;

    const shot = await cdp("Page.captureScreenshot", {
      format: "png",
      fromSurface: true,
      captureBeyondViewport: false,
    });
    const fileName = `${capture.name}-${viewport.label}.png`;
    await writeFile(join(outputDir, fileName), Buffer.from(shot.result.data, "base64"));
    evidence.push({ file: fileName, ...details });
  }
}

await cdp("Emulation.setDeviceMetricsOverride", {
  width: 1440,
  height: 900,
  deviceScaleFactor: 1,
  mobile: false,
});
await cdp("Page.navigate", { url: `${origin}/m01-publication-review` });
await new Promise((resolve) => setTimeout(resolve, 700));
await cdp("Runtime.evaluate", {
  expression: "document.querySelector('[role=tab]')?.focus()",
});
const keyboardBefore = await cdp("Runtime.evaluate", {
  expression: `({activeId:document.activeElement?.id, selected:document.activeElement?.getAttribute('aria-selected')})`,
  returnByValue: true,
});
await cdp("Input.dispatchKeyEvent", { type: "keyDown", key: "ArrowRight", code: "ArrowRight", windowsVirtualKeyCode: 39 });
await cdp("Input.dispatchKeyEvent", { type: "keyUp", key: "ArrowRight", code: "ArrowRight", windowsVirtualKeyCode: 39 });
const keyboardAfter = await cdp("Runtime.evaluate", {
  expression: `({activeId:document.activeElement?.id, selected:document.activeElement?.getAttribute('aria-selected'), selectedPanelHidden:document.getElementById(document.querySelector('[role=tab][aria-selected=true]')?.getAttribute('aria-controls'))?.hidden, tabs:[...document.querySelectorAll('[role=tab]')].map(x=>({id:x.id,selected:x.getAttribute('aria-selected'),tabIndex:x.tabIndex}))})`,
  returnByValue: true,
});
evidence.push({ keyboardArrowRight: { before: keyboardBefore.result?.result?.value, after: keyboardAfter.result?.result?.value } });
await cdp("Runtime.evaluate", { expression: "document.querySelector('[role=tab]')?.click()" });
await cdp("Runtime.evaluate", {
  expression: `(() => { const field = document.querySelector('textarea'); const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set; setter.call(field, 'Vui lòng chỉnh sửa trước khi công khai.'); field.dispatchEvent(new Event('input', { bubbles: true })); })()`,
});
await cdp("Runtime.evaluate", {
  expression: `[...document.querySelectorAll('button')].find((button) => button.innerText.includes('Yêu cầu chỉnh sửa'))?.click()`,
});
await new Promise((resolve) => setTimeout(resolve, 250));
const rejectionState = await cdp("Runtime.evaluate", {
  expression: `({route:location.pathname+location.search, heading:[...document.querySelectorAll('h1,h2')].map(x=>x.innerText).slice(0,8), text:document.body.innerText.slice(0,600)})`,
  returnByValue: true,
});
const rejectionShot = await cdp("Page.captureScreenshot", {
  format: "png",
  fromSurface: true,
  captureBeyondViewport: false,
});
const rejectionFile = "m01-after-request-changes-desktop.png";
await writeFile(join(outputDir, rejectionFile), Buffer.from(rejectionShot.result.data, "base64"));
evidence.push({ file: rejectionFile, ...rejectionState.result?.result?.value });

const serializedEvidence = JSON.stringify(evidence, null, 2);
await writeFile(join(outputDir, "capture-observations.json"), serializedEvidence, "utf8");
console.log(serializedEvidence);
await cdp("Browser.close").catch(() => undefined);
