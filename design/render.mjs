// Render README, social, and demo assets from design/build (run `python design/compose.py` first).
// Needs Chrome or Edge, ffmpeg on PATH, and `npm install --prefix design` for playwright-core.
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createRequire } from "node:module";

// CommonJS resolution so NODE_PATH or design/node_modules can supply playwright-core.
const { chromium } = createRequire(import.meta.url)("playwright-core");

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const build = path.join(root, "design", "build");
const out = path.join(root, "docs", "brand");
const frames = path.join(build, "frames");
fs.mkdirSync(out, { recursive: true });
fs.rmSync(frames, { recursive: true, force: true });
fs.mkdirSync(frames, { recursive: true });

const executablePath = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
  "/usr/bin/google-chrome", "/usr/bin/chromium"
].find((candidate) => fs.existsSync(candidate));
const browser = await chromium.launch({ executablePath });
const url = (file) => pathToFileURL(file).href;

async function open(file, { width, height, scheme = "light", scale = 1 }) {
  const page = await browser.newPage({ viewport: { width, height }, colorScheme: scheme, deviceScaleFactor: scale });
  await page.goto(url(file), { waitUntil: "load" });
  await page.evaluate(() => document.fonts.ready);
  return page;
}

// 1. Captures of the committed status page for the annotated views, taken at the width they are shown.
const status = path.join(root, "index.html");
let page = await open(status, { width: 390, height: 844, scale: 2 });
await page.screenshot({ path: path.join(build, "cap-mobile.png") });
await page.close();
page = await open(status, { width: 760, height: 1000, scale: 2 });
await page.locator(".job-recovered").screenshot({ path: path.join(build, "cap-trail.png") });
await page.locator("#v2-proof").screenshot({ path: path.join(build, "cap-v2.png") });
await page.close();

// 2. Hero (light and dark), social preview, annotated views.
for (const scheme of ["light", "dark"]) {
  page = await open(path.join(build, "hero.html"), { width: 1280, height: 690, scheme, scale: 1.5 });
  await page.screenshot({ path: path.join(out, `hero-${scheme}.png`) });
  await page.close();
}
page = await open(path.join(build, "social.html"), { width: 1280, height: 640, scheme: "dark" });
await page.screenshot({ path: path.join(out, "social-preview.png") });
await page.close();
for (const name of ["view-mobile", "view-trail", "view-v2"]) {
  page = await open(path.join(build, `${name}.html`), { width: 1240, height: 600, scale: 1.5 });
  await page.locator(".canvas").screenshot({ path: path.join(out, `${name}.png`) });
  await page.close();
}

// 3. Replay frames: one still per recorded event, held long enough to read.
page = await open(path.join(build, "replay.html"), { width: 1280, height: 720 });
const count = await page.evaluate(() => window.stepCount);
const list = [];
for (let index = 0; index < count; index += 1) {
  await page.evaluate((step) => window.showStep(step), index);
  const file = path.join(frames, `f${String(index).padStart(2, "0")}.png`);
  await page.screenshot({ path: file });
  list.push(`file '${path.basename(file)}'`, `duration ${index === count - 1 ? 3.2 : 1.9}`);
}
list.push(`file 'f${String(count - 1).padStart(2, "0")}.png'`);
fs.copyFileSync(path.join(frames, `f${String(count - 1).padStart(2, "0")}.png`), path.join(out, "replay-poster.png"));
await page.close();
await browser.close();

const concat = path.join(frames, "list.txt");
fs.writeFileSync(concat, `${list.join("\n")}\n`);
const ffmpeg = (args) => execFileSync("ffmpeg", ["-y", "-loglevel", "error", ...args], { stdio: "inherit" });
ffmpeg(["-f", "concat", "-safe", "0", "-i", concat, "-vf",
  "fps=8,scale=960:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=48:stats_mode=full[p];[b][p]paletteuse=dither=none",
  "-loop", "0", path.join(out, "replay.gif")]);
ffmpeg(["-f", "concat", "-safe", "0", "-i", concat, "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "20",
  "-movflags", "+faststart", "-an", path.join(out, "replay.mp4")]);

for (const file of fs.readdirSync(out).sort()) {
  console.log(`${file} ${(fs.statSync(path.join(out, file)).size / 1024).toFixed(0)}KB`);
}
console.log(`RENDER_OK frames=${count}`);
