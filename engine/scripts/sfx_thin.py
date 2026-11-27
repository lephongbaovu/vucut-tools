#!/usr/bin/env python3
"""vucut · sfx_thin.py — lọc cues.json cho THƯA + NHỎ (chuẩn v5, ~1 hiệu ứng / 2.3 s, không dày gây khó chịu).
Dùng: python -X utf8 sfx_thin.py cues.json cues_lite.json [--hook-end 1.0]
Luật: bỏ hết swish; tick chỉ giữ trong hook (t ≤ --hook-end); riser chỉ giữ khi đi cùng boom (panel đỏ);
giữ theo ưu tiên glitch/sub > hit > boom/ding > whoosh > count/pop, cách nhau ≥ 0.7 s (pop ≥ 1.5 s) — chuẩn v5;
mức tuyệt đối (dB) ghi đè mức trong cues → trộn bằng sfx_mix.py --sfx-db 0."""
import json, sys, argparse
ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('out'); ap.add_argument('--hook-end', type=float, default=1.0); ap.add_argument('--gap-avg', type=float, default=2.1)
a = ap.parse_args()
C = json.load(open(a.src, encoding='utf-8'))
PRI = {'glitch': 1, 'sub': 1, 'hit': 2, 'stamp': 2, 'metal': 2, 'boom': 3, 'ding': 3, 'creak': 3, 'whoosh': 4, 'scan': 4, 'thud': 4, 'shutter': 4, 'wash': 4, 'air': 4,
       'paper': 4, 'flap': 4, 'ratchet': 4, 'riser': 5, 'count': 6, 'pop': 6, 'block': 6, 'pen': 6}
DB = {'glitch': -11, 'sub': -8, 'hit': -11, 'boom': -13, 'ding': -13, 'whoosh': -13, 'riser': -17, 'count': -16, 'pop': -15, 'tick': -22,
      'stamp': -11, 'metal': -14, 'creak': -15, 'scan': -14, 'thud': -12, 'shutter': -13, 'wash': -13, 'air': -14,
      'paper': -13, 'flap': -15, 'ratchet': -16, 'block': -15, 'pen': -17}
cand = [c for c in C if c['s'] != 'swish' and not (c['s'] == 'tick' and c['t'] > a.hook_end)]
cand.sort(key=lambda c: (PRI.get(c['s'], 9), c['t']))
kept = []
for c in cand:
    if c['s'] == 'riser':
        if any(k['s'] == 'boom' and abs(k['t'] - c['t']) < .05 for k in C): kept.append(dict(c, db=DB['riser']))
        continue
    win = 1.5 if c['s'] in ('pop', 'block', 'pen') else (0.0 if c['s'] == 'tick' else 0.7)
    if any(abs(k['t'] - c['t']) < win and k['s'] != 'riser' for k in kept): continue
    kept.append(dict(c, db=DB.get(c['s'], -15)))
kept.sort(key=lambda c: c['t'])
# trần mật độ: trung bình không dày hơn 1 hiệu ứng / --gap-avg giây (mặc định 2.1) — bỏ dần hiệu ứng ưu tiên thấp, đứng sát hàng xóm nhất
dur = max([c['t'] for c in C] + [1])
def crowd(k):
    t = kept[k]['t']; nb = [abs(kept[j]['t'] - t) for j in (k - 1, k + 1) if 0 <= j < len(kept)]
    return min(nb) if nb else 9
while len([c for c in kept if c['s'] != 'tick']) > dur / a.gap_avg:
    cands = [k for k, c in enumerate(kept) if c['s'] != 'tick' and PRI.get(c['s'], 9) >= 3]
    if not cands: break
    k = max(cands, key=lambda k: (PRI.get(kept[k]['s'], 9), -crowd(k)))
    kept.pop(k)
json.dump(kept, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print(f'{len(C)} → {len(kept)} hiệu ứng (≈ 1 / {dur / max(1, len([c for c in kept if c["s"] != "tick"])):.1f} s, không tính tick hook)')
