#!/usr/bin/env python3
"""Recentraliza na horizontal o recorte de cada plano parado no meio dos olhos (mediana de 5 quadros do plano).
O face_track deixa planos alguns % para um lado e o punch/zoom amplia isso; na emenda entre um plano torto e um
centrado o pulo aparece (Priscilla 03, 13/10/2026: "não tá com ela centralizada, um pouco pra esquerda").
uso: centraliza.py job.json      (só mexe em framings [x, y, w, h]; planos com movimento, dict com kx, ficam)"""
import json, subprocess, sys
from pathlib import Path
import numpy as np, cv2

jf = sys.argv[1]; j = json.load(open(jf))
det = cv2.FaceDetectorYN.create(str(Path.home() / '.cache/yunet/face_detection_yunet_2023mar.onnx'), '', (540, 960), 0.6, 0.3, 5000)
rot = {'clock': 'transpose=1,', 'cclock': 'transpose=2,'}.get(j.get('rotate'), '')
SW = 2160 if rot else 3840
for k, (a, b, _) in enumerate(j['shots']):
    fr = j['framings'][k]
    if not isinstance(fr, list):
        continue
    xs = []
    for t in np.linspace(a + 0.2, b - 0.2, 5):
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.2f}', '-noautorotate', '-i', j['src'], '-frames:v', '1', '-vf', f'{rot}scale=540:960',
                              '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture_output=True).stdout
        if len(raw) != 540 * 960 * 3:
            continue
        _, f = det.detect(np.frombuffer(raw, np.uint8).reshape(960, 540, 3))
        if f is not None and len(f):
            f = max(f, key=lambda r: r[2] * r[3]); xs.append((f[4] + f[6]) / 2 * SW / 540)
    if not xs:
        continue
    x, y, w, h = fr
    nx = int(round(min(max(np.median(xs) - w / 2, 0), SW - w)))
    if abs(nx - x) > 4:
        print(f'plano {k}: x {x} → {nx} ({(nx - x) / w:+.1%})')
    j['framings'][k] = [nx, y, w, h]
json.dump(j, open(jf, 'w'), ensure_ascii=False, indent=1)
