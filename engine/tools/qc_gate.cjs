// vucut-tools v6 · CỔNG KIỂM TRA + TỰ CĂN VÙNG AN TOÀN: node ~/.vucut/tools/qc_gate.cjs <DA>  → in ⚠ từng lỗi, thoát 1 nếu còn lỗi.
// B1 TỰ CĂN: đo chữ của MỌI hình [data-mg] suốt thời gian hiện → dời/thu tối thiểu cho vào vùng an toàn → ghi <style id="vc-safe"> vào build/master.html
// B2 KIỂM: lỗi JS + timeline · chữ DÍNH qua mốc cắt · chữ ngoài VÙNG AN TOÀN TikTok/Reels (x 40–680 · y 120–1000 · y > 560 thì x ≤ 630) · chữ phụ đề CHỒNG chữ đồ hoạ
// Chạy lại build.py là mất phần tự căn → luôn chạy cổng SAU build, TRƯỚC probe/render.
const fs = require('fs'), path = require('path'), os = require('os'), { pathToFileURL } = require('url');
let pw; try { pw = require(path.join(os.homedir(), '.vucut', 'node', 'node_modules', 'playwright')); } catch { pw = require('playwright'); }
const { chromium } = pw;
const S = { top: 120, bottom: 1000, left: 40, right: 680, rx: 630, ry: 560 };
const P = { l: 446, t: 700, r: 626, b: 895 };   // khung người nói nhỏ (#pip) — chữ không được nằm dưới khung
const DA = process.argv[2], HTML = path.join(DA, 'build', 'master.html');
const src = fs.readFileSync(path.join(DA, 'build.py'), 'utf8');
const cuts = new Set();
for (const m of src.matchAll(/V\.L_(?:person|full|split|card)\(\s*([\d.]+)\s*,\s*([\d.]+)/g)) { cuts.add(+m[1]); cuts.add(+m[2]); }
let T = +(src.match(/V\.init\(T=([\d.]+)/) || [0, 0])[1];
const STEP = .25;
const SNAP = () => {   // mọi chữ đang hiện → {own: id hình | 'mix:id', r:[l,t,r,b]} (bỏ ký tự trang trí 1 ký tự: “ ” ✕ …)
  const on = el => { let e = el; while (e && e.nodeType === 1) { const c = getComputedStyle(e); if (c.display === 'none' || c.visibility === 'hidden' || +c.opacity < .3) return false; e = e.parentElement; } return true; };
  const out = []; const tw = document.createTreeWalker(document.getElementById('root') || document.body, NodeFilter.SHOW_TEXT);
  for (let n = tw.nextNode(); n; n = tw.nextNode()) {
    const tx = n.textContent.trim(), el = n.parentElement;
    if (!tx || !el || el.closest('script,style') || (tx.length === 1 && !/[0-9A-Za-zÀ-ỹ]/.test(tx)) || !on(el)) continue;
    const rg = document.createRange(); rg.selectNodeContents(n); const q = rg.getBoundingClientRect(); if (!q.width) continue;
    const g = el.closest('[data-mg]'), m = el.closest('.mix,.hook');
    out.push({ own: m ? 'mix:' + m.id : g ? g.id : '', mg: g ? g.getAttribute('data-mg') : '', tx: tx.slice(0, 30), r: [q.left, q.top, q.right, q.bottom] });
  }
  const pp = document.getElementById('pip');
  if (pp && on(pp)) out.push({ own: '#pip', mg: '', tx: '', r: [446, 700, 626, 895] });
  return out;
};
function fit(R, pip) {   // khung chữ của 1 hình → {s, dx, dy, oy} nhỏ nhất đưa hết vào vùng an toàn (hình nửa trên SPLIT: chỉ thu, không dời xuống)
  const half = Math.max(...R.map(r => r[3])) <= 612, ox = 360, oy = half ? 600 : 400;
  for (let s = 1; s >= .7; s -= .02) {
    const Q = R.map(r => [ox + (r[0] - ox) * s, oy + (r[1] - oy) * s, ox + (r[2] - ox) * s, oy + (r[3] - oy) * s]);
    const lo = S.top - Math.min(...Q.map(q => q[1])), hi = S.bottom - Math.max(...Q.map(q => q[3]));
    if (lo > hi + .5 || (half && lo > .5)) continue;
    const dy = lo > 0 ? lo : (hi < 0 ? hi : 0);
    const xl = S.left - Math.min(...Q.map(q => q[0]));
    const xh = Math.min(...Q.map(q => (pip && q[3] + dy > P.t - 8 && q[1] + dy < P.b + 8 ? P.l - 8 : q[3] + dy > S.ry ? S.rx : S.right) - q[2]));
    if (xl > xh + .5) continue;
    const dx = xl > 0 ? xl : (xh < 0 ? xh : 0);
    if (Math.abs(dx) < .5 && Math.abs(dy) < .5 && s > .999) return null;
    return { s: +s.toFixed(2), dx: Math.round(dx), dy: Math.round(dy), oy };
  }
  return { s: .7, dx: 0, dy: 0, oy, fail: true };
}
(async () => {
  const br = await chromium.launch(); const pg = await br.newPage({ viewport: { width: 720, height: 1280 } });
  const errs = []; pg.on('pageerror', e => errs.push(String(e).split('\n')[0]));
  let html = fs.readFileSync(HTML, 'utf8').replace(/<style id="vc-safe">[\s\S]*?<\/style>/, '');
  fs.writeFileSync(HTML, html);
  await pg.goto(pathToFileURL(HTML).href); await pg.waitForTimeout(800);
  const bad = [];
  const dur = await pg.evaluate(() => window.__timelines ? window.__timelines.master.duration() : 0);
  if (!T) T = dur;
  if (dur < T - 0.2) bad.push(`TIMELINE chỉ ${dur.toFixed(2)} s < ${T} s (lỗi JS làm mất cảnh sau)`);
  const snapAt = t => pg.evaluate(([t, f]) => { window.__timelines.master.seek(t, false); return eval('(' + f + ')')(); }, [t, SNAP.toString()]);
  // ---- B1 tự căn
  const per = {}, pipOn = {};
  for (let t = .1; t < T; t += STEP) { const O = await snapAt(t), hasPip = O.some(o => o.own === '#pip');
    for (const o of O) if (o.own && o.own !== '#pip' && !o.own.startsWith('mix:') && o.mg !== 'disclaimer') { (per[o.own] = per[o.own] || []).push(o.r); if (hasPip) pipOn[o.own] = 1; } }
  const css = [], moved = [];
  for (const [id, R] of Object.entries(per)) {
    const f = fit(R, pipOn[id]); if (!f) continue;
    css.push(`#${id}{translate:${f.dx}px ${f.dy}px!important;scale:${f.s}!important;transform-origin:360px ${f.oy}px!important}`);
    moved.push(`${id}${f.s < 1 ? ' ×' + f.s : ''}${f.dy ? ' ↕' + f.dy : ''}${f.dx ? ' ↔' + f.dx : ''}${f.fail ? ' ⚠ thu tối đa vẫn chưa vừa' : ''}`);
  }
  if (css.length) {
    html = html.replace('</head>', `<style id="vc-safe">${css.join('')}</style></head>`); fs.writeFileSync(HTML, html);
    await pg.goto(pathToFileURL(HTML).href); await pg.waitForTimeout(800);
    console.log('TỰ CĂN VÙNG AN TOÀN:', moved.join(' · '));
    const tiny = moved.filter(x => +((x.match(/×([\d.]+)/) || [0, 1])[1]) < .85); if (tiny.length) console.log('  ⚠ hình bị thu nhiều (< ×0.85):', tiny.join(' · '), '→ bỏ title= của hình / bớt chữ / dùng cảnh toàn khung thay SPLIT');
  }
  errs.forEach(e => bad.push('LỖI JS: ' + e));
  // ---- B2 kiểm
  const vis = t => pg.evaluate(t => {
    window.__timelines.master.seek(t, false);
    const on = el => { let e = el; while (e && e.nodeType === 1) { const c = getComputedStyle(e); if (c.display === 'none' || c.visibility === 'hidden' || +c.opacity < .06) return false; e = e.parentElement; } return true; };
    return [...document.querySelectorAll('.mix, .hook')].filter(on).map(e => e.id);
  }, t);
  const B = [...cuts].filter(t => t > 0.01 && t < T - 0.05).sort((a, b) => a - b);
  for (const b of B) {
    const before = await vis(b - 0.1), after = await vis(b + 0.04);
    const stuck = before.filter(id => after.includes(id));
    if (stuck.length) bad.push(`CHỮ DÍNH qua mốc ${b.toFixed(2)} s: #${stuck.join(', #')}`);
  }
  const seen = new Set();
  for (let t = .1; t < T; t += STEP) {
    const O = await snapAt(t);
    const hasPip = O.some(o => o.own === '#pip');
    for (const o of O) {
      if (o.own === '#pip') continue;
      const [l, tp, r, bt] = o.r;
      if (hasPip && Math.min(r, P.r) - Math.max(l, P.l) > 6 && Math.min(bt, P.b) - Math.max(tp, P.t) > 6 && !seen.has('pip' + o.own + o.tx)) { seen.add('pip' + o.own + o.tx); bad.push(`CHỮ DƯỚI KHUNG NGƯỜI NÓI t=${t.toFixed(2)}: #${o.own.replace('mix:', '')} "${o.tx}" → rút chữ / đặt chữ lên trên y 680 / bỏ title hình`); }
      const why = tp < S.top - .5 ? 'đỉnh' : bt > S.bottom + .5 ? 'đáy' : l < S.left - .5 ? 'mép trái' : r > S.right + .5 ? 'mép phải' : (bt > S.ry && r > S.rx + .5) ? 'cột nút phải' : '';
      const k = o.own + o.tx + why;
      if (why && !seen.has(k)) { seen.add(k); bad.push(`NGOÀI VÙNG AN TOÀN t=${t.toFixed(2)}: #${o.own.replace('mix:', '')} "${o.tx}" (${why}) x ${l.toFixed(0)}–${r.toFixed(0)} y ${tp.toFixed(0)}–${bt.toFixed(0)}`); }
    }
    const M = O.filter(o => o.own.startsWith('mix:')), G = O.filter(o => o.own && o.own !== '#pip' && !o.own.startsWith('mix:'));
    for (const m of M) for (const g of G) {
      const ix = Math.min(m.r[2], g.r[2]) - Math.max(m.r[0], g.r[0]), iy = Math.min(m.r[3], g.r[3]) - Math.max(m.r[1], g.r[1]);
      const k = 'ov' + m.own + g.own;
      if (ix > 6 && iy > 6 && !seen.has(k)) { seen.add(k); bad.push(`CHỮ CHỒNG t=${t.toFixed(2)}: #${m.own.slice(4)} "${m.tx}" đè "${g.tx}" (#${g.own}) → hạ top .mix / rút chữ / bỏ title hình`); }
    }
  }
  await br.close();
  console.log(`Cổng kiểm tra: ${B.length} mốc cắt · quét ${Math.ceil(T / STEP)} thời điểm × 2 · vùng an toàn TikTok/Reels`);
  if (bad.length) { bad.forEach(x => console.log('⚠ ' + x)); console.log(`✖ ${bad.length} lỗi — CHƯA được xuất`); process.exit(1); }
  console.log('✅ SẠCH — được xuất');
})();
