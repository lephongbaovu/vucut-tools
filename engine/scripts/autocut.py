"""vucut · autocut.py — TỰ CẮT đoạn thừa cho video nói-trước-camera, giữ nhịp nói tự nhiên.
Bỏ: khoảng lặng dài, từ đệm (ờ/ừm/ơ…), lặp từ/lặp cụm (nói vấp), câu nói lại (retake: giữ lần nói SAU).
Dùng:  python -X utf8 autocut.py <video> <words.json> <out_dir> [--dry] [--gap 0.35] [--pad 0.115]
         [--sim 0.6] [--drop 12.3-13.1,20-21.5] [--keep 40.2-41.0]
  words.json: phiên âm có mốc từng từ — list [{word|text,start,end}] hoặc {"words":[..]} hoặc {"segments":[{"words":[..]}]}
Ra:   out_dir/cut.mp4        video đã cắt (fade âm 12 ms ở mỗi mối nối)
      out_dir/words_cut.json mốc từng từ theo video MỚI (dùng cho mọi bước sau, không phiên âm lại)
      out_dir/cut.json       {keep:[[a,b]..], cuts_new:[t..], removed:[..], dur_old, dur_new}
--dry: chỉ in bảng đoạn bỏ + ghi cut.json, không render."""
import argparse, json, os, re, subprocess, sys, unicodedata
from difflib import SequenceMatcher

HARD_FILLERS = {"ờ", "ơ", "ừ", "ừm", "ừa", "ờm", "ơm", "ừmm", "ờờ", "hmm", "hm", "um", "uh", "uhm", "ầy", "ê"}
SOFT_FILLERS = {"à", "ạ", "thì"}          # chỉ bỏ khi đứng lẻ (có ngừng ≥ 0.15 s cả trước lẫn sau)
REDUP_OK = {"từ", "dần", "luôn", "thường", "ngày", "người", "nhiều", "đâu", "rõ", "mãi", "xa", "đều", "vừa",
            "càng", "chầm", "lần", "năm", "tháng", "nhà", "ai", "gì", "cái", "rất", "thật", "cứ", "mỗi"}


def norm(t):
    return re.sub(r"[^\w]+", "", unicodedata.normalize("NFC", t.lower()))


def load_words(p):
    d = json.load(open(p, encoding="utf-8"))
    if isinstance(d, dict):
        d = d.get("words") or [w for s in d.get("segments", []) for w in s.get("words", [])]
    out = []
    for w in d:
        t = (w.get("word") or w.get("text") or "").strip()
        if t:
            out.append({"w": t, "n": norm(t), "s": float(w["start"]), "e": float(w["end"]), "drop": None})
    out.sort(key=lambda x: x["s"])
    return out


def ranges(s):
    r = []
    for part in (s or "").split(","):
        if "-" in part:
            a, b = part.split("-", 1)
            r.append((float(a), float(b)))
    return r


def probe_dur(v):
    o = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", v],
                       capture_output=True, text=True).stdout.strip()
    return float(o)


def mark(W, args):
    keep_r, drop_r = ranges(args.keep), ranges(args.drop)
    inr = lambda w, R: any(a <= (w["s"] + w["e"]) / 2 <= b for a, b in R)
    n = len(W)
    # 0 · bỏ cưỡng bức theo --drop
    for w in W:
        if inr(w, drop_r):
            w["drop"] = "cắt tay"
    # 1 · từ đệm
    for i, w in enumerate(W):
        if w["drop"] or not w["n"]:
            continue
        if w["n"] in HARD_FILLERS:
            w["drop"] = "từ đệm"
        elif w["n"] in SOFT_FILLERS:
            gb = w["s"] - W[i - 1]["e"] if i else 9
            ga = W[i + 1]["s"] - w["e"] if i + 1 < n else 9
            if gb >= .15 and ga >= .15:
                w["drop"] = "từ đệm"
    # 2 · lặp cụm liền nhau (nói vấp): A A → bỏ A đầu; xét cụm 4→1 từ
    alive = lambda: [w for w in W if not w["drop"]]
    for size in (4, 3, 2, 1):
        A = alive()
        k = 0
        while k + 2 * size <= len(A):
            a, b = A[k:k + size], A[k + size:k + 2 * size]
            if [x["n"] for x in a] == [x["n"] for x in b] and all(x["n"] for x in a):
                gap = b[0]["s"] - a[-1]["e"]
                legit = size == 1 and a[0]["n"] in REDUP_OK and gap < .15
                # hết câu rồi mở câu mới bằng cùng cụm ("…tuyến cao tốc. Cao tốc Khánh Hòa…") ≠ nói vấp
                if re.search(r"[.,?!;:…]$", a[-1]["w"]): legit = True
                if not legit and gap < 1.2:
                    for x in a:
                        x["drop"] = "lặp từ" if size == 1 else "lặp cụm"
                    k += size
                    continue
            k += 1
    # 3 · câu nói lại (retake): cụm i giống phần đầu cụm j (j = i+1..i+2) → bỏ cụm i, giữ lần nói sau
    A = alive()
    phrases, cur = [], []
    for i, w in enumerate(A):
        cur.append(w)
        nxt = A[i + 1] if i + 1 < len(A) else None
        if nxt is None or nxt["s"] - w["e"] > .45 or re.search(r"[.?!…]$", w["w"]):
            phrases.append(cur)
            cur = []
    for i, p in enumerate(phrases):
        if any(x["drop"] for x in p) or len(p) < 2:
            continue
        a = [x["n"] for x in p]
        for j in (i + 1, i + 2):
            if j >= len(phrases):
                break
            b = [x["n"] for x in phrases[j]][:len(a)]
            if len(b) >= 2 and SequenceMatcher(None, a, b).ratio() >= args.sim:
                for x in p:
                    x["drop"] = "nói lại"
                break
    # 4 · giữ cưỡng bức theo --keep (thắng mọi luật)
    for w in W:
        if w["drop"] and w["drop"] != "cắt tay" and inr(w, keep_r):
            w["drop"] = None


def intervals(W, dur, args):
    """Đoạn giữ = các từ còn lại; ngừng ≤ gap giữ nguyên, ngừng dài rút còn ~2*pad; pad không ăn vào từ bị bỏ."""
    segs = []
    for i, w in enumerate(W):
        if w["drop"]:
            continue
        lo = W[i - 1]["e"] if i else 0.0
        hi = W[i + 1]["s"] if i + 1 < len(W) else dur
        a, b = max(lo, w["s"] - args.pad, 0.0), min(hi, w["e"] + args.pad, dur)
        prev_kept = segs and segs[-1][2] == i - 1 and (w["s"] - W[i - 1]["e"]) <= args.gap
        if prev_kept:
            segs[-1][1], segs[-1][2] = b, i
        else:
            segs.append([a, b, i])
    out = []
    for a, b, _ in segs:
        if out and a - out[-1][1] < .02:
            out[-1][1] = max(out[-1][1], b)
        elif b - a >= .08:
            out.append([round(a, 3), round(b, 3)])
    return out


def remap(t, keep):
    acc = 0.0
    for a, b in keep:
        if t <= b:
            return acc + max(0.0, t - a)
        acc += b - a
    return acc


def render(video, keep, out_mp4):
    F, D = [], .012
    for k, (a, b) in enumerate(keep):
        d = b - a
        F.append(f"[0:v]trim=start={a}:end={b},setpts=PTS-STARTPTS[v{k}];")
        F.append(f"[0:a]atrim=start={a}:end={b},asetpts=PTS-STARTPTS,"
                 f"afade=t=in:st=0:d={D},afade=t=out:st={max(0, d - D):.3f}:d={D}[a{k}];")
    F.append("".join(f"[v{k}][a{k}]" for k in range(len(keep))) + f"concat=n={len(keep)}:v=1:a=1[v][a]")
    script = out_mp4 + ".filter.txt"
    open(script, "w", encoding="utf-8").write("\n".join(F))
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", video, "-filter_complex_script", script, "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
           "-movflags", "+faststart", out_mp4]
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("words"); ap.add_argument("out")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--gap", type=float, default=.35, help="ngừng tự nhiên tối đa giữ nguyên (s)")
    ap.add_argument("--pad", type=float, default=.115, help="đệm trước/sau mỗi đoạn giữ (s)")
    ap.add_argument("--sim", type=float, default=.6, help="ngưỡng giống nhau để coi là câu nói lại")
    ap.add_argument("--drop", default=""); ap.add_argument("--keep", default="")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    W = load_words(args.words)
    dur = probe_dur(args.video)
    mark(W, args)
    keep = intervals(W, dur, args)
    dur_new = sum(b - a for a, b in keep)
    removed, run = [], None
    for w in W:
        if w["drop"]:
            if run and run["reason"] == w["drop"] and w["s"] - run["e"] < .6:
                run["text"] += " " + w["w"]; run["e"] = w["e"]
            else:
                run = {"s": w["s"], "e": w["e"], "reason": w["drop"], "text": w["w"]}
                removed.append(run)
        else:
            run = None
    cuts_new, acc = [], 0.0
    for a, b in keep[:-1]:
        acc += b - a
        cuts_new.append(round(acc, 3))
    res = {"keep": keep, "cuts_new": cuts_new, "removed": [{**r, "s": round(r["s"], 2), "e": round(r["e"], 2)} for r in removed],
           "dur_old": round(dur, 2), "dur_new": round(dur_new, 2)}
    json.dump(res, open(os.path.join(args.out, "cut.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    wc = [{"word": w["w"], "start": round(remap(w["s"], keep), 3), "end": round(remap(w["e"], keep), 3)}
          for w in W if not w["drop"]]
    json.dump(wc, open(os.path.join(args.out, "words_cut.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"Gốc {dur:.2f} s → còn {dur_new:.2f} s (bỏ {dur - dur_new:.2f} s, {100 * (1 - dur_new / dur):.0f} %), "
          f"{len(keep)} đoạn, {len(cuts_new)} mối nối")
    print("ĐOẠN BỎ (giây gốc · lý do · lời):")
    for r in removed:
        print(f"  {r['s']:7.2f}–{r['e']:6.2f}  {r['reason']:<8} {r['text']}")
    print("Khoảng lặng dài được rút: tự động theo --gap/--pad.")
    print("Mối nối (giây MỚI) — phủ bằng panel B-roll hoặc đổi tỉ lệ khung:", ", ".join(map(str, cuts_new)))
    if not args.dry:
        render(args.video, keep, os.path.join(args.out, "cut.mp4"))
        print("→", os.path.join(args.out, "cut.mp4"))


if __name__ == "__main__":
    main()
