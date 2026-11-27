"""vucut · tighten.py — bước 2 của tự cắt: dò khoảng lặng THẬT bằng mức âm (ffmpeg silencedetect) trên video đã cắt,
rút mỗi đoạn lặng dài còn ~2×keep giây. Bù cho Whisper (tắt VAD) hay kéo dài mốc từ sang cả chỗ ngừng.
Dùng: python -X utf8 tighten.py cut/cut.mp4 cut/words_cut.json cut2 [--db -38] [--min 0.3] [--keep 0.13]
Ra:   cut2/cut.mp4 · cut2/words_cut.json · cut2/map.json {removed:[[a,b]..] (giây của video VÀO), dur_old, dur_new}
Ánh xạ mốc cũ → mới: t_new = t − Σ(độ dài các đoạn bỏ nằm trước t)  (dùng chung cho timeline, cues, nhạc)."""
import argparse, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from autocut import render, probe_dur

ap = argparse.ArgumentParser()
ap.add_argument('video'); ap.add_argument('words'); ap.add_argument('out')
ap.add_argument('--db', type=float, default=-38); ap.add_argument('--min', type=float, default=.3); ap.add_argument('--keep', type=float, default=.13)
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
log = subprocess.run(['ffmpeg', '-i', a.video, '-af', f'silencedetect=noise={a.db}dB:d={a.min}', '-vn', '-f', 'null', '-'],
                     capture_output=True, text=True).stderr
st = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', log)]
en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', log)]
dur = probe_dur(a.video)
rem = [[round(s + a.keep, 3), round(e - a.keep, 3)] for s, e in zip(st, en) if e - s > a.min and s > .05 and e < dur - .05]
keep, p = [], 0.0
for s, e in rem:
    keep.append([p, s]); p = e
keep.append([p, dur])

def M(t):
    d = 0.0
    for s, e in rem:
        if t >= e: d += e - s
        elif t > s: d += t - s
    return t - d

W = json.load(open(a.words, encoding='utf-8'))
for w in W: w['start'] = round(M(w['start']), 3); w['end'] = round(M(w['end']), 3)
json.dump(W, open(os.path.join(a.out, 'words_cut.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
dn = sum(e - s for s, e in keep)
json.dump({'removed': rem, 'dur_old': round(dur, 3), 'dur_new': round(dn, 3)}, open(os.path.join(a.out, 'map.json'), 'w'), indent=1)
print(f'{len(rem)} khoảng lặng rút gọn, bỏ {dur - dn:.2f} s: {dur:.2f} → {dn:.2f} s')
for s, e in rem: print(f'  bỏ {s:.2f}–{e:.2f} ({e - s:.2f} s)')
render(a.video, keep, os.path.join(a.out, 'cut.mp4'))
