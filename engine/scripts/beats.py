#!/usr/bin/env python3
"""vucut · beats.py — BẢNG NHỊP: chấm từng câu theo (1) cách người nói THỂ HIỆN và (2) VAI của câu → gợi ý mặt / hình.
Dùng: python -X utf8 beats.py <video> <words.json> <ra.json>      (vucut.py beats DA tự gọi, giây = cut/cut.mp4)

Năng lượng thể hiện (NL, 1–5) — so trong CHÍNH video này (không so giữa các video):
  độ to trung bình · độ lên xuống của giọng (cao độ, bán cung) · đỉnh nhấn · tốc độ nói · khoảng lặng chủ ý trước câu.
  NL cao = câu nói có lửa → giữ MẶT dù câu nhiều số. NL thấp = câu đuối/đọc → PHỦ HÌNH dù là câu quan điểm.
Vai câu (từ lời): TIN (quan điểm, khuyên, hỏi) · HIỂU (số, năm, %, so sánh) · THẤY (địa danh, công trình, tuyến) · LIỆT KÊ (thứ nhất/thứ hai…) · CẢM (câu chốt, nhấn mạnh) · KỂ (còn lại).
Chỉ là GỢI Ý — Claude quyết cuối cùng trong SHOTBOOK và ghi lý do khi làm khác."""
import argparse, json, os, re, subprocess, unicodedata
import numpy as np

VC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser(); ap.add_argument('video'); ap.add_argument('words'); ap.add_argument('out')
ap.add_argument('--gap', type=float, default=.55, help='lặng ≥ gap giây cũng tách câu')
a = ap.parse_args()

W = json.load(open(a.words, encoding='utf-8'))
W = W['words'] if isinstance(W, dict) else W
W = [w for w in W if str(w.get('word', '')).strip()]
SR = 16000
pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', a.video, '-vn', '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'],
                     capture_output=True, check=True).stdout
A = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768

# ---- tách câu: dấu câu cuối từ, hoặc lặng dài, hoặc câu quá dài (> 22 từ)
S, cur = [], []
for k, w in enumerate(W):
    cur.append(w)
    end = re.search(r'[.?!…]$', w['word'].strip())
    gap = (W[k + 1]['start'] - w['end']) if k + 1 < len(W) else 9
    if end or gap >= a.gap or len(cur) >= 22:
        S.append(cur); cur = []
if cur: S.append(cur)

def f0(seg):
    """cao độ từng khung 40 ms bằng tự tương quan (80–400 Hz); None nếu không có tiếng nói hữu thanh"""
    out = []; n = int(.04 * SR)
    for i in range(0, len(seg) - n, n):
        x = seg[i:i + n] - seg[i:i + n].mean()
        if np.sqrt((x * x).mean()) < .01: continue
        c = np.correlate(x, x, 'full')[n - 1:]
        lo, hi = SR // 400, SR // 80
        if hi >= len(c): continue
        p = lo + int(np.argmax(c[lo:hi]))
        if c[p] > .3 * c[0]: out.append(SR / p)
    return out

rows = []
for k, s in enumerate(S):
    t0, t1 = s[0]['start'], s[-1]['end']
    seg = A[int(t0 * SR):int(t1 * SR)]
    if len(seg) < SR * .2: seg = A[int(t0 * SR):int(t0 * SR) + int(SR * .2)]
    fr = seg[:len(seg) // 400 * 400].reshape(-1, 400) if len(seg) >= 400 else seg.reshape(1, -1)
    rms = np.sqrt((fr ** 2).mean(1) + 1e-9); db = 20 * np.log10(rms)
    voiced = db[db > db.max() - 30]
    p = f0(seg); st = 12 * np.log2(np.array(p) / np.median(p)) if len(p) >= 4 else np.zeros(1)
    prev = S[k - 1][-1]['end'] if k else t0
    txt = ' '.join(w['word'].strip() for w in s)
    rows.append(dict(t0=round(t0, 2), t1=round(t1, 2), text=txt,
                     loud=float(voiced.mean()) if len(voiced) else -60, peak=float(np.percentile(db, 95)),
                     pitch=float(np.std(st)), rate=len(s) / max(.3, t1 - t0), pause=round(max(0, t0 - prev), 2)))

def z(key):
    v = np.array([r[key] for r in rows]); sd = v.std() or 1
    return (v - v.mean()) / sd

if rows:
    sc = .35 * z('loud') + .3 * z('pitch') + .15 * z('peak') + .1 * z('rate') + .1 * np.clip(z('pause'), -1, 2)
    qs = np.quantile(sc, [.2, .4, .6, .8]) if len(sc) >= 5 else [sc.min() - 1] * 4
    for r, v in zip(rows, sc): r['nl'] = int(1 + sum(v > q for q in qs)); r['score'] = round(float(v), 2)

# ---- vai câu (tiếng Việt, bỏ dấu để khớp rộng)
def nd(s): return ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn').replace('đ', 'd')
PLACES = set()
for f in ('tu_vung_daklak.txt',):
    p = os.path.join(VC, 'reference', f)
    if os.path.exists(p): PLACES |= {nd(l.strip()) for l in open(p, encoding='utf-8') if l.strip() and not l.startswith('#')}
R_TIN = r'\b(theo toi|toi (nghi|thay|cho rang|tin|khuyen)|minh (nghi|thay)|anh chi|cac ban|ban (nen|co|nghi)|nen |dung |hay |lieu|vay thi|co nen)\b|\?'
R_HIEU = r'\d|\b(phan tram|ty|trieu|nghin|km|ha|hecta|m2|met|nam 20|gap|tang|giam|so voi|hon|bang)\b'
R_THAY = r'\b(duong|quoc lo|cao toc|san bay|cang|khu|phuong|xa|huyen|tuyen|nut giao|cau|ho|cong vien|khu cong nghiep|du an)\b'
R_LIST = r'\b(thu (nhat|hai|ba|tu|nam)|mot la|hai la|ba la|cuoi cung)\b'
R_CAM = r'(?<!thu )\bnhat\b|\b(cuc ky|rat|that su|quan trong|bat buoc|phai|khong the|bom|soc|canh bao|rui ro|co hoi)\b|!'
for r in rows:
    t = nd(r['text']); v = []
    if re.search(R_TIN, t): v.append('TIN')
    if re.search(R_HIEU, t): v.append('HIỂU')
    if re.search(R_THAY, t) or any(p and p in t for p in PLACES): v.append('THẤY')
    if re.search(R_LIST, t): v.append('LIỆT KÊ')
    if re.search(R_CAM, t): v.append('CẢM')
    r['vai'] = v or ['KỂ']
    nl, vv = r.get('nl', 3), r['vai']
    if nl >= 4: g = 'MẶT (câu có lửa' + (', số đọc trên chữ .mix' if 'HIỂU' in vv else '') + ')'
    elif 'LIỆT KÊ' in vv and nl <= 3: g = 'HÌNH dồn (chuỗi liệt kê)'
    elif nl <= 2 and ('HIỂU' in vv or 'THẤY' in vv or vv == ['KỂ']): g = 'HÌNH (câu đuối → phủ)'
    elif nl <= 2: g = 'SPLIT / push chậm (cần tin nhưng nói đuối)'
    elif 'THẤY' in vv or 'HIỂU' in vv: g = 'HÌNH'
    elif 'TIN' in vv or 'CẢM' in vv: g = 'MẶT'
    else: g = 'tuỳ nhịp'
    r['goi_y'] = g

json.dump(rows, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'BẢNG NHỊP ({len(rows)} câu · NL 1–5 so trong video này · giây cut/cut.mp4)')
print(' giây        NL  vai           gợi ý                         lời')
for r in rows:
    print(f"{r['t0']:6.2f}–{r['t1']:<6.2f} {'●' * r.get('nl', 3):<5} {'/'.join(r['vai']):<13} {r['goi_y'][:28]:<29} {r['text'][:60]}")
hi = [r for r in rows if r.get('nl', 0) == 5]
if hi: print('Câu lửa nhất (ứng viên câu móc / cao trào / giữ mặt):', ' · '.join(f"{r['t0']} \"{r['text'][:30]}\"" for r in hi))
print('→', a.out)
