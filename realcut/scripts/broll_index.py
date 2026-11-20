"""Lập chỉ mục thư mục B-roll → DA/broll/index.json + bảng ảnh mỗi clip (DA/broll/sheet_XX.jpg) để TỰ XEM (Read) và gắn nhãn.
python3 broll_index.py THU_MUC_BROLL DA
Ảnh tĩnh (.jpg/.png/.webp) cũng được nhận — khi dựng sẽ có chuyển động chậm (Ken Burns).
Sau khi xem, ghi nhãn vào index.json (trường "tag", "best_in", "note") hoặc thẳng vào edit.json.
"""
import argparse, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import probe, Reader, save_json, font_path

VID = ('.mp4', '.mov', '.m4v', '.mkv', '.webm', '.avi', '.mts')
IMG = ('.jpg', '.jpeg', '.png', '.webp')

def motion_score(path, dur, w=160, h=90):
    """Độ rung/chuyển động trung bình (0 = tĩnh) và độ sáng — chọn đoạn ổn định nhất."""
    r = Reader(path, w, h, fps=4); prev = None; diffs = []; lum = []
    while True:
        f = r.read()
        if r.eof or f is None:
            break
        g = f.mean(2)
        lum.append(g.mean())
        if prev is not None:
            diffs.append(np.abs(g - prev).mean())
        prev = g
    r.close()
    return (float(np.mean(diffs)) if diffs else 0.0), (float(np.mean(lum)) if lum else 0.0), diffs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('folder'); ap.add_argument('da')
    a = ap.parse_args()
    from PIL import Image, ImageDraw, ImageFont
    od = os.path.join(a.da, 'broll'); os.makedirs(od, exist_ok=True)
    files = sorted(f for f in os.listdir(a.folder) if f.lower().endswith(VID + IMG))
    items = []
    fnt = ImageFont.truetype(font_path('medium'), 22)
    for k, fn in enumerate(files):
        p = os.path.abspath(os.path.join(a.folder, fn))
        if fn.lower().endswith(IMG):
            im = Image.open(p); w, h = im.size
            it = dict(id=f'B{k+1:02d}', file=p, kind='image', w=w, h=h, dur=None, orient='doc' if h > w else 'ngang')
            thumbs = [im.convert('RGB')]
        else:
            info = probe(p)
            mv, lum, diffs = motion_score(p, info['dur'])
            # đoạn 3 s ổn định nhất (ít rung) → gợi ý điểm vào
            best = 0.0
            if len(diffs) > 12:
                win = 12; s = np.convolve(diffs, np.ones(win), 'valid')
                best = round(float(np.argmin(s)) / 4, 2)
            it = dict(id=f'B{k+1:02d}', file=p, kind='video', w=info['w'], h=info['h'], fps=round(info['fps'], 2),
                      dur=round(info['dur'], 2), orient='doc' if info['h'] > info['w'] else 'ngang',
                      motion=round(mv, 2), luma=round(lum, 1), best_in=best,
                      shaky=bool(mv > 9))
            thumbs = []
            for i in range(4):
                t = info['dur'] * (i + 0.5) / 4
                tw = 360; th = int(tw * info['h'] / info['w']) // 2 * 2
                r = Reader(p, tw, th, ss=t); f = r.read(); r.close()
                if f is not None:
                    im = Image.fromarray(f); ImageDraw.Draw(im).text((8, 6), f'{t:.1f}s', font=fnt, fill=(255, 220, 120))
                    thumbs.append(im)
        it['tag'] = ''; it['note'] = ''
        # bảng ảnh
        tw = 360; ims = [t.resize((tw, int(tw * t.height / t.width))) for t in thumbs]
        H = max(i.height for i in ims) + 40
        sheet = Image.new('RGB', (tw * len(ims), H), (24, 20, 17))
        for i, im in enumerate(ims):
            sheet.paste(im, (i * tw, 40))
        d = ImageDraw.Draw(sheet)
        d.text((10, 8), f"{it['id']} · {fn} · {it['w']}×{it['h']}" + (f" · {it['dur']}s · rung {it['motion']}" if it['dur'] else ' · ảnh'),
               font=fnt, fill=(236, 214, 170))
        sp = os.path.join(od, f"sheet_{it['id']}.jpg"); sheet.save(sp, quality=85); it['sheet'] = sp
        items.append(it)
        print(f"· {it['id']} {fn} {it['w']}×{it['h']} " + (f"{it['dur']}s rung={it['motion']} sáng={it['luma']} vào≈{it['best_in']}s" + (' ⚠ RUNG' if it.get('shaky') else '') if it['dur'] else 'ảnh'))
    save_json(os.path.join(od, 'index.json'), dict(folder=os.path.abspath(a.folder), items=items))
    print(f'✓ {len(items)} tư liệu → {od}/index.json · xem bảng ảnh: {od}/sheet_*.jpg')

if __name__ == '__main__':
    main()
