import {readFile, writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const packageDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const distDir = path.join(packageDir, 'dist');
const indexPath = path.join(distDir, 'index.html');
const html = await readFile(indexPath, 'utf8');

const scriptMatch = html.match(/<script\b(?=[^>]*\btype="module")(?=[^>]*\bsrc="([^"]+)")[^>]*><\/script>/i);
const styleMatch = html.match(/<link\b(?=[^>]*\brel="stylesheet")(?=[^>]*\bhref="([^"]+)")[^>]*>/i);

if (!scriptMatch || !styleMatch) {
  throw new Error('Expected exactly one Vite JavaScript bundle and stylesheet reference in dist/index.html.');
}

const scriptPath = path.resolve(distDir, decodeURIComponent(scriptMatch[1].replace(/^\.\//, '')));
const stylePath = path.resolve(distDir, decodeURIComponent(styleMatch[1].replace(/^\.\//, '')));
const [script, styles] = await Promise.all([
  readFile(scriptPath, 'utf8'),
  readFile(stylePath, 'utf8'),
]);

const inlineScript = `<script type="module">\n${script.replace(/<\/script/gi, '<\\/script')}\n</script>`;
const inlineStyles = `<style>\n${styles.replace(/<\/style/gi, '<\\/style')}\n</style>`;
const bundledHtml = html
  .replace(scriptMatch[0], () => inlineScript)
  .replace(styleMatch[0], () => inlineStyles);

const documentMarkup = bundledHtml
  .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, '')
  .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, '');
if (/<script\b[^>]*\bsrc=|<link\b[^>]*\bhref=/i.test(documentMarkup)) {
  throw new Error('Parent Android HTML still contains a relative asset request.');
}

const outputPath = path.join(distDir, 'parent-ui-webview.html');
await writeFile(outputPath, bundledHtml, 'utf8');
console.log(`Created self-contained Android WebView document: ${path.relative(packageDir, outputPath)} (${Buffer.byteLength(bundledHtml)} bytes)`);
