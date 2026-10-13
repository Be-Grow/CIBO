#!/usr/bin/env python3
"""Autoteste da vinheta-marca (sintético, sem arquivos externos):  python3 autoteste.py
- prepara_logo: logo falsa com símbolo + nome + assinatura -> 3 faixas, margem transparente, logo.json coerente
- clipes: vídeo falso com corte em 1,0 s -> detecta o corte e avisa quando a janela cruza o corte
"""
import json, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
tmp = tempfile.mkdtemp(prefix='cibo_vinheta_')
fails = []


def check(nome, ok, info=''):
    print(('ok   ' if ok else 'FALHA') + f' {nome} {info}')
    if not ok: fails.append(nome)


im = Image.new('RGBA', (900, 600), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
d.ellipse((350, 0, 550, 200), fill=(181, 158, 100, 255))     # símbolo
d.rectangle((50, 250, 850, 380), fill=(255, 255, 255, 255))  # nome
d.rectangle((250, 450, 650, 520), fill=(255, 255, 255, 255)) # assinatura
im.save(f'{tmp}/logo.png')
subprocess.run([sys.executable, f'{HERE}/prepara_logo.py', f'{tmp}/logo.png', f'{tmp}/public', '--pad', '100'], capture_output=True, check=True)
js = json.load(open(f'{tmp}/public/logo.json'))
p = js['parts']
check('3 faixas', len(p) == 3, str([(x['w'], x['h'], x['top']) for x in p]))
check('posições', len(p) == 3 and p[0]['top'] == 0 and p[1]['top'] == 250 and p[2]['top'] == 450 and js['srcH'] == 521)
a0 = Image.open(f'{tmp}/public/logo_part0.png')
check('margem transparente', a0.size == (p[0]['w'] + 200, p[0]['h'] + 200) and a0.getpixel((5, 5))[3] == 0, str(a0.size))

v = f'{tmp}/v.mp4'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'testsrc2=s=320x568:r=30:d=1', '-f', 'lavfi', '-i', 'smptebars=s=320x568:r=30:d=1',
                '-filter_complex', '[0][1]concat=n=2:v=1[o]', '-map', '[o]', '-pix_fmt', 'yuv420p', v], check=True)
out = subprocess.run([sys.executable, f'{HERE}/clipes.py', 'cortes', v], capture_output=True, text=True).stdout.split()
check('detecta corte', any(abs(float(x) - 1.0) < 0.07 for x in out), str(out))
open(f'{tmp}/l.txt', 'w').write(f'a {v} 0.1 0.6\nb {v} 0.6 0.8\n')
out = subprocess.run([sys.executable, f'{HERE}/clipes.py', 'extrai', f'{tmp}/l.txt', f'{tmp}/pub'], capture_output=True, text=True).stdout
check('avisa janela que cruza corte', 'AVISO b' in out and 'AVISO a' not in out, out.strip().replace('\n', ' | '))
check('vertical sai 1080x1920', '1080,1920' in subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=width,height', '-of', 'csv=p=0',
                                                              f'{tmp}/pub/a.mp4'], capture_output=True, text=True).stdout)

print('\nTUDO OK' if not fails else f'\n{len(fails)} FALHA(S): {fails}')
sys.exit(1 if fails else 0)
