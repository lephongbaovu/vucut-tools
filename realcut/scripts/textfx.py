"""realcut · dựng chữ thành ảnh RGBA (numpy) + ghép lớp. Mọi chữ tiếng Việt chuẩn hoá NFC.
Sprite = dict(rgb=float32(h,w,3), a=float32(h,w), base=int  # baseline trong ảnh
              ,w,h)
"""
import os, sys, unicodedata
from functools import lru_cache
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import font_path, PALETTE

@lru_cache(maxsize=64)
def F(key, size):
    return ImageFont.truetype(font_path(key), int(size))

def nfc(s):
    return unicodedata.normalize('NFC', s)

def text_width(text, key, size, tracking=0.0):
    f = F(key, size); text = nfc(text)
    if not tracking:
        return f.getlength(text)
    return sum(f.getlength(c) for c in text) + tracking * size * max(0, len(text) - 1)

def fit_size(text, key, size, max_w, tracking=0.0, min_size=10):
    s = size
    while s > min_size and text_width(text, key, s, tracking) > max_w:
        s *= 0.95
    return s

def _mask(text, key, size, tracking=0.0):
    f = F(key, size); text = nfc(text)
    asc, desc = f.getmetrics()
    pad = int(size * 0.45)
    w = int(text_width(text, key, size, tracking)) + 2 * pad
    h = asc + desc + 2 * pad
    im = Image.new('L', (max(w, 1), max(h, 1)), 0)
    d = ImageDraw.Draw(im)
    base = pad + asc
    if not tracking:
        d.text((pad, base), text, font=f, fill=255, anchor='ls')
    else:
        x = pad
        for c in text:
            d.text((x, base), c, font=f, fill=255, anchor='ls')
            x += f.getlength(c) + tracking * size
    a = np.asarray(im, np.float32) / 255.0
    # cắt bớt lề trống nhưng giữ baseline
    rows = np.where(a.max(1) > 0)[0]; cols = np.where(a.max(0) > 0)[0]
    if len(rows) == 0:
        return a[:2, :2], 1, pad
    y0, y1 = max(0, rows[0] - 2), min(a.shape[0], rows[-1] + 3)
    x0, x1 = max(0, cols[0] - 2), min(a.shape[1], cols[-1] + 3)
    return a[y0:y1, x0:x1], base - y0, pad - x0

def gradient(h, w, top, mid, bot):
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    top, mid, bot = [np.array(c, np.float32) for c in (top, mid, bot)]
    g = np.where(t < 0.5, top + (mid - top) * (t / 0.5), mid + (bot - mid) * ((t - 0.5) / 0.5))
    return np.broadcast_to(g[:, None, :], (h, w, 3)).copy()

def glitter_gold(h, w, seed=7, tw=0.0):
    """vàng nhũ: nền vàng ấm + hạt nhũ lấp lánh (tw = pha lấp lánh)"""
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    top, mid, bot = np.array((255, 247, 214), np.float32), np.array((246, 196, 72), np.float32), np.array((178, 108, 24), np.float32)
    g = np.where(t < 0.5, top + (mid - top) * (t / 0.5), mid + (bot - mid) * ((t - 0.5) / 0.5))
    g = np.broadcast_to(g[:, None, :], (h, w, 3)).copy()
    rng = np.random.default_rng(seed + h * 7 + w)
    grain = rng.normal(0, 1, (h, w)).astype(np.float32)
    g += (grain * 10)[..., None]
    sp = rng.random((h, w)).astype(np.float32)
    ph = rng.random((h, w)).astype(np.float32) * 6.283
    tw_k = 0.5 + 0.5 * np.sin(ph + tw * 9.0)
    spark = ((sp > 0.965) * (0.55 + 0.45 * tw_k)).astype(np.float32)
    import cv2 as _cv
    spark = _cv.GaussianBlur(spark, (0, 0), 0.8) * 2.2
    g += spark[..., None] * np.array((90, 80, 55), np.float32)
    return np.clip(g, 0, 255)

def sprite(text, key, size, color='cream', tracking=0.0, shadow=0.0, glow=0.0):
    """color: tên trong PALETTE, (r,g,b) hoặc 'gold' (gradient vàng đồng)."""
    a, base, xoff = _mask(text, key, size, tracking)
    h, w = a.shape
    if color == 'gold':
        rgb = glitter_gold(h, w)
    elif color == 'gold_soft':
        rgb = gradient(h, w, PALETTE['cream'], PALETTE['gold_hi'], PALETTE['gold'])
    else:
        c = PALETTE.get(color, color) if isinstance(color, str) else color
        rgb = np.empty((h, w, 3), np.float32); rgb[:] = c
    sp = dict(rgb=rgb, a=a, base=base, w=w, h=h, xoff=xoff)
    if shadow > 0:
        sp = add_shadow(sp, shadow, size)
    return sp

def add_shadow(sp, strength, size, color=(20, 14, 10)):
    """Bóng mềm phía dưới chữ — đọc được trên nền sáng mà không thành viền cứng."""
    r = max(2, int(size * 0.09)); dy = max(1, int(size * 0.04))
    h, w = sp['h'] + 2 * r + dy, sp['w'] + 2 * r
    sa = np.zeros((h, w), np.float32)
    sa[r + dy:r + dy + sp['h'], r:r + sp['w']] = sp['a']
    dk = max(1, int(size * 0.035)) * 2 + 1          # nở nét trước khi làm mờ → chữ mảnh vẫn có bóng đủ đậm
    sa = cv2.dilate(sa, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dk, dk)))
    k = r * 2 + 1
    sa = np.clip(cv2.GaussianBlur(sa, (k, k), r / 1.6) * strength * 1.15, 0, 0.85)
    ta = np.zeros((h, w), np.float32); ta[r:r + sp['h'], r:r + sp['w']] = sp['a']
    trgb = np.zeros((h, w, 3), np.float32); trgb[r:r + sp['h'], r:r + sp['w']] = sp['rgb']
    out_a = ta + sa * (1 - ta)
    srgb = np.empty((h, w, 3), np.float32); srgb[:] = color
    out_rgb = (trgb * ta[..., None] + srgb * (sa * (1 - ta))[..., None]) / np.maximum(out_a[..., None], 1e-4)
    return dict(rgb=out_rgb, a=out_a, base=sp['base'] + r, w=w, h=h, xoff=sp.get('xoff', 0) + r)

def scaled(sp, s):
    if abs(s - 1) < 1e-3:
        return sp
    w, h = max(1, int(sp['w'] * s)), max(1, int(sp['h'] * s))
    return dict(rgb=cv2.resize(sp['rgb'], (w, h), interpolation=cv2.INTER_LINEAR),
                a=cv2.resize(sp['a'], (w, h), interpolation=cv2.INTER_LINEAR),
                base=int(sp['base'] * s), w=w, h=h, xoff=int(sp.get('xoff', 0) * s))

def over(dst, sp, x, y, opacity=1.0, amask=None):
    """Ghép sprite lên dst (uint8 HxWx3) tại góc trên-trái (x,y). amask: alpha bổ sung cùng cỡ sprite."""
    if opacity <= 0.003:
        return
    H, W = dst.shape[:2]
    x, y = int(round(x)), int(round(y))
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + sp['w']), min(H, y + sp['h'])
    if x1 <= x0 or y1 <= y0:
        return
    sx0, sy0 = x0 - x, y0 - y
    a = sp['a'][sy0:sy0 + (y1 - y0), sx0:sx0 + (x1 - x0)] * opacity
    if amask is not None:
        a = a * amask[sy0:sy0 + (y1 - y0), sx0:sx0 + (x1 - x0)]
    rgb = sp['rgb'][sy0:sy0 + (y1 - y0), sx0:sx0 + (x1 - x0)]
    roi = dst[y0:y1, x0:x1].astype(np.float32)
    roi += (rgb - roi) * a[..., None]
    dst[y0:y1, x0:x1] = np.clip(roi, 0, 255).astype(np.uint8)

def rect(w, h, color, alpha, radius=0):
    a = np.full((h, w), alpha, np.float32)
    if radius:
        m = np.zeros((h, w), np.uint8)
        cv2.rectangle(m, (radius, 0), (w - radius - 1, h - 1), 255, -1)
        cv2.rectangle(m, (0, radius), (w - 1, h - radius - 1), 255, -1)
        for cx, cy in ((radius, radius), (w - radius - 1, radius), (radius, h - radius - 1), (w - radius - 1, h - radius - 1)):
            cv2.circle(m, (cx, cy), radius, 255, -1, lineType=cv2.LINE_AA)
        a = a * (m.astype(np.float32) / 255)
    rgb = np.empty((h, w, 3), np.float32); rgb[:] = PALETTE.get(color, color) if isinstance(color, str) else color
    return dict(rgb=rgb, a=a, base=0, w=w, h=h, xoff=0)

def glass(dst, x, y, w, h, tint=(30, 24, 19), alpha=0.42, blur=0.03, radius=18, opacity=1.0):
    """Thẻ kính mờ ấm: làm mờ vùng nền rồi phủ màu nâu trong suốt."""
    H, W = dst.shape[:2]
    x, y, w, h = int(x), int(y), int(w), int(h)
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0 or opacity <= 0.003:
        return
    k = max(3, int(W * blur) | 1)
    roi = dst[y0:y1, x0:x1]
    bl = cv2.GaussianBlur(roi, (k, k), 0)
    r = rect(x1 - x0, y1 - y0, tint, alpha, radius)
    mixed = bl.astype(np.float32); mixed += (r['rgb'] - mixed) * r['a'][..., None]
    m = rect(x1 - x0, y1 - y0, (0, 0, 0), 1.0, radius)['a'] * opacity
    out = roi.astype(np.float32); out += (mixed - out) * m[..., None]
    dst[y0:y1, x0:x1] = out.astype(np.uint8)

def hline(dst, x, y, length, thick=2, color='gold', opacity=1.0):
    if length < 1:
        return
    sp = rect(int(length), max(1, int(thick)), color, 1.0)
    over(dst, sp, x, y, opacity)

def pin_icon(size, color='gold'):
    """Ghim vị trí vẽ tay (giọt nước + chấm) — RGBA sprite."""
    s = int(size); m = np.zeros((s * 4, s * 4), np.uint8); S = s * 4
    cx, cy, r = S // 2, int(S * 0.38), int(S * 0.3)
    cv2.circle(m, (cx, cy), r, 255, -1, cv2.LINE_AA)
    pts = np.array([[cx - int(r * 0.86), cy + int(r * 0.5)], [cx + int(r * 0.86), cy + int(r * 0.5)], [cx, int(S * 0.97)]], np.int32)
    cv2.fillConvexPoly(m, pts, 255, cv2.LINE_AA)
    cv2.circle(m, (cx, cy), int(r * 0.42), 0, -1, cv2.LINE_AA)
    a = cv2.resize(m, (s, s), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    rgb = gradient(s, s, PALETTE['gold_hi'], PALETTE['gold'], PALETTE['gold_lo']) if color == 'gold' else np.full((s, s, 3), PALETTE.get(color, color), np.float32)
    return dict(rgb=rgb, a=a, base=s, w=s, h=s, xoff=0)

# ── easing ──
def clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x

def ease_out(x):
    x = clamp01(x); return 1 - (1 - x) ** 3

def ease_in_out(x):
    x = clamp01(x); return 0.5 - 0.5 * np.cos(np.pi * x)

def env(t, t0, t1, fin=0.35, fout=0.3):
    """Độ hiện 0..1 của phần tử sống trong [t0,t1] (vào/ra mềm)."""
    if t < t0 or t > t1:
        return 0.0
    return min(ease_out((t - t0) / max(fin, 1e-3)), ease_out((t1 - t) / max(fout, 1e-3)))
