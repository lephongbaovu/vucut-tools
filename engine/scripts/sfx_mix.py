#!/usr/bin/env python3
"""vucut · trộn hiệu ứng âm thanh lên tiếng gốc theo danh sách mốc.
Dùng: python -X utf8 sfx_mix.py <video_hoặc_audio_gốc> <cues.json> <sfx_dir> <ra.m4a> [--voice-db 0] [--sfx-db -4]
cues.json: [{"t": 0.05, "s": "tick", "db": -14}, {"t": 2.86, "s": "whoosh"}, {"t": 13.8, "s": "riser", "end": true}, ...]
  t   = giây (cùng mốc với timeline HTML)      s  = tên file trong sfx_dir (không .wav)
  db  = chỉnh mức riêng (mặc định 0)           end = true → âm KẾT THÚC tại t (dùng cho riser)
Tiếng nói luôn là chính: sfx mặc định thấp hơn 4 dB, cuối chuỗi có limiter chống vỡ tiếng.
Nếu đã có sfx_mix.py của seecut thì vẫn dùng được file này độc lập (chỉ cần ffmpeg)."""
import argparse, json, os, subprocess, wave
ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('cues'); ap.add_argument('sfx'); ap.add_argument('out')
ap.add_argument('--voice-db', type=float, default=0); ap.add_argument('--sfx-db', type=float, default=-4)
a = ap.parse_args()
cues = json.load(open(a.cues, encoding='utf-8'))
def dur(p):
    w = wave.open(p); d = w.getnframes() / w.getframerate(); w.close(); return d
ins = ['-i', a.src]; fl = [f'[0:a]aresample=48000,volume={a.voice_db}dB[v]']; labs = ['[v]']
for i, c in enumerate(cues):
    p = os.path.join(a.sfx, c['s'] + '.wav'); ins += ['-i', p]
    st = c['t'] - (dur(p) if c.get('end') else 0); ms = max(0, int(st * 1000))
    fl.append(f'[{i+1}:a]aresample=48000,volume={a.sfx_db + c.get("db", 0)}dB,adelay={ms}|{ms}[s{i}]'); labs.append(f'[s{i}]')
fl.append(''.join(labs) + f'amix=inputs={len(labs)}:normalize=0:duration=first,alimiter=limit=0.89[out]')
subprocess.run(['ffmpeg', '-v', 'error', '-y', *ins, '-filter_complex', ';'.join(fl), '-map', '[out]', '-c:a', 'aac', '-b:a', '192k', a.out], check=True)
print('xong →', a.out, f'({len(cues)} hiệu ứng)')
