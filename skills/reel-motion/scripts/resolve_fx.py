#!/usr/bin/env python3
"""Movimentos de câmera em clipes de ajuste com Transform do Fusion (motion blur, shutter 360°), um por zoom/punch/troca de
tela dividida (Andreia 19/10/2026). O FCPXML não leva clipe de ajuste: a timeline já importada (bruto só com o enquadramento
base, "camera_fusion" no reel.json) é exportada em .drt, ganha faixas de ajuste logo acima do bruto (modelo em
assets/davinci_faixa_ajuste.xml, copiado do clipe que o editor montou), volta para o projeto com o mesmo nome e cada
Transform recebe os keyframes de movimentos.json (Size e Center, pivô no centro do quadro).
uso: resolve_fx.py PACOTE [PACOTE…]   (projeto já aberto no Resolve, timeline com o nome da pasta do pacote)"""
if __name__ == '__main__':   # saída curta + log completo em 05_qa/logs (client-router/scripts/saida_curta.py)
    import os as _o, sys as _s; _s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.realpath(__file__)), '../../client-router/scripts')); import saida_curta; saida_curta.curta()
import json, os, re, shutil, sys, tempfile, unicodedata, uuid, zipfile
from pathlib import Path
sys.path.append("/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules")
import DaVinciResolveScript as dvr

MODELO = (Path(__file__).parent.parent / 'assets' / 'davinci_faixa_ajuste.xml').read_text(encoding='utf-8')
cab, clip, rodape = re.match(r'(.*?<Items>\n)(     <Element>\n.*?     </Element>\n)(    </Items>.*)', MODELO, re.S).groups()
r = dvr.scriptapp("Resolve"); p = r.GetProjectManager().GetCurrentProject(); mp = p.GetMediaPool()
uid = lambda t: re.sub(r'DbId="[0-9a-f-]{36}"', lambda _: f'DbId="{uuid.uuid4()}"', t)


EASE = 0.5                                                      # alça = metade do intervalo até a pose vizinha (ease in/out)


def poses(kf):
    """quadros onde o movimento começa, para ou vira (pico do punch): só eles viram keyframe. "Andando" = velocidade acima
    de 4% da máxima da camada (a cauda do ease e o ajuste fino do rosto na tela dividida não contam); poses a menos de
    5 quadros viram uma só (a mais parada). Entre poses, pose extra só se a reta erra mais de ~12 px."""
    n = len(kf)
    vel = [max(abs(kf[i + 1][c] - kf[i][c]) for c in (1, 2, 3)) for i in range(n - 1)] or [0]
    thr = max(vel) * 0.04; anda = [v > thr for v in vel]
    P = [0] + [i for i in range(1, n - 1) if anda[i - 1] != anda[i]] + [n - 1]
    vel_q = lambda i: min(vel[max(0, i - 1)], vel[min(len(vel) - 1, i)])
    G = []
    for q in P:
        if G and q - G[-1][-1] < 5: G[-1].append(q)
        else: G.append([q])
    P = [0 if 0 in g else n - 1 if n - 1 in g else min(g, key=vel_q) for g in G]
    def refina(a, b):                                           # subdivisão recursiva contra o S do ease; trecho < 1 s fica só no ease
        if b - a < 30:
            return []
        pior, ip = 0, None
        for i in range(a + 5, b - 4):
            u = (i - a) / (b - a); u = u * u * (3 - 2 * u)
            e = max(abs(kf[i][c] - (kf[a][c] + (kf[b][c] - kf[a][c]) * u)) for c in (1, 2, 3))
            if e > pior: pior, ip = e, i
        return refina(a, ip) + [ip] + refina(ip, b) if pior > 0.006 and ip else []
    out = [P[0]]
    for b in P[1:]:
        out += refina(out[-1], b) + [b]
    out = sorted(set(out))
    # pose quase igual à vizinha (< 20% da excursão da camada) a menos de 1 s dela é cauda de ease: sai (mantém os segurados longos)
    rng = max(max(q[c] for q in kf) - min(q[c] for q in kf) for c in (1, 2, 3)) or 1
    dif = lambda a, b: max(abs(kf[a][c] - kf[b][c]) for c in (1, 2, 3)) / rng
    i = 1
    while i < len(out) - 1:
        a, p, b = out[i - 1], out[i], out[i + 1]
        if p - a < 30 and dif(p, a) < 0.2:
            out.pop(i)                                          # fica a primeira do par (o pico no tempo da palavra)
        elif b - p < 30 and dif(p, b) < 0.2:
            out.pop(i + 1 if i + 1 < len(out) - 1 else i)
        else:
            i += 1
    return out


def curvas(comp, tf, c):
    """Size e Center com keyframe só nas poses e alças planas (ease in/out), substituindo o que houver"""
    kf = c['kf']; P = poses(kf)
    ent = {i.ID: i for i in tf.GetInputList().values()}
    xy = ent['Center'].GetConnectedOutput().GetTool(); xin = {i.ID: i for i in xy.GetInputList().values()}
    spl = {'Size': ent['Size'].GetConnectedOutput().GetTool(), 'X': xin['X'].GetConnectedOutput().GetTool(), 'Y': xin['Y'].GetConnectedOutput().GetTool()}
    for nome, col in (('Size', 1), ('X', 2), ('Y', 3)):
        tab = {}; T = [kf[q][0] for q in P]; V = [kf[q][col] for q in P]
        for j, q in enumerate(P):
            f, v = T[j], V[j]; k = {1: v}
            # cúbica monotônica (Fritsch–Carlson): alça plana (ease) onde o canal começa, para ou vira; no meio de um
            # movimento a curva passa direto (antes cada keyframe da segurada freava e o rosto saía até 58 px do lugar)
            d0 = (V[j] - V[j - 1]) / (T[j] - T[j - 1]) if j > 0 else 0.0
            d1 = (V[j + 1] - V[j]) / (T[j + 1] - T[j]) if j < len(P) - 1 else 0.0
            m = 0.0 if d0 * d1 <= 0 else 2 * d0 * d1 / (d0 + d1)
            if m:
                if j > 0: k['LH'] = {1: -(T[j] - T[j - 1]) / 3, 2: -m * (T[j] - T[j - 1]) / 3}
                if j < len(P) - 1: k['RH'] = {1: (T[j + 1] - T[j]) / 3, 2: m * (T[j + 1] - T[j]) / 3}
                tab[f] = k; continue
            # alças RELATIVAS ao keyframe no Fusion do Resolve (absolutas faziam a curva estourar para o dobro, 19/10/2026)
            if j > 0: k['LH'] = {1: -(f - kf[P[j - 1]][0]) * EASE, 2: 0.0}
            if j < len(P) - 1: k['RH'] = {1: (kf[P[j + 1]][0] - f) * EASE, 2: 0.0}
            tab[f] = k
        spl[nome].SetKeyFrames(tab, True)
    return len(P)


def faixas(camadas):
    """camadas → faixas sem sobreposição; zooms embaixo (aplicados antes), trocas de tela dividida em cima"""
    out = []
    for tipo in ('z', 's'):
        fins = []
        for c in [c for c in camadas if c['tipo'] == tipo]:
            k = next((i for i, e in enumerate(fins) if e <= c['inicio']), len(fins))
            if k == len(fins):
                fins.append(0); out.append([])
            fins[k] = c['inicio'] + c['dur']; out[len(out) - len(fins) + k].append(c)
    return out


SO_CURVAS = '--curvas' in sys.argv
for pac in map(Path, [a for a in sys.argv[1:] if not a.startswith('--')]):
    if SO_CURVAS:
        mv = json.load(open(pac / 'movimentos.json', encoding='utf-8'))
        tl = next(p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1) if p.GetTimelineByIndex(i).GetName() == pac.name)
        por = {(c['inicio'], c['nome']): c for c in mv['camadas']}; feitos = []
        for k in range(1, tl.GetTrackCount('video') + 1):
            for it in tl.GetItemListInTrack('video', k) or []:
                c = por.get((it.GetStart(), it.GetName()))
                if c and it.GetFusionCompCount():
                    comp = it.GetFusionCompByIndex(1); comp.Lock(); feitos.append(curvas(comp, comp.FindTool('Transform1'), c)); comp.Unlock()
        print(f'{pac.name}: {len(feitos)} camadas, keyframes por canal {feitos}', flush=True); continue
    nome = pac.name; mv = json.load(open(pac / 'movimentos.json', encoding='utf-8'))
    tl = next((p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1) if p.GetTimelineByIndex(i).GetName() == nome), None)
    assert tl, f'timeline não achada: {nome}'
    tmp = Path(tempfile.mkdtemp()); drt = tmp / 'a.drt'
    assert tl.Export(str(drt), r.EXPORT_DRT, r.EXPORT_NONE), 'exportação .drt falhou'
    d = tmp / 'x'; zipfile.ZipFile(drt).extractall(d)
    seq = next((d / 'SeqContainer').glob('*.xml')); s = seq.read_text(encoding='utf-8'); nfc = lambda x: unicodedata.normalize('NFC', x)
    vv = s[s.index('<VideoTrackVec>'):s.index('</VideoTrackVec>')]
    trilhas = re.findall(r'  <Element>\n   <Sm2TiTrack .*?</Sm2TiTrack>\n  </Element>\n', vv, re.S)
    ib = next(i for i, t in enumerate(trilhas) if f'<MediaFilePath>{nfc(mv["src"])}</MediaFilePath>' in nfc(t))
    FX = faixas(mv['camadas']); novas = ''
    for fx in FX:
        itens = ''.join(clip.replace('<Start>117</Start>', f'<Start>{c["inicio"]}</Start>').replace('<Duration>408</Duration>', f'<Duration>{c["dur"]}</Duration>') for c in fx)
        novas += uid(cab + itens + rodape)
    s = s.replace(trilhas[ib], trilhas[ib] + novas, 1); seq.write_text(s, encoding='utf-8')
    drt2 = tmp / 'b.drt'
    with zipfile.ZipFile(drt2, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in d.rglob('*'):
            if f.is_file(): z.write(f, f.relative_to(d))
    tl.SetName(nome + ' (antiga)')
    novo = mp.ImportTimelineFromFile(str(drt2), {'timelineName': nome})
    assert novo, 'importação .drt falhou'
    novo.SetName(nome); p.SetCurrentTimeline(novo)
    for j, fx in enumerate(FX):
        itens = {it.GetStart(): it for it in novo.GetItemListInTrack('video', ib + 2 + j) or []}
        for c in fx:
            it = itens[c['inicio']]; it.SetName(c['nome'])
            comp = it.GetFusionCompByIndex(1); tf = comp.FindTool('Transform1'); comp.Lock()
            comp.SetAttrs({'COMPN_GlobalStart': 0, 'COMPN_GlobalEnd': c['dur'] - 1, 'COMPN_RenderStart': 0, 'COMPN_RenderEnd': c['dur'] - 1})
            tf.SetInput('MotionBlur', 1); tf.SetInput('Quality', 10); tf.SetInput('ShutterAngle', 360)
            if c['tipo'] == 's':
                tf.SetInput('Edges', 3)                          # espelha a borda que descobre na troca (fica sob o painel)
            tf.AddModifier('Size', 'BezierSpline'); tf.AddModifier('Center', 'XYPath')
            q, sz, cx, cy = c['kf'][0]; tf.SetInput('Size', sz, q); tf.SetInput('Center', {1: cx, 2: cy}, q)
            curvas(comp, tf, c); comp.Unlock()
    if not any(it.GetName() == 'Adjustment Clip' for k in range(1, tl.GetTrackCount('video') + 1) for it in tl.GetItemListInTrack('video', k) or []):
        mp.DeleteTimelines([tl])                                 # a antiga só fica se o editor já tinha mexido nela
    shutil.rmtree(tmp, ignore_errors=True)
    sys.path.insert(0, str(Path(__file__).parent)); from resolve_cores import aplica; aplica(novo)   # cores/nomes (regra do CIBO)
    print(f'{nome}: {sum(map(len, FX))} camadas de ajuste em {len(FX)} faixas acima do bruto (faixa {ib + 1})', flush=True)
