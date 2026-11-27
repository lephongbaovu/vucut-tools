#!/usr/bin/env python3
"""vucut · tự tổng hợp bộ hiệu ứng âm thanh (offline, không bản quyền) theo kiểu video mẫu.
Dùng: python -X utf8 make_sfx.py <thư_mục_ra>      → ghi các file .wav 48 kHz mono
Bộ âm (tên file = tên dùng trong cues.json của sfx_mix.py):
  tick     0.04 s  gõ phím khô       — từng chữ cái của HOOK, từng từ trắng (nhỏ, -14 dB)
  pop      0.12 s  bụp tròn          — từ khoá có chân đỏ bật ra, icon bóng, dấu ?
  whoosh   0.45 s  gió lướt          — vào/ra panel, chữ trượt ngang
  swish    0.20 s  lướt ngắn         — thẻ số liệu, chữ đổi cụm nhanh
  boom     0.90 s  trầm dội          — PUNCH-IN vào đoạn quan trọng, panel đỏ
  hit      0.35 s  đập chắc          — zoom-slam, rung khung, dấu ✕
  glitch   0.32 s  nhiễu số giật     — chuyển cảnh glitch
  riser    1.00 s  dâng dần          — đặt KẾT THÚC đúng lúc vào panel đỏ / câu hỏi lớn (t - 1.0)
  ding     0.70 s  chuông sáng       — số liệu chốt, ý đúng
  count    0.50 s  tích tắc dồn      — số đếm lên
  sub      0.60 s  sub-drop          — câu chốt cuối
  --- v9 · âm THEO CHỦ ĐỀ BĐS (mg_bds tự gắn; vật thật → tiếng thật, người xem "nghe" ra vật) ---
  paper    0.40 s  lật giấy          — sổ mở, thẻ lật, hồ sơ
  stamp    0.45 s  dấu đóng          — con dấu, kết luận pháp lý
  flap     0.70 s  bảng lật số       — bảng giá
  metal    0.90 s  thép va           — cẩu, công trình, dầm đặt xuống
  block    0.14 s  gõ gỗ             — tầng / lô / ô mọc lên (thay pop cho vật thể)
  pen      0.32 s  bút dạ kẻ         — vẽ ranh thửa, kẻ đường, tick
  creak    0.60 s  đòn gỗ kẽo kẹt    — cân nghiêng
  ratchet  0.60 s  kim đồng hồ       — kim đo quét
  air      0.80 s  gió nhẹ dâng      — bản đồ mở rộng, toà nhà mọc
  --- âm CHUYỂN CẢNH theo bộ màu (V.TR('wipe') tự chọn) ---
  scan 0.40 (thep) · thud 0.50 (bazan) · shutter 0.40 (muc) · wash 0.70 (bien) · air (reu) · whoosh (docdo)
"""
import os, sys, wave
import numpy as np
SR = 48000
rng = np.random.default_rng(7)

def t(d): return np.arange(int(SR * d)) / SR
def env(n, a=.003, r=None, curve=4.0):
    x = np.linspace(0, 1, n); e = np.exp(-curve * x) if r is None else np.clip((1 - x) / r, 0, 1)
    k = max(1, int(SR * a)); e[:k] *= np.linspace(0, 1, k); return e
def lp(x, a):  # một cực, a nhỏ = cắt mạnh
    y = np.empty_like(x); s = 0.0
    for i, v in enumerate(x): s += a * (v - s); y[i] = s
    return y
def lp_sweep(x, a0, a1):
    y = np.empty_like(x); s = 0.0; A = np.linspace(a0, a1, len(x))
    for i, v in enumerate(x): s += A[i] * (v - s); y[i] = s
    return y
def norm(x, db=-3): return x / (np.abs(x).max() + 1e-9) * 10 ** (db / 20)

def tick():
    n = t(.04); x = rng.standard_normal(len(n)) * env(len(n), .0005, curve=60)
    x += .6 * np.sin(2 * np.pi * 2400 * n) * env(len(n), .0005, curve=80)
    return norm(x - lp(x, .2), -6)
def pop():
    n = t(.12); f = 900 * np.exp(-n * 38) + 180
    return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(n), .001, curve=30), -4)
def whoosh(d=.45):
    n = t(d); x = rng.standard_normal(len(n)); bell = np.sin(np.pi * np.linspace(0, 1, len(n))) ** 1.6
    a = np.concatenate([np.linspace(.02, .35, len(n) // 2), np.linspace(.35, .04, len(n) - len(n) // 2)])
    y = np.empty_like(x); s = 0.0
    for i, v in enumerate(x): s += a[i] * (v - s); y[i] = s
    return norm(y * bell, -5)
def swish(): return whoosh(.2)
def boom():
    n = t(.9); f = 70 * np.exp(-n * 3) + 38
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(n), .002, curve=4.5)
    x += .5 * lp(rng.standard_normal(len(n)), .03) * env(len(n), .001, curve=18)
    return norm(np.tanh(2.2 * x), -2)
def hit():
    n = t(.35); x = np.sin(2 * np.pi * (110 * np.exp(-n * 20) + 55) * n) * env(len(n), .001, curve=12)
    x += .8 * lp(rng.standard_normal(len(n)), .25) * env(len(n), .0005, curve=40)
    return norm(np.tanh(2.5 * x), -2)
def glitch():
    out = np.zeros(int(SR * .32))
    for k in range(9):
        a = int(rng.uniform(0, .29) * SR); L = int(rng.uniform(.012, .04) * SR)
        f = rng.choice([180, 420, 900, 1600, 3200]); n = np.arange(L) / SR
        seg = np.sign(np.sin(2 * np.pi * f * n)) * .5 + rng.standard_normal(L) * .6
        seg = np.round(seg * 6) / 6                     # nén bit
        out[a:a + L] += seg[:len(out) - a] * rng.uniform(.4, 1)
    return norm(out, -6)
def riser():
    n = t(1.0); x = rng.standard_normal(len(n)); y = lp_sweep(x, .01, .5)
    y += .4 * np.sin(2 * np.pi * np.cumsum(200 + 900 * np.linspace(0, 1, len(n)) ** 2) / SR)
    e = np.linspace(0, 1, len(n)) ** 2.2; e[-int(SR * .015):] *= np.linspace(1, 0, int(SR * .015))
    return norm(y * e, -6)
def ding():
    n = t(.7); x = sum(a * np.sin(2 * np.pi * f * n) for f, a in [(1318, 1), (2637, .4), (3951, .18), (5274, .08)])
    return norm(x * env(len(n), .001, curve=6), -7)
def count():
    out = np.zeros(int(SR * .5)); k = tick() * .7; times = np.cumsum(np.linspace(.07, .03, 12))
    for s in times:
        a = int(s * SR)
        if a + len(k) < len(out): out[a:a + len(k)] += k
    return norm(out, -9)
def sub():
    n = t(.6); f = 90 * np.exp(-n * 6) + 32
    return norm(np.tanh(1.6 * np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(n), .004, curve=4)), -3)

def bp(x, lo, hi): return lp(x, hi) - lp(x, lo)
def lp2(x, a): return lp(lp(x, a), a)
def paper():
    n = t(.4); x = rng.standard_normal(len(n)); x = lp(bp(x, .08, .6), .5)
    am = np.zeros(len(n))
    for _ in range(22):
        a = int(rng.uniform(0, .36) * SR); L = int(rng.uniform(.004, .02) * SR); am[a:a + L] += rng.uniform(.4, 1)
    am = lp(am, .02) + .25 * np.sin(np.pi * np.linspace(0, 1, len(n))) ** 2
    return norm(x * am * env(len(n), .01, curve=3), -7)
def stamp():
    n = t(.45); x = np.sin(2 * np.pi * (95 * np.exp(-n * 30) + 60) * n) * env(len(n), .001, curve=22)
    x += .7 * lp2(bp(rng.standard_normal(len(n)), .02, .25), .25) * env(len(n), .0005, curve=70)
    x += .25 * np.sin(2 * np.pi * 1900 * n) * env(len(n), .0003, curve=120)
    return norm(np.tanh(2 * x), -3)
def _click(f=2800, d=.012, g=1.0):
    n = t(d); return g * (bp(rng.standard_normal(len(n)), .15, .8) + .5 * np.sin(2 * np.pi * f * n)) * env(len(n), .0003, curve=90)
def flap():
    out = np.zeros(int(SR * .7)); ts = np.cumsum(np.concatenate([np.full(10, .035), np.linspace(.04, .08, 5)]))
    for k, s0 in enumerate(ts):
        c = _click(rng.uniform(1800, 2600), .02, 1 if k == len(ts) - 1 else .6); a = int(s0 * SR)
        if a + len(c) < len(out): out[a:a + len(c)] += c
    return norm(out, -8)
def metal():
    n = t(.9); x = .9 * sum(a * np.sin(2 * np.pi * f * n + rng.uniform(0, 6)) * np.exp(-n * dcy) for f, a, dcy in
                       [(523, 1, 5), (1307, .7, 7), (2190, .5, 9), (3420, .35, 12), (4710, .2, 16), (237, .5, 6)])
    x += .9 * bp(rng.standard_normal(len(n)), .1, .7) * env(len(n), .0005, curve=60)
    return norm(x * env(len(n), .001, curve=2.5), -7)
def block():
    n = t(.14); x = (np.sin(2 * np.pi * 690 * n) + .5 * np.sin(2 * np.pi * 1180 * n)) * env(len(n), .0005, curve=38)
    return norm(x + .12 * lp(_click(3000, .14, 1)[:len(n)], .4), -6)
def pen():
    n = t(.32); x = lp(bp(rng.standard_normal(len(n)), .1, .5), .5)
    am = .6 + .4 * np.abs(np.sin(2 * np.pi * 34 * n + 3 * np.sin(2 * np.pi * 5 * n)))
    e = np.minimum(1, n / .03) * np.clip((.32 - n) / .08, 0, 1)
    return norm(x * am * e, -12)
def creak():
    n = t(.6); f = 120 + 35 * np.sin(2 * np.pi * 3 * n) + 20 * rng.standard_normal(len(n)).cumsum() / SR * 40
    saw = 2 * ((np.cumsum(f) / SR) % 1) - 1; x = bp(saw, .02, .2)
    gr = (np.sin(2 * np.pi * 28 * n) > .2).astype(float); x = x * lp(gr, .02)
    return norm(x * np.sin(np.pi * np.linspace(0, 1, len(n))) ** .7, -9)
def ratchet():
    out = np.zeros(int(SR * .6)); g = np.concatenate([np.linspace(.05, .018, 9), np.linspace(.02, .06, 6)]); s0 = 0
    for d in g:
        c = _click(4200, .008, .7); a = int(s0 * SR); s0 += d
        if a + len(c) < len(out): out[a:a + len(c)] += c
    return norm(out, -6)
def air():
    n = t(.8); x = rng.standard_normal(len(n)); y = lp(lp_sweep(x, .01, .1), .08)
    return norm(y * np.sin(np.pi * np.linspace(0, 1, len(n))) ** 2, -9)
def scan():
    n = t(.4); f = 300 + 2100 * np.linspace(0, 1, len(n)) ** 1.5
    x = np.round(np.sin(2 * np.pi * np.cumsum(f) / SR) * 4) / 4 * .5 + .3 * bp(rng.standard_normal(len(n)), .2, .9)
    return norm(x * np.sin(np.pi * np.linspace(0, 1, len(n))) ** 1.4, -12)
def thud():
    n = t(.5); x = lp2(lp_sweep(rng.standard_normal(len(n)), .02, .08), .06) * np.sin(np.pi * np.linspace(0, 1, len(n))) ** 1.5
    x += .6 * np.sin(2 * np.pi * (70 * np.exp(-n * 8) + 40) * n) * env(len(n), .06, curve=7)
    return norm(x, -6)
def shutter():
    out = whoosh(.4) * .5
    for k in range(6):
        c = _click(1500, .015, .7); a = int((.04 + k * .045) * SR); out[a:a + len(c)] += c
    return norm(out, -8)
def wash():
    n = t(.7); x = rng.standard_normal(len(n)); a = .03 + .1 * (.5 + .5 * np.sin(2 * np.pi * 4 * n))
    y = np.empty_like(x); s0 = 0.0
    for i, v in enumerate(x): s0 += a[i] * (v - s0); y[i] = s0
    return norm(lp(y, .1) * np.sin(np.pi * np.linspace(0, 1, len(n))) ** 1.2, -7)

def save(path, x):
    x = np.clip(x, -1, 1); w = wave.open(path, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((x * 32767).astype('<i2').tobytes()); w.close()

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'sfx'; os.makedirs(out, exist_ok=True)
    for name, fn in dict(tick=tick, pop=pop, whoosh=whoosh, swish=swish, boom=boom, hit=hit, glitch=glitch,
                         riser=riser, ding=ding, count=count, sub=sub, paper=paper, stamp=stamp, flap=flap, metal=metal,
                         block=block, pen=pen, creak=creak, ratchet=ratchet, air=air, scan=scan, thud=thud, shutter=shutter, wash=wash).items():
        save(os.path.join(out, name + '.wav'), fn())
    print('xong →', out)
