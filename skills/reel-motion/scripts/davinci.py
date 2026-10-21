#!/usr/bin/env python3
"""Pacote editável para o DaVinci Resolve, fragmentado ao máximo (pedido do editor, 14/10/2026: "deixar tudo em blocos
sólidos não me dá liberdade nenhuma"; corrigir erro bobo sem depender da IA). Chamado por `reel.py PROJ rNN davinci`,
que antes renderiza no Remotion cada camada/elemento isolado em _camadas/ (elementos só no seu trecho de tempo).

Timeline (de baixo para cima): bruto da câmera em takes (arquivo original, in/out = trecho mantido, sobra como alça para
estender; girado, enquadrado e com punch/respiro e o deslocamento da tela dividida em keyframes) · câmera renderizada
(referência, desligada) · mídia · fundo de cada painel · gráfico de cada painel · número da etapa · cada etiqueta ·
fundo do gancho, gancho, cada título, tarja · cada bloco de legenda · burns (alfa; o DaVinci ignora Screen do FCPXML) ·
capa no quadro 0. Áudio: voz por take (mesmos cortes), trilha com ducking, cada SFX com ganho; WAV float no ganho
final do mix, limitador -1 dBTP no master do DaVinci. Também: legenda.srt.
O ajuste fino da transformação do bruto é do editor no DaVinci (não validado aqui por pedido dele).
uso: davinci.py PROJ rNN PASTA_SAIDA"""
if __name__ == '__main__':   # saída curta + log completo em 05_qa/logs (client-router/scripts/saida_curta.py)
    import os as _o, sys as _s; _s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.realpath(__file__)), '../../client-router/scripts')); import saida_curta; saida_curta.curta()
import json, os, re, shutil, subprocess, sys
from fractions import Fraction
from pathlib import Path
from xml.sax.saxutils import quoteattr
import numpy as np, soundfile as sf

P, R, OUT = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]).resolve()
W = P / '04_work' / R; PUB = P / '04_work' / 'public'; CAM = OUT / '_camadas'
C = json.load(open(W / 'reel.json')); PR = json.load(open(PUB / R / 'props.json'))
# "grosso" (aula longa, João 21/10/2026: "só editar o grosso"): bruto cortado, voz, trilha e legenda.srt; sem painel,
# título, burn, SFX, rastreio nem movimento de câmera, e nada renderizado no Remotion
GROSSO = bool(C.get('grosso'))
if GROSSO:
    PR = {**PR, 'split': [], 'panels': [], 'burns': [], 'inserts': [], 'hook': None, 'titles': [], 'lower': None, 'keywords': [], 'endCard': None}
    C = {**C, 'camera_davinci': True, 'camera_moves': []}; C.pop('track', None)
# versão horizontal 16:9 ("orient": "h", Andreia 19/10/2026): timeline 1920×1080, painel à esquerda, deslocamento da pessoa em x
HZ = C.get('orient') == 'h'; VW, VH = (1920, 1080) if HZ else (1080, 1920)
SFXDIR = '/Volumes/SSD/CIBO Acervo/sfx/_global/'
FD = Fraction(1001, 30000)
if GROSSO:                                                     # aula longa: timeline no fps da fonte, sem cópia 29,97 (João 21/10/2026:
    _s = Path(C['src']) if os.path.isabs(C['src']) else P / '01_sources' / C['src']   # "o Resolve consegue fazer isso sozinho")
    _r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate', '-of', 'csv=p=0', str(_s)],
                        capture_output=True, text=True).stdout.strip()
    FD = 1 / Fraction(_r)
fr = lambda t: max(0, round(t / FD))                       # segundos → quadros
tt = lambda n: f'{n * FD.numerator}/{FD.denominator}s' if n else '0s'         # quadros → tempo FCPXML
D = fr(PR['duration'])
slug = lambda s, n=40: re.sub(r'[^\w]+', '_', s.lower()).strip('_')[:n] or 'x'
# nome único por pacote (Andreia 20/10/2026: o Resolve junta arquivos de MESMO NOME de pacotes diferentes num item só e o 03
# tocou a voz do 01; vale para voz, trilha, SFX, burns, capa, legenda e cada elemento: r01 e r01h têm a mesma legenda)
U = lambda nome: f'{Path(nome).stem}__{R}{Path(nome).suffix}'


def sh(*a, **kw):
    subprocess.run(list(map(str, a)), check=True, **kw)


def lufs(f):
    r = subprocess.run(['ffmpeg', '-i', str(f), '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(r[r.rfind('I:'):].split()[1])


def dur(f):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(f)], capture_output=True, text=True).stdout)


def runs(layer):
    """quadros com algo visível na camada (alfa > 0), agrupados em trechos [a, b)"""
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(layer), '-vf', 'alphaextract,scale=54:96', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'],
                         capture_output=True, check=True).stdout
    vis = np.frombuffer(raw, np.uint8).reshape(-1, 96 * 54).max(1) > 2
    out, a = [], None
    for i, v in enumerate(list(vis) + [False]):
        if v and a is None:
            a = i
        if not v and a is not None:
            out.append([a, i]); a = None
    merged = []
    for r in out:                                           # junta buracos de 1–2 quadros (fade de saída/entrada)
        if merged and r[0] - merged[-1][1] <= 2:
            merged[-1][1] = r[1]
        else:
            merged.append(r)
    return merged


def pedacos(layer, cortes, nomes, pasta):
    """divide a camada nos trechos visíveis e, dentro deles, em cada corte (início do elemento seguinte)"""
    (OUT / pasta).mkdir(exist_ok=True)
    for f in (OUT / pasta).glob('*.mov'):
        f.unlink()
    res = []
    for a, b in runs(layer):
        cs = sorted({c for c in cortes if a + 2 < c < b - 2})
        for x, y in zip([a] + cs, cs + [b]):
            nome = nomes(x, y)
            f = OUT / pasta / U(f'{len(res) + 1:03d}_{slug(nome)}.mov')
            sh('ffmpeg', '-v', 'error', '-y', '-ss', f'{float(x * FD):.6f}', '-i', layer, '-frames:v', y - x, '-c', 'copy', f)
            res.append((f, x, y - x, nome))
    return res


def perto(lista, x, y):
    """elemento da lista (com s/e em segundos) que mais cobre o trecho [x, y) em quadros"""
    return max(lista, key=lambda e: min(y, fr(e['e'])) - max(x, fr(e['s']))) if lista else None


(OUT / 'sfx').mkdir(parents=True, exist_ok=True); (OUT / 'burns').mkdir(exist_ok=True)
# ---- áudio ----
G = lufs(W / 'mix.wav') - lufs(W / 'mix_pre.wav')         # ganho do master (mix_pre → mix normalizado)
for src, dst in ((W / 'voz.wav', U('voz.wav')), (W / 'musica.wav', U('trilha.wav'))):
    sh('ffmpeg', '-v', 'error', '-y', '-i', src, '-af', f'volume={G:.2f}dB', '-c:a', 'pcm_f32le', OUT / dst)
sfx = []
for f in (OUT / 'sfx').glob('*'):
    f.unlink()
for i, e in enumerate([] if GROSSO else json.load(open(W / 'sfx.json'))):
    f = Path(e['f'] if os.path.isabs(e['f']) else SFXDIR + e['f'] + '.wav')
    # 48 kHz/24 bit com 0,2 s de silêncio no fim: o asset em quadros inteiros arredondava para além do fim do arquivo e o
    # Resolve deixava o SFX offline (João, anúncios 21/10/2026: 1,4014 s de asset para 1,393 s de arquivo)
    dst = OUT / 'sfx' / U(f'{i:02d}_{f.stem}.wav')
    sh('ffmpeg', '-v', 'error', '-y', '-i', f, '-af', 'apad=pad_dur=0.2', '-ar', '48000', '-c:a', 'pcm_s24le', dst)
    x, sr = sf.read(dst); x = x.mean(1) if x.ndim > 1 else x; pk = int(np.argmax(np.abs(x))) / sr
    st = e['t'] - pk                                          # o pico cai no instante do evento
    sfx.append((dst, fr(max(0.0, -st)), fr(max(0.0, st)), fr(dur(dst) - 0.2 - max(0.0, -st)), e['db'] + G))
# ---- burns com a cor do tema e alfa ----
burns = []
for f in (OUT / 'burns').glob('*'):
    f.unlink()
for i, b in enumerate(PR.get('burns', [])):
    dst = OUT / 'burns' / U(f'burn_{i:02d}.mov')
    # aproximação do burnFilter CSS do tema (theme.burnFF); sem ele, o sépia da Priscilla (antes fixo para todo cliente)
    tint = f'scale={VW}:{VH}:force_original_aspect_ratio=increase,crop={VW}:{VH},' + ((PR.get('theme') or {}).get('burnFF') or
            'colorchannelmixer=rr=0.6735:rg=0.4235:rb=0.1040:gr=0.1925:gg=0.8355:gb=0.0925:br=0.1500:bg=0.2970:bb=0.6185,'
            'hue=h=-12:s=1.6,colorchannelmixer=rr=1.05:gg=1.05:bb=1.05') + ',format=rgb24'
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-t', f"{b['dur'] + 0.1:.3f}", '-i', str(PUB / b['src']), '-vf', tint, '-r', '30000/1001',
                          '-f', 'rawvideo', '-'], capture_output=True, check=True).stdout
    q = np.frombuffer(raw, np.uint8).reshape(-1, VH, VW, 3).astype(np.float32) / 255
    a = q.max(3, keepdims=True); c = np.where(a > 1e-3, q / np.maximum(a, 1e-3), 0)   # Screen ≈ Normal com alfa = canal mais forte
    sh('ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{VW}x{VH}', '-r', '30000/1001', '-i', '-',
       '-c:v', 'prores_ks', '-profile:v', '4444', '-pix_fmt', 'yuva444p10le', dst, input=(np.concatenate([c, a], 3) * 255 + 0.5).astype(np.uint8).tobytes())
    burns.append((dst, fr(b['t'] - b['peak']), max(1, round(b['dur'] / FD))))
BOP = (PR.get('theme') or {}).get('burnOpacity') or 0.85
# ---- capa e SRT ----
CP = P / '06_deliverables' / f"CAPA - {C['name']}.jpg"
if not CP.exists():
    CP = next(P.glob(f"06_deliverables/CAPA - {R[1:]} -*"), None)
if CP: sh('ffmpeg', '-v', 'error', '-y', '-loop', '1', '-i', CP, '-frames:v', '1', '-r', '30000/1001', '-vf', f'scale={VW}:{VH}',
   '-c:v', 'prores_videotoolbox', '-profile:v', 'standard', OUT / U('capa.mov'))
hms = lambda t: f'{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{int(t % 60):02d},{int(round(t % 1 * 1000)) % 1000:03d}'
txt = lambda b: ' '.join(w['t'] for w in b['words'])
open(OUT / 'legenda.srt', 'w').write(''.join(f"{i + 1}\n{hms(b['s'])} --> {hms(b['e'])}\n{txt(b)}\n\n" for i, b in enumerate(PR['captions'])))
# ---- camadas de vídeo em pedaços ----
pan = PR.get('panels', [])
fundos = [] if not (CAM / U('painel_fundo.mov')).exists() else pedacos(CAM / U('painel_fundo.mov'), [fr(p['s']) for p in pan],
                 lambda x, y: (lambda p: f"fundo {p['type']} {p.get('title', '')}" if p else 'fundo')(perto(pan, x, y)), 'paineis_fundo')
cap = PR['captions']
legenda = [] if not (CAM / U('legenda.mov')).exists() else pedacos(CAM / U('legenda.mov'), [fr(b['s']) for b in cap], lambda x, y: (lambda b: txt(b) if b else 'legenda')(perto(cap, x, y)), 'legenda')
# elementos isolados (um arquivo cada, renderizado só no seu trecho): o clipe vai do 1º ao último quadro visível
elem = {}
for m in json.load(open(CAM / 'elementos.json')):
    f = CAM / m['arq']
    if not f.exists():
        continue
    rr = runs(f)
    if rr:
        r0, r1 = rr[0][0], rr[-1][1]
        elem.setdefault(m['grupo'], []).append((f, m['a'] + r0, r1 - r0, m['nome'], r0))
ins = PR.get('inserts') or []
midia = [(CAM / U('midia.mov'), fr(v['s']) - 8, fr(v['e']) - fr(v['s']) + 16, Path(v['src']).stem) for v in ins] if (CAM / U('midia.mov')).exists() else []
# takes: pontos de corte no tempo editado
S = json.load(open(W / 'segs.json')); S = S.get('segs', S) if isinstance(S, dict) else S
takes, acc = [], 0.0
for a, b in S:
    takes.append((fr(acc), fr(acc + b - a), a, b)); acc += b - a
takes[-1] = (takes[-1][0], D, *takes[-1][2:])                # o último take segura até o fim (rabo do fade)


# ---- câmera a partir do BRUTO (o editor estende o take para corrigir corte; 14/10/2026) ----
# Cada take é o arquivo original da câmera com in/out = trecho mantido (as sobras ficam como alça), girado, com o
# enquadramento do face track (zoom + posição) e animado: punch/respiro do camera.py e o deslocamento da tela dividida.
# FCPXML: conform "none" (1 px da fonte = 1 px da timeline), posição em % da ALTURA do quadro (1920), y para cima.
def bezier(x1, y1, x2, y2):
    def f(u):
        lo, hi = 0.0, 1.0
        for _ in range(40):
            m = (lo + hi) / 2; bx = 3 * (1 - m) ** 2 * m * x1 + 3 * (1 - m) * m * m * x2 + m ** 3
            lo, hi = (m, hi) if bx < u else (lo, m)
        m = (lo + hi) / 2
        return 3 * (1 - m) ** 2 * m * y1 + 3 * (1 - m) * m * m * y2 + m ** 3
    return lambda u: f(min(1.0, max(0.0, u)))


EASE = bezier(0.33, 0, 0.67, 1)
# modo crop (fonte com recorte fixo ou que segue o rastreio do rosto, "track"): sem job.json do face track
CROP = not (W / 'job.json').exists()
if CROP:
    _src = Path(C['src']) if os.path.isabs(C['src']) else P / '01_sources' / C['src']
    JOB = {'src': str(_src), 'rotate': C.get('rotate', ''), 'tc_drop': C.get('tc_drop', False), 'camera_moves': C.get('camera_moves', [])}
    _iw, _ih = map(int, subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', str(_src)],
                                       capture_output=True, text=True).stdout.strip().split(',')[:2])
    RW, RH = (_ih, _iw) if C.get('rotate') in ('clock', 'cclock') else (_iw, _ih)      # quadro já girado
    # unidade do position no Resolve: VH/100 px na timeline vertical (no r01 da Andreia, com RH/RW a câmera desceu 2,1×
    # demais, 19/10/2026); na horizontal com clipe girado, VH/100 * RH/RW (medido no r01h)
    PU = VH / 100 * (RH / RW if C.get('rotate') in ('clock', 'cclock') and VW > VH else 1)
    TRK = json.load(open(P / '04_work' / C['track'])) if C.get('track') else None
    CRP = sorted(C.get('crops', [{'at': 0, 'cx': RW / 2}]), key=lambda c: c['at'])
else:
    JOB = json.load(open(W / 'job.json'))
LAY = {'camShift': 600, 'camUp': 300, **((PR.get('theme') or {}).get('layout') or {})}
TR = 0.42                                                       # troca de layout do Reel.tsx
ramp = lambda t, a, d: EASE((t - a) / d)


# movimentos de câmera em camadas de ajuste com Transform do Fusion (Andreia 19/10/2026: "mover os movimentos de câmera
# para dentro do transform do Fusion com shutter angle e blur, uma camada de clip de ajuste por zoom ou movimento"):
# com "camera_fusion" no reel.json o bruto leva só o enquadramento base; ON escolhe quais movimentos entram na conta
FX = bool(C.get('camera_fusion'))
ON = {'z': None, 's': None}                                     # None = todos; set() = nenhum


def SPL(inv=False):
    return [g for i, g in enumerate(PR['split']) if (ON['s'] is None or i in ON['s']) and (not inv or g.get('inv'))]


def split_amt(t, gs):
    v = 0.0
    for g in gs:
        a, b = g['s'] - TR * 0.35, g['e'] - TR * 0.35
        v = max(v, min(ramp(t, a, TR), 1 - ramp(t, b, TR)))
    return v


def zlog(t):
    import math
    s = 0.0
    for i, m in enumerate(JOB.get('camera_moves') or []):
        if ON['z'] is not None and i not in ON['z']:
            continue
        t0, t1, Lg = float(m['t']), float(m['until']), math.log1p(float(m['amount']))
        if t < t0:
            continue
        if m['kind'] == 'punch':
            zi = float(m.get('in', 0.3)); o = max(1.2, t1 - t0 - zi)
            if t <= t0 + zi: s += Lg * EASE((t - t0) / zi)
            elif t <= t0 + zi + o: s += Lg * (1 - EASE((t - t0 - zi) / o))
        else:
            s += Lg * EASE((t - t0) / max(1e-3, t1 - t0)) if t <= t1 else (Lg if t <= float(m.get('hold_until', t1)) else 0.0)
    return s


def transf(k, t):
    """(posição x, y em % da altura, escala) do take k no instante editado t"""
    import math
    if CROP:
        st = takes[k][2] + (t - TK0[k])                               # instante na fonte
        if TRK:
            cx = float(np.interp(st, [r[0] for r in TRK], [r[1] for r in TRK])); fy = float(np.interp(st, [r[0] for r in TRK], [r[2] for r in TRK]))
        else:
            cx = [c for c in CRP if c['at'] <= st + 1e-3][-1]['cx'] if any(c['at'] <= st + 1e-3 for c in CRP) else CRP[0]['cx']; fy = RH * 0.42
        w = RW if HZ else RH * 9 / 16
        if not HZ and VW / w > 1:                                     # vertical sem zoom além da escala nativa (Andreia 19/10/2026:
            w = VW                                                    # "a cabeça ficou muito pequena… tira zoom e põe background com blur")
        cx = min(max(cx, w / 2), RW - w / 2); sc0 = VW / w * C.get('zoom', 1)
        # "zoom"/"zoom_cy" no reel.json: recorte fixo feito no Resolve (aula do João 21/10/2026: 1,2245x em y 549 tira os logos
        # do palco, sem rastreio e sem mezanino renderizado)
        # zoom in/out (camera_moves do reel.json, Easy Ease em espaço log) centrado no rosto: o ponto do rosto fica parado
        z = math.exp(zlog(t)); sc = sc0 * z
        dx, dy = (RW / 2 - cx) * sc, (fy - RH / 2) * sc0 * (1 - z)
        sp = split_amt(t, SPL())
        if HZ:
            # tela dividida lado a lado (Andreia 19/10/2026, "ela não tá na lateral direita centralizada"): o rosto do rastreio
            # vai para o meio da área à direita do painel, com o zoom ancorado nele; na tela cheia o rosto fica onde está.
            # Antes usava o camX das props e o zoom no centro do quadro: rosto medido em x≈1406 com alvo 1600.
            PW = ((PR.get('theme') or {}).get('layoutH') or {}).get('panelW', 1040)
            fx = float(np.interp(st, [r[0] for r in TRK], [r[1] for r in TRK])) if TRK else cx
            alvo = fx + (PW + (VW - PW) / 2 - fx) * sp
            sc = max(sc, (VW - alvo) / max(1.0, RW - fx))                 # borda direita sempre com imagem
            dx = alvo - (VW / 2 + (fx - RW / 2) * sc)                      # a esquerda descoberta fica sob o painel
            dy = (fy - RH / 2) * (sc0 - sc) + (C.get('zoom_cy', RH / 2) - RH / 2) * sc
        else:
            spI = split_amt(t, SPL(True))
            if RH * sc0 < VH - 1:                                     # imagem mais baixa que o quadro: na tela dividida o topo dela
                shift = LAY.get('splitH', 940) + RH * sc0 / 2 - VH / 2    # encosta no painel; o resto é o fundo desfocado (BLUR)
            else:
                shift = LAY['camShift']
            dy += -LAY['camUp'] * sp if spI > 0.001 else shift * sp
        return dx / PU, -dy / PU, sc
    fm = JOB['framings'][min(k, len(JOB['framings']) - 1)]
    if isinstance(fm, dict):                                    # enquadramento que acompanha o rosto: kx/ky = [[s no take, px]]
        u = t - TK0[k]; w, h = fm['w'], fm['h']
        x = float(np.interp(u, [p[0] for p in fm['kx']], [p[1] for p in fm['kx']]))
        y = float(np.interp(u, [p[0] for p in fm['ky']], [p[1] for p in fm['ky']]))
    else:
        x, y, w, h = fm
    fx, fy = (JOB.get('face_pos') or [[0.5, 0.5]] * (k + 1))[min(k, len(JOB.get('face_pos') or [0]) - 1)]
    z = math.exp(zlog(t)); px, py = x + fx * w, y + fy * h
    cx, cy = x + w / 2, y + h / 2
    if JOB.get('zoom_center_face'):
        cx, cy = px + (cx - px) / z, py + (cy - py) / z
    sc = 1080 / (w / z)
    SW, SH = (2160, 3840) if JOB.get('rotate', 'clock') in ('clock', 'cclock') else (3840, 2160)
    dx, dy = (SW / 2 - cx) * sc, (SH / 2 - cy) * sc
    spI = split_amt(t, SPL(True)); sp = split_amt(t, SPL())
    cam = -LAY['camUp'] * sp if spI > 0.001 else LAY['camShift'] * sp
    return dx / 19.2, -(dy + cam) / 19.2, sc


def tc_frames(f):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format_tags=timecode:stream_tags=timecode', '-of', 'csv=p=0', str(f)],
                       capture_output=True, text=True).stdout.split()
    if not r:
        return 0
    hh, mm, ss, ff = map(int, re.split('[:;]', r[0]))
    n = ((hh * 60 + mm) * 60 + ss) * 30 + ff
    # 29,97 da Sony é drop-frame: o DaVinci lê 10:41:20;13 (o ffprobe mostra ':'). Sem descontar os quadros pulados
    # (2 por minuto, exceto a cada 10) o take caía 38 s adiante na fonte e o DaVinci recusava a timeline (14/10/2026)
    if JOB.get('tc_drop', True):
        m = hh * 60 + mm
        n -= 2 * (m - m // 10)
    return n


def kf(vals, nfmt):
    """keyframes só onde a curva dobra (linear entre eles); vals = [(quadro_local, valor)]"""
    keep = [vals[0]]
    for i in range(1, len(vals) - 1):
        (a0, v0), (a1, v1), (a2, v2) = keep[-1], vals[i], vals[i + 1]
        lin = v0 + (v2 - v0) * (a1 - a0) / max(1, a2 - a0)
        if abs(v1 - lin) > 0.02:
            keep.append(vals[i])
    keep.append(vals[-1])
    return keep


def fonte_2997(src):
    """bruto fora de 29,97 (iPhone 30 fps, Andreia 19/10/2026): o Resolve conforma 1:1 na timeline 29,97, escorrega 1 quadro
    a cada 1000, o áudio atrasa e o último take passa do fim do arquivo (Media Offline). Cópia por TEMPO em 01_sources/_2997/
    (mesmos segundos, 1 s de folga no fim, sem timecode), feita uma vez e reaproveitada por todos os reels da mesma fonte"""
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate', '-of', 'csv=p=0', str(src)],
                       capture_output=True, text=True).stdout.strip()
    if r == '30000/1001' or GROSSO:
        return src
    dst = src.parent / '_2997' / (src.stem + '.mov') if src.parent.name != '_2997' else src
    if not dst.exists():
        dst.parent.mkdir(exist_ok=True); tmp = dst.with_name('.parcial_' + dst.name)
        print(f'bruto em {r} fps → cópia 29,97 em {dst.parent.name}/ (uma vez por fonte)', flush=True)
        sh('ffmpeg', '-v', 'error', '-y', '-i', src, '-vf', 'fps=30000/1001,tpad=stop_mode=clone:stop_duration=1', '-af', 'apad=pad_dur=1',
           '-c:v', 'libx264', '-crf', '16', '-preset', 'medium', '-c:a', 'pcm_s16le', '-write_tmcd', '0', '-f', 'mov', tmp)
        tmp.rename(dst)
    return dst


SRC = fonte_2997(Path(JOB['src'])); TC0 = tc_frames(SRC) if SRC == Path(JOB['src']) else 0
TK0, _acc = [], 0.0                                             # início de cada take no tempo editado
for _a, _b in (lambda S: S.get('segs', S) if isinstance(S, dict) else S)(json.load(open(W / 'segs.json'))):
    TK0.append(_acc); _acc += _b - _a
ROT = {'clock': -90, 'cclock': 90}.get(JOB.get('rotate'), 0)

# ---- FCPXML 1.10: um gap do tamanho do reel e tudo conectado nele (offset = tempo da timeline) ----
assets, ids = [], {}


def asset(f, video, audio, tc=0):
    f = Path(f)
    if f not in ids:
        ids[f] = f'a{len(ids) + 1}'
        assets.append(f'<asset id="{ids[f]}" name={quoteattr(f.name)} start="{tt(tc)}" duration="{tt(int(dur(f) / FD))}" hasVideo="{int(video)}" hasAudio="{int(audio)}"'
                      + (' format="r1"' if video else '') + (' audioSources="1" audioChannels="1" audioRate="48000"' if audio else '')
                      + f'>\n  <media-rep kind="original-media" src={quoteattr(f.resolve().as_uri())}/>\n</asset>')
    return ids[f]


def clip(f, lane, off, n, nome, start=0, video=True, audio=False, extra=''):
    n = min(n, D - off)
    if n <= 0:
        return ''
    return (f'<asset-clip ref="{asset(f, video, audio)}" lane="{lane}" offset="{tt(off)}"' + (f' start="{tt(start)}"' if start else '')
            + f' duration="{tt(n)}" name={quoteattr(nome[:80])}' + (f'>{extra}</asset-clip>' if extra else '/>'))


def bruto(k, a, b, s0):
    """take k do bruto: offset a..b (quadros editados), in-point s0 (s na fonte), com transformação animada"""
    ref = asset(SRC, 1, 1, TC0)
    st = TC0 + fr(s0)
    if FX:
        ON.update(z=set(), s=set())
    vals = [(n, transf(k, float((a + n) * FD))) for n in range(0, b - a + 1)]
    ON.update(z=None, s=None)
    px = kf([(n, v[0]) for n, v in vals], 0); py = kf([(n, v[1]) for n, v in vals], 0); sc = kf([(n, v[2] * 100) for n, v in vals], 0)
    x0, y0, s_ = vals[0][1]
    pv = dict(vals)
    def anim(nome, quadros, fmt, muda):
        if not muda:
            return ''
        return (f'<param name="{nome}"><keyframeAnimation>' + ''.join(f'<keyframe time="{tt(st + n)}" value="{fmt(n)}"/>' for n in quadros)
                + '</keyframeAnimation></param>')
    var = lambda i: max(v[i] for _, v in vals) - min(v[i] for _, v in vals)
    P_ = anim('position', sorted({n for n, _ in px} | {n for n, _ in py}), lambda n: f'{pv[n][0]:.4f} {pv[n][1]:.4f}', var(0) > 0.02 or var(1) > 0.02)
    S_ = anim('scale', [n for n, _ in sc], lambda n: f'{pv[n][2]:.5f} {pv[n][2]:.5f}', var(2) > 0.0005)
    return (f'<asset-clip ref="{ref}" lane="1" offset="{tt(a)}" start="{tt(st)}" duration="{tt(b - a)}" srcEnable="video" name={quoteattr(f"bruto {SRC.stem} {s0:.2f}")}>'
            f'<adjust-conform type="none"/><adjust-transform position="{x0:.4f} {y0:.4f}" scale="{s_:.5f} {s_:.5f}" rotation="{ROT}">{P_}{S_}</adjust-transform></asset-clip>')


L = []
lane = [0]


def nova():
    lane[0] += 1
    return lane[0]


def faixas(itens, nomear):
    """itens (arquivo, início, duração, nome, in) em faixas novas sem sobreposição"""
    fins, base = [], lane[0]
    for f, off, n, nome, st in sorted(itens, key=lambda z: z[1]):
        k = next((i for i, e in enumerate(fins) if e <= off), len(fins))
        if k == len(fins):
            fins.append(0); nova()
        fins[k] = off + n
        L.append(clip(f, base + 1 + k, off, n, nome, start=st))


BLUR = CROP and not HZ and RH * VW / min(RW, RH * 9 / 16) > RH * 1.001 and (PUB / R / 'camera.mov').exists()
if BLUR:                                                      # fundo desfocado sob o bruto sem zoom (vertical): câmera editada, cobrindo o quadro
    bg = OUT / '_camadas' / U('fundo_desfocado.mov')
    if not bg.exists():
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(PUB / R / 'camera.mov'), '-an', '-vf',
                        f'scale={VW // 8}:{VH // 8}:force_original_aspect_ratio=increase,crop={VW // 8}:{VH // 8},gblur=sigma=6,eq=brightness=-0.06,scale={VW}:{VH}',
                        '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', '-r', '30000/1001', str(bg)], check=True)
    L.append(clip(bg, nova(), 0, D, 'fundo desfocado'))
V1 = nova()                                                   # bruto, take a take, com alça
for k, (a, b, s0, s1) in enumerate(takes):
    L.append(bruto(k, a, b, s0).replace('lane="1"', f'lane="{V1}"', 1))
    L.append(clip(OUT / U('voz.wav'), -1, a, b - a, f'voz {s0:.2f}-{s1:.2f}', start=a, video=False, audio=True))
V2 = nova()                                                   # câmera renderizada por cima (imagem aprovada); para estender um
for a, b, s0, s1 in takes:                                    # take, desligue o clipe dela e use o bruto embaixo
    if (CAM / U('camera.mov')).exists() and not C.get('camera_davinci'):   # "camera_davinci": o DaVinci monta a câmera do bruto (validado 19/10/2026)
        L.append(clip(CAM / U('camera.mov'), V2, a, b - a, f'câmera renderizada {s0:.2f}', start=a))
if midia:
    V = nova()
    for f, off, n, nome in midia:
        L.append(clip(f, V, max(0, off), n, nome, start=max(0, off)))
faixas([(f, off, n, nome, 0) for f, off, n, nome in fundos], None)
faixas(elem.get('painel', []), None)
faixas(elem.get('step', []), None)
faixas(elem.get('tag', []), None)
faixas(elem.get('titulo', []), None)
faixas([(f, off, n, nome, 0) for f, off, n, nome in legenda], None)
# extras do reel.json ("extras": [{"arq": "extras/x.mov", "s": 0.4, "nome": "…"}]): elementos feitos fora do Remotion
# (ex.: cartão com o logo da Growth no gancho do 06, 14/10/2026), cada um na sua faixa
for e in C.get('extras', []):
    src = W / e['arq']; dst = OUT / 'extras' / src.name
    dst.parent.mkdir(exist_ok=True); shutil.copy(src, dst)
    shutil.copy(src.with_suffix('.png'), dst.with_suffix('.png')) if src.with_suffix('.png').exists() else None
    L.append(clip(dst, nova(), fr(e.get('s', 0)), fr(dur(dst)), e.get('nome', src.stem)))
V = nova()
for f, off, n in burns:
    L.append(clip(f, V, off, n, 'burn', extra=f'<adjust-blend amount="{BOP}"/>'))
if CP: L.append(clip(OUT / U('capa.mov'), nova(), 0, 1, 'capa (quadro 0)'))
L.append(clip(OUT / U('trilha.wav'), -2, 0, fr(dur(OUT / U('trilha.wav'))), 'trilha', video=False, audio=True))
fim = []                                                      # SFX: faixas de áudio sem sobreposição
for f, ins_, off, n, db in sorted(sfx, key=lambda z: z[2]):
    k = next((i for i, e in enumerate(fim) if e <= off), len(fim))
    if k == len(fim):
        fim.append(0)
    fim[k] = off + n
    L.append(clip(f, -3 - k, off, n, f.stem, start=ins_, video=False, audio=True, extra=f'<adjust-volume amount="{db:.1f}dB"/>'))
if FX:                                                        # movimentos.json: uma camada de ajuste por movimento (resolve_fx.py)
    U = PU if CROP else 19.2
    def estado(n, z, s_):
        ON.update(z=z, s=s_); t = float(n * FD)
        k = next(i for i, tk in enumerate(takes) if tk[0] <= n < tk[1] or i == len(takes) - 1)
        x, y, sc = transf(k, t); ON.update(z=None, s=None)
        return x * U, -y * U, sc
    MV = []
    for i, m in enumerate(JOB.get('camera_moves') or []):
        t0, t1 = float(m['t']), float(m['until'])
        fim_ = t0 + float(m.get('in', 0.3)) + max(1.2, t1 - t0 - float(m.get('in', 0.3))) if m['kind'] == 'punch' else max(t1, float(m.get('hold_until', t1)))
        MV.append(('z', i, t0, fim_, f"{'punch' if m['kind'] == 'punch' else 'zoom'} {t0:.2f}s"))
    for i, g in enumerate(PR['split']):
        MV.append(('s', i, g['s'] - TR * 0.35, g['e'] - TR * 0.35 + TR, f"tela dividida{' invertida' if g.get('inv') else ''} {g['s']:.2f}s"))
    camadas = []
    for j, (tipo, i, a_, b_, nome) in enumerate(MV):
        antes = ({x[1] for x in MV[:j] if x[0] == 'z'}, {x[1] for x in MV[:j] if x[0] == 's'})
        depois = (antes[0] | ({i} if tipo == 'z' else set()), antes[1] | ({i} if tipo == 's' else set()))
        n0, n1 = max(0, int(a_ / FD) - 1), min(D, int(b_ / FD) + 2)
        kfs = []
        for n in range(n0, n1):
            x0, y0, s0 = estado(n, *antes); x1, y1, s1 = estado(n, *depois); kk = s1 / s0
            kfs.append((n - n0, kk, 0.5 + (x1 - x0 * kk) / VW, 0.5 - (y1 - y0 * kk) / VH))
        if max(abs(v[1] - 1) for v in kfs) < 1e-3 and max(abs(v[2] - 0.5) + abs(v[3] - 0.5) for v in kfs) < 2e-4:
            continue
        red = kfs                                               # quadro a quadro: o resolve_fx.py tira as poses e põe o ease
        camadas.append(dict(nome=nome, tipo=tipo, inicio=n0, dur=n1 - n0, kf=[[q[0], round(q[1], 5), round(q[2], 5), round(q[3], 5)] for q in red]))
    json.dump(dict(src=str(SRC.resolve()), camadas=camadas), open(OUT / 'movimentos.json', 'w'), ensure_ascii=False, indent=1)
    print(f'movimentos de câmera em camadas de ajuste: {len(camadas)}')
# aula no grosso: legenda como títulos (Text+ no Resolve) já na fonte do tema; a faixa de legenda (SRT) do Resolve não aceita
# fonte pela API (João 21/10/2026: "precisa que tudo seja em Montserrat"). Um título por bloco, embaixo, caixa alta se o tema pede
if GROSSO and PR.get('captions'):
    _cp = ((PR.get('theme') or {}).get('caption') or {}); _up = _cp.get('upper', False)
    _w = {700: 'Bold', 800: 'ExtraBold', 900: 'Black'}.get(_cp.get('weight', 800), 'ExtraBold')
    assets.append('<effect id="rT" name="Basic Title" uid=".../Titles.localized/Bumper:Opener.localized/Basic Title.localized/Basic Title.moti"/>')
    for i, b in enumerate(PR['captions']):
        a0, a1 = fr(b['s']), max(fr(b['s']) + 1, fr(b['e']))
        tx = txt(b).upper() if _up else txt(b)
        L.append(f'<title ref="rT" lane="20" offset="{tt(a0)}" duration="{tt(a1 - a0)}" name={quoteattr(tx[:40])}>'
                 '<adjust-transform position="0 -38"/>'                          # % da altura, como a câmera (y para cima)
                 f'<text><text-style ref="ts{i}">{tx.replace("&", "&amp;").replace("<", "&lt;")}</text-style></text>'
                 f'<text-style-def id="ts{i}"><text-style font="Montserrat" fontSize="{VH * 0.05:.0f}" fontFace="{_w}" fontColor="1 1 1 1" '
                 f'shadowColor="0 0 0 0.75" shadowOffset="3 315" shadowBlurRadius="6" alignment="center"/></text-style-def></title>')
    (OUT / 'legenda.srt').rename(OUT / 'legenda_texto.srt')      # o SRT fica de referência, sem ir para a timeline
xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.10">
<resources>
<format id="r1" name="FFVideoFormat{VW}x{VH}p{'2997' if FD == Fraction(1001, 30000) else round(1 / FD)}" frameDuration="{FD.numerator}/{FD.denominator}s" width="{VW}" height="{VH}" colorSpace="1-1-1 (Rec. 709)"/>
{chr(10).join(assets)}
</resources>
<library><event name={quoteattr(C['name'])}><project name={quoteattr(C['name'])}>
<sequence format="r1" duration="{tt(D)}" tcStart="0s" tcFormat="NDF" audioLayout="stereo" audioRate="48k">
<spine>
<gap name="reel" offset="0s" start="0s" duration="{tt(D)}">
{chr(10).join(l for l in L if l)}
</gap>
</spine>
</sequence></project></event></library>
</fcpxml>
'''
open(OUT / 'timeline.fcpxml', 'w').write(xml)
print(f'pacote DaVinci: {OUT.name} — {len(takes)} takes do bruto, {len(fundos)} fundos, ' + ', '.join(f'{len(v)} {k}' for k, v in elem.items()) + f', {len(legenda)} blocos de legenda, '
      f'{len(burns)} burns, {len(sfx)} SFX, {len(midia)} mídias; master {G:+.1f} dB')
