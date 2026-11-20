"""Tự cắt khoảng lặng + từ đệm, cắt khung theo tỉ lệ (bám người nói) → cut.mp4 + words_cut.json + segments.json
python3 autocut.py goc.mp4 DA --ratio 9:16 [--clip a-b] [--keep a-b,..] [--drop a-b,..] [--pad .12] [--gap .45] [--no-fillers] [--no-cut]
Mọi mốc --keep/--drop/--clip tính theo GIÂY GỐC. Sau bước này mọi mốc trong edit.json tính theo giây cut.mp4.
"""
import argparse, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import probe, run, load_json, save_json, out_size, die

FILLERS = {'ờ', 'ừm', 'ừ', 'ơ', 'ờm', 'ưm', 'hmm', 'ừa', 'à'}  # 'à' chỉ bỏ khi đứng riêng một cụm

def ranges(s):
    out = []
    for part in (s or '').split(','):
        if '-' in part:
            a, b = part.split('-'); out.append((float(a), float(b)))
    return out

def norm(w):
    return re.sub(r'[^\w]', '', w.lower())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('da')
    ap.add_argument('--ratio', default='9:16', choices=['9:16', '16:9'])
    ap.add_argument('--clip'); ap.add_argument('--keep'); ap.add_argument('--drop')
    ap.add_argument('--pad', type=float, default=0.12, help='giữ lại trước/sau mỗi cụm lời (s)')
    ap.add_argument('--gap', type=float, default=0.45, help='khoảng lặng dài hơn mức này thì rút')
    ap.add_argument('--no-fillers', action='store_true', help='KHÔNG bỏ từ đệm (ờ, ừm…)')
    ap.add_argument('--no-cut', action='store_true', help='không cắt gì, chỉ cắt khung')
    ap.add_argument('--crop-x', type=float, default=None, help='ép tâm ngang khung (0..1)')
    ap.add_argument('--hq', action='store_true', help='mã hoá chất lượng cao hơn (chậm)')
    a = ap.parse_args()
    info = probe(a.src)
    W, H = out_size(a.ratio)
    wj = load_json(os.path.join(a.da, 'words.json'))
    if wj is None:
        die('Chưa có words.json — chạy transcribe trước')
    words = wj['words']
    c0, c1 = (0.0, info['dur'])
    if a.clip:
        c0, c1 = [float(x) for x in a.clip.split('-')]

    # 1 · khoảng cần giữ
    if a.no_cut or not words:
        keep = [(c0, c1)]
    else:
        drop_words = set()
        if not a.no_fillers:
            for i, w in enumerate(words):
                n = norm(w['w'])
                if n in FILLERS and n != 'à':
                    drop_words.add(i)
                elif n == 'à':
                    prev_gap = w['s'] - words[i - 1]['e'] if i else 9
                    next_gap = words[i + 1]['s'] - w['e'] if i + 1 < len(words) else 9
                    if prev_gap > .25 and next_gap > .25:
                        drop_words.add(i)
        islands = []
        for i, w in enumerate(words):
            if i in drop_words:
                continue
            s, e = max(c0, w['s'] - a.pad), min(c1, w['e'] + a.pad)
            if islands and s - islands[-1][1] < (a.gap - 2 * a.pad) and not any(j in drop_words for j in range(islands[-1][2] + 1, i)):
                islands[-1][1] = e; islands[-1][2] = i
            else:
                islands.append([s, e, i])
        keep = [(s, e) for s, e, _ in islands]
        for s, e in ranges(a.drop):
            nk = []
            for ks, ke in keep:
                if e <= ks or s >= ke:
                    nk.append((ks, ke))
                else:
                    if s > ks: nk.append((ks, s))
                    if e < ke: nk.append((e, ke))
            keep = nk
        for s, e in ranges(a.keep):
            keep.append((s, e))
        keep.sort(); merged = []
        for s, e in keep:
            if merged and s <= merged[-1][1] + 0.02:
                merged[-1] = (merged[-1][0], max(merged[-1][1], e))
            else:
                merged.append((s, e))
        keep = [(round(s, 3), round(e, 3)) for s, e in merged if e - s > 0.08]

    # 2 · cắt khung
    if a.ratio == '9:16':
        tw = info['h'] * 9 / 16
        if tw <= info['w'] - 2:
            cx = a.crop_x
            if cx is None:
                from matte import person_center_x
                cx = person_center_x(a.src, c0, c1)
                print(f'· người nói ở x={cx:.2f} (khung tự bám)')
            x = min(max(cx * info['w'] - tw / 2, 0), info['w'] - tw)
            crop = f'crop={int(tw)//2*2}:{info["h"]}:{int(x)}:0,'
        else:
            th = info['w'] * 16 / 9
            crop = f'crop={info["w"]}:{min(info["h"], int(th))//2*2},' if th < info['h'] else ''
    else:
        th = info['w'] * 9 / 16
        crop = f'crop={info["w"]}:{int(th)//2*2}:0:{int((info["h"]-th)/2)},' if th < info['h'] - 2 else ''
        if not crop and info['w'] / info['h'] < 16 / 9 - 0.01:  # nguồn dọc → khung ngang: đặt giữa nền mờ
            crop = None
    if crop is None:
        vf = (f'split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=40:2[bg];'
              f'[b]scale=-2:{H}[fg];[bg][fg]overlay=(W-w)/2:0')
    else:
        vf = f'{crop}scale={W}:{H}:flags=lanczos'
    if min(info['w'], info['h']) < 1000:
        print(f'  ⚠ nguồn chỉ {info["w"]}×{info["h"]} — phóng lên {W}×{H} sẽ mềm; nên quay 4K/1080p dọc')

    # 3 · ghép đoạn (fade âm 10 ms ở mỗi mối nối để không lách tách)
    parts = []; fc = []
    for i, (s, e) in enumerate(keep):
        d = e - s
        fc.append(f'[0:v]trim={s}:{e},setpts=PTS-STARTPTS[v{i}]')
        fc.append(f'[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={max(0, d-0.01):.3f}:d=0.01[a{i}]')
        parts.append(f'[v{i}][a{i}]')
    fc.append(''.join(parts) + f'concat=n={len(keep)}:v=1:a=1[vc][ac]')
    fc.append(f'[vc]{vf},fps=30,format=yuv420p[vo]')
    out = os.path.join(a.da, 'cut.mp4')
    lst = os.path.join(a.da, 'cut_parts.txt'); names = []
    for i, (s, e) in enumerate(keep):
        d = e - s; pn = os.path.join(a.da, f'_part{i}.mov'); names.append(pn)
        run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', str(s), '-i', a.src, '-t', f'{d:.3f}',
             '-vf', f'{vf},fps=30,format=yuv420p', '-af', f'afade=t=in:d=0.01,afade=t=out:st={max(0, d-0.01):.3f}:d=0.01',
             '-c:v', 'libx264', '-preset', 'fast', '-crf', '16', '-c:a', 'pcm_s16le', pn])
    open(lst, 'w').write(''.join(f"file '{n}'\n" for n in names))
    run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', out])
    for n in names: os.remove(n)

    # 4 · đổi mốc từ sang giây cut
    segs = []; acc = 0.0
    for s, e in keep:
        segs.append(dict(src_s=s, src_e=e, cut_s=round(acc, 3))); acc += e - s
    def to_cut(t):
        for sg in segs:
            if sg['src_s'] - 1e-3 <= t <= sg['src_e'] + 1e-3:
                return round(sg['cut_s'] + t - sg['src_s'], 3)
        return None
    wc = []
    for w in words:
        s, e = to_cut(w['s']), to_cut(w['e'])
        if s is not None and e is not None:
            wc.append(dict(w=w['w'], s=s, e=e))
    save_json(os.path.join(a.da, 'segments.json'), dict(ratio=a.ratio, W=W, H=H, keep=segs, dur=round(acc, 3)))
    save_json(os.path.join(a.da, 'words_cut.json'), dict(words=wc, dur=round(acc, 3)))
    src_len = c1 - c0
    print(f'✓ cut.mp4 {W}×{H} · {src_len:.1f}s → {acc:.1f}s (rút {100*(1-acc/max(src_len,1e-6)):.0f}%) · {len(keep)} đoạn')
    removed = []
    prev = c0
    for s, e in keep:
        if s - prev > 0.3:
            txt = ' '.join(w['w'] for w in words if w['s'] >= prev - .05 and w['e'] <= s + .05)
            removed.append(f'{prev:.2f}-{s:.2f}' + (f' «{txt}»' if txt else ''))
        prev = e
    if removed:
        print('  ĐOẠN BỎ (giây gốc):', ' | '.join(removed))
    if src_len and acc / src_len < 0.6:
        print('  ⚠ đã bỏ > 40 % — hỏi người dùng trước khi dựng tiếp')

if __name__ == '__main__':
    main()
