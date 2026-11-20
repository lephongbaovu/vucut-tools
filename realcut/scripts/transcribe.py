"""Phiên âm tiếng Việt có mốc từng từ (faster-whisper) → words.json
python3 transcribe.py goc.mp4 DA [--clip a-b] [--model medium]
- Mồi tên riêng Đắk Lắk từ reference/tu_vung_daklak.txt (+ DA/tu_vung.txt nếu có)
- Tự sửa lỗi nghe sai theo reference/sua_chinh_ta.tsv (+ DA/sua_chinh_ta.tsv)
"""
import argparse, os, re, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import REF, run, save_json, die

def load_vocab(da):
    words = []
    for p in (os.path.join(REF, 'tu_vung_daklak.txt'), os.path.join(da, 'tu_vung.txt')):
        if os.path.exists(p):
            for line in open(p, encoding='utf-8'):
                line = line.strip()
                if line and not line.startswith('#'):
                    words.append(line)
    return words

def load_fixes(da):
    fixes = []
    for p in (os.path.join(REF, 'sua_chinh_ta.tsv'), os.path.join(da, 'sua_chinh_ta.tsv')):
        if os.path.exists(p):
            for line in open(p, encoding='utf-8'):
                if '\t' in line and not line.startswith('#'):
                    a, b = line.rstrip('\n').split('\t')[:2]
                    if a:
                        fixes.append((a, b))
    return fixes

def apply_fixes(words, fixes):
    """Sửa trên chuỗi nối (để bắt cụm nhiều từ) rồi chia lại vào các từ theo số lượng âm tiết."""
    n_fixed = 0
    for wrong, right in fixes:
        wt = wrong.lower().split()
        k = len(wt)
        i = 0
        while i <= len(words) - k:
            seg = [re.sub(r'[^\w\']', '', w['w'].lower()) for w in words[i:i + k]]
            if seg == [re.sub(r'[^\w\']', '', t) for t in wt]:
                rt = right.split()
                trail = re.sub(r'^.*?([.,!?;:…]*)$', r'\1', words[i + k - 1]['w'])
                if len(rt) == k:
                    for j in range(k):
                        words[i + j]['w'] = rt[j]
                else:  # khác số âm tiết → gộp vào từ đầu, bỏ từ thừa
                    words[i]['w'] = right
                    words[i]['e'] = words[i + k - 1]['e']
                    del words[i + 1:i + k]
                    k2 = 1
                    words[i]['w'] += trail
                    n_fixed += 1; i += k2; continue
                words[i + k - 1]['w'] += trail
                n_fixed += 1
            i += 1
    return n_fixed

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('da')
    ap.add_argument('--clip', default=None, help='a-b (giây gốc)')
    ap.add_argument('--model', default=os.environ.get('REALCUT_WHISPER', 'medium'))
    a = ap.parse_args()
    os.makedirs(a.da, exist_ok=True)
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        die('Thiếu faster-whisper: pip install faster-whisper  (hoặc chạy realcut.py setup)')
    t0 = 0.0
    wav = os.path.join(a.da, 'voice16k.wav')
    cmd = ['ffmpeg', '-nostdin', '-v', 'error', '-y']
    if a.clip:
        s, e = [float(x) for x in a.clip.split('-')]
        cmd += ['-ss', str(s), '-to', str(e)]; t0 = s
    cmd += ['-i', a.src, '-vn', '-ac', '1', '-ar', '16000', wav]
    run(cmd)
    vocab = load_vocab(a.da)
    prompt = 'Video review bất động sản Đắk Lắk. ' + ', '.join(vocab[:60]) + '.'
    print(f'· whisper {a.model} (CPU int8) …', flush=True)
    model = WhisperModel(a.model, device='cpu', compute_type='int8')
    import numpy as np, wave
    with wave.open(wav) as wf:
        audio = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32) / 32768.0
    segs, info = model.transcribe(audio, language='vi', word_timestamps=True, initial_prompt=prompt,
                                  vad_filter=True, vad_parameters=dict(min_silence_duration_ms=300),
                                  beam_size=5, condition_on_previous_text=False)
    words = []
    for sg in segs:
        for w in sg.words or []:
            txt = w.word.strip()
            if txt:
                words.append(dict(w=txt, s=round(w.start + t0, 3), e=round(w.end + t0, 3), p=round(w.probability, 2)))
    n = apply_fixes(words, load_fixes(a.da))
    save_json(os.path.join(a.da, 'words.json'), dict(src=os.path.abspath(a.src), clip=a.clip, words=words))
    txt = ' '.join(w['w'] for w in words)
    open(os.path.join(a.da, 'transcript.txt'), 'w', encoding='utf-8').write(txt + '\n')
    low = [w['w'] for w in words if w['p'] < 0.45]
    print(f'✓ {len(words)} từ · sửa chính tả {n} chỗ → {a.da}/words.json')
    if low:
        print('  ⚠ từ nghe kém chắc chắn (soát lại tên riêng/số):', ', '.join(low[:30]))
    print(f'  (lời đầy đủ: {a.da}/transcript.txt · xem theo mốc: realcut.py phrases)')

if __name__ == '__main__':
    main()
