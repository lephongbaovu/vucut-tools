"""realcut · tự soát bằng máy (chạy sau khi có base.mp4 + ads.json, trước/sau khi render fx):
  ✔ chữ ra ngoài vùng an toàn Meta (y 0.14–0.65, x 0.06–0.94)
  ✔ chữ đè lên đầu người nói (dùng matte)          ✔ chữ hiện không đủ lâu để đọc (0.3 s + 0.2 s/từ, tối thiểu 0.8 s)
  ✔ quãng ≥ 4 s không có gì mới (cảnh/chữ/thẻ)      ✔ 0.5 s đầu có chữ móc + hình không tối
  python qc.py DA [--step 0.25]   → in báo cáo + DA/qc/qc_report.txt + DA/qc/qc_flags.jpg (vùng lỗi tô đỏ)
"""
import argparse, os
import numpy as np, cv2
import adsfx as X
from common import probe, die

def words(s): return len([w for w in s.replace('&', ' ').split() if w.strip()])

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('da'); ap.add_argument('--step', type=float, default=0.25)
    a = ap.parse_args()
    src = os.path.join(a.da, 'base.mp4')
    if not os.path.exists(src): die('Chưa có base.mp4')
    mp = os.path.join(a.da, 'matte.mp4'); t_end = probe(src)['dur']
    fx = X.FX(a.da); A = fx.A
    W, H = X.W, X.H; sx0, sy0, sx1, sy1 = X.SAFE
    rep, flags = [], []

    # 1 · thời gian đọc
    def need(n): return max(0.8, 0.3 + 0.2 * n)
    for k in fx.kw:
        n = words(k['main']) + words(k.get('sub', '')); d = k['t1'] - k['t0']
        if d < need(n) - 0.05: rep.append(f'ĐỌC  {k["t0"]:.2f}s «{k["main"]} {k.get("sub", "")}»: hiện {d:.2f}s < cần {need(n):.2f}s → kéo dài hoặc bớt chữ')
    q = A.get('quote')
    if q and q['t1'] - q.get('t2', q['t0']) < need(words(q['l2'])): rep.append(f'ĐỌC  câu trích «{q["l2"]}» hiện quá ngắn')
    o = A.get('offer')
    if o and o['t1'] - o['t0'] < 1.5: rep.append('ĐỌC  khối ưu đãi < 1.5 s (con số then chốt cần ≥ 1.5 s)')
    if A.get('end') and t_end - A['end']['t'] < 2.0: rep.append('ĐỌC  khung kết < 2 s — hotline cần ≥ 2 s để chụp màn hình')

    # 2 · nhịp: quãng không có gì mới
    ev = [0.0]
    for t0, t1 in fx.broll: ev += [t0, t1]
    ev += [k['t0'] for k in fx.kw] + [t for t, _ in A.get('transitions', [])]
    ev += [c['t'] for c in A.get('cards', [])]
    ev += [z['t'] for z in X.load_json(os.path.join(a.da, 'edit.json'), {}).get('aroll_zoom', [])]
    for c in A.get('chips', []): ev += [it['t'] for it in c['items']]
    for key in ('offer', 'stats', 'quote', 'road', 'wordmark'):
        if A.get(key): ev.append(A[key]['t0'])
    if A.get('hook'): ev += [x[1] for x in A['hook'].get('strike', [])] + [A['hook']['price_t']]
    ev = sorted(e for e in ev if e <= fx.end_t)
    for p, n in zip(ev, ev[1:] + [min(fx.end_t, t_end)]):
        if n - p >= 4.0: rep.append(f'NHỊP {p:.2f}–{n:.2f}s: {n - p:.1f}s không có gì mới → chèn B-roll/zoom/chữ')

    # 3 · quét khung: vùng an toàn + đè đầu + mở đầu
    X.MASK['on'] = True
    ts = list(np.arange(0.05, t_end, a.step))
    for t in ts:
        for k in fx.kw:
            if k.get('pos') == 'auto' and k['t0'] <= t <= k['t1'] + 0.35 and (k['t0'], k['main']) not in fx.mode:
                fx.kw_mode(X.frame_at(src, k['t0'] + 0.02), k)
        base = X.frame_at(src, t)
        if base is None: continue
        m = X.frame_at(mp, t, gray=True, vf='scale=1080:1920') if os.path.exists(mp) else None
        X.MASK['m'] = np.zeros((H, W), np.float32)
        if fx.end and t >= fx.end_t and hasattr(fx, '_eb'): del fx._eb
        img = fx.frame(base, m, t, t_end)
        mk = X.MASK['m'] > 0.3
        if t < 0.55 and t + a.step >= 0.55 and not mk.any() and not A.get('hook'):
            rep.append('MỞ   0.5 s đầu chưa có chữ móc')
        if t < 0.1 and base.mean() < 25: rep.append('MỞ   khung đầu tối — không mở từ màn đen (khung đầu = ảnh bìa)')
        out = mk.copy(); out[int(H * sy0):int(H * sy1), int(W * sx0):int(W * sx1)] = False
        bad_safe = out.sum() > 250
        bad_head = False
        if m is not None and fx.is_aroll(t) and mk.any():
            hp = m > 128; rows = np.where(hp.any(1))[0]
            if len(rows):
                top = rows[0]; band = np.zeros_like(hp); band[top:top + int(H * 0.13)] = hp[top:top + int(H * 0.13)]
                band = cv2.dilate(band.astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool)
                bad_head = (mk & band).sum() > 300
        if bad_safe or bad_head:
            why = ' + '.join(x for x, b in (('ngoài vùng an toàn', bad_safe), ('đè đầu người nói', bad_head)) if b)
            rep.append(f'KHUNG {t:.2f}s: chữ {why}')
            ov = img.copy(); ov[out | (mk & (band if bad_head else False))] = (255, 40, 40)
            X.guides(ov); flags.append((t, ov))
    X.MASK['on'] = False

    # gộp lỗi khung liên tiếp
    lines, prev = [], None
    for r in rep:
        if r.startswith('KHUNG') and prev and prev.startswith('KHUNG') and r.split(':', 1)[1] == prev.split(':', 1)[1]:
            continue
        lines.append(r); prev = r
    qc = os.path.join(a.da, 'qc'); os.makedirs(qc, exist_ok=True)
    txt = '\n'.join(lines) if lines else '✓ Không phát hiện lỗi vùng an toàn / đè đầu / thời gian đọc / nhịp.'
    open(os.path.join(qc, 'qc_report.txt'), 'w', encoding='utf-8').write(txt + '\n')
    print(txt)
    if flags:
        tiles = [cv2.resize(im, (270, 480)) for _, im in flags[:24]]
        for (t, _), tl in zip(flags, tiles): cv2.putText(tl, f'{t:.2f}', (6, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        rows = [np.hstack(tiles[i:i + 6] + [np.zeros_like(tiles[0])] * (6 - len(tiles[i:i + 6]))) for i in range(0, len(tiles), 6)]
        cv2.imwrite(os.path.join(qc, 'qc_flags.jpg'), np.vstack(rows)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 85])
        print(f'→ ảnh lỗi: {qc}/qc_flags.jpg (XEM bằng Read)')

if __name__ == '__main__':
    main()
