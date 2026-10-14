#!/usr/bin/env python3
"""QA denso dos painéis: renderiza o reel a cada STEP s dentro da tela dividida, recorta a faixa do painel
(+ a legenda) e monta folhas de 6×4 com o tempo marcado, para achar sobreposição e corte de elemento.
uso: qa_paineis.py PROJ rNN [step=0.5] [--video PREVIA.mp4]  → PROJ/05_qa/rNN_paineis_*.jpg
  --video: tira os quadros da prévia já renderizada (ffmpeg), bem mais rápido que renderStill quadro a quadro"""
import json, os, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw
P = Path(sys.argv[1]); R = sys.argv[2]; STEP = float(sys.argv[3]) if len(sys.argv) > 3 and not sys.argv[3].startswith('--') else 0.5
ENG = Path(__file__).resolve().parent.parent; PUB = P / '04_work/public'
props = json.load(open(PUB / R / 'props.json'))
H = (props.get('theme', {}).get('layout', {}) or {}).get('splitH', 940)
ts = []
for g in props['split']:
    t = g['s'] + 0.45
    while t < g['e'] - 0.1:
        ts.append(round(t, 2)); t += STEP
out = Path(os.environ.get('TMPDIR', '/tmp')) / f'qa_{R}'
subprocess.run(['rm', '-rf', str(out)])
env = dict(os.environ, PUBLIC_DIR=str(PUB))
VID = sys.argv[sys.argv.index('--video') + 1] if '--video' in sys.argv else None
if VID:
    out.mkdir(parents=True, exist_ok=True)
    for t in ts:
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', VID, '-frames:v', '1', '-vf', 'scale=1080:1920', str(out / f'f_{t}.png')], check=True)
else:
    subprocess.run(['node', 'stills.mjs', str(PUB / R / 'props.json'), str(out)] + [str(t) for t in ts], cwd=ENG / 'mg', env=env, check=True,
                   stdout=subprocess.DEVNULL)
W, HH = 270, int(270 * H / 1080)
pages = [ts[i:i + 24] for i in range(0, len(ts), 24)]
for n, page in enumerate(pages):
    sheet = Image.new('RGB', (W * 6, HH * 4), 'black'); d = ImageDraw.Draw(sheet)
    for k, t in enumerate(page):
        inv = any(g.get('inv') and g['s'] <= t <= g['e'] for g in props['split'])
        PAD = (props.get('theme', {}).get('layout', {}) or {}).get('invPad', 150)
        box = (0, 1920 - H - PAD - 110, 1080, 1920 - PAD - 110) if inv else (0, 0, 1080, H)   # invertida: painel embaixo + legenda acima dele
        im = Image.open(out / f'f_{t}.png').convert('RGB').crop(box).resize((W, HH))
        sheet.paste(im, ((k % 6) * W, (k // 6) * HH)); d.text(((k % 6) * W + 4, (k // 6) * HH + 3), f'{t:.1f}', fill='yellow')
    f = P / '05_qa' / f'{R}_paineis_{n + 1}.jpg'; sheet.save(f, quality=88); print(f)
