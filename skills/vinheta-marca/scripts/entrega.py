#!/usr/bin/env python3
"""Fecha a entrega da vinheta: junta vídeo (ProRes do Remotion) + som (mix.py) em MP4 H.264 e master
ProRes, para 1080p, 4K e versão curta; move a entrega anterior para 04_work/vN (uma versão só em
06_entregas) e gera o QA (folha a cada 0,5 s, blackdetect, recorte ampliado da logo com gamma alto).

Uso: entrega.py PROJETO "Vinheta - Nome da Marca" --video out/v.mov --som som.wav
                [--video4k out/v4k.mov] [--curta out/curta.mov --curta-ini 9.267] [--logo-em 13.0]
  --curta-ini  segundo da vinheta longa onde a curta começa (CURTA_INI/30, impresso pelo Remotion: impacto - 2,5 s)
  --logo-em    segundo com a logo completa e o glow no máximo (padrão: fim - 4 s), para o recorte de QA
"""
import argparse, os, re, shutil, subprocess

ap = argparse.ArgumentParser()
ap.add_argument('projeto'); ap.add_argument('nome')
ap.add_argument('--video', required=True); ap.add_argument('--som', required=True)
ap.add_argument('--video4k'); ap.add_argument('--curta'); ap.add_argument('--curta-ini', type=float)
ap.add_argument('--logo-em', type=float)
a = ap.parse_args()

ent = os.path.join(a.projeto, '06_entregas'); qa = os.path.join(a.projeto, '04_work', 'qa')
os.makedirs(ent, exist_ok=True); os.makedirs(qa, exist_ok=True)
run = lambda c: subprocess.run(c, check=True)

# versão anterior -> 04_work/vN
velhos = [f for f in os.listdir(ent) if f.startswith(a.nome)]
if velhos:
    n = 1
    while os.path.exists(os.path.join(a.projeto, '04_work', f'v{n}')): n += 1
    dst = os.path.join(a.projeto, '04_work', f'v{n}'); os.makedirs(dst)
    for f in velhos: shutil.move(os.path.join(ent, f), dst)
    print(f'entrega anterior -> 04_work/v{n} ({len(velhos)} arquivos)')


def mux(video, sufixo, crf, extra_a=None):
    base = os.path.join(ent, a.nome + sufixo)
    af = ['-af', extra_a] if extra_a else []
    run(['ffmpeg', '-v', 'error', '-y', '-i', video, '-i', a.som, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'slow',
         '-crf', str(crf), '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
         *af, '-c:a', 'aac', '-b:a', '320k', '-movflags', '+faststart', '-shortest', base + '.mp4'])
    run(['ffmpeg', '-v', 'error', '-y', '-i', video, '-i', a.som, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', *af,
         '-c:a', 'pcm_s24le', '-shortest', base + ' (master ProRes).mov'])
    return base + '.mp4'


saidas = [mux(a.video, '', 15)]
if a.video4k: saidas.append(mux(a.video4k, ' 4K', 16))
if a.curta:
    if a.curta_ini is None: raise SystemExit('--curta exige --curta-ini')
    # som da curta = mesmo som a partir do ponto de entrada, com fade de 0,27 s
    a.som, som_longo = os.path.join(qa, 'som_curta.wav'), a.som
    run(['ffmpeg', '-v', 'error', '-y', '-ss', str(a.curta_ini), '-i', som_longo, '-af', 'afade=t=in:d=0.27', '-c:a', 'pcm_s24le', a.som])
    saidas.append(mux(a.curta, ' (curta)', 15))

for mp4 in saidas:
    pr = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=width,height', '-of', 'csv=p=0', mp4],
                        capture_output=True, text=True).stdout.split()
    bl = re.findall(r'black_start:(\S+) black_end:(\S+)', subprocess.run(
        ['ffmpeg', '-i', mp4, '-vf', 'blackdetect=d=0.1:pix_th=0.05', '-an', '-f', 'null', '-'], capture_output=True, text=True).stderr)
    print(f'{os.path.basename(mp4)}: {" ".join(pr)} | preto: {bl or "nenhum"}')

longa = saidas[0]
dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', longa], capture_output=True, text=True).stdout)
run(['ffmpeg', '-v', 'error', '-y', '-i', longa, '-vf', 'fps=2,scale=320:-1,tile=6x6', '-frames:v', '1', os.path.join(qa, 'folha.jpg')])
t = a.logo_em if a.logo_em is not None else dur - 4
run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', longa, '-frames:v', '1', '-vf', 'crop=1100:560:410:160,eq=gamma=1.8', os.path.join(qa, 'logo_gamma.jpg')])
print(f'QA: {qa}/folha.jpg (preto no 1,5 s inicial = cold open, proposital) e {qa}/logo_gamma.jpg (procure borda retangular no glow)')
if not os.environ.get('CIBO_SEM_OPEN'): subprocess.run(['open', ent])
