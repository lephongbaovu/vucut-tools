"""realcut · chuẩn hoá B-roll về 1080×1920 trước khi dựng (sắc nét, không vỡ):
  - nguồn DỌC (kể cả flycam xoay metadata)  → scale phủ kín 9:16
  - nguồn NGANG ≥ 3840 px (3D/4K)           → cắt dọc trực tiếp (--crop-x 0..1 chọn phần giữ)  [--mode crop]
  - nguồn NGANG còn lại                     → blur-fit: tiền cảnh rộng 1400 px, tâm 0.335 H, nền mờ tối  [--mode blur]
  python prep_broll.py IN_DIR_hoặc_FILE OUT_DIR [--mode auto|crop|blur] [--crop-x 0.5]
"""
import argparse, os, subprocess
from common import probe

EXT = ('.mp4', '.mov', '.m4v', '.mkv', '.avi', '.MP4', '.MOV')

def one(src, out, mode, cx):
    i = probe(src); w, h = i['w'], i['h']
    grade = 'eq=saturation=1.06:contrast=1.03'
    if h >= w:
        vf = f'scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,fps=30,{grade}'
        args = ['-vf', vf]; how = 'dọc → phủ kín'
    elif mode == 'crop' or (mode == 'auto' and w >= 3800):
        cw = int(h * 9 / 16) // 2 * 2
        vf = f'crop={cw}:{h}:{int((w - cw) * cx)}:0,scale=1080:1920:flags=lanczos,fps=30,{grade}'
        args = ['-vf', vf]; how = f'ngang {w}px → cắt dọc'
    else:
        fc = ('[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=40:2,eq=brightness=-0.12[bg];'
              f'[0:v]scale=1400:-2:flags=lanczos,crop=1080:ih,{grade}[fg];[bg][fg]overlay=(W-w)/2:H*0.335-h/2,fps=30')
        args = ['-filter_complex', fc]; how = 'ngang → blur-fit'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-map', '0:v:0', '-an'] + args +
                   ['-c:v', 'libx264', '-crf', '15', '-preset', 'medium', '-pix_fmt', 'yuv420p', out], check=True)
    print(f'✓ {os.path.basename(src)} ({how}) → {out}')

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('out')
    ap.add_argument('--mode', default='auto', choices=['auto', 'crop', 'blur']); ap.add_argument('--crop-x', type=float, default=0.5)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    files = [a.src] if os.path.isfile(a.src) else [os.path.join(a.src, f) for f in sorted(os.listdir(a.src)) if f.endswith(EXT)]
    for f in files:
        one(f, os.path.join(a.out, os.path.splitext(os.path.basename(f))[0] + '_916.mp4'), a.mode, a.crop_x)

if __name__ == '__main__':
    main()
