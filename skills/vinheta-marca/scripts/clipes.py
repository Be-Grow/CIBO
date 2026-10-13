#!/usr/bin/env python3
"""Takes da pessoa para a vinheta.

  clipes.py cortes FONTE [--limiar 12]
      lista os cortes de cena (teaser já editado tem corte a cada ~1-3 s): escolha janelas entre eles.
  clipes.py folha FONTE T1 T2 ... --out folha.jpg
      folha de contato com um quadro por tempo, legendado — uma folha por decisão.
  clipes.py extrai LISTA.txt PUBLIC
      LISTA.txt: uma linha por clipe  ->  nome  fonte  inicio  duracao  [lento]
      (lento = câmera lenta 2x; só em fonte 60 fps). Vertical sai 1080x1920, horizontal 1920x1080, 30 fps.
      Avisa se houver corte de cena dentro da janela (take pulando no meio do painel).
"""
import argparse, os, re, shlex, subprocess, sys

FONT = '/System/Library/Fonts/Supplemental/Arial.ttf'


def cortes(src, limiar=12):
    out = subprocess.run(['ffmpeg', '-v', 'info', '-i', src, '-an', '-vf', f'scale=320:-1,scdet=threshold={limiar}', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    return [float(x) for x in re.findall(r'lavfi\.scd\.time: ([0-9.]+)', out)]


def probe(src):
    o = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,r_frame_rate',
                        '-of', 'csv=p=0', src], capture_output=True, text=True).stdout.strip().split(',')
    n, d = o[2].split('/')
    return int(o[0]), int(o[1]), float(n) / float(d)


ap = argparse.ArgumentParser()
sp = ap.add_subparsers(dest='cmd', required=True)
c = sp.add_parser('cortes'); c.add_argument('fonte'); c.add_argument('--limiar', type=float, default=12)
f = sp.add_parser('folha'); f.add_argument('fonte'); f.add_argument('tempos', nargs='+', type=float); f.add_argument('--out', required=True)
e = sp.add_parser('extrai'); e.add_argument('lista'); e.add_argument('public')
a = ap.parse_args()

if a.cmd == 'cortes':
    print(' '.join(f'{t:.2f}' for t in cortes(a.fonte, a.limiar)))
elif a.cmd == 'folha':
    tmp = a.out + '_q'
    os.makedirs(tmp, exist_ok=True)
    for i, t in enumerate(a.tempos):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', a.fonte, '-frames:v', '1', '-vf',
                        f"scale=-2:360,drawtext=fontfile={FONT}:text='{t:.1f}':fontsize=24:fontcolor=yellow:x=6:y=6", f'{tmp}/{i:02d}.jpg'], check=True)
    cols = min(len(a.tempos), 8)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{tmp}/%02d.jpg', '-vf', f'tile={cols}x{(len(a.tempos) + cols - 1) // cols}',
                    '-frames:v', '1', a.out], check=True)
    print(a.out)
else:
    os.makedirs(a.public, exist_ok=True)
    cache = {}
    for ln in open(a.lista):
        ln = ln.strip()
        if not ln or ln.startswith('#'): continue
        p = shlex.split(ln)
        nome, src, ini, dur = p[0], p[1], float(p[2]), float(p[3])
        lento = len(p) > 4 and p[4] == 'lento'
        w, h, fps = probe(src)
        span = dur / 2 if lento else dur
        if lento and fps < 50: print(f'AVISO {nome}: câmera lenta em fonte {fps:.0f} fps vai engasgar')
        cache.setdefault(src, cortes(src))
        dentro = [t for t in cache[src] if ini + 0.05 < t < ini + span - 0.05]
        if dentro: print(f'AVISO {nome}: corte de cena dentro da janela em {dentro} — mude o início')
        vf = ('setpts=2*PTS,' if lento else '') + 'fps=30,' + ('scale=1080:1920' if h > w else 'scale=1920:1080')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(ini), '-t', str(span), '-i', src, '-an', '-vf', vf,
                        '-c:v', 'libx264', '-crf', '14', '-pix_fmt', 'yuv420p', os.path.join(a.public, nome + '.mp4')], check=True)
        print(f'{nome}.mp4  {ini:.2f}+{span:.2f}s{" lento" if lento else ""}')
