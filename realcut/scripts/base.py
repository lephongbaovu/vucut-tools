"""realcut · tầng A — dựng NỀN sạch: A-roll (cut.mp4) + B-roll + zoom + màu. Không vẽ chữ (chữ ở adsfx.py).
Dùng: python base.py DA [--draft] [--sheet 1.0 | --frames a,b,..]
Đọc DA/edit.json: {"broll":[{t,d,src,in,speed,move,focus_x,xf}], "aroll_zoom":[...], "grade":{"preset":"neutral"}, "end_hold":0}
"""
import argparse, os, time
import numpy as np, cv2
from common import Reader, Writer, load_json, out_size, probe, die
import textfx as T

FPS = 30

class Seq:
    def __init__(self, path, w, h, vf=None, gray=False, t0=0.0, speed=1.0):
        self.path, self.w, self.h, self.vf, self.gray, self.t0, self.speed = path, w, h, vf, gray, t0, speed
        self.r = None; self.idx = -10; self.frame = None

    def _open(self, i):
        if self.r:
            self.r.close()
        vf = self.vf
        if abs(self.speed - 1) > 1e-3:
            vf = (f'setpts=PTS/{self.speed}' + (',' + vf if vf else ''))
        ss = self.t0 + i / FPS * self.speed
        self.r = Reader(self.path, self.w, self.h, ss=ss, vf=vf, fps=FPS, gray=self.gray)
        self.idx = i - 1

    def get(self, i):
        """i = chỉ số khung (FPS) tính từ t0."""
        if self.r is None or i < self.idx or i > self.idx + 45:
            self._open(i)
        while self.idx < i:
            f = self.r.read(); self.idx += 1
            if f is not None:
                self.frame = f
        return self.frame

    def close(self):
        if self.r:
            self.r.close(); self.r = None

# ───────────────────────── chỉnh màu ─────────────────────────

def make_lut(preset='warm', strength=1.0):
    x = np.arange(256, dtype=np.float32) / 255
    if preset == 'neutral':
        y = x - 0.025 * np.sin(2 * np.pi * x)
        r, g, b = y, y, y
    else:
        y = x - 0.035 * np.sin(2 * np.pi * x)           # S nhẹ
        y = 0.035 + 0.95 * y                              # nâng đen kiểu phim, hạ trắng nhẹ
        warm = 1.0 if preset == 'warm' else 1.6           # golden = ấm hơn
        r = np.clip(y ** (1 - 0.03 * warm) + 0.012 * warm, 0, 1)
        g = np.clip(y ** (1 - 0.005 * warm) + 0.004 * warm, 0, 1)
        b = np.clip(y ** (1 + 0.06 * warm) * (1 - 0.025 * warm), 0, 1)
    lut = np.stack([r, g, b], 1)
    lut = x[:, None] + (lut - x[:, None]) * strength
    return np.clip(lut * 255 + 0.5, 0, 255).astype(np.uint8)

def apply_grade(img, lut, sat=1.0):
    out = np.empty_like(img)
    for c in range(3):
        out[..., c] = cv2.LUT(img[..., c], lut[:, c])
    if abs(sat - 1) > 1e-3:
        hsv = cv2.cvtColor(out, cv2.COLOR_RGB2HSV)
        hsv[..., 1] = cv2.convertScaleAbs(hsv[..., 1], alpha=sat)
        out = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    return out

MOVES = {   # (scale đầu, scale cuối, dx đầu, dx cuối, dy đầu, dy cuối) — dx/dy theo phần dư (−1..1)
    'push':  (1.00, 1.10, 0, 0, 0, 0),
    'pull':  (1.10, 1.00, 0, 0, 0, 0),
    'left':  (1.08, 1.08, 0.9, -0.9, 0, 0),
    'right': (1.08, 1.08, -0.9, 0.9, 0, 0),
    'up':    (1.08, 1.08, 0, 0, 0.9, -0.9),
    'down':  (1.08, 1.08, 0, 0, -0.9, 0.9),
    'rise':  (1.06, 1.12, 0, 0, 0.6, -0.6),
    'none':  (1.00, 1.00, 0, 0, 0, 0),
}

class BRoll:
    def __init__(self, b, index, W, H):
        self.b = b; self.W, self.H = W, H
        it = next((x for x in index if x['id'] == b['src'] or os.path.basename(x['file']) == b['src']), None) if index else None
        path = it['file'] if it else b['src']
        if not os.path.exists(path):
            die(f'Không thấy B-roll {b["src"]}')
        self.path = path
        self.is_img = path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))
        self.move = MOVES.get(b.get('move', 'push'), MOVES['push'])
        if b.get('scale'):
            self.move = (b['scale'][0], b['scale'][1]) + self.move[2:]
        smax = max(self.move[0], self.move[1]) + (0.04 if b.get('move') in ('left', 'right', 'up', 'down') else 0)
        self.bw, self.bh = int(W * smax) // 2 * 2, int(H * smax) // 2 * 2
        fx = b.get('focus_x', 0.5)
        if self.is_img:
            im = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)
            self.img = self._cover(im, fx)
            self.seq = None
        else:
            info = probe(path)
            vf = self._cover_vf(info['w'], info['h'], fx)
            self.seq = Seq(path, self.bw, self.bh, vf=vf, t0=b.get('in', 0.0), speed=b.get('speed', 1.0))
            self.src_dur = info['dur']

    def _cover_vf(self, w, h, fx):
        tr = self.bw / self.bh
        if w / h > tr:      # nguồn rộng hơn → cắt ngang theo focus_x
            cw = int(h * tr) // 2 * 2
            return f'crop={cw}:{h // 2 * 2}:{int((w - cw) * fx)}:0'
        ch = int(w / tr) // 2 * 2
        return f'crop={w // 2 * 2}:{ch}:0:{int((h - ch) / 2)}'

    def _cover(self, im, fx):
        h, w = im.shape[:2]; tr = self.bw / self.bh
        if w / h > tr:
            cw = int(h * tr); x = int((w - cw) * fx); im = im[:, x:x + cw]
        else:
            ch = int(w / tr); y = (h - ch) // 2; im = im[y:y + ch]
        return cv2.resize(im, (self.bw, self.bh), interpolation=cv2.INTER_AREA)

    def frame(self, t):
        b = self.b; i = int(round((t - b['t']) * FPS))
        src = self.img if self.is_img else self.seq.get(max(0, i))
        if src is None:
            return None
        p = T.clamp01((t - b['t']) / max(b['d'], 1e-3))
        p = p if b.get('ease', 'linear') == 'linear' else T.ease_in_out(p)
        s0, s1, dx0, dx1, dy0, dy1 = self.move
        s = s0 + (s1 - s0) * p
        # vùng nhìn (W/s × H/s) trong ảnh nguồn bw×bh (bw = W·smax)
        k = self.bw / (self.W * s)            # 1 px ra = k px nguồn
        vw, vh = self.W * k, self.H * k
        slack_x, slack_y = (self.bw - vw) / 2, (self.bh - vh) / 2
        cx = self.bw / 2 + (dx0 + (dx1 - dx0) * p) * slack_x
        cy = self.bh / 2 + (dy0 + (dy1 - dy0) * p) * slack_y
        M = np.array([[1 / k, 0, self.W / 2 - cx / k], [0, 1 / k, self.H / 2 - cy / k]], np.float32)
        return cv2.warpAffine(src, M, (self.W, self.H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

    def close(self):
        if self.seq:
            self.seq.close()

class Comp:
    def __init__(self, da, draft=False):
        self.da = da
        E = load_json(os.path.join(da, 'edit.json'))
        if E is None:
            die('Chưa có DA/edit.json (xem reference/schema.md)')
        self.E = E
        self.W, self.H = out_size(E.get('ratio', '9:16'), draft)
        self.aroll = os.path.join(da, 'cut.mp4')
        self.dur = probe(self.aroll)['dur']
        self.total = self.dur + E.get('end_hold', 0.0)
        self.A = Seq(self.aroll, self.W, self.H)
        hj = load_json(os.path.join(da, 'head.json'))
        self.heads = hj['head'] if hj else None
        g = E.get('grade', {})
        self.lut = make_lut(g.get('preset', 'neutral'), g.get('strength', 1.0))
        self.sat = g.get('sat', 1.03)
        self.blut = make_lut(g.get('preset', 'neutral'), g.get('broll_strength', g.get('strength', 1.0)))
        idx = load_json(os.path.join(da, 'broll', 'index.json'), {'items': []})['items']
        self.bcfg = sorted(E.get('broll', []), key=lambda b: b['t'])
        self.bidx = idx; self.live = {}
        self.zooms = E.get('aroll_zoom', [])

    def zoom_at(self, t):
        s = 1.0
        for z in self.zooms:
            if z['t'] <= t <= z['t'] + z['d']:
                if z.get('type') == 'punch':
                    s = max(s, z.get('scale', 1.12))
                else:
                    p = T.ease_in_out((t - z['t']) / z['d'])
                    s *= z.get('from', 1.0) + (z.get('to', 1.06) - z.get('from', 1.0)) * p
        return s

    def frame(self, t):
        W, H = self.W, self.H
        i = int(round(t * FPS)); ia = min(i, int(self.dur * FPS) - 1)
        a = self.A.get(ia)
        if a is None:
            a = np.zeros((H, W, 3), np.uint8)
        s = self.zoom_at(t)
        if s > 1.001:
            hd = self.heads[min(max(ia, 0), len(self.heads) - 1)] if self.heads else None
            cx = (hd[0] if hd else 0.5) * W; cy = (hd[2] if hd else 0.35) * H
            M = np.array([[s, 0, cx * (1 - s)], [0, s, cy * (1 - s)]], np.float32)
            a = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        img = apply_grade(a, self.lut, self.sat)
        for k, b in enumerate(self.bcfg):
            xf = b.get('xf', 0.0)
            if not (b['t'] - xf <= t <= b['t'] + b['d'] + xf):
                if k in self.live and (t > b['t'] + b['d'] + xf + 0.2):
                    self.live.pop(k).close()
                continue
            if k not in self.live:
                self.live[k] = BRoll(b, self.bidx, W, H)
            bf = self.live[k].frame(t)
            if bf is None:
                continue
            bf = apply_grade(bf, self.blut, self.sat)
            if xf > 0:
                w_in = T.clamp01((t - (b['t'] - xf)) / (2 * xf)); w_out = T.clamp01(((b['t'] + b['d'] + xf) - t) / (2 * xf))
                wgt = T.ease_in_out(min(w_in, w_out))
            else:
                wgt = 1.0 if b['t'] <= t < b['t'] + b['d'] else 0.0
            if wgt >= 0.999:
                img = bf
            elif wgt > 0.001:
                img = cv2.addWeighted(img, 1 - wgt, bf, wgt, 0)
        return img

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('da'); ap.add_argument('--draft', action='store_true')
    ap.add_argument('--frames', default=None); ap.add_argument('--sheet', type=float, default=None)
    a = ap.parse_args()
    C = Comp(a.da, draft=a.draft or bool(a.frames or a.sheet))
    if a.frames or a.sheet:
        qc = os.path.join(a.da, 'qc'); os.makedirs(qc, exist_ok=True)
        ts = [float(x) for x in a.frames.split(',')] if a.frames else list(np.arange(0.2, C.total, a.sheet))
        ims = [C.frame(t) for t in ts]
        for t, f in zip(ts, ims):
            cv2.putText(f, f'{t:.1f}s', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 230, 120), 2)
        cols, tw = 6, 270; th = int(tw * C.H / C.W)
        rows = [ims[i:i + cols] for i in range(0, len(ims), cols)]
        sheet = np.full((th * len(rows), tw * cols, 3), 20, np.uint8)
        for r, row in enumerate(rows):
            for c_, im in enumerate(row):
                sheet[r * th:(r + 1) * th, c_ * tw:(c_ + 1) * tw] = cv2.resize(im, (tw, th), interpolation=cv2.INTER_AREA)
        sp = os.path.join(qc, 'base_sheet.jpg'); cv2.imwrite(sp, sheet[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 85])
        print(f'✓ bảng ảnh nền: {sp}'); return
    out = os.path.join(a.da, 'base_draft.mp4' if a.draft else 'base.mp4')
    wr = Writer(out, C.W, C.H, FPS, crf=23 if a.draft else 15, preset='veryfast' if a.draft else 'medium')
    n = int(C.total * FPS); st = time.time()
    for i in range(n):
        wr.write(C.frame(i / FPS))
        if i and i % max(300, n // 4) == 0:
            print(f'  nền {i}/{n} khung · còn ~{(time.time() - st) / i * (n - i):.0f}s', flush=True)
    wr.close()
    print(f'✓ {out} · {n / FPS:.1f}s (nền, chưa chữ, chưa tiếng)')

if __name__ == '__main__':
    main()
