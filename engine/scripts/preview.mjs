// vucut · xem thử / render độc lập (khi không có bộ script của seecut, hoặc để soát nhanh).
// Dùng:
//   node preview.mjs <build_dir> <person_frames_dir> <fps> probe 0.5,3.2,8.0 [out_dir]   → chụp vài khung PNG
//   node preview.mjs <build_dir> <person_frames_dir> <fps> full [out_dir] [scale]         → chụp mọi khung (ghép bằng ffmpeg)
// person_frames_dir: khung hình người nói đã tách sẵn: ffmpeg -i goc.mp4 -vf fps=30,scale=720:1280 frames/%05d.jpg
// build_dir chứa master.html + lib/ (vucut.css, vucut.js, gsap.min.js, fonts/) + img/.
import { createRequire } from 'module';
import fs from 'fs'; import path from 'path'; import os from 'os'; import { pathToFileURL } from 'url';
import { execSync } from 'child_process';
// Tìm playwright theo thứ tự: ~/.vucut/node (setup tự cài) → cạnh script → thư mục đang đứng → NODE_PATH → npm root -g.
function loadPlaywright() {
  const bases = [path.join(os.homedir(), '.vucut', 'node') + '/', import.meta.url, process.cwd() + '/'];
  for (const d of (process.env.NODE_PATH || '').split(path.delimiter).filter(Boolean)) bases.push(path.dirname(d) + '/');
  try { bases.push(path.dirname(execSync('npm root -g', { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim()) + '/'); } catch {}
  for (const b of bases) { try { return createRequire(b)('playwright'); } catch {} }
  console.error('❌ Không tìm thấy playwright → chạy: python vucut.py setup'); process.exit(2);
}
const { chromium } = loadPlaywright();
if (process.argv[2] === '--check') {   // vucut.py setup gọi: thử mở Chromium thật
  try { const b = await chromium.launch(); await b.close(); console.log('ok'); process.exit(0); }
  catch (e) { console.error(String(e).split('\n')[0]); process.exit(3); }
}
const [build, framesDir, fpsS, mode, arg5, arg6, arg7, arg8] = process.argv.slice(2);   // full: arg7/arg8 = khung đầu/cuối (render song song)
const fps = +fpsS || 30;
const html = path.resolve(build, 'master.html');
const out = path.resolve(mode === 'probe' ? (arg6 || path.join(build, '..', 'qc')) : (arg5 || path.join(build, '..', 'frames_out')));
const scale = mode === 'full' ? (+arg6 || 1) : 1;
fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 720, height: 1280 }, deviceScaleFactor: scale });
await page.goto(pathToFileURL(html).href);
await page.evaluate(() => document.fonts.ready);
const dur = await page.evaluate(() => Math.min(window.__timelines.master.duration(), +document.getElementById('root').dataset.duration || 1e9));
const nFrames = fs.readdirSync(framesDir).length;
const frameFile = t => { const n = Math.min(Math.round(t * fps) + 1, nFrames); return pathToFileURL(path.resolve(framesDir, String(n).padStart(5, '0') + '.jpg')).href; };
const total = Math.floor(dur * fps);
// lớp tách nền cho cảnh chia đôi (matte_split.py → build/cut/NNNNN.png): có file thì nạp vào #personCut
const cutDir = path.resolve(build, 'cut');
const cutFile = t => { const n = Math.min(Math.round(t * fps) + 1, nFrames); const f = path.resolve(cutDir, String(n).padStart(5, '0') + '.png'); return fs.existsSync(f) ? pathToFileURL(f).href : null; };
const i0 = mode === 'full' ? (+arg7 || 0) : 0, i1 = mode === 'full' ? (arg8 ? +arg8 : total) : 0;
const idx = mode === 'probe' ? arg5.split(',').map(Number) : Array.from({ length: i1 - i0 }, (_, k) => i0 + k);
for (let k = 0; k < idx.length; k++) {
  const t = mode === 'probe' ? idx[k] : idx[k] / fps;
  await page.evaluate(async ([src, t, cut]) => {
    const im = document.getElementById('person');
    if (im.src !== src) { im.src = src; await im.decode().catch(() => {}); }
    const pi = document.getElementById('pipImg');   // khung người nói nhỏ: cùng khung hình với #person
    if (pi && pi.src !== src) { pi.src = src; await pi.decode().catch(() => {}); }
    const pc = document.getElementById('personCut');
    if (pc && cut) { if (pc.src !== cut) { pc.src = cut; await pc.decode().catch(() => {}); } pc.style.visibility = 'visible'; }
    else if (pc) pc.style.visibility = 'hidden';
    window.__timelines.master.seek(t, false);
    for (const el of document.querySelectorAll('img[data-seq]')) {   // vucut-tools: chuỗi khung dựng sẵn (bản đồ 3D)
      const src = el.dataset.seq.replace('%04d', String(+el.dataset.f || 0).padStart(4, '0'));
      if (el.getAttribute('src') !== src) { el.setAttribute('src', src); await el.decode().catch(() => {}); } }
  }, [frameFile(t), t, cutFile(t)]);
  if (mode === 'probe') {   // soát chữ: tràn mép / từ to bị xuống dòng
    const w = await page.evaluate(() => { const o = [];
      document.querySelectorAll('.mix, .hook, .stack, .ptitle').forEach(el => { const cs = getComputedStyle(el);
        if (+cs.opacity < .5 || cs.visibility === 'hidden' || cs.display === 'none') return; let r = el.getBoundingClientRect(); const kids = el.querySelectorAll('span');
        if (kids.length) { let L = 1e9, R = -1e9; kids.forEach(k => { const q = k.getBoundingClientRect(); if (q.width && +getComputedStyle(k).opacity > .3) { L = Math.min(L, q.left); R = Math.max(R, q.right); } }); r = { left: L, right: R, width: R - L }; }
        if (!(r.width > 0)) return;
        if (r.right > 712 || r.left < 8) o.push('#' + el.id + ' tràn mép');
        el.querySelectorAll('.s').forEach(s => { const fs = parseFloat(getComputedStyle(s).fontSize) || 80;
          if (s.getClientRects().length > 1 || s.getBoundingClientRect().height > fs * 1.6) o.push('#' + el.id + ' từ to xuống dòng: "' + s.textContent + '"'); }); });
      return o; });
    if (w.length) console.log(`⚠ t=${t.toFixed(2)}: ` + w.join(' · '));
  }
  const name = mode === 'probe' ? `t_${t.toFixed(2)}.png` : `${String(idx[k] + 1).padStart(5, '0')}.png`;
  await page.screenshot({ path: path.join(out, name), type: 'png' });
  if (mode === 'full' && k % 150 === 0) console.log(`${idx[k]}/${total}`);
}
await browser.close();
console.log('xong →', out, `(${idx.length} khung, dài ${dur.toFixed(2)} s)`);
