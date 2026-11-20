"""realcut · ghép A-roll (nhiều clip người nói) + tăng tốc → 1 file liền mạch, không lệch tiếng.
  python aroll.py OUT.mp4 clip1.mp4 clip2.mp4[@a-b] … [--speed 1.1]
  clip@a-b = chỉ lấy đoạn a→b giây của clip đó. Dùng concat FILTER (concat demuxer làm rớt khung).
  Tăng tốc: setpts + aresample=async=1:first_pts=0 + atempo (thiếu aresample → tiếng lệch ~0.17 s).
"""
import argparse, subprocess
from common import probe, die

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('clips', nargs='+')
    ap.add_argument('--speed', type=float, default=1.1); ap.add_argument('--fps', type=int, default=30)
    a = ap.parse_args()
    ins, fc, n = [], [], 0
    first = probe(a.clips[0].split('@')[0])
    W, H = (first['w'], first['h'])
    for c in a.clips:
        path, _, rg = c.partition('@')
        info = probe(path)
        if not info['has_audio']: die(f'{path} không có tiếng')
        if rg:
            s, e = [float(x) for x in rg.split('-')]; ins += ['-ss', f'{s}', '-to', f'{e}']
        ins += ['-i', path]
        fc.append(f'[{n}:v]scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={a.fps}[v{n}];'
                  f'[{n}:a]aresample=48000,aformat=channel_layouts=stereo[a{n}]')
        n += 1
    cat = ''.join(f'[v{i}][a{i}]' for i in range(n)) + f'concat=n={n}:v=1:a=1[vc][ac]'
    sp = a.speed
    tail = (f';[vc]setpts=PTS/{sp}[v];[ac]aresample=async=1:first_pts=0,atempo={sp}[a]' if abs(sp - 1) > 1e-3
            else ';[vc]null[v];[ac]anull[a]')
    cmd = ['ffmpeg', '-v', 'error', '-y'] + ins + ['-filter_complex', ';'.join(fc) + ';' + cat + tail,
           '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-crf', '16', '-preset', 'medium', '-r', str(a.fps),
           '-c:a', 'aac', '-b:a', '256k', a.out]
    subprocess.run(cmd, check=True)
    print(f'✓ {a.out} · {n} clip · tốc độ {sp}× · {probe(a.out)["dur"]:.2f}s')

if __name__ == '__main__':
    main()
