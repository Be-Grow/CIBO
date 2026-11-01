#!/usr/bin/env python3
"""Cortes a partir do EPISÓDIO EDITADO (editor, 01/11/2026: "é pra usar a versão editada pra pegar os cortes") e enquadramento
por plano de câmera (EP 10: o Daniel tem dois ângulos; o pan era um só por trecho e a troca no meio deixava ele na borda /
cadeira vazia).

Para cada rNN: segs do bruto (segs_bruto.json, guardado na 1ª vez) -> tempo do editado (07_manifests/episodio_keeps.json);
trecho que caiu fora do editado é avisado e cortado; cada trecho é partido em toda troca de câmera (ffmpeg scdet) e cada
pedaço ganha crops[{at, cx}] pelo maior rosto no meio do pedaço (OpenCV). reel.json: src = editado, zoom 1.7778.

uso: cortes_do_editado.py PROJ SRC_RELATIVO_A_01_sources r01 [r02 …]   (rode com o venv da bombordo-boreste: cv2)
Depois: reel.py voz/legenda/props/mix e fila_davinci.py.
"""
import json, os, re, subprocess, sys
import cv2, numpy as np

P = os.path.abspath(sys.argv[1]); SRC = sys.argv[2]; RS = sys.argv[3:]
SRCP = os.path.join(P, '01_sources', SRC)
K = json.load(open(os.path.join(P, '07_manifests', 'episodio_keeps.json')))['keeps_s']
FACE = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')


def ed(raw):
    acc = 0.0
    for a, b in K:
        if a <= raw <= b: return acc + raw - a
        acc += b - a
    return None


def cortes_de_camera(a, b):
    out = subprocess.run(['ffmpeg', '-v', 'info', '-ss', f'{a:.3f}', '-to', f'{b:.3f}', '-i', SRCP, '-an', '-vf',
                          'scale=320:-1,scdet=threshold=12', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return [a + float(t) for t in re.findall(r'lavfi\.scd\.time: ([\d.]+)', out)]


def rosto_cx(t):
    fr = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.3f}', '-i', SRCP, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'],
                        capture_output=True).stdout
    im = np.frombuffer(fr, np.uint8).reshape(1080, 1920)
    fs = FACE.detectMultiScale(im, 1.1, 6, minSize=(120, 120))
    if not len(fs): return None
    x, y, w, h = max(fs, key=lambda f: f[2] * f[3]); return int(x + w / 2)


for r in RS:
    W = os.path.join(P, '04_work', r)
    bru = os.path.join(W, 'segs_bruto.json')
    if not os.path.exists(bru): os.replace(os.path.join(W, 'segs.json'), bru)
    S = []
    for a, b in json.load(open(bru)):
        A, B = ed(a), ed(b)
        if A is None or B is None or B - A < 0.3:
            print(f'{r}: trecho {a:.2f}-{b:.2f} do bruto está fora do episódio editado (cartilha) -> sai'); continue
        S.append([round(A, 3), round(B, 3)])
    pecas, crops = [], []
    for a, b in S:
        cuts = [c for c in cortes_de_camera(a, b) if a + 0.3 < c < b - 0.3]
        bord = [a] + cuts + [b]
        for x, y in zip(bord, bord[1:]):
            pecas.append([round(x, 3), round(y, 3)])
            cx = rosto_cx((x + y) / 2) or (crops[-1]['cx'] if crops else 960)
            crops.append({'at': round(x, 3), 'cx': cx})
    crops = sorted(crops, key=lambda c: c['at']); crops[0] = dict(crops[0], at=0)
    json.dump(pecas, open(os.path.join(W, 'segs.json'), 'w'))
    C = json.load(open(os.path.join(W, 'reel.json'))); C.update(src=SRC, crops=crops, zoom=1.7778)
    json.dump(C, open(os.path.join(W, 'reel.json'), 'w'), ensure_ascii=False, indent=1)
    print(f'{r}: {len(S)} trechos -> {len(pecas)} pedaços por plano; cx {[c["cx"] for c in crops]}')
