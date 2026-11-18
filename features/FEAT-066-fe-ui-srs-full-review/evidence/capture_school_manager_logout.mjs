import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const origin = "http://127.0.0.1:5173";
const evidenceDir = dirname(fileURLToPath(import.meta.url));
const outputDir = join(evidenceDir, "screenshots", "logout-check");
const targets = await fetch("http://127.0.0.1:9233/json/list").then((response) => response.json());
const page = targets.find((target) => target.type === "page");
if (!page?.webSocketDebuggerUrl) throw new Error("Local headless browser page is not available.");
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
  clearTimeout(callbacks.timeout);
  if (message.error) callbacks.reject(new Error(message.error.message));
  else callbacks.resolve(message);
});
function cdp(method, params = {}) {
  const id = ++nextId;
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      pending.delete(id);
      reject(new Error(`Timed out waiting for ${method}`));
    }, 10000);
    pending.set(id, { resolve, reject, timeout });
    socket.send(JSON.stringify({ id, method, params }));
  });
}
async function evaluate(expression) {
  const response = await cdp("Runtime.evaluate", { expression, returnByValue: true });
  if (response.result.exceptionDetails) throw new Error(response.result.exceptionDetails.text);
  return response.result.result.value;
}
async function navigate(url) {
  await cdp("Page.navigate", { url });
  await new Promise((resolve) => setTimeout(resolve, 700));
}
async function screenshot(name) {
  const result = await cdp("Page.captureScreenshot", { format: "png", fromSurface: true, captureBeyondViewport: false });
  await writeFile(join(outputDir, name), Buffer.from(result.result.data, "base64"));
}
await mkdir(outputDir, { recursive: true });
await cdp("Page.enable");
await cdp("Runtime.enable");
await cdp("Network.enable");
await cdp("Network.setBlockedURLs", { urls: ["https://*", "http://localhost:8000/*", "http://127.0.0.1:8000/*"] });
const observations = [];
const cases = [
  { route: "/m02-organization-management", label: "dashboard" },
  { route: "/m02-organization-management?section=settings", label: "settings" },
];
for (const viewport of [
  { label: "desktop", width: 1440, height: 900, mobile: false },
  { label: "narrow", width: 390, height: 844, mobile: true },
]) {
  await cdp("Emulation.setDeviceMetricsOverride", { width: viewport.width, height: viewport.height, deviceScaleFactor: 1, mobile: viewport.mobile });
  for (const pageCase of cases) {
    await navigate(`${origin}/login`);
    await evaluate("sessionStorage.clear(); sessionStorage.setItem('s2l-web-role','MANAGER'); sessionStorage.setItem('s2l-web-authenticated','true')");
    await navigate(`${origin}${pageCase.route}`);
    const before = await evaluate(`(() => {
      const button = document.querySelector('button[aria-label="Đăng xuất"]');
      const bounds = button?.getBoundingClientRect();
      return {
        route: location.pathname + location.search,
        viewportWidth: innerWidth,
        documentWidth: document.documentElement.scrollWidth,
        horizontalOverflow: document.documentElement.scrollWidth > innerWidth,
        logoutButton: button ? {
          tag: button.tagName,
          role: button.getAttribute('role') || 'native button',
          accessibleName: button.getAttribute('aria-label'),
          text: button.innerText.trim(),
          tabIndex: button.tabIndex,
          visible: getComputedStyle(button).display !== 'none' && bounds.width > 0 && bounds.height > 0,
          width: Math.round(bounds.width),
          height: Math.round(bounds.height),
          insideViewport: bounds.left >= 0 && bounds.right <= innerWidth && bounds.top >= 0 && bounds.bottom <= innerHeight,
          left: Math.round(bounds.left), top: Math.round(bounds.top),
        } : null,
      };
    })()`);
    const beforeName = `logout-${pageCase.label}-${viewport.label}-before.png`;
    await screenshot(beforeName);
    const focus = await evaluate(`(() => { const button = document.querySelector('button[aria-label="Đăng xuất"]'); button?.focus(); return { focused: document.activeElement === button, activeTag: document.activeElement?.tagName, activeName: document.activeElement?.getAttribute('aria-label') }; })()`);
    await cdp("Input.dispatchKeyEvent", { type: "rawKeyDown", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13, nativeVirtualKeyCode: 13 });
    await cdp("Input.dispatchKeyEvent", { type: "char", key: "Enter", code: "Enter", text: "\r", unmodifiedText: "\r", windowsVirtualKeyCode: 13, nativeVirtualKeyCode: 13 });
    await cdp("Input.dispatchKeyEvent", { type: "keyUp", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13, nativeVirtualKeyCode: 13 });
    await new Promise((resolve) => setTimeout(resolve, 500));
    let after = await evaluate(`({ route: location.pathname + location.search, roleKey: sessionStorage.getItem('s2l-web-role'), authenticatedKey: sessionStorage.getItem('s2l-web-authenticated'), logoutButtonPresent: Boolean(document.querySelector('button[aria-label="Đăng xuất"]')) })`);
    let activationMethod = "keyboard-enter";
    if (after.route !== "/login" || after.roleKey !== null || after.authenticatedKey !== null) {
      const point = await evaluate(`(() => { const r = document.querySelector('button[aria-label="Đăng xuất"]').getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; })()`);
      await cdp("Input.dispatchMouseEvent", { type: "mouseMoved", x: point.x, y: point.y });
      await cdp("Input.dispatchMouseEvent", { type: "mousePressed", x: point.x, y: point.y, button: "left", clickCount: 1 });
      await cdp("Input.dispatchMouseEvent", { type: "mouseReleased", x: point.x, y: point.y, button: "left", clickCount: 1 });
      activationMethod = "pointer-click";
      await new Promise((resolve) => setTimeout(resolve, 700));
      after = await evaluate(`({ route: location.pathname + location.search, roleKey: sessionStorage.getItem('s2l-web-role'), authenticatedKey: sessionStorage.getItem('s2l-web-authenticated'), loginVisible: /Đăng nhập|Đăng ký|Chào mừng/.test(document.body.innerText), logoutButtonPresent: Boolean(document.querySelector('button[aria-label="Đăng xuất"]')) })`);
    } else {
      after = await evaluate(`({ route: location.pathname + location.search, roleKey: sessionStorage.getItem('s2l-web-role'), authenticatedKey: sessionStorage.getItem('s2l-web-authenticated'), loginVisible: /Đăng nhập|Đăng ký|Chào mừng/.test(document.body.innerText), logoutButtonPresent: Boolean(document.querySelector('button[aria-label="Đăng xuất"]')) })`);
    }
    const logoutResult = after;
    await navigate(`${origin}${pageCase.route}`);
    const protectedRouteAfterLogout = await evaluate(`({ route: location.pathname + location.search, roleKey: sessionStorage.getItem('s2l-web-role'), authenticatedKey: sessionStorage.getItem('s2l-web-authenticated'), loginVisible: /Đăng nhập|Đăng ký|Chào mừng/.test(document.body.innerText), logoutButtonPresent: Boolean(document.querySelector('button[aria-label="Đăng xuất"]')) })`);
    const afterName = `logout-${pageCase.label}-${viewport.label}-after.png`;
    await screenshot(afterName);
    observations.push({ page: pageCase.label, viewport: viewport.label, before: { screenshot: beforeName, ...before }, keyboardFocus: focus, activationMethod, after: { screenshot: afterName, logoutSucceeded: logoutResult.route === "/login" && logoutResult.roleKey === null && logoutResult.authenticatedKey === null && !logoutResult.logoutButtonPresent, ...logoutResult }, protectedRouteAfterLogout });
  }
}
await writeFile(join(outputDir, "observations.json"), JSON.stringify({ origin, browser: "Microsoft Edge headless, CDP bound to 127.0.0.1:9233", externalHttpsBlocked: true, backendLocalhostBlocked: true, observations }, null, 2), "utf8");
console.log(JSON.stringify(observations, null, 2));
socket.close();
