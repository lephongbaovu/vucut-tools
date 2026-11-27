#!/usr/bin/env python3
"""vucut · matte_split.py — tách nền người nói từng khung, CHỈ trong cảnh chia đôi, để đầu nổi lên B-roll (C2).
Dùng: python -X utf8 matte_split.py <frames_dir> <out_dir> <fps> <a-b,a-b,...> [--jobs 2] [--blur 1.2]
- frames_dir: khung JPG mà preview.mjs dùng (frames/00001.jpg…). Khoảng a-b = giây của video CUỐI (sau tighten).
- Tự đệm 1 khung trước, 2 khung sau. Ra out_dir/NNNNN.png (RGBA) — đặt out_dir = build/cut để preview.mjs tự nạp.
- Cần `pip install rembg` (mô hình u2net_human_seg ~170 MB, ~1 s/khung CPU). File đã có thì bỏ qua (chạy lại được)."""
import argparse, os
from multiprocessing import Process

def work(ids, src, out, blur):
    from rembg import remove, new_session
    from PIL import Image, ImageFilter
    s = new_session('u2net_human_seg')
    for i in ids:
        dst = os.path.join(out, '%05d.png' % i)
        if os.path.exists(dst): continue
        im = Image.open(os.path.join(src, '%05d.jpg' % i)).convert('RGB')
        sm = im if im.width <= 720 else im.resize((720, round(im.height * 720 / im.width)), Image.LANCZOS)   # tách nền ở 720 cho nhanh
        a = remove(sm, session=s, post_process_mask=True).getchannel('A')
        if sm is not im: a = a.resize(im.size, Image.LANCZOS)
        a = a.filter(ImageFilter.GaussianBlur(blur * im.width / 720))
        im.putalpha(a); im.save(dst)

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('frames'); ap.add_argument('out'); ap.add_argument('fps', type=float); ap.add_argument('ranges')
    ap.add_argument('--jobs', type=int, default=2); ap.add_argument('--blur', type=float, default=1.2)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    n = len([f for f in os.listdir(a.frames) if f.endswith('.jpg')])
    ids = []
    for r in a.ranges.split(','):
        s, e = map(float, r.split('-'))
        ids += range(max(1, int(s * a.fps)), min(n, int(e * a.fps) + 3) + 1)
    ids = sorted(set(ids)); print(len(ids), 'khung cần tách nền')
    from rembg import new_session; new_session('u2net_human_seg')   # tải mô hình 1 lần TRƯỚC khi chia tiến trình (tránh tải trùng / hỏng file)
    ps = [Process(target=work, args=(ids[k::a.jobs], a.frames, a.out, a.blur)) for k in range(a.jobs)]
    [p.start() for p in ps]; [p.join() for p in ps]
    print('xong →', a.out)
