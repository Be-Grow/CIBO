#!/usr/bin/env python3
"""Acha os momentos em que a pessoa desvia o olhar da câmera (cabeça virando ou olho correndo para o lado).
Feedback da Priscilla (13/10/2026): "às vezes ela olha para o lado e isso aparece no corte".

uso: olhar.py VIDEO.mov [--passo 3] [--min 0.3] [--folha saida.jpg] [--json saida.json]
  VIDEO   câmera do reel (public/rNN/camera.mov, tempo = tempo editado)
Mede a cada `passo` quadros, com o YuNet do face_track (olhos, nariz):
  - giro da cabeça: nariz em relação ao meio dos olhos, pela distância entre os olhos
  - olho: centro do ponto mais escuro (pupila) em volta de cada olho, pela distância entre os olhos
A referência é a mediana do vídeo (o jeito dela de olhar para a câmera). Marca trechos de pelo menos
`min` segundos fora da faixa e grava uma folha com o rosto no meio de cada trecho.
"""
import argparse, json, subprocess, sys
from pathlib import Path
import numpy as np, cv2

ap = argparse.ArgumentParser()
ap.add_argument('video'); ap.add_argument('--passo', type=int, default=3); ap.add_argument('--min', type=float, default=0.3)
ap.add_argument('--giro', type=float, default=0.09); ap.add_argument('--olho', type=float, default=0.07)
ap.add_argument('--folha'); ap.add_argument('--json')
a = ap.parse_args()

MODEL = str(Path.home() / '.cache/yunet/face_detection_yunet_2023mar.onnx')
cap = cv2.VideoCapture(a.video); fps = cap.get(cv2.CAP_PROP_FPS) or 29.97
W, H = int(cap.get(3)), int(cap.get(4)); S = 0.5
det = cv2.FaceDetectorYN.create(MODEL, '', (int(W * S), int(H * S)), 0.6, 0.3, 5000)


def pupila(gray, c, r):
    x0, y0 = int(c[0] - r), int(c[1] - r * 0.6)
    p = gray[max(y0, 0):int(c[1] + r * 0.6), max(x0, 0):int(c[0] + r)]
    if p.size < 50:
        return None
    p = cv2.GaussianBlur(p, (5, 5), 0)
    thr = np.percentile(p, 8)
    ys, xs = np.nonzero(p <= thr)
    if len(xs) < 5:
        return None
    return (xs.mean() + max(x0, 0) - c[0])


amostras = []
i = 0
while True:
    ok = cap.grab()
    if not ok:
        break
    if i % a.passo == 0:
        _, im = cap.retrieve()
        sm = cv2.resize(im, (int(W * S), int(H * S)))
        _, f = det.detect(sm)
        if f is not None and len(f):
            f = max(f, key=lambda r: r[2] * r[3]) / S
            le, re_, no = np.array(f[4:6]), np.array(f[6:8]), np.array(f[8:10])
            iod = np.linalg.norm(re_ - le)
            giro = (no[0] - (le[0] + re_[0]) / 2) / max(iod, 1)
            g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
            ps = [pupila(g, e, iod * 0.28) for e in (le, re_)]
            ps = [p for p in ps if p is not None]
            olho = (np.mean(ps) / iod) if ps else np.nan
            amostras.append((i / fps, giro, olho, f[:4].tolist()))
        else:
            amostras.append((i / fps, np.nan, np.nan, None))
    i += 1
cap.release()

t = np.array([s[0] for s in amostras]); gi = np.array([s[1] for s in amostras]); ol = np.array([s[2] for s in amostras])
dg = gi - np.nanmedian(gi); do = ol - np.nanmedian(ol)
fora = (np.abs(dg) > a.giro) | (np.abs(np.nan_to_num(do)) > a.olho)
trechos, k = [], 0
while k < len(t):
    if fora[k]:
        j = k
        while j + 1 < len(t) and (fora[j + 1] or (j + 2 < len(t) and fora[j + 2])):   # tolera 1 amostra no meio
            j += 1
        if t[j] - t[k] + a.passo / fps >= a.min:
            m = k + int(np.nanargmax(np.abs(dg[k:j + 1]) + np.abs(np.nan_to_num(do[k:j + 1]))))
            lado = 'direita' if (dg[m] + np.nan_to_num(do[m])) > 0 else 'esquerda'
            trechos.append(dict(ini=round(float(t[k]), 2), fim=round(float(t[j] + a.passo / fps), 2), pico=round(float(t[m]), 2),
                                giro=round(float(dg[m]), 3), olho=round(float(np.nan_to_num(do[m])), 3), lado=lado))
        k = j + 1
    else:
        k += 1
print(f'{len(t)} amostras, referência giro {np.nanmedian(gi):.3f} olho {np.nanmedian(ol):.3f}; {len(trechos)} trecho(s) fora:')
for tr in trechos:
    print(f"  {tr['ini']:6.2f}-{tr['fim']:6.2f}s  pico {tr['pico']:6.2f}  giro {tr['giro']:+.3f}  olho {tr['olho']:+.3f}  ({tr['lado']})")
if a.json:
    json.dump(trechos, open(a.json, 'w'), indent=1)
if a.folha and trechos:
    cap = cv2.VideoCapture(a.video); tiles = []
    for tr in trechos[:24]:
        cap.set(cv2.CAP_PROP_POS_MSEC, tr['pico'] * 1000); ok, im = cap.read()
        if not ok:
            continue
        s = next((x for x in amostras if abs(x[0] - tr['pico']) < 0.05 and x[3]), None)
        if s:
            x, y, w, h = map(int, s[3]); im = im[max(y - h // 3, 0):y + h + h // 4, max(x - w // 3, 0):x + w + w // 3]
        im = cv2.resize(im, (240, 260)); cv2.putText(im, f"{tr['pico']:.1f}s {tr['lado'][:3]}", (6, 24), 0, 0.7, (0, 255, 255), 2)
        tiles.append(im)
    while len(tiles) % 6:
        tiles.append(np.zeros_like(tiles[0]))
    rows = [np.hstack(tiles[r:r + 6]) for r in range(0, len(tiles), 6)]
    cv2.imwrite(a.folha, np.vstack(rows))
    print('folha:', a.folha)
