"""realcut · tầng C — âm thanh: giọng (lọc + nén) + nhạc năng lượng (né giọng, drop trùng câu giá) + SFX thưa → loudnorm −14 LUFS.
  python mix.py DA [--video DA/fx.mp4] [--out DA/final.mp4]
Cấu hình trong ads.json → "audio" (reference/schema.md). Thiếu file SFX → tự tổng hợp whoosh/hit/shimmer (không bản quyền).
"""
import argparse, os, subprocess, wave
import numpy as np
from common import load_json, probe, die

SR = 48000

def decode(path, sr=22050):
    b = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(sr), '-f', 's16le', '-'], capture_output=True).stdout
    return np.frombuffer(b, np.int16).astype(np.float32) / 32768, sr

def peak_time(path):
    """giây đỉnh năng lượng của SFX — để đỉnh rơi đúng mốc."""
    x, sr = decode(path)
    if len(x) == 0: return 0.0
    hop = sr // 100
    env = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, mode='same'))
    return float(np.argmax(env)) / sr

def write_wav(path, x, sr=SR):
    x = np.clip(x, -1, 1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((x * 32767).astype(np.int16).tobytes())

def synth(kind, path):
    """SFX tổng hợp: whoosh (nhiễu quét), hit (boom trầm), shimmer (lấp lánh cao)."""
    rng = np.random.default_rng(7)
    if kind == 'whoosh':
        n = int(SR * 0.7); t = np.arange(n) / SR; x = rng.normal(0, 1, n)
        out = np.zeros(n); y = 0.0
        for i in range(n):                       # lọc thông thấp quét lên rồi xuống
            f = 0.02 + 0.25 * np.sin(np.pi * t[i] / 0.7) ** 2
            y += f * (x[i] - y); out[i] = y
        out *= np.sin(np.pi * t / 0.7) ** 2 * 1.6
    elif kind == 'hit':
        n = int(SR * 1.2); t = np.arange(n) / SR
        out = np.sin(2 * np.pi * (55 + 40 * np.exp(-t * 8)) * t) * np.exp(-t * 3.2) * 0.9
        out += rng.normal(0, 1, n) * np.exp(-t * 40) * 0.25
    else:  # shimmer
        n = int(SR * 1.0); t = np.arange(n) / SR; out = np.zeros(n)
        for f in (2637, 3136, 3951, 4699):
            out += np.sin(2 * np.pi * f * t + rng.random() * 6) * np.exp(-((t - 0.25) / 0.22) ** 2)
        out *= 0.18
    write_wav(path, out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('da'); ap.add_argument('--video'); ap.add_argument('--out')
    a = ap.parse_args()
    A = load_json(os.path.join(a.da, 'ads.json'), {}); cfg = A.get('audio', {})
    vid = a.video or os.path.join(a.da, 'fx.mp4')
    if not os.path.exists(vid): die(f'Không thấy {vid} — chạy `fx` trước')
    out = a.out or os.path.join(a.da, 'final.mp4')
    dur = probe(vid)['dur']
    voice = cfg.get('voice', os.path.join(a.da, 'cut.mp4'))
    sfxd = os.path.join(a.da, 'sfx_synth'); os.makedirs(sfxd, exist_ok=True)
    lib = dict(cfg.get('sfx_lib', {}))
    for k in ('whoosh', 'hit', 'shimmer'):
        if not lib.get(k) or not os.path.exists(lib[k]):
            p = os.path.join(sfxd, k + '.wav')
            if not os.path.exists(p): synth(k, p)
            lib[k] = p
    # sự kiện SFX: tự động theo cấu trúc + danh sách tay
    ev = []
    if cfg.get('sfx_auto', True):
        for t, _ in A.get('transitions', []): ev.append(('whoosh', t, -14))
        h = A.get('hook')
        if h: ev.append(('hit', h['price_t'], -6))
        o = A.get('offer')
        if o: ev.append(('shimmer', o['t0'] + 0.35, -14))
        if A.get('end'): ev.append(('hit', A['end']['t'] + 0.2, -9))
    for e in cfg.get('sfx', []):
        ev.append((e['file'], e['t'], e.get('db', -12)))
    ev.sort(key=lambda e: e[1])
    keep, last = [], -9                       # thưa: ≥ 2.5 s giữa 2 SFX (trừ hit)
    for e in ev:
        if e[0] == 'hit' or e[1] - last >= 2.5:
            keep.append(e); last = e[1]
    inputs = ['-i', vid, '-i', voice]
    fc = ['[1:a]highpass=f=80,acompressor=threshold=-20dB:ratio=3:attack=5:release=120:makeup=2,'
          'equalizer=f=3000:t=q:w=1.2:g=2,aresample=48000,apad,asplit=2[vo][vsc]']
    mix = ['[vo]']
    if cfg.get('music'):
        mi = cfg.get('music_in', 0.0)
        if 'drop' in cfg:                     # {"track": giây drop trong bài, "video": giây cần drop}
            mi = cfg['drop']['track'] - cfg['drop']['video']
        inputs += ['-ss', f'{max(0, mi):.3f}', '-i', cfg['music']]
        g = cfg.get('music_gain', 0.5); endt = A.get('end', {}).get('t', dur)
        vol = f"if(lt(t,{endt}),{g},{g}+0.30*min(1,(t-{endt})/0.8))"
        fc.append(f"[2:a]atrim=0:{dur:.2f},asetpts=PTS-STARTPTS,aresample=48000,volume='{vol}':eval=frame,"
                  f"afade=t=in:d=0.25,afade=t=out:st={dur - 1.6:.2f}:d=1.6[mu]")
        fc.append('[mu][vsc]sidechaincompress=threshold=0.05:ratio=3.5:attack=20:release=350:makeup=1[mud]')
        mix.append('[mud]')
    n0 = 3 if cfg.get('music') else 2
    labels = []
    for i, (f, t, db) in enumerate(keep):
        path = lib.get(f, f)
        if not os.path.exists(path): print('  ⚠ bỏ SFX thiếu file:', path); continue
        inputs += ['-i', path]
        st = max(0.0, t - peak_time(path)); ms = int(st * 1000)
        fc.append(f'[{n0 + len(labels)}:a]aresample=48000,volume={db}dB,adelay={ms}|{ms}[e{len(labels)}]')
        labels.append(f'[e{len(labels)}]')
    if labels:
        fc.append(''.join(labels) + f'amix=inputs={len(labels)}:normalize=0:dropout_transition=0[sfx]'); mix.append('[sfx]')
    lufs = cfg.get('lufs', -14)
    fc.append(''.join(mix) + f'amix=inputs={len(mix)}:normalize=0:duration=first,loudnorm=I={lufs}:TP=-1.2:LRA=9,aresample=48000[aout]')
    cmd = ['ffmpeg', '-v', 'error', '-y'] + inputs + ['-filter_complex', ';'.join(fc), '-map', '0:v', '-map', '[aout]',
           '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-movflags', '+faststart', '-t', f'{dur:.2f}', out]
    subprocess.run(cmd, check=True)
    print(f'✓ {out} · {len(labels)} SFX · {"có nhạc" if cfg.get("music") else "KHÔNG nhạc (thêm audio.music)"}')

if __name__ == '__main__':
    main()
