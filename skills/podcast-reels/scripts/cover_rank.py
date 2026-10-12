#!/usr/bin/env python3
"""Ranqueia candidatos a capa com o Vision da Apple e entrega UMA folha com os melhores.

uso: cover_rank.py SCAN.json VIDEO [--top 8] [--pool 120] [--crop-h 992] [--avoid 6415.6,5909.5]
                   [--sheet capas_top.jpg] [--json capas_top.json]

SCAN.json vem do `cover_scan.py` (YuNet a 2 qps). Daqui saem até `--pool` candidatos (rosto
grande, de frente, telas estáticas fora, ≥ 3 s entre si), cada um recortado como a capa
(9:16, `--crop-h` igual ao do clipe) e avaliado pelo `face_quality` (Vision): qualidade do
rosto, pose, olhos, mão acima do queixo e tamanho do rosto.

Nota = qualidade + 0,1·tamanho − 0,15·mão acima do queixo − 0,05·rosto virado (>25°) −
0,1·olho fechado. Calibrada com as capas do João (12/10/2026): as 6 aprovadas ("de rosto tá
ótimo") ficaram acima das 3 reprovadas (braço erguido, dedo apontando, rosto pequeno).
Ainda assim é triagem: olhe a folha antes de escolher.
"""
import argparse, json, os, subprocess, sys, tempfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = os.path.expanduser("~/.cache/cibo/bin/face_quality")


def ensure_bin():
    src = os.path.join(HERE, "face_quality.swift")
    if not os.path.exists(BIN) or os.path.getmtime(BIN) < os.path.getmtime(src):
        os.makedirs(os.path.dirname(BIN), exist_ok=True)
        r = subprocess.run(["swiftc", "-O", src, "-o", BIN], capture_output=True, text=True)
        if r.returncode:
            sys.exit("face_quality não compilou (precisa do swiftc do macOS): " + r.stderr[-500:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scan"); ap.add_argument("video")
    ap.add_argument("--top", type=int, default=8); ap.add_argument("--pool", type=int, default=120)
    ap.add_argument("--crop-h", type=int, default=1080)
    ap.add_argument("--avoid", default="")
    ap.add_argument("--sheet", default="capas_top.jpg"); ap.add_argument("--json", default="capas_top.json")
    a = ap.parse_args()
    ensure_bin()
    d = np.array(json.load(open(a.scan)))
    t, x, w, sc, sh, fr, mo = d.T
    # tela parada (vinheta de abertura com foto, intervalo): rosto que não se mexe 1 px em ±5 s
    stat = np.zeros(len(t), bool)
    for i in range(len(t)):
        for nb in ((t >= t[i] - 5) & (t <= t[i]), (t >= t[i]) & (t <= t[i] + 5)):   # antes ou depois
            if nb.sum() >= 6 and np.ptp(x[nb]) < 1.5 and np.ptp(w[nb]) < 1.5:
                stat[i] = True
    st = t[stat]   # alarga 1 s: a dissolvência entre a tela parada e a câmera também é ruim
    stat = np.array([st.size > 0 and np.abs(st - v).min() <= 1.0 for v in t])
    m = (~stat) & (w >= np.percentile(w[~stat], 60)) & (sc > 0.8) & (fr > 0.35)
    avoid = [float(v) for v in a.avoid.split(",") if v]
    pre = (w / w.max()) + 0.6 * np.minimum(sh, np.percentile(sh, 95)) / np.percentile(sh, 95) + 0.5 * fr
    sel = []
    for i in np.argsort(-np.where(m, pre, -9)):
        if not m[i] or len(sel) >= a.pool:
            break
        if all(abs(t[i] - t[j]) >= 3 for j in sel) and all(abs(t[i] - v) >= 3 for v in avoid):
            sel.append(i)
    cw = int(round(a.crop_h * 9 / 16)) // 2 * 2
    with tempfile.TemporaryDirectory() as tmp:
        files = []
        for i in sel:
            cx = int(max(0, min(1920 - cw, x[i] - cw / 2)))
            f = os.path.join(tmp, f"{t[i]:.1f}_{cx}.png")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t[i]:.2f}", "-i", a.video, "-frames:v", "1",
                            "-vf", f"crop={cw}:{a.crop_h}:{cx}:0,scale=540:-2", f])
            files.append(f)
        out = subprocess.run([BIN, *files], capture_output=True, text=True).stdout
        rows = []
        for line in out.splitlines():
            r = json.loads(line)
            if not r.get("faces"):
                continue
            q, ar, yaw, eyes = r.get("quality") or 0, r.get("area", 0), abs(r.get("yaw") or 0), r.get("eyes") or 0.2
            s = q + 0.1 * min(ar / 0.085, 1) - 0.15 * bool(r.get("hand_up")) - 0.05 * (yaw > 25) - 0.1 * (eyes < 0.12)
            tt, cx = os.path.basename(r["file"])[:-4].split("_")
            rows.append({"t": float(tt), "cover_src_x": int(cx) + cw // 2, "score": round(s, 3), "quality": round(q, 3),
                         "hand_up": r.get("hand_up"), "yaw": round(yaw), "eyes": round(eyes, 2), "img": r["file"]})
        rows.sort(key=lambda r: -r["score"])
        top = rows[: a.top]
        # folha: uma linha, rótulo com tempo e nota
        ins, lab = [], []
        for j, r in enumerate(top):
            ins += ["-i", r["img"]]
            lab.append(f"[{j}:v]scale=270:-2,drawtext=text='{r['t']:.1f}s  {r['score']:.2f}':x=6:y=6:fontsize=20:"
                       f"fontcolor=yellow:box=1:boxcolor=black@0.6[l{j}]")
        if top:
            fc = ";".join(lab) + ";" + "".join(f"[l{j}]" for j in range(len(top))) + f"hstack={len(top)}" if len(top) > 1 else lab[0].replace("[l0]", "")
            subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", fc, "-q:v", "4", a.sheet])
    for r in top:
        r.pop("img")
    json.dump(top, open(a.json, "w"), indent=1)
    print(f"{len(rows)} avaliados; top {len(top)} em {a.sheet} / {a.json}")
    for r in top:
        print(f"  {r['t']:8.1f}s  x={r['cover_src_x']}  nota {r['score']:.2f}  (q {r['quality']:.2f}, mão {r['hand_up']}, yaw {r['yaw']})")


if __name__ == "__main__":
    main()
