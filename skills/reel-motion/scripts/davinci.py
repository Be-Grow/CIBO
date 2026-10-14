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
import json, os, re, shutil, subprocess, sys
from fractions import Fraction
from pathlib import Path
from xml.sax.saxutils import quoteattr
import numpy as np, soundfile as sf

P, R, OUT = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]).resolve()
W = P / '04_work' / R; PUB = P / '04_work' / 'public'; CAM = OUT / '_camadas'
C = json.load(open(W / 'reel.json')); PR = json.load(open(PUB / R / 'props.json'))
SFXDIR = '/Volumes/SSD/CIBO Acervo/sfx/_global/'
FD = Fraction(1001, 30000)
fr = lambda t: max(0, round(t / FD))                       # segundos → quadros
tt = lambda n: f'{n * 1001}/30000s' if n else '0s'         # quadros → tempo FCPXML
D = fr(PR['duration'])
slug = lambda s, n=40: re.sub(r'[^\w]+', '_', s.lower()).strip('_')[:n] or 'x'


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
            f = OUT / pasta / f'{len(res) + 1:03d}_{slug(nome)}.mov'
            sh('ffmpeg', '-v', 'error', '-y', '-ss', f'{float(x * FD):.6f}', '-i', layer, '-frames:v', y - x, '-c', 'copy', f)
            res.append((f, x, y - x, nome))
    return res


def perto(lista, x, y):
    """elemento da lista (com s/e em segundos) que mais cobre o trecho [x, y) em quadros"""
    return max(lista, key=lambda e: min(y, fr(e['e'])) - max(x, fr(e['s']))) if lista else None


(OUT / 'sfx').mkdir(parents=True, exist_ok=True); (OUT / 'burns').mkdir(exist_ok=True)
# ---- áudio ----
G = lufs(W / 'mix.wav') - lufs(W / 'mix_pre.wav')         # ganho do master (mix_pre → mix normalizado)
for src, dst in ((W / 'voz.wav', 'voz.wav'), (W / 'musica.wav', 'trilha.wav')):
    sh('ffmpeg', '-v', 'error', '-y', '-i', src, '-af', f'volume={G:.2f}dB', '-c:a', 'pcm_f32le', OUT / dst)
sfx = []
for f in (OUT / 'sfx').glob('*'):
    f.unlink()
for i, e in enumerate(json.load(open(W / 'sfx.json'))):
    f = Path(e['f'] if os.path.isabs(e['f']) else SFXDIR + e['f'] + '.wav')
    dst = OUT / 'sfx' / f'{i:02d}_{f.stem}{f.suffix}'; shutil.copy(f, dst)
    x, sr = sf.read(dst); x = x.mean(1) if x.ndim > 1 else x; pk = int(np.argmax(np.abs(x))) / sr
    st = e['t'] - pk                                          # o pico cai no instante do evento
    sfx.append((dst, fr(max(0.0, -st)), fr(max(0.0, st)), fr(dur(dst) - max(0.0, -st)), e['db'] + G))
# ---- burns com a cor do tema e alfa ----
burns = []
for f in (OUT / 'burns').glob('*'):
    f.unlink()
for i, b in enumerate(PR.get('burns', [])):
    dst = OUT / 'burns' / f'burn_{i:02d}.mov'
    tint = ('scale=1080:1920,colorchannelmixer=rr=0.6735:rg=0.4235:rb=0.1040:gr=0.1925:gg=0.8355:gb=0.0925:br=0.1500:bg=0.2970:bb=0.6185,'
            'hue=h=-12:s=1.6,colorchannelmixer=rr=1.05:gg=1.05:bb=1.05,format=rgb24')   # aproximação do burnFilter CSS
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-t', f"{b['dur'] + 0.1:.3f}", '-i', str(PUB / b['src']), '-vf', tint, '-r', '30000/1001',
                          '-f', 'rawvideo', '-'], capture_output=True, check=True).stdout
    q = np.frombuffer(raw, np.uint8).reshape(-1, 1920, 1080, 3).astype(np.float32) / 255
    a = q.max(3, keepdims=True); c = np.where(a > 1e-3, q / np.maximum(a, 1e-3), 0)   # Screen ≈ Normal com alfa = canal mais forte
    sh('ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', '1080x1920', '-r', '30000/1001', '-i', '-',
       '-c:v', 'prores_ks', '-profile:v', '4444', '-pix_fmt', 'yuva444p10le', dst, input=(np.concatenate([c, a], 3) * 255 + 0.5).astype(np.uint8).tobytes())
    burns.append((dst, fr(b['t'] - b['peak']), max(1, round(b['dur'] / FD))))
BOP = (PR.get('theme') or {}).get('burnOpacity') or 0.85
# ---- capa e SRT ----
CP = next(P.glob(f"06_deliverables/CAPA - {R[1:]} -*"))
sh('ffmpeg', '-v', 'error', '-y', '-loop', '1', '-i', CP, '-frames:v', '1', '-r', '30000/1001', '-vf', 'scale=1080:1920',
   '-c:v', 'prores_videotoolbox', '-profile:v', 'standard', OUT / 'capa.mov')
hms = lambda t: f'{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{int(t % 60):02d},{int(round(t % 1 * 1000)) % 1000:03d}'
txt = lambda b: ' '.join(w['t'] for w in b['words'])
open(OUT / 'legenda.srt', 'w').write(''.join(f"{i + 1}\n{hms(b['s'])} --> {hms(b['e'])}\n{txt(b)}\n\n" for i, b in enumerate(PR['captions'])))
# ---- camadas de vídeo em pedaços ----
pan = PR.get('panels', [])
fundos = pedacos(CAM / 'painel_fundo.mov', [fr(p['s']) for p in pan],
                 lambda x, y: (lambda p: f"fundo {p['type']} {p.get('title', '')}" if p else 'fundo')(perto(pan, x, y)), 'paineis_fundo')
cap = PR['captions']
legenda = pedacos(CAM / 'legenda.mov', [fr(b['s']) for b in cap], lambda x, y: (lambda b: txt(b) if b else 'legenda')(perto(cap, x, y)), 'legenda')
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
midia = [(CAM / 'midia.mov', fr(v['s']) - 8, fr(v['e']) - fr(v['s']) + 16, Path(v['src']).stem) for v in ins] if (CAM / 'midia.mov').exists() else []
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
JOB = json.load(open(W / 'job.json'))
LAY = {'camShift': 600, 'camUp': 300, **((PR.get('theme') or {}).get('layout') or {})}
TR = 0.42                                                       # troca de layout do Reel.tsx
ramp = lambda t, a, d: EASE((t - a) / d)


def split_amt(t, gs):
    v = 0.0
    for g in gs:
        a, b = g['s'] - TR * 0.35, g['e'] - TR * 0.35
        v = max(v, min(ramp(t, a, TR), 1 - ramp(t, b, TR)))
    return v


def zlog(t):
    import math
    s = 0.0
    for m in JOB.get('camera_moves') or []:
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
    spI = split_amt(t, [g for g in PR['split'] if g.get('inv')]); sp = split_amt(t, PR['split'])
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


SRC = Path(JOB['src']); TC0 = tc_frames(SRC)
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
        assets.append(f'<asset id="{ids[f]}" name={quoteattr(f.name)} start="{tt(tc)}" duration="{tt(fr(dur(f)))}" hasVideo="{int(video)}" hasAudio="{int(audio)}"'
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
    vals = [(n, transf(k, float((a + n) * FD))) for n in range(0, b - a + 1)]
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


V1 = nova()                                                   # bruto, take a take, com alça
for k, (a, b, s0, s1) in enumerate(takes):
    L.append(bruto(k, a, b, s0).replace('lane="1"', f'lane="{V1}"', 1))
    L.append(clip(OUT / 'voz.wav', -1, a, b - a, f'voz {s0:.2f}-{s1:.2f}', start=a, video=False, audio=True))
V2 = nova()                                                   # câmera renderizada por cima (imagem aprovada); para estender um
for a, b, s0, s1 in takes:                                    # take, desligue o clipe dela e use o bruto embaixo
    L.append(clip(CAM / 'camera.mov', V2, a, b - a, f'câmera renderizada {s0:.2f}', start=a))
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
V = nova()
for f, off, n in burns:
    L.append(clip(f, V, off, n, 'burn', extra=f'<adjust-blend amount="{BOP}"/>'))
L.append(clip(OUT / 'capa.mov', nova(), 0, 1, 'capa (quadro 0)'))
L.append(clip(OUT / 'trilha.wav', -2, 0, fr(dur(OUT / 'trilha.wav')), 'trilha', video=False, audio=True))
fim = []                                                      # SFX: faixas de áudio sem sobreposição
for f, ins_, off, n, db in sorted(sfx, key=lambda z: z[2]):
    k = next((i for i, e in enumerate(fim) if e <= off), len(fim))
    if k == len(fim):
        fim.append(0)
    fim[k] = off + n
    L.append(clip(f, -3 - k, off, n, f.stem, start=ins_, video=False, audio=True, extra=f'<adjust-volume amount="{db:.1f}dB"/>'))
xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.10">
<resources>
<format id="r1" name="FFVideoFormat1080x1920p2997" frameDuration="1001/30000s" width="1080" height="1920" colorSpace="1-1-1 (Rec. 709)"/>
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
