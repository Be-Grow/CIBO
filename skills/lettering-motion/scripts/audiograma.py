#!/usr/bin/env python3
"""Audiograma (podcast só de áudio) numa linha: áudio + legenda + foto + título -> MP4 9:16.

uso: audiograma.py --audio EP.wav --mg PROJETO_REMOTION --out audiograma.mp4 [--srt legenda.srt]
                   [--image foto.png] [--title "..."] [--subtitle "@perfil"] [--color "#4F95FF"]
                   [--inicio S --fim S]

`--mg` é a pasta Remotion do projeto (cópia de assets/remotion-template com `npm i`). A legenda
vem de um SRT (Whisper ou `alinha_mfa.py --srt`, este com tempo exato); blocos curtos de até ~3
palavras são montados aqui. O trecho `--inicio/--fim` (s) corta o áudio e a legenda juntos.
"""
import argparse, json, re, shutil, subprocess
from pathlib import Path


def srt(path):
    out = []
    for b in re.split(r"\n\s*\n", Path(path).read_text(encoding="utf-8").strip()):
        m = re.search(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", b)
        if m:
            g = [int(x) for x in m.groups()]
            t = " ".join(l for l in b.splitlines() if "-->" not in l and not l.strip().isdigit()).strip()
            out.append((g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000, g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000, t))
    return out


def blocos(cues, maxw=3, maxc=22):
    """Junta palavras (SRT palavra a palavra) em blocos curtos de leitura."""
    res, cur = [], []
    for s, e, t in cues:
        if cur and (len(cur) >= maxw or len(" ".join(x[2] for x in cur + [(s, e, t)])) > maxc or s - cur[-1][1] > 0.35
                    or cur[-1][2].endswith((".", "?", "!"))):
            res.append(cur); cur = []
        cur.append((s, e, t))
    if cur:
        res.append(cur)
    return [{"s": round(b[0][0], 3), "e": round(b[-1][1], 3), "t": " ".join(x[2] for x in b)} for b in res]


def main():
    ap = argparse.ArgumentParser()
    for o in ("--audio", "--mg", "--out"):
        ap.add_argument(o, required=True)
    for o in ("--srt", "--image", "--title", "--subtitle", "--color"):
        ap.add_argument(o)
    ap.add_argument("--inicio", type=float, default=0.0); ap.add_argument("--fim", type=float)
    a = ap.parse_args()
    mg = Path(a.mg); pub = mg / "public"; pub.mkdir(exist_ok=True)
    cut = ["-ss", str(a.inicio)] + (["-to", str(a.fim)] if a.fim else [])
    subprocess.run(["ffmpeg", "-v", "error", "-y", *cut, "-i", a.audio, "-vn", "-ac", "2", "-ar", "48000",
                    str(pub / "ag_audio.wav")], check=True)
    props = {"audio": "ag_audio.wav", "title": a.title or "", "subtitle": a.subtitle or "", "captions": []}
    if a.image:
        shutil.copy2(a.image, pub / ("ag_img" + Path(a.image).suffix)); props["image"] = "ag_img" + Path(a.image).suffix
    if a.color:
        props["color"] = a.color
    if a.srt:
        cues = [(s - a.inicio, e - a.inicio, t) for s, e, t in srt(a.srt) if s >= a.inicio and (not a.fim or e <= a.fim)]
        props["captions"] = blocos(cues) if cues and max(len(t.split()) for *_, t in cues) <= 1 else \
            [{"s": round(s, 3), "e": round(e, 3), "t": t} for s, e, t in cues]
    pj = mg / "ag_props.json"
    pj.write_text(json.dumps(props, ensure_ascii=False))
    r = subprocess.run(["npx", "remotion", "render", "src/index.ts", "Audiogram", str(Path(a.out).resolve()),
                        f"--props={pj}"], cwd=mg, capture_output=True, text=True)
    print(("OK " + a.out) if r.returncode == 0 else ("ERRO\n" + (r.stderr or r.stdout)[-800:]))


if __name__ == "__main__":
    main()
