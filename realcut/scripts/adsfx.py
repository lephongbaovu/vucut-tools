"""realcut · tầng B — chữ & hiệu ứng mẫu "ads dự án cao cấp" (vàng nhũ), điều khiển bằng DA/ads.json.
Đọc DA/base.mp4 (nền từ base.py) + DA/matte.mp4 + DA/head.json + DA/edit.json (vị trí B-roll) → DA/fx.mp4 (chưa tiếng).

  python adsfx.py DA                       render toàn bộ
  python adsfx.py DA --frames 3.5,10.2     ảnh thử → DA/qc/fx_*.jpg (thêm --guides để vẽ khung vùng an toàn)
  python adsfx.py DA --sheet 0.5           bảng ảnh toàn video → DA/qc/fx_sheet.jpg
Mọi mốc thời gian trong ads.json = giây của cut.mp4 (đã 1.1×). Cấu trúc ads.json: reference/schema.md
"""
import argparse, math, os, subprocess, sys, time
import numpy as np, cv2
from common import load_json, probe, die, PALETTE, Writer
import textfx as T
from cards import Cards

W, H, FPS = 1080, 1920, 30
SAFE = (0.06, 0.14, 0.94, 0.65)          # x0, y0, x1, y1 — vùng an toàn Meta Reels
CUR = {'t': 0.0}
MASK = {'on': False, 'm': None, 'skip': False}   # dùng cho qc.py: gom alpha mọi chữ đã vẽ

# ─────────────────── tiện ích vẽ ───────────────────
_over = T.over
def _over_mask(dst, sp, x, y, opacity=1.0, amask=None):
    _over(dst, sp, x, y, opacity, amask)
    if MASK['on'] and not MASK['skip'] and opacity > 0.05 and MASK['m'] is not None:
        h, w = sp['a'].shape; x, y = int(round(x)), int(round(y))
        x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
        if x1 > x0 and y1 > y0:
            a = sp['a'][y0 - y:y1 - y, x0 - x:x1 - x] * opacity
            np.maximum(MASK['m'][y0:y1, x0:x1], a, out=MASK['m'][y0:y1, x0:x1])
T.over = _over_mask

def ease(x): return T.ease_out(T.clamp01(x))
def eio(x): return T.ease_in_out(T.clamp01(x))
def clamp(x): return T.clamp01(x)

_sc = {}
def S(text, font, size, color='cream', tracking=0.0, shadow=0.0):
    k = (text, font, int(size), str(color), round(tracking, 3), shadow)
    if k not in _sc:
        if len(_sc) > 800: _sc.clear()
        _sc[k] = T.sprite(T.nfc(text), font, size, color, tracking=tracking, shadow=shadow)
    return _sc[k]

_gc = {}
def G(text, font, size, pad=8):
    """chữ VÀNG NHŨ: gradient vàng + hạt nhũ lấp lánh (đổi pha 5 lần/s) + bóng mềm rất nhẹ — không viền."""
    ph = int(CUR['t'] * 5) % 3
    key = (text, font, int(size), ph)
    if key in _gc: return _gc[key]
    base = T.sprite(T.nfc(text), font, size, 'cream', tracking=0.03)
    h, w = base['h'] + 2 * pad, base['w'] + 2 * pad
    a = np.zeros((h, w), np.float32); a[pad:pad + base['h'], pad:pad + base['w']] = base['a']
    sh = np.roll(cv2.GaussianBlur(a, (0, 0), max(2, size * 0.05)), int(size * 0.03) + 1, axis=0)
    g = T.glitter_gold(h, w, seed=len(text) * 13 + int(size), tw=ph * 0.7)
    col = np.array((60, 40, 20), np.float32)[None, None, :] * (1 - a[..., None]) + g * a[..., None]
    sp = dict(rgb=col, a=np.clip(np.maximum(a, sh * 0.16), 0, 1), fill=a, base=base['base'] + pad, w=w, h=h,
              xoff=base.get('xoff', 0) - pad)
    if len(_gc) > 600: _gc.clear()
    _gc[key] = sp; return sp

def shimmer(sp, k):
    h, w = sp['h'], sp['w']
    xx = np.arange(w)[None, :] + np.arange(h)[:, None] * 0.5
    c = -0.3 * w + k * (w * 1.6 + h * 0.5)
    band = np.exp(-((xx - c) / (w * 0.06)) ** 2).astype(np.float32) * sp.get('fill', sp['a'])
    return dict(rgb=np.full((h, w, 3), 255, np.float32), a=band, base=sp['base'], w=w, h=h, xoff=sp.get('xoff', 0))

def fit(text, font, size, maxw):
    while T.text_width(T.nfc(text), font, size) > maxw and size > 30: size -= 2
    return size

def gline(img, text, font, size, cx, base, op, shim=None):
    """1 dòng vàng nhũ căn giữa tại baseline `base`; shim 0→1 = vệt sáng quét."""
    if op <= 0: return None
    sp = G(text, font, size)
    T.over(img, sp, cx - sp['w'] / 2, base - sp['base'], op)
    if shim is not None and 0 <= shim <= 1:
        T.over(img, shimmer(sp, shim), cx - sp['w'] / 2, base - sp['base'], 0.7 * op)
    return sp

def cline(img, text, font, size, cx, base, op, color='cream', tracking=0.0, shadow=0.6):
    if op <= 0: return None
    sp = S(text, font, size, color, tracking, shadow)
    T.over(img, sp, cx - sp['w'] / 2 - sp['xoff'], base - sp['base'], op)
    return sp

def warm_dim(img, y0, y1, strength):
    if strength <= 0.002: return
    a, b = int(H * y0), int(H * y1)
    g = np.linspace(1, 0, b - a, dtype=np.float32) ** 1.6 * strength
    ink = np.array(PALETTE['ink'], np.float32)
    roi = img[a:b].astype(np.float32); roi += (ink - roi) * g[:, None, None]
    img[a:b] = roi.clip(0, 255).astype(np.uint8)

def dim_all(img, k):
    if k > 0.002: img[:] = (img.astype(np.float32) * (1 - k)).astype(np.uint8)

def bright(img, x0, y0, x1, y1, thr=125):
    r = img[int(y0):int(y1), int(x0):int(x1)].astype(np.float32)
    return r.size > 0 and (0.299 * r[..., 0] + 0.587 * r[..., 1] + 0.114 * r[..., 2]).mean() > thr

def pill(img, cx, cy, w, h, op, alpha=0.55, ring=True):
    x0, y0 = cx - w / 2, cy - h / 2
    T.glass(img, x0, y0, w, h, tint=(30, 24, 19), alpha=alpha, opacity=op, radius=int(h / 2))
    if ring and op > 0:
        w_, h_ = int(w), int(h); rr = h_ // 2
        rm = np.zeros((h_, w_), np.uint8)
        cv2.ellipse(rm, (rr, rr), (rr - 2, rr - 2), 0, 90, 270, 255, 3, cv2.LINE_AA)
        cv2.ellipse(rm, (w_ - rr - 1, rr), (rr - 2, rr - 2), 0, -90, 90, 255, 3, cv2.LINE_AA)
        rm[1:4, rr:w_ - rr] = 255; rm[h_ - 4:h_ - 1, rr:w_ - rr] = 255
        g = T.gradient(h_, w_, PALETTE['gold_hi'], PALETTE['gold'], PALETTE['gold_lo'])
        T.over(img, dict(rgb=g, a=rm.astype(np.float32) / 255, base=0, w=w_, h=h_, xoff=0), x0, y0, op)

def frame_at(path, t, gray=False, vf=None):
    cmd = ['ffmpeg', '-v', 'error', '-ss', f'{max(0, t):.3f}', '-i', path]
    if vf: cmd += ['-vf', vf]
    cmd += ['-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'gray' if gray else 'rgb24', '-']
    b = subprocess.run(cmd, capture_output=True).stdout
    n = W * H * (1 if gray else 3)
    if len(b) < n: return None
    a = np.frombuffer(b[:n], np.uint8)
    return a.reshape(H, W) if gray else a.reshape(H, W, 3).copy()

def reader(path, gray=False, vf=None, ss=None):
    cmd = ['ffmpeg', '-v', 'error'] + (['-ss', f'{ss:.3f}'] if ss else []) + ['-i', path]
    if vf: cmd += ['-vf', vf]
    cmd += ['-f', 'rawvideo', '-pix_fmt', 'gray' if gray else 'rgb24', '-']
    pr = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=10 ** 8)
    n = W * H * (1 if gray else 3)
    while True:
        b = pr.stdout.read(n)
        if len(b) < n: return
        a = np.frombuffer(b, np.uint8)
        yield a.reshape(H, W) if gray else a.reshape(H, W, 3)

# ─────────────────── dựng ───────────────────
class FX:
    def __init__(self, da):
        self.da = da
        self.A = load_json(os.path.join(da, 'ads.json'))
        if self.A is None: die('Chưa có DA/ads.json (xem reference/schema.md + templates/ads_example.json)')
        E = load_json(os.path.join(da, 'edit.json'), {})
        self.broll = [(b['t'], b['t'] + b['d']) for b in E.get('broll', [])]
        hj = load_json(os.path.join(da, 'head.json'))
        self.heads = hj['head'] if hj else None
        self.cards = Cards(self.A.get('cards', []), W, H)
        self.kw = sorted(self.A.get('keywords', []), key=lambda k: k['t0'])
        self.mode = {}
        tr = self.A.get('transitions', [])
        self.trans = {round(float(t), 3): ty for t, ty in tr}
        self.leaks = self.A.get('leaks')
        if self.leaks is None:   # mặc định: 1 vệt sáng nhẹ ở mỗi chuyển chương
            self.leaks = [[t - 0.06, 0.55, 0.5, (1 if i % 2 == 0 else -1), 0.35] for i, (t, _) in enumerate(tr)]
        self.end = self.A.get('end')
        self.end_t = self.end['t'] if self.end else 1e9
        self.road = self.A.get('road'); self._road = {}
        self.wm = None
        self._dark_cache = {}

    # —— trạng thái A-roll / đỉnh đầu ——
    def is_aroll(self, t):
        return not any(a <= t < b for a, b in self.broll)

    def head_top(self, t0, t1):
        """đỉnh đầu cao nhất (px) trong [t0,t1] khi đang là A-roll; None nếu không có người nói."""
        if not self.heads: return None
        ys = []
        for t in np.arange(t0, t1 + 1e-3, 0.1):
            if not self.is_aroll(t): continue
            i = min(max(int(t * FPS), 0), len(self.heads) - 1)
            if self.heads[i]: ys.append(self.heads[i][1] * H)
        return min(ys) if ys else None

    # —— 1 · móc giá (lớp SAU người nói) ——
    def hook_bg(self, img, t):
        h = self.A.get('hook')
        if not h: return
        out = h['out']
        warm_dim(img, 0.0, 0.48, 0.62 * T.env(t, 0.0, out + 0.27, 0.32, 0.32))
        p0 = h['price_t']
        out_k = 1 - eio((t - (p0 - 0.29)) / 0.29)   # các giá so sánh rời đi ngay trước khi giá chính hiện
        for txt, t0, ts, y in h.get('strike', []):
            if t < t0 or out_k <= 0: continue
            k = ease((t - t0) / 0.25); st = ease((t - ts) / 0.2)
            sp = S(txt, 'semibold', 92, 'cream', 0.04, 0.6)
            by = H * y + (1 - k) * 22 - (1 - out_k) * 40
            T.over(img, sp, W / 2 - sp['w'] / 2, by - sp['base'], k * (1 - 0.55 * st) * out_k)
            if st > 0:
                T.hline(img, W / 2 - sp['w'] * 0.56, by - 92 * 0.36, sp['w'] * 1.12 * st, 7, 'gold', out_k)
        if p0 <= t < h.get('behind_until', 0):
            self.price(img, t)

    def price(self, img, t):
        h = self.A['hook']; p0, out = h['price_t'], h['out']
        k = ease((t - p0) / 0.5); fo = 1 - eio((t - out) / 0.27)
        if fo <= 0: return
        sc = 1.18 - 0.18 * k
        sp = G(h['price'], 'serif_black', h.get('price_size', 250))
        spx = T.scaled(sp, sc) if sc != 1 else sp
        base = H * h.get('price_y', 0.312)
        T.over(img, spx, W / 2 - spx['w'] / 2, base - spx['base'], min(1, (t - p0) / 0.11) * fo)
        for ts in (p0 + 0.21, h.get('behind_until', p0 + 1.8) + 0.05):
            ks = (t - ts) / 0.7
            if 0 <= ks <= 1:
                sh = shimmer(sp, ks); sh = T.scaled(sh, sc) if sc != 1 else sh
                T.over(img, sh, W / 2 - sh['w'] / 2, base - sh['base'], 0.8 * fo)

    def hook_fg(self, img, t):
        h = self.A.get('hook')
        if not h: return
        if t >= h.get('behind_until', 0): self.price(img, t)
        fo = 1 - eio((t - h['out']) / 0.27)
        if fo <= 0: return
        if h.get('tag') and t >= h['tag_t']:
            k = ease((t - h['tag_t']) / 0.4) * fo
            lab = S(h['tag'], 'black', 50, 'cream', 0.42)
            cy = H * h.get('tag_y', 0.352) + (1 - k) * 16
            pill(img, W / 2, cy, lab['w'] + 96, 86, k, alpha=0.62)
            T.over(img, lab, W / 2 - lab['w'] / 2 - lab['xoff'], cy - lab['h'] / 2 - 2, k)
        sp_ = h.get('specs')
        if sp_ and t >= sp_[0][1]:
            sps = [S(p, 'semibold' if i else 'medium', 50 if i else 42, 'cream' if i == 0 else 'gold_hi', 0, 0.6) for i, (p, _) in enumerate(sp_)]
            gap = 40; tw = sum(s['w'] for s in sps) + gap * (len(sps) - 1) + 20
            k = ease((t - sp_[0][1]) / 0.4) * fo; y = H * h.get('specs_y', 0.600)
            T.glass(img, W / 2 - tw / 2 - 40, y - 74, tw + 80, 108, alpha=0.62, opacity=k, radius=54)
            x = W / 2 - tw / 2
            for i, ((p, ti), s) in enumerate(zip(sp_, sps)):
                kk = ease((t - ti) / 0.32) * fo
                T.over(img, s, x - s['xoff'], y - s['base'] - (1 - kk) * 8, kk)
                x += s['w'] + gap + (20 if i == 0 else 0)
                if i < len(sps) - 1:
                    d_ = S('·', 'semibold', 50, 'gold_hi'); T.over(img, d_, x - gap / 2 - d_['w'] / 2 - d_['xoff'], y - d_['base'], kk)

    # —— 2 · wordmark dự án trên cảnh phối cảnh ——
    def wordmark(self, img, t):
        w = self.A.get('wordmark')
        if not w or not (w['t0'] <= t <= w['t1']): return
        e = T.env(t, w['t0'], w['t1'], 0.36, 0.27); k = ease((t - w['t0']) / 0.8)
        warm_dim(img, 0.0, 0.45, 0.68 * e)
        sp = G(w['text'], 'serif_black', w.get('size', 128))
        T.over(img, sp, W / 2 - sp['w'] / 2, H * 0.265 - sp['base'], e)
        if w.get('label'):
            cline(img, w['label'], 'medium', 30, W / 2, H * 0.185, e * ease((t - w['t0'] - 0.18) / 0.36), 'gold_hi', 0.6)
        L = 260 * ease((t - w['t0'] - 0.23) / 0.55)
        T.hline(img, W / 2 - L / 2, H * 0.265 + 36, L, 2, 'gold', e)

    # —— 3 · từ khoá vàng nhũ ——
    def kw_mode(self, img, k):
        key = (k['t0'], k['main'])
        if key not in self.mode:
            pos = k.get('pos', 'low')
            if pos == 'auto':
                self.mode[key] = 'bright' if bright(img, W * 0.15, H * 0.55, W * 0.85, H * 0.66) else 'low'
            else:
                self.mode[key] = pos
        return self.mode[key]

    def darkness(self, img, t):
        """làm tối CẢ KHUNG khi chữ hiện trên nền sáng; liền mạch nếu các chữ nối nhau."""
        d = 0.0
        for k in self.kw:
            if k.get('pos') == 'auto' and k['t0'] <= t <= k['t1'] + 0.35:
                if self.kw_mode(img, k) == 'bright':
                    d = max(d, ease((t - k['t0']) / 0.28) * clamp((k['t1'] + 0.32 - t) / 0.32))
        q = self.A.get('quote')
        if q and q.get('darken', True) and q['t0'] <= t <= q['t1'] + 0.35:
            d = max(d, ease((t - q['t0']) / 0.28) * clamp((q['t1'] + 0.32 - t) / 0.32))
        return d * self.A.get('darken', 0.52)

    def keywords(self, img, t):
        for k in self.kw:
            t0, t1 = k['t0'], k['t1']
            if not (t0 - 0.02 <= t <= t1): continue
            md = self.kw_mode(img, k)
            a = ease((t - t0) / 0.18); ko = clamp((t1 - t) / 0.12); op = a * ko
            main, sub = k['main'], k.get('sub', '')
            layout = k.get('layout', 'two')
            if layout == 'stack3':                  # DÒNG NGƯỜI / & / DÒNG TIỀN
                sz = min(fit(main, 'serif_black', k.get('size', 94), W * 0.80), fit(sub, 'serif_black', k.get('size', 94), W * 0.80))
                by = H * k['y'] if 'y' in k else H * 0.638 - sz * 1.88
                gline(img, main, 'serif_black', sz, W / 2, by + (1 - a) * 10, op, (t - t0 - 0.12) / 0.7)
                k2 = ease((t - t0 - 0.15) / 0.25)
                gline(img, k.get('amp', '&'), 'serif_xbi', sz * 0.8, W / 2, by + sz * 0.90 + (1 - k2) * 6, k2 * ko)
                k3 = ease((t - t0 - 0.28) / 0.25)
                gline(img, sub, 'serif_black', sz, W / 2, by + sz * 1.88 + (1 - k3) * 10, k3 * ko, (t - t0 - 0.4) / 0.7)
                return
            if md == 'top':
                big = k.get('big', False)
                sz = fit(main, 'serif_black', k.get('size', 215 if big else 176), W * (0.86 if big else 0.84))
                ssz = fit(sub, 'serif_xbi', k.get('sub_size', 72), W * 0.80) if sub else 0
                if 'y' in k:
                    by = H * k['y']
                else:                               # tự đặt ngay trên đỉnh đầu, không che đầu
                    ht = self.head_top(t0, t1)
                    bottom = (sz * 0.5 + ssz * 0.28) if sub else sz * 0.26
                    by = H * 0.272 if ht is None else min(H * 0.36, ht - 36 - bottom)
                    while by - sz * 0.98 < H * SAFE[1] and sz > 90:   # chạm mép trên vùng an toàn → thu chữ
                        sz -= 6; by = min(by + 3, H * 0.36)
                sy = by + sz * 0.5
            elif md == 'bright':
                sz = fit(main, 'serif_black', k.get('size', 128), W * 0.84)
                ssz = fit(sub, 'serif_xbi', k.get('sub_size', 60), W * 0.80) if sub else 0
                by = H * k.get('y', 0.420); sy = by + 70
            else:                                   # low: dải dưới vùng an toàn
                sz = fit(main, 'serif_black', k.get('size', 140), W * 0.84)
                ssz = fit(sub, 'serif_xbi', k.get('sub_size', 64), W * 0.80) if sub else 0
                if sub:
                    sy = H * k.get('y_sub', 0.642); by = H * k['y'] if 'y' in k else sy - sz * 0.56
                else:
                    by = H * k.get('y', 0.630); sy = by
            gline(img, main, 'serif_black', sz, W / 2, by + (1 - a) * 10, op, (t - t0 - 0.12) / 0.7)
            if sub:
                kk = ease((t - t0 - 0.15) / 0.25) * ko
                gline(img, sub, 'serif_xbi', ssz, W / 2, sy + (1 - kk) * 6, kk)
            return

    # —— 4 · câu trích (2 tầng: kem + vàng nhũ nghiêng) ——
    def quote(self, img, t):
        q = self.A.get('quote')
        if not q or not (q['t0'] <= t <= q['t1']): return
        ko = clamp((q['t1'] - t) / 0.2)
        k1 = ease((t - q['t0']) / 0.35) * ko
        cline(img, q['l1'], 'semibold', q.get('size1', 62), W / 2, H * q.get('y1', 0.395) + (1 - k1) * 8, k1, 'cream', 0.01, 0.4)
        t2 = q.get('t2', q['t0'] + 0.6)
        if t >= t2:
            k2 = ease((t - t2) / 0.3) * ko
            gline(img, q['l2'], 'serif_xbi', fit(q['l2'], 'serif_xbi', q.get('size2', 116), W * 0.84), W / 2,
                  H * q.get('y2', 0.458) + (1 - k2) * 8, k2, (t - t2 - 0.1) / 0.8)

    # —— 5 · khối ưu đãi % ——
    def offer(self, img, t):
        o = self.A.get('offer')
        if not o or not (o['t0'] <= t <= o['t1']): return
        t0, t1 = o['t0'], o['t1']; s = o.get('scale', 1.28)
        k = ease((t - t0) / 0.35); op = clamp((t1 - t) / 0.15)
        warm_dim(img, 0.0, 0.42, 0.50 * k * op)
        val = float(o['value']); cnt = val * ease((t - t0) / 0.6)
        txt = (f'{cnt:.1f}'.replace('.', ',') if val != int(val) else str(int(round(cnt))))
        num = G(txt, 'serif_black', int(210 * s)); pct = G(o.get('unit', '%'), 'serif_black', int(110 * s))
        tw = num['w'] + pct['w'] - 12; x0 = W / 2 - tw / 2; base = H * o.get('y', 0.263)
        T.over(img, num, x0, base - num['base'], op * k)
        T.over(img, pct, x0 + num['w'] - 12, base - pct['base'] - 84 * s, op * k)
        ks = (t - t0 - 0.6) / 0.8
        if 0 <= ks <= 1: T.over(img, shimmer(num, ks), x0, base - num['base'], 0.7 * op)
        if o.get('pre'):
            kl = ease((t - t0 - 0.1) / 0.3) * op
            le = S(o['pre'], 'semibold', 46, 'cream', 0.02, 0.6)
            T.over(img, le, x0 + 10 - le['xoff'], base - 150 * s - le['base'] - (1 - kl) * 8, kl)
        kb = ease((t - t0 - 0.35) / 0.35) * op
        if o.get('label'):
            l1 = S(o['label'], 'semibold', 38, 'cream', 0.22, 0.6); y1 = base + 80
            T.over(img, l1, W / 2 - l1['w'] / 2 - l1['xoff'], y1 - l1['base'] + (1 - kb) * 10, kb)
            L = 80 * kb
            T.hline(img, W / 2 - l1['w'] / 2 - 26 - L, y1 - 13, L, 2, 'gold', kb)
            T.hline(img, W / 2 + l1['w'] / 2 + 26, y1 - 13, L, 2, 'gold', kb)
        if o.get('sub'):
            kk = ease((t - t0 - 0.5) / 0.35) * op
            gline(img, o['sub'], 'serif_xbi', 84, W / 2, base + 170 + (1 - kk) * 10, kk, (t - t0 - 0.9) / 0.8)

    # —— 6 · thẻ liệt kê (tag 2 cột hoặc danh sách đánh số) ——
    def tag(self, img, text, cx, base, op, dy):
        tx = S(text, 'semibold', 36, 'cream', 0.01, 0.0)
        pw, ph = int(tx['w'] + 66), 70
        x0, y0 = cx - pw / 2, base - ph + 14 + dy
        T.glass(img, x0, y0, pw, ph, tint=(24, 19, 15), alpha=0.58, opacity=op, radius=14)
        bar = dict(rgb=T.glitter_gold(ph - 24, 5, seed=3), a=np.ones((ph - 24, 5), np.float32), base=0, w=5, h=ph - 24, xoff=0)
        T.over(img, bar, x0 + 18, y0 + 12, op)
        T.over(img, tx, x0 + 38 - tx['xoff'], y0 + ph / 2 - tx['h'] / 2 - 1, op)

    def chips(self, img, t):
        for c in self.A.get('chips', []):
            if not (c['t'] <= t <= c['t'] + c['d']): continue
            eo = clamp((c['t'] + c['d'] - t) / 0.25); items = c['items']
            if c.get('numbered') or items[0]['text'][:2].isdigit():
                x0 = W * 0.11; rows = [H * 0.528, H * 0.584, H * 0.640][-len(items):] if len(items) <= 3 else \
                    [H * 0.640 - (len(items) - 1 - i) * H * 0.056 for i in range(len(items))]
                for i, (it, by) in enumerate(zip(items, rows)):
                    if t < it['t'] - 0.05: continue
                    k = ease((t - it['t'] + 0.05) / 0.35) * eo
                    n, txt = (it['text'][:2], it['text'][2:].strip()) if it['text'][:2].isdigit() else (f'{i + 1:02d}', it['text'])
                    ns = G(n, 'serif_black', 56)
                    T.over(img, ns, x0 - (1 - k) * 30, by - ns['base'], k)
                    ts = S(txt, 'semibold', 40, 'cream', 0.01, 0.6)
                    tx = x0 + ns['w'] + 18 - (1 - k) * 30
                    T.over(img, ts, tx - ts['xoff'], by - ts['base'] - 4, k)
                    T.hline(img, tx, by + 14, ts['w'] * ease((t - it['t'] - 0.15) / 0.5), 2, 'gold', k * 0.8)
            else:
                rows = [items[i:i + 2] for i in range(0, len(items), 2)]
                base_rows = [H * 0.640 - (len(rows) - 1 - r) * H * 0.050 for r in range(len(rows))]
                for r, row in enumerate(rows):
                    widths = [int(S(it['text'], 'semibold', 36, 'cream', 0.01, 0.0)['w'] + 66) for it in row]
                    gap = 18; tot = sum(widths) + gap * (len(row) - 1); x = W / 2 - tot / 2
                    for it, wd in zip(row, widths):
                        if t >= it['t'] - 0.05:
                            k = ease((t - it['t'] + 0.05) / 0.3) * eo
                            self.tag(img, it['text'], x + wd / 2, base_rows[r], k, (1 - k) * 14)
                        x += wd + gap

    # —— 7 · dãy số liệu 3 cột ——
    def stats(self, img, t):
        s = self.A.get('stats')
        if not s or not (s['t0'] <= t <= s['t1']): return
        ko = clamp((s['t1'] - t) / 0.2); items = s['items']; n = len(items)
        colw = (W * 0.88) / n; x0 = W * 0.06
        for i, (v, lab) in enumerate(items):
            k = ease((t - s['t0'] - i * 0.35) / 0.35) * ko
            cx = x0 + colw * (i + 0.5)
            vs = S(v, 'bold', 44 if len(v) < 10 else 40, 'cream', 0.0, 0.5)
            ls = S(lab, 'medium', 20, 'gold_hi', 0.22, 0.4)
            T.over(img, ls, cx - ls['w'] / 2 - ls['xoff'], H * 0.590 - ls['base'] + (1 - k) * 6, k)
            T.over(img, vs, cx - vs['w'] / 2 - vs['xoff'], H * 0.632 - vs['base'] + (1 - k) * 6, k)
            if i < n - 1:
                T.over(img, dict(rgb=np.full((70, 1, 3), 220, np.float32), a=np.full((70, 1), 0.45, np.float32), base=0, w=1, h=70, xoff=0),
                       x0 + colw * (i + 1), H * 0.574, k)

    # —— 8 · nhãn đường chạy dọc con đường, bám flycam ——
    def road_layer(self):
        if 'pm' in self._road: return self._road
        r = self.road; cw, ch = 1000, 320; ly = 160
        cv = np.zeros((ch, cw, 3), np.float32); ca = np.zeros((ch, cw), np.float32)
        def paste(sp, x, y):
            h, w = sp['h'], sp['w']; x, y = int(round(x)), int(round(y))
            a = sp['a'][:, :, None]
            cv[y:y + h, x:x + w] = cv[y:y + h, x:x + w] * (1 - a) + sp['rgb'] * a
            ca[y:y + h, x:x + w] = ca[y:y + h, x:x + w] * (1 - a[..., 0]) + a[..., 0]
        title = G(r['title'], 'serif_black', r.get('size', 104))
        paste(title, cw / 2 - title['w'] / 2, ly - 16 - title['base'])
        sub = T.sprite(T.nfc(r.get('sub', '')), 'semibold', 30, 'cream', tracking=0.16, shadow=0.7) if r.get('sub') else None
        lw = int(max(title['w'], sub['w'] if sub else 0) + 20)
        paste(dict(rgb=np.broadcast_to(np.array((240, 196, 96), np.float32), (4, lw, 3)).copy(), a=np.ones((4, lw), np.float32), w=lw, h=4),
              cw / 2 - lw / 2, ly - 2)
        if sub: paste(sub, cw / 2 - sub['w'] / 2 - sub.get('xoff', 0), ly + 14)
        ang = math.degrees(math.atan2(r['p2'][1] - r['p1'][1], r['p2'][0] - r['p1'][0]))
        cx = r['p1'][0] + (r['p2'][0] - r['p1'][0]) * r.get('at', 0.5); cy = r['p1'][1] + (r['p2'][1] - r['p1'][1]) * r.get('at', 0.5)
        M = cv2.getRotationMatrix2D((cw / 2, ly), -ang, 1.0); M[0, 2] += cx - cw / 2; M[1, 2] += cy - ly
        self._road['pm'] = cv2.warpAffine(cv * ca[..., None], M, (W, H)); self._road['a'] = cv2.warpAffine(ca, M, (W, H))
        self._road['orb'] = cv2.ORB_create(3000); self._road['H'] = {}
        return self._road

    def road_label(self, img, base, t):
        r = self.road
        if not r or not (r['t0'] <= t <= r['t1']): return
        e = ease((t - r['t0']) / 0.45) * clamp((r['t1'] - t) / 0.35)
        if e <= 0: return
        L = self.road_layer(); orb = L['orb']
        def gray(im):
            g = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY); g[:int(H * 0.2)] = 0; return g
        if 'ref' not in L:
            ref = frame_at(os.path.join(self.da, 'base.mp4'), r['ref_t'])
            L['ref'] = orb.detectAndCompute(gray(ref), None)
        key = round(t * FPS)
        if key not in L['H']:
            kp, d = orb.detectAndCompute(gray(base), None); Hm = np.eye(3)
            if d is not None and L['ref'][1] is not None:
                m = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(L['ref'][1], d)
                if len(m) >= 30:
                    a_ = np.float32([L['ref'][0][x.queryIdx].pt for x in m]); b_ = np.float32([kp[x.trainIdx].pt for x in m])
                    Hm2, _ = cv2.findHomography(a_, b_, cv2.RANSAC, 3.0)
                    if Hm2 is not None: Hm = Hm2
            L['H'][key] = Hm
        Hm = L['H'][key]
        pm = cv2.warpPerspective(L['pm'], Hm, (W, H)); a = cv2.warpPerspective(L['a'], Hm, (W, H)) * e
        sh = cv2.GaussianBlur(a, (0, 0), 6) * 0.45
        f = img.astype(np.float32) * (1 - sh[..., None]); f = f * (1 - a[..., None]) + pm * e
        img[:] = np.clip(f, 0, 255).astype(np.uint8)
        if MASK['on'] and MASK['m'] is not None: np.maximum(MASK['m'], a, out=MASK['m'])

    # —— 9 · chuyển cảnh chương + vệt sáng ——
    @staticmethod
    def _zoomed(img, sc):
        h, w = img.shape[:2]
        big = cv2.resize(img, (int(w * sc), int(h * sc)), interpolation=cv2.INTER_LINEAR)
        y0 = (big.shape[0] - h) // 2; x0 = (big.shape[1] - w) // 2
        return big[y0:y0 + h, x0:x0 + w]

    def transition(self, img, t):
        if not self.trans: return img
        c = min(self.trans, key=lambda c: abs(t - c)); d = t - c; R = 0.13
        if abs(d) > R: return img
        s = (1 - abs(d) / R) ** 1.4
        small = cv2.resize(img, (540, 960), interpolation=cv2.INTER_AREA).astype(np.float32)
        if self.trans[c] == 'whip':
            sh = int((-1 if d < 0 else 1) * 540 * 0.24 * s)
            small = cv2.warpAffine(small, np.float32([[1, 0, sh], [0, 1, 0]]), (540, 960), borderMode=cv2.BORDER_REFLECT)
            kk = 1 + int(80 * s); out = cv2.filter2D(small, -1, np.ones((1, kk), np.float32) / kk, borderType=cv2.BORDER_REFLECT)
        else:
            sc = 1 + 0.18 * s; acc = np.zeros_like(small)
            for j in range(6): acc += self._zoomed(small, sc * (1 + 0.06 * s * j / 5))
            out = acc / 6
        out = cv2.resize(out, (W, H), interpolation=cv2.INTER_CUBIC); a = min(1, s * 1.6)
        return (img.astype(np.float32) * (1 - a) + out * a).clip(0, 255).astype(np.uint8)

    def leak(self, img, t):
        lw, lh = 135, 240
        acc = None
        for t0, d, pk, dr, yc in self.leaks:
            if not (t0 <= t <= t0 + d): continue
            if acc is None:
                acc = np.zeros((lh, lw, 3), np.float32); self._yx = np.mgrid[0:lh, 0:lw].astype(np.float32)
            YY, XX = self._yx; k = (t - t0) / d
            amp = max(0.0, math.sin(math.pi * k)) ** 1.3 * pk
            cx = lw * (0.5 + dr * (-0.9 + 1.8 * k)); cy = lh * yc
            r1 = np.exp(-(((XX - cx) / (lw * 0.55)) ** 2 + ((YY - cy) / (lh * 0.42)) ** 2))
            r2 = np.exp(-(((XX - cx * 0.7 - lw * 0.15) / (lw * 0.25)) ** 2 + ((YY - cy - lh * 0.1) / (lh * 0.2)) ** 2))
            acc += (r1[..., None] * np.array([255, 150, 70], np.float32) * 0.85 + r2[..., None] * np.array([255, 214, 150], np.float32)) * amp
        if acc is None: return img
        lay = cv2.resize(np.clip(acc, 0, 255), (W, H), interpolation=cv2.INTER_CUBIC)
        a = img.astype(np.float32)
        return (255 - (255 - a) * (255 - lay) / 255).clip(0, 255).astype(np.uint8)

    # —— 10 · watermark SĐT trôi chậm ——
    def watermark(self, img, t):
        txt = self.A.get('watermark') or self.A.get('brand', {}).get('hotline')
        if not txt: return
        if self.wm is None: self.wm = T.sprite(txt, 'medium_italic', 30, 'cream', tracking=0.06, shadow=0.35)
        x = W * 0.5 + W * 0.27 * math.sin(2 * math.pi * t / 26.0) - self.wm['w'] / 2
        y = H * 0.40 + H * 0.17 * math.sin(2 * math.pi * t / 37.0 + 1.1)
        MASK['skip'] = True; T.over(img, self.wm, x, y, 0.38); MASK['skip'] = False

    # —— 11 · khung kết ——
    def end_bg(self, t):
        b = self.end.get('bg')
        if not b: return None
        if not hasattr(self, '_eb'):
            vf = "crop=ih*9/16:ih:(iw-ih*9/16)*0.5:0,scale=1080:1920:flags=lanczos,fps=30"
            self._eb = reader(b['src'] if os.path.isabs(b['src']) else os.path.join(self.da, b['src']), vf=vf, ss=b.get('in', 0.0) + max(0, t - self.end_t))
        return next(self._eb, None)

    def end_card(self, img, t, t_end):
        en = self.end; k0 = t - self.end_t
        s = 1.0 + 0.05 * clamp(k0 / 3.4)
        if s > 1.0: img[:] = self._zoomed(img, s)
        a = img.astype(np.float32); ink = np.array(PALETTE['ink'], np.float32)
        a += (ink - a) * (0.45 * ease(k0 / 0.6)); img[:] = a.clip(0, 255).astype(np.uint8)
        e = lambda d, dur=0.5: ease((k0 - d) / dur)
        brand = self.A.get('brand', {})
        k = e(0.2, 0.9); y = H * 0.270
        sp = G(en.get('title', brand.get('name', '')), 'serif_black', 140)
        T.over(img, sp, W / 2 - sp['w'] / 2, y - sp['base'], k)
        L = 300 * e(0.5, 0.7); T.hline(img, W / 2 - L / 2, y + 34, L, 2, 'gold', k)
        for i, ln in enumerate(en.get('lines', [])):
            if i == 0: cline(img, ln, 'medium', 28, W / 2, y + 92, e(0.7), 'cream', 0.14, 0.6)
            else: cline(img, ln, 'semibold', 38, W / 2, y + 150 + (i - 1) * 50, e(0.85), 'gold_hi', 0.0, 0.6)
        kp = e(1.1)
        if en.get('price') and kp > 0:
            pr = G(en['price'], 'serif_black', 112)
            gf = S(en.get('price_tag', ''), 'black', 32, 'cream', 0.4) if en.get('price_tag') else None
            tw = pr['w'] + ((30 + gf['w'] + 52) if gf else 0); x = W / 2 - tw / 2; base = H * 0.468
            T.over(img, pr, x, base - pr['base'], kp)
            if gf:
                pill(img, x + pr['w'] + 30 + (gf['w'] + 52) / 2, base - 40, gf['w'] + 52, 62, kp, alpha=0.6)
                T.over(img, gf, x + pr['w'] + 30 + 26 - gf['xoff'], base - 40 - gf['h'] / 2 - 2, kp)
        kc = e(1.4)
        if en.get('cta') and kc > 0:
            cta = S(en['cta'], 'medium', 36, 'cream')
            cy = H * 0.535 + (1 - kc) * 12
            pill(img, W / 2, cy, cta['w'] + 100, 88, kc, alpha=0.5)
            T.over(img, cta, W / 2 - cta['w'] / 2 - cta['xoff'], cy - cta['h'] / 2 - 2, kc)
        kh = e(1.7); hot = en.get('hotline', brand.get('hotline'))
        if hot and kh > 0:
            hl = S('HOTLINE', 'semibold', 26, 'gold_hi', 0.4, 0.4); ph = G(hot, 'serif_black', 84)
            tw = hl['w'] + 26 + ph['w']; x = W / 2 - tw / 2; base = H * 0.625 + (1 - kh) * 10
            T.over(img, hl, x - hl['xoff'], base - 22 - hl['base'], kh)
            T.over(img, ph, x + hl['w'] + 26, base - ph['base'], kh)
        fo = clamp((t_end - t) / 0.45)
        if fo < 1: img[:] = (img.astype(np.float32) * fo).astype(np.uint8)

    # —— ghép 1 khung ——
    def frame(self, base, matte, t, t_end):
        CUR['t'] = t
        img = base.copy()
        dc = self.cards.dim_amount(t)
        if dc > 0.001: img = cv2.addWeighted(img, 1 - dc, np.full_like(img, PALETTE['ink']), dc, 0)
        self.cards.draw(img, t)
        h = self.A.get('hook')
        if h and t < h['out'] + 0.4:
            bg = img.copy()
            MASK['skip'] = True; self.hook_bg(bg, t); MASK['skip'] = False
            if matte is not None and t < h.get('behind_until', 0) and self.is_aroll(t):
                a = cv2.GaussianBlur(matte, (5, 5), 0).astype(np.float32)[..., None] / 255
                img = (img.astype(np.float32) * a + bg.astype(np.float32) * (1 - a)).astype(np.uint8)
            else:
                img = bg
            self.hook_fg(img, t)
        self.wordmark(img, t)
        dim_all(img, self.darkness(img, t))
        self.keywords(img, t)
        self.offer(img, t)
        self.chips(img, t)
        self.quote(img, t)
        self.stats(img, t)
        self.road_label(img, base, t)
        img = self.transition(img, t)
        if self.end and t >= self.end_t:
            b = self.end_bg(t)
            if b is not None:
                kx = clamp((t - self.end_t) / 0.35)
                img = (img.astype(np.float32) * (1 - kx) + b.astype(np.float32) * kx).astype(np.uint8) if kx < 1 else b.copy()
            self.end_card(img, t, t_end)
        img = self.leak(img, t)
        self.watermark(img, t)
        return img

def guides(img):
    x0, y0, x1, y1 = SAFE
    cv2.rectangle(img, (int(W * x0), int(H * y0)), (int(W * x1), int(H * y1)), (255, 60, 60), 2)
    return img

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('da'); ap.add_argument('--frames'); ap.add_argument('--sheet', type=float)
    ap.add_argument('--guides', action='store_true'); ap.add_argument('--out')
    a = ap.parse_args()
    src = os.path.join(a.da, 'base.mp4')
    if not os.path.exists(src): die('Chưa có DA/base.mp4 — chạy `realcut.py base DA` trước')
    mp = os.path.join(a.da, 'matte.mp4'); has_m = os.path.exists(mp)
    t_end = probe(src)['dur']
    fx = FX(a.da)
    if a.frames or a.sheet:
        qc = os.path.join(a.da, 'qc'); os.makedirs(qc, exist_ok=True)
        ts = [float(x) for x in a.frames.split(',')] if a.frames else list(np.arange(0.2, t_end, a.sheet))
        ims = []
        for t in ts:
            for k in fx.kw:          # quyết định chế độ màu như lúc render (tại t0)
                if k.get('pos') == 'auto' and k['t0'] <= t <= k['t1'] + 0.35 and (k['t0'], k['main']) not in fx.mode:
                    b0 = frame_at(src, k['t0'] + 0.02); fx.kw_mode(b0, k)
            base = frame_at(src, t)
            m = frame_at(mp, t, gray=True, vf='scale=1080:1920') if has_m else None
            if fx.end and t >= fx.end_t and hasattr(fx, '_eb'): del fx._eb
            im = fx.frame(base, m, t, t_end)
            if a.guides: guides(im)
            if a.frames: cv2.imwrite(os.path.join(qc, f'fx_{t:06.2f}.jpg'), im[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 90])
            ims.append(im)
        if a.sheet:
            cols, tw = 8, 216; th = int(tw * H / W); rows = [ims[i:i + cols] for i in range(0, len(ims), cols)]
            sheet = np.full((th * len(rows), tw * cols, 3), 20, np.uint8)
            for r, row in enumerate(rows):
                for c_, im in enumerate(row):
                    tile = cv2.resize(im, (tw, th), interpolation=cv2.INTER_AREA)
                    cv2.putText(tile, f'{ts[r * cols + c_]:.1f}', (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 230, 120), 2)
                    sheet[r * th:(r + 1) * th, c_ * tw:(c_ + 1) * tw] = tile
            cv2.imwrite(os.path.join(qc, 'fx_sheet.jpg'), sheet[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 85])
        print(f'✓ {len(ts)} khung → {qc}')
        return
    out = a.out or os.path.join(a.da, 'fx.mp4')
    wr = Writer(out, W, H, FPS, crf=17, preset='medium')
    mt = reader(mp, gray=True, vf='scale=1080:1920') if has_m else None
    st = time.time(); n = int(round(t_end * FPS))
    for i, fr in enumerate(reader(src)):
        t = i / FPS
        m = next(mt, None) if mt else None
        wr.write(np.ascontiguousarray(fx.frame(fr, m, t, t_end)))
        if i and i % max(300, n // 4) == 0: print(f'  chữ {i}/{n} · còn ~{(time.time() - st) / i * (n - i):.0f}s', flush=True)
    wr.close()
    print(f'✓ {out} (có chữ, chưa tiếng)')

if __name__ == '__main__':
    main()
