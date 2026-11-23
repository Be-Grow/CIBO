"""Varre uma gravação inteira (2 qps) e pontua quadros candidatos a capa.
Pontua: rosto grande (close), nítido, de frente, olhos visíveis, boca larga (sorriso/fala enfática).
uso: cover_scan.py SAIDA.json VIDEO  -> lista [t, x_centro, w, score, sharp, front, mouth]"""
import json, os, subprocess, sys
import cv2, numpy as np
MODEL = os.environ.get("YUNET", str(Path(__file__).resolve().parents[2] / "content-hub" / "assets" / "yunet.onnx"))
SRC = sys.argv[2] if len(sys.argv) > 2 else sys.exit("uso: cover_scan.py SAIDA.json VIDEO")
W, H = 960, 540; FPS = 2
det = cv2.FaceDetectorYN.create(MODEL, '', (W, H), 0.7)
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', SRC, '-vf', f'fps={FPS},scale={W}:{H}', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'],
                     stdout=subprocess.PIPE)
out = []; i = 0
while True:
    b = p.stdout.read(W * H * 3)
    if len(b) < W * H * 3: break
    fr = np.frombuffer(b, np.uint8).reshape(H, W, 3)
    t = i / FPS; i += 1
    _, faces = det.detect(fr)
    if faces is None: continue
    f = max(faces, key=lambda z: z[2])
    x, y, w, h = f[:4]; sc = f[14]
    if w < 45: continue
    re, le, no, rm, lm = f[4:6], f[6:8], f[8:10], f[10:12], f[12:14]
    eye = np.linalg.norm(le - re) + 1e-6
    front = 1 - abs((no[0] - re[0]) / (le[0] - re[0] + 1e-6) - 0.5) * 2   # 1 = de frente
    mouth = np.linalg.norm(lm - rm) / eye                                  # sorriso abre os cantos
    x0, y0 = int(max(0, x)), int(max(0, y))
    g = cv2.cvtColor(fr[y0:int(y + h), x0:int(x + w)], cv2.COLOR_BGR2GRAY)
    sharp = float(cv2.Laplacian(g, cv2.CV_64F).var()) if g.size else 0
    out.append([round(t, 2), round(float(x + w / 2) * 2, 1), round(float(w) * 2, 1), round(float(sc), 3),
                round(sharp, 1), round(float(front), 3), round(float(mouth), 3)])
json.dump(out, open(sys.argv[1], 'w'))
print(i, 'quadros,', len(out), 'com rosto')
