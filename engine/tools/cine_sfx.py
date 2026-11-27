"""vucut-tools v6 · cine_sfx.py — python cine_sfx.py $DA/sfx : tổng hợp 8 âm điện ảnh · python cine_sfx.py --layer $DA : SAU vucut.py audio, trộn lớp điện ảnh
impact reverse braam tape heart shimmer camera rumble"""
import sys, os, wave, numpy as np
from scipy.signal import fftconvolve
SR = 48000; R = np.random.default_rng(11)
def T(d): return np.arange(int(SR * d)) / SR
def lp(x, a):
    y = np.empty_like(x); s = 0.0
    for i, v in enumerate(x): s += a * (v - s); y[i] = s
    return y
def nz(x, db=-3): return x / (np.abs(x).max() + 1e-9) * 10 ** (db / 20)
def verb(x, d=.9, mix=.35):
    n = int(SR * d); ir = R.standard_normal(n) * np.exp(-np.linspace(0, 7, n)); ir = lp(ir, .25)
    y = np.zeros(len(x) + n); c = fftconvolve(x, ir); y[:min(len(c), len(y))] = c[:len(y)]; return np.concatenate([x, np.zeros(n)]) * (1 - mix) + nz(y, -6) * mix
def impact():
    n = T(1.6); f = 95 * np.exp(-n * 3) + 38
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-n * 2.6)
    crack = lp(R.standard_normal(len(n)), .35) * np.exp(-n * 30)
    return nz(verb(body + .5 * crack, 1.2, .3), -2)
def reverse():
    n = T(.7); x = lp(R.standard_normal(len(n)), .08) + .4 * np.sin(2 * np.pi * 220 * n)
    return nz(verb(x * np.exp(-n * 5), .5, .5)[::-1][-int(SR * .75):], -5)
def braam():
    n = T(1.8); x = sum(np.sign(np.sin(2 * np.pi * f * n + p)) for f, p in ((55, 0), (55.6, 1), (82.4, 2), (110.3, .5)))
    e = np.minimum(1, n / .05) * np.exp(-n * 1.4); return nz(verb(lp(x, .05) * e, 1.0, .35), -3)
def tape():
    n = T(.6); f = 330 * (1 - n / .6) ** 2 + 20
    x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * (1 - n / .6); return nz(lp(x, .12), -6)
def heart():
    def th(d): m = T(d); return np.sin(2 * np.pi * (60 * np.exp(-m * 9) + 40) * m) * np.exp(-m * 16)
    a = th(.25); s = np.zeros(int(SR * .9)); s[:len(a)] += a; s[int(SR * .28):int(SR * .28) + len(a)] += .7 * a; return nz(s, -3)
def shimmer():
    n = T(1.2); x = sum(np.sin(2 * np.pi * f * n) * np.exp(-n * k) for f, k in ((2093, 3), (2637, 3.5), (3136, 4), (4186, 5)))
    return nz(verb(x * (1 + .3 * np.sin(2 * np.pi * 9 * n)) * np.minimum(1, n / .08), .8, .4), -10)
def camera():
    def cl(d, a): m = T(d); return lp(R.standard_normal(len(m)), a) * np.exp(-m * 120)
    s = np.zeros(int(SR * .2)); c1 = cl(.05, .6); c2 = cl(.06, .4); s[:len(c1)] += c1; s[int(SR * .09):int(SR * .09) + len(c2)] += .8 * c2; return nz(s, -6)
def rumble():
    n = T(2.0); x = lp(lp(R.standard_normal(len(n)), .01), .02) * np.sin(np.pi * n / 2.0); return nz(x, -6)
def save(p, x):
    x = np.clip(x, -1, 1); w = wave.open(p, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((x * 32767).astype('<i2').tobytes()); w.close()
DB = dict(impact=-9, reverse=-14, braam=-11, tape=-12, heart=-10, shimmer=-15, camera=-13, rumble=-15)
def layer(da):
    import json, shutil, subprocess
    j = lambda *x: os.path.join(da, *x); cues = json.load(open(j('cine_cues.json')))
    base = j('final_audio_base.m4a')
    if not os.path.exists(base): shutil.copy(j('final_audio.m4a'), base)
    if not cues: shutil.copy(base, j('final_audio.m4a')); print('không có âm điện ảnh'); return
    ins, fc = ['-i', base], []
    for k, c in enumerate(cues):
        ins += ['-i', j('sfx', c['s'] + '.wav')]; ms = max(0, int(c['t'] * 1000))
        fc.append(f"[{k + 1}:a]aresample=48000,volume={DB.get(c['s'], -14)}dB,adelay={ms}|{ms},pan=stereo|c0=c0|c1=c0[c{k}]")
    fc.append('[0:a]' + ''.join(f'[c{k}]' for k in range(len(cues))) + f'amix=inputs={len(cues) + 1}:normalize=0:duration=first,alimiter=limit=0.95,loudnorm=I=-14:TP=-1.5:LRA=11[o]')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *ins, '-filter_complex', ';'.join(fc), '-map', '[o]', '-ar', '48000', '-c:a', 'aac', '-b:a', '256k', j('final_audio.m4a')], check=True)
    print(f'xong → lớp điện ảnh {len(cues)} âm:', ', '.join(f"{c['s']}@{c['t']}" for c in cues))
if __name__ == '__main__':
    if sys.argv[1] == '--layer': layer(sys.argv[2]); sys.exit()
    d = sys.argv[1]; os.makedirs(d, exist_ok=True)
    for k, fn in dict(impact=impact, reverse=reverse, braam=braam, tape=tape, heart=heart, shimmer=shimmer, camera=camera, rumble=rumble).items():
        save(os.path.join(d, k + '.wav'), fn())
    print('xong → 8 âm điện ảnh trong', d)
