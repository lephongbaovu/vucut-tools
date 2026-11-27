#!/usr/bin/env python3
"""vucut · facetrack.py — dò mặt người nói theo thời gian → khung cắt dọc 9:16 BÁM MẶT như người quay giữ máy.
Dùng: python -X utf8 facetrack.py <video> <ra.json> [--step .2] [--dz .07] [--ease .6]
- Dò mặt bằng YuNet (assets/models/face_yunet.onnx, có sẵn trong skill) → dự phòng Haar của OpenCV → không thấy mặt thì giữ vị trí cũ.
- Máy quay ảo: đứng YÊN khi mặt xê dịch trong vùng chết (dz × bề rộng khung cắt); mặt ra khỏi vùng đó → lia mềm (ease giây) đưa mặt VỀ GIỮA rồi đứng yên
  → không rung theo từng cử động đầu.
- Ra json: {w,h,crop_w, fps, x:[cột trái khung cắt mỗi khung hình 30 fps], face:[fx,fy] tâm mặt trung vị TRONG khung cắt (0–1)}.
  Nguồn dọc (≤ 9:16) không cần cắt: x rỗng, chỉ tính face để đặt tâm phóng punch/push/slam.
Cần: pip install opencv-python numpy (vucut.py setup tự cài)."""
import argparse, json, os, subprocess
import numpy as np

VC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def probe(v):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height:format=duration',
                        '-of', 'json', v], capture_output=True, text=True, check=True)
    j = json.loads(r.stdout); s = j['streams'][0]
    return int(s['width']), int(s['height']), float(j['format']['duration'])


def detector():
    import cv2
    m = os.path.join(VC, 'assets', 'models', 'face_yunet.onnx')
    if os.path.exists(m) and hasattr(cv2, 'FaceDetectorYN'):
        try:
            d = cv2.FaceDetectorYN.create(m, '', (320, 320), 0.6, 0.3, 5000)
            def yunet(img):
                d.setInputSize((img.shape[1], img.shape[0])); _, f = d.detect(img)
                return None if f is None else [(x, y, w, h, s) for x, y, w, h, *_, s in f]
            return yunet
        except Exception as e:
            print('⚠ YuNet lỗi, dùng Haar:', e)
    xml = os.path.join(getattr(cv2, 'data', None).haarcascades if hasattr(cv2, 'data') else '', 'haarcascade_frontalface_default.xml')
    if os.path.exists(xml):
        c = cv2.CascadeClassifier(xml)
        def haar(img):
            g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            f = c.detectMultiScale(g, 1.1, 6, minSize=(img.shape[0] // 12,) * 2)
            return [(x, y, w, h, w * h) for x, y, w, h in f] if len(f) else None
        return haar
    print('⚠ không có bộ dò mặt → khung giữa'); return lambda img: None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video'); ap.add_argument('out')
    ap.add_argument('--step', type=float, default=.2, help='giây giữa 2 lần dò')
    ap.add_argument('--dz', type=float, default=.07, help='vùng chết (tỉ lệ bề rộng khung cắt)')
    ap.add_argument('--ease', type=float, default=.6, help='thời gian lia (giây)')
    ap.add_argument('--fps', type=float, default=30)
    a = ap.parse_args()
    W, H, D = probe(a.video)
    sw = 640 if W >= H else 360; sh = int(round(H * sw / W / 2) * 2)
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', a.video, '-vf', f'fps={1 / a.step},scale={sw}:{sh}', '-f', 'rawvideo',
                          '-pix_fmt', 'bgr24', '-'], capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, sh, sw, 3)
    det = detector(); k = W / sw
    cx, cy, top, prev = [], [], [], None
    for im in fr:
        f = det(np.ascontiguousarray(im))
        if f:
            if prev is None: x, y, w, h, _ = max(f, key=lambda r: r[2] * r[3])
            else: x, y, w, h, _ = min(f, key=lambda r: abs(r[0] + r[2] / 2 - prev) - r[2] * r[3] * 1e-4)   # bám người đang theo
            prev = x + w / 2; cx.append((x + w / 2) * k); cy.append((y + h / 2) * k); top.append((y - .45 * h) * k)   # đỉnh tóc ≈ trán − 0.45 mặt
        else:
            cx.append(np.nan); cy.append(np.nan); top.append(np.nan)
    cx, cy, top = np.array(cx, float), np.array(cy, float), np.array(top, float)
    hit = ~np.isnan(cx); print(f'dò {len(cx)} mẫu · thấy mặt {hit.mean() * 100:.0f}%')
    if hit.sum() == 0: cx[:] = W / 2; cy[:] = H * .38; top[:] = H * .10
    else:
        idx = np.arange(len(cx)); cx = np.interp(idx, idx[hit], cx[hit]); cy = np.interp(idx, idx[hit], cy[hit]); top = np.interp(idx, idx[hit], top[hit])
    # trung vị trượt (bỏ khung dò sai)
    med = lambda v, r=2: np.array([np.median(v[max(0, i - r):i + r + 1]) for i in range(len(v))])
    cx, cy = med(cx), med(cy)
    cw = H * 9 / 16
    res = {'w': W, 'h': H, 'fps': a.fps, 'x': [], 'crop_w': None}
    n = int(D * a.fps)
    ts = np.arange(n) / a.fps; tsamp = np.arange(len(cx)) * a.step
    if W / H > 9 / 16 + .01:
        res['crop_w'] = round(cw)
        # máy quay ảo: vùng chết + lia ease theo khung hình
        tgt = np.interp(ts, tsamp, cx); cam = np.empty(n); c = tgt[0]; v = 0.0; moving = False
        dz = a.dz * cw; k_ = 1 / max(1, a.ease * a.fps)
        for i in range(n):
            d = tgt[i] - c
            if not moving and abs(d) > dz: moving = True          # mặt ra khỏi vùng chết → bắt đầu lia
            if moving and abs(d) < .01 * cw and abs(v) < .5: moving = False   # đã đưa mặt về giữa → đứng yên
            goal = d if moving else 0.0
            v += (goal * k_ - v) * .25          # tăng/giảm tốc mềm
            c += v; cam[i] = c
        x = np.clip(cam - cw / 2, 0, W - cw)
        res['x'] = [round(float(t), 1) for t in x]
        fx = np.median((np.interp(ts, tsamp, cx) - x) / cw)
    else:
        fx = np.median(cx) / W
    fy = np.median(cy) / H
    # ĐỈNH ĐẦU theo thời gian (tỉ lệ chiều cao khung) → V.L_split tự tính độ dời để mép panel KHÔNG cắt đầu
    tp = np.array([np.min(top[max(0, i - 2):i + 3]) for i in range(len(top))]) / H
    res['step'] = a.step; res['top'] = [round(float(np.clip(v, 0, .9)), 3) for v in tp]; res['cy'] = [round(float(v / H), 3) for v in med(cy)]; res['head'] = round(float(np.clip(np.percentile(tp, 10), 0, .9)), 3)
    res['face'] = [round(float(np.clip(fx, .2, .8)), 3), round(float(np.clip(fy, .2, .6)), 3)]
    json.dump(res, open(a.out, 'w', encoding='utf-8'))
    pan = (max(res['x']) - min(res['x'])) if res['x'] else 0
    print(f'→ {a.out} · tâm mặt trong khung {res["face"]} · biên độ lia {pan:.0f}px')


if __name__ == '__main__':
    main()
