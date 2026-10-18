"""Componentes do Histórias do Porto para a timeline do DaVinci (o render final é feito lá).

  python3 componentes.py <historia>      # ginecologista | grego

Grava em <historia>/: ref_<nome>.mov (painéis 1080xP, ProRes 422 HQ), legenda_animada.mov (ProRes 4444
com alfa, faixa 1080x560), seam_shadow.png, fade_preto.mov (ProRes 4444 com alfa), trilha_mix.wav
(trilha a -27 dB com ducking pela voz e silêncio no punchline), capa.png e xml_cfg.json.
"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
K = sys.argv[1]
D_ = os.path.join(HERE, K)
os.chdir(D_)
MASTER = '/Volumes/SSD/Movies/Edição/Mídia/content/bombordo/EP 06 - Felipe Segins/2026-10-01 18-18-46.mp4'
EP04 = '/Volumes/SSD/Movies/Edição/Mídia/content/bombordo/EP 04 - Ayrton Fernandes/04_work/historias_daniel/work'
ASSETS = os.path.join(EP04, '../../codex_reels/assets')
SK = os.path.expanduser('~/.claude/skills/bombordo-boreste')
W, H, FPS = 1080, 1920, 30
P, D, RAMP, TAIL = 660, 460, 0.35, 0.5
CROP_X = 600                       # recorte 608x1080 (rosto em x~905, câmera fixa)
GRADE = ("curves=master='0/0.012 0.06/0.05 0.25/0.225 0.5/0.52 0.75/0.795 0.94/0.95 1/0.985',"
         "colorbalance=rs=-0.03:bs=0.04:rm=0.04:gm=-0.01,eq=saturation=1.05")
BR = os.path.join(HERE, 'broll')

STORIES = {
    'ginecologista': dict(
        name="HISTÓRIAS DO PORTO - ELE FOI TRADUZIR A CONSULTA DA GINECOLOGISTA E ACABOU EXPULSO DA SALA",
        headline="ELE FOI TRADUZIR A CONSULTA\nDA GINECOLOGISTA E\nACABOU EXPULSO DA SALA",
        cover_t=217.67, cover_x0=484,
        # (nome, entra, sai, arquivo, início no arquivo)
        refs=[('porto', 19.90, 25.30, 'px_15187012.mp4', 0.0),
              ('medica', 37.30, 42.10, 'px_7579841.mp4', 0.0),
              ('estudo', 60.90, 66.60, 'px_855418.mp4', 0.0),
              ('maca', 91.50, 95.30, 'px_6151283.mp4', 0.5)],
        music_off=[(41.20, 42.10), (129.85, 139.20)], voice_db=-7.5,
        # (arquivo do acervo, início na timeline, início no arquivo, duração, dB)
        sfx=[('disco_arranhado_108233.mp3', 41.22, 0.50, 0.55, -20.0)]),
    'grego': dict(
        name="HISTÓRIAS DO PORTO - XINGARAM O COMANDANTE GREGO ACHANDO QUE ELE NÃO ENTENDIA PORTUGUÊS",
        headline="XINGARAM O COMANDANTE GREGO\nACHANDO QUE ELE NÃO\nENTENDIA PORTUGUÊS",
        cover_t=516.33, cover_x0=583,
        refs=[('navio', 17.71, 23.01, 'px_29928556.mp4', 5.0),
              ('calculos', 32.71, 37.81, 'px_855232.mp4', 0.5),
              ('comandante', 59.61, 67.86, 'px_5104378.mp4', 1.0),
              ('pratico', 67.86, 72.71, 'px_16992795.mp4', 2.0)],
        music_off=[(105.91, 118.51)], voice_db=-7.7,
        sfx=[('grilos_awkward_407257.mp3', 108.71, 0.0, 3.40, -6.0)],
        bleeps=[(104.19, 104.51), (117.65, 118.07)]),        # "cu": voz sai, bipe entra
}
S = STORIES[K]
E = json.load(open('edit.json')); TOTAL = E['total']


def run(cmd): subprocess.run(cmd, check=True)


def panels():
    for name, a, b, src, s0 in S['refs']:
        dur = (b - a) + 2 * RAMP
        ss = max(0.0, s0 - RAMP)
        run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{ss:.3f}', '-i', os.path.join(BR, src), '-t', f'{dur:.3f}',
             '-vf', f'fps={FPS},scale=-2:{P}:flags=lanczos,crop={W}:{P},setsar=1', '-an',
             '-c:v', 'prores_ks', '-profile:v', '3', '-pix_fmt', 'yuv422p10le', f'ref_{name}.mov'])
    print('painéis ok', flush=True)


def caption():
    run(['ffmpeg', '-v', 'error', '-y', '-i', 'caps_rgb.mp4', '-i', 'caps_a.mp4', '-filter_complex',
         '[1:v]format=gray[a];[0:v][a]alphamerge,format=yuva444p10le[v]', '-map', '[v]',
         '-c:v', 'prores_ks', '-profile:v', '4', '-pix_fmt', 'yuva444p10le', '-alpha_bits', '16', '-r', str(FPS),
         'legenda_animada.mov'])
    print('legenda ok', flush=True)


def shadow():
    h, c = 320, 200
    y = np.arange(h)[:, None].astype(float)
    a = np.where(y < c, (y / c) ** 1.4, ((h - y) / (h - c)) ** 2.0) * 205
    img = np.zeros((h, W, 4), np.uint8); img[..., 3] = a.astype(np.uint8).repeat(W, 1)
    Image.fromarray(img, 'RGBA').save('seam_shadow.png')


def fade():
    d = 0.42 + TAIL
    run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'color=c=black:s={W}x{H}:r={FPS}:d={d:.3f}',
         '-vf', 'format=yuva444p10le,fade=t=in:st=0:d=0.42:alpha=1',
         '-c:v', 'prores_ks', '-profile:v', '4', '-pix_fmt', 'yuva444p10le', 'fade_preto.mov'])


def music():
    # -23 dB e ducking mais leve (ratio 3): o editor achou a trilha baixa a -27 no EP 06 (18/10/2026)
    dur = TOTAL + TAIL
    gate = ''.join(f"*if(lt(t,{a0}),1,if(lt(t,{a0}+0.18),1-(t-{a0})/0.18,if(lt(t,{a1}),0,min(1,(t-{a1})/0.6))))"
                   for a0, a1 in S['music_off'])
    fc = (f"[0:a]volume={S['voice_db']}dB,aresample=48000[key];"
          f"[1:a]atrim=0:{dur:.3f},asetpts=PTS-STARTPTS,volume=-23dB,"
          f"volume='1{gate}':eval=frame,"
          f"afade=t=in:d=0.8,afade=t=out:st={TOTAL - 1.6:.3f}:d={1.6 + TAIL:.3f}[mus];"
          f"[mus][key]sidechaincompress=threshold=0.08:ratio=3:attack=12:release=420,apad=whole_dur={dur:.3f}[out]")
    run(['ffmpeg', '-v', 'error', '-y', '-i', 'edit_voz.wav', '-i', os.path.join(EP04, 'music/bed.wav'),
         '-filter_complex', fc, '-map', '[out]', '-ar', '48000', '-c:a', 'pcm_s24le', 'trilha_mix.wav'])
    print('trilha ok', flush=True)


def cover():
    run(['ffmpeg', '-v', 'error', '-y', '-ss', str(S['cover_t']), '-i', MASTER, '-frames:v', '1', '-vf', GRADE,
         '-c:v', 'libx264', '-crf', '10', '-pix_fmt', 'yuv420p', 'cover_src_graded.mp4'])
    os.environ.setdefault('FONT', os.path.join(SK, 'assets/CalSans-Regular.ttf'))
    os.environ.setdefault('LOGO', os.path.join(SK, 'assets/logo_portos_color.png'))
    sys.path.insert(0, os.path.join(SK, 'scripts'))
    import cover as cv
    cv.build(dict(headline=S['headline'],
                  cover_from=dict(src=os.path.abspath('cover_src_graded.mp4'), t=0, x0=S['cover_x0'])),
             None, 'capa.png')
    print('capa ok', flush=True)


def cfg():
    cap_n = int(open(os.path.join(EP04, 'cap_cy.txt')).read())
    json.dump(dict(name=S['name'], master=MASTER, crop_x=CROP_X, P=P, D=D, RAMP=RAMP, TAIL=TAIL,
                   CAP_N=cap_n, SHADOW_C=200, BURN_D=1.3667, BURN_PEAK=0.52,
                   burn=os.path.join(ASSETS, 'filmburn_blue.mp4'), click=os.path.join(ASSETS, 'click_lens_trimmed.wav'),
                   click_db=-15.9, voice_db=S['voice_db'] + 3.0,   # +3: o Resolve põe a voz numa trilha mono centralizada (-3 dB)
                   sfx_dir='/Volumes/SSD/CIBO Acervo/sfx/_global',
                   whoosh_burn=['whoosh-medium-1s.wav', 0.55, -4.0], whoosh_panel=['whoosh-short.wav', 0.158, -8.0],
                   sfx=S['sfx'], bleeps=S.get('bleeps', []), bleep=['bipe_censura_1khz.wav', -5.0],
                   REFS=[[n, a, b] for n, a, b, _, _ in S['refs']]),
              open('xml_cfg.json', 'w'), indent=1, ensure_ascii=False)


if __name__ == '__main__':
    steps = sys.argv[2:] or ['panels', 'caption', 'shadow', 'fade', 'music', 'cover', 'cfg']
    for s in steps: globals()[s]()
