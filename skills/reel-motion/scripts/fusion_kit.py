#!/usr/bin/env python3
"""Kit único de Resolve + Fusion do CIBO. Todo script que fala com o Resolve importa daqui; nada de `dvr.scriptapp` à mão
em pasta de job (14/11/2026: 57 scripts de job refaziam a conexão e a mesma correção caiu só em um deles).

Fusion direto NO CLIPE pela API (sem clipe de ajuste, sem ciclo de .drt). Vem do `resolve_logo.py` da Andreia (21/10/2026,
validado em 8 timelines) e do `resolve_fx.py` (motion blur, shutter 360°):
  - `AddFusionComp` sozinho não persiste nem renderiza: exporte e reimporte o comp (`fixa`).
  - alças do `SetKeyFrames` são RELATIVAS ao keyframe; absolutas estouram a curva.
  - o comp conta do início do CLIPE (quadro 0 = primeiro quadro na timeline), mesmo com a fonte aparada (testado 14/11/2026).
  - `GlobalIn` do MediaIn1 = −(quadros aparados no início da fonte): 0 em clipe inteiro, −60 em clipe que entra no quadro 60.
    O que não pode é ele MUDAR no exportar/importar (ciclo de .drt somava 1 e o render falhava): `fixa` confere.

Como biblioteca:
    import fusion_kit as K
    r, pm, p = K.resolve(); tl = K.timeline(p, 'NOME'); it = K.clipe_em(tl, 'CÂMERA bruto', 12.5)
    K.zoom(it, [(0, 1.0), (15, 1.10), (100, 1.10), (124, 1.0)], COMPS / 'zoom_01.comp')

Na mão (projeto aberto, limite de tempo embutido):
    fusion_kit.py lista "TIMELINE"                               faixas, clipes e quem tem Fusion
    fusion_kit.py zoom "TIMELINE" "FAIXA" T0 T1 ESCALA [--entra 0.5] [--sai 0.8] [--cx 0.5 --cy 0.5] [--seco]
    fusion_kit.py entra-sai "TIMELINE" "FAIXA" [--escala 1.06] [--blur 20] [--px X Y W H]
T0/T1 em segundos da timeline. `zoom` = zoom in suave até T0+entra, segura, zoom out até T1; `--seco` volta no corte, sem zoom out.
Os comps ficam em PROJ/04_work/comps (ou --comps PASTA)."""
import os, signal, subprocess, sys, time, unicodedata
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../_shared'))
import resolve_env  # noqa: E402  (API do Resolve em Mac/Windows; no Mac os mesmos caminhos de antes)
API = resolve_env.api_dir()

E = 1 / 3                                   # alça = 1/3 do intervalo (ease in/out do motor)
nfc = lambda x: unicodedata.normalize('NFC', x or '')


# ---------- conexão e projeto ----------
def limite(seg):
    """A API trava calada com diálogo aberto no Resolve: todo script tem tempo limite."""
    resolve_env.limite(seg, lambda: f'PAREI: {seg} s sem resposta do Resolve. Janelas abertas: {dialogos()}')


def dialogos():
    """janelas do Resolve além da principal (diálogo modal = API presa)"""
    return resolve_env.janelas_resolve()


def resolve(espera=180):
    """(resolve, project manager, projeto aberto). Espera o Resolve responder; não abre o app sozinho."""
    import DaVinciResolveScript as dvr
    r, t0 = None, time.time()
    while time.time() - t0 < espera:
        r = dvr.scriptapp('Resolve')
        if r: break
        time.sleep(3)
    assert r, 'Resolve não respondeu à API (está aberto? Preferences > System > General > External scripting = Local)'
    pm = r.GetProjectManager()
    return r, pm, pm.GetCurrentProject()


def salva(pm):
    """SaveProject com o "Untitled Project" aberto abre o diálogo de nome e prende a API (EP 07 20/10, João 14/11/2026)."""
    cur = pm.GetCurrentProject()
    if cur and not cur.GetName().startswith('Untitled Project'):
        return pm.SaveProject()
    return False


def abre_projeto(pm, pasta, nome):
    """Abre (ou cria) `nome` em `pasta` ("BeGrow/Cliente") sem cair no diálogo de salvar. Devolve (projeto, era_novo)."""
    salva(pm); pm.GotoRootFolder()
    for f in [x for x in pasta.split('/') if x]:
        if f not in (pm.GetFolderListInCurrentFolder() or []): pm.CreateFolder(f)
        assert pm.OpenFolder(f), f'não abriu a pasta {f}'
    novo = nome not in (pm.GetProjectListInCurrentFolder() or [])
    p = pm.CreateProject(nome) if novo else pm.LoadProject(nome)
    assert p and p.GetName() == nome, f'projeto {nome} não abriu (janelas: {dialogos()})'
    return p, novo


# ---------- timeline ----------
def timelines(p):
    return [p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1)]


def timeline(p, nome):
    tl = next((t for t in timelines(p) if nfc(t.GetName()) == nfc(nome)), None)
    assert tl, f'timeline não achada: {nome} (tem: {[t.GetName() for t in timelines(p)]})'
    p.SetCurrentTimeline(tl); return tl


def fps(tl):
    return float(tl.GetSetting('timelineFrameRate'))


def faixa(tl, nome, tipo='video'):
    """índice da faixa pelo nome (ou pelo número, se vier "3")"""
    if str(nome).isdigit(): return int(nome)
    k = next((k for k in range(1, tl.GetTrackCount(tipo) + 1) if nfc(tl.GetTrackName(tipo, k)) == nfc(nome)), None)
    assert k, f'faixa "{nome}" não existe (tem: {[tl.GetTrackName(tipo, k) for k in range(1, tl.GetTrackCount(tipo) + 1)]})'
    return k


def itens(tl, nome_faixa, tipo='video'):
    return sorted(tl.GetItemListInTrack(tipo, faixa(tl, nome_faixa, tipo)) or [], key=lambda i: i.GetStart())


def clipe_em(tl, nome_faixa, t, tipo='video'):
    """clipe da faixa que está tocando no segundo t da timeline"""
    q = tl.GetStartFrame() + round(t * fps(tl))
    it = next((i for i in itens(tl, nome_faixa, tipo) if i.GetStart() <= q < i.GetEnd()), None)
    assert it, f'nenhum clipe em {t}s na faixa {nome_faixa}'
    return it


def copia_transform(de, para):
    """Clipe recolocado pela API entra com Scaling 0 e sem rotação (Andreia 20/10): copie do irmão."""
    pr = de.GetProperty() or {}
    return {k: para.SetProperty(k, pr[k]) for k in ('ZoomGang', 'ZoomX', 'ZoomY', 'Pan', 'Tilt', 'RotationAngle', 'CropLeft', 'CropRight', 'CropTop', 'CropBottom', 'Scaling') if k in pr}


# ---------- Fusion no clipe ----------
def q0(comp):
    """quadro do comp onde o clipe começa"""
    return int((comp.GetAttrs() or {}).get('COMPN_RenderStart', 0) or 0)


def anima(tool, inp, pts, ease=E):
    """keyframes [(quadro, valor)…] com alças planas (ease in/out). Quadros no tempo do comp."""
    tool.AddModifier(inp, 'BezierSpline')
    spl = {i.ID: i for i in tool.GetInputList().values()}[inp].GetConnectedOutput().GetTool(); tab = {}
    for j, (f, v) in enumerate(pts):
        k = {1: float(v)}
        if j: k['LH'] = {1: -(f - pts[j - 1][0]) * ease, 2: 0.0}
        if j < len(pts) - 1: k['RH'] = {1: (pts[j + 1][0] - f) * ease, 2: 0.0}
        tab[f] = k
    spl.SetKeyFrames(tab, True)
    return spl


def le(tool, inp, quadros):
    """lê a curva de volta: confira antes de dizer que animou"""
    return [round(float(tool.GetInput(inp, q)), 4) for q in quadros]


def reenquadrado(it):
    """Pan/Tilt do Inspector no clipe (lido ANTES de pôr Fusion: com comp o Pan lido cai para 1/4, Michelle 19/11/2026)"""
    try:
        return abs(float(it.GetProperty('Pan') or 0)) > 0.5 or abs(float(it.GetProperty('Tilt') or 0)) > 0.5
    except (TypeError, ValueError):
        return False


def abre_comp(it):
    """comp novo no clipe, travado para editar. Devolve (comp, MediaIn1, MediaOut1).
    Trava (23/11/2026): clipe reenquadrado com Pan/Tilt não leva Fusion. O Fusion processa ANTES do Inspector (manual do
    Resolve, cap. 11 "Fusion Effects and Resolution", p. 287) e o Pan desloca a saída: faixa/quadro preto (Michelle 19/11/2026,
    "frames pretos em 25 s"). Zoom nesse clipe vai no Zoom do Inspector, ou componha o vertical antes. Liberar: CIBO_FUSION_PAN_OK=1."""
    if not it.GetFusionCompCount() and reenquadrado(it) and os.environ.get('CIBO_FUSION_PAN_OK') != '1':
        raise AssertionError(f'clipe "{it.GetName()}" reenquadrado com Pan/Tilt ({it.GetProperty("Pan")}, {it.GetProperty("Tilt")}): '
                             'Fusion aqui revela preto (o Fusion vem antes do Pan). Use o Zoom do Inspector ou componha o vertical antes.')
    comp = it.AddFusionComp(); assert comp, 'AddFusionComp falhou'
    comp.Lock()
    return comp, comp.FindTool('MediaIn1'), comp.FindTool('MediaOut1')


def no(comp, tipo, nome, entrada):
    """nó novo ligado depois de `entrada`"""
    t = comp.AddTool(tipo, -32768, -32768); assert t, f'AddTool {tipo} falhou'
    t.SetAttrs({'TOOLS_Name': nome}); t.ConnectInput('Input', entrada)
    return t


def fixa(it, comp, arq):
    """Exporta e reimporta o comp (sem isso não persiste nem renderiza) e confere que o GlobalIn do MediaIn1 não andou."""
    gi0 = int(comp.FindTool('MediaIn1').GetInput('GlobalIn') or 0)
    comp.Unlock(); arq = Path(arq); arq.parent.mkdir(parents=True, exist_ok=True)
    antes = list(it.GetFusionCompNameList() or [])
    assert it.ExportFusionComp(str(arq), len(antes)), 'ExportFusionComp falhou'
    novo = it.ImportFusionComp(str(arq)); assert novo, 'ImportFusionComp falhou'
    nomes = list(it.GetFusionCompNameList() or [])
    it.LoadFusionCompByName(nomes[-1])
    for n in antes:                                              # fica só o comp reimportado
        if n != nomes[-1]: it.DeleteFusionCompByName(n)
    gi = int(novo.FindTool('MediaIn1').GetInput('GlobalIn') or 0)
    assert gi == gi0, f'GlobalIn andou de {gi0} para {gi}: o render do Fusion falha; refaça o comp'
    return gi


def zoom(it, pts, arq, centro=(0.5, 0.5), blur=True, nome='Zoom'):
    """Zoom in/out no Transform do Fusion do próprio clipe, com motion blur (Quality 10, Shutter 360°): o jeito do CIBO de
    fazer zoom/punch (Andreia 19/10/2026: "mover os movimentos de câmera para dentro do transform do Fusion com shutter angle
    e blur"). pts = [(quadro a partir do início do clipe, escala)…]; centro = ponto que fica parado (0–1, y de baixo)."""
    comp, mi, mo = abre_comp(it); d = q0(comp)
    tf = no(comp, 'Transform', nome, mi); mo.ConnectInput('Input', tf)
    tf.SetInput('Pivot', {1: centro[0], 2: centro[1]})
    if blur:
        tf.SetInput('MotionBlur', 1); tf.SetInput('Quality', 10); tf.SetInput('ShutterAngle', 360)
    pts = [(d + f, v) for f, v in pts]
    anima(tf, 'Size', pts)
    lido = le(tf, 'Size', [f for f, _ in pts])
    gi = fixa(it, comp, arq)
    assert all(abs(a - b) < 0.002 for a, (_, b) in zip(lido, pts)), f'curva lida {lido} ≠ pedida {pts}'
    return lido


def entra_sai(it, arq, pivo=(0.5, 0.5), escala=1.06, blur_ent=20, blur_sai=12, ent=24, sai=18, nome='Peca'):
    """Entrada e saída de selo/logo/cartão: escala→1, blur→0 e opacidade 0→1; na saída blur e opacidade voltam.
    pivo = centro da peça no quadro (0–1, y de baixo)."""
    comp, mi, mo = abre_comp(it); d = q0(comp); D = it.GetDuration()
    tf = no(comp, 'Transform', nome + 'Escala', mi); bl = no(comp, 'Blur', nome + 'Blur', tf); bc = no(comp, 'BrightnessContrast', nome + 'Opacidade', bl)
    mo.ConnectInput('Input', bc)
    tf.SetInput('Pivot', {1: pivo[0], 2: pivo[1]}); bl.SetInput('LockXY', 1); bc.SetInput('Alpha', 1)
    anima(tf, 'Size', [(d, escala), (d + ent, 1.0)])
    anima(bl, 'XBlurSize', [(d, blur_ent), (d + ent, 0), (d + D - 1 - sai, 0), (d + D - 1, blur_sai)])
    anima(bc, 'Gain', [(d, 0), (d + ent, 1), (d + D - 1 - sai, 1), (d + D - 1, 0)])
    return fixa(it, comp, arq)


# ---------- ciclo de .drt ----------
TRANSF = ('Pan', 'Tilt', 'ZoomX', 'ZoomY')


def transforms(tl):
    """foto do Pan/Tilt/Zoom dos clipes de vídeo SEM Fusion, por (nome, início, fim), para conferir depois de um ciclo de .drt"""
    foto, vistos = {}, set()
    for k in range(1, tl.GetTrackCount('video') + 1):
        for it in tl.GetItemListInTrack('video', k) or []:
            if it.GetFusionCompCount(): continue
            ch = (nfc(it.GetName()), it.GetStart(), it.GetEnd())
            if ch in vistos: foto.pop(ch, None); continue        # chave repetida: ambíguo, não mexe
            vistos.add(ch); foto[ch] = {p: it.GetProperty(p) for p in TRANSF}
    return foto


def reaplica_transforms(tl, foto, nome=''):
    """Ciclo de .drt (export/import) MULTIPLICA por 4 o Pan dos clipes em scaleToCrop (Michelle 19/11/2026: tela preta nos
    horizontais). Depois de todo .drt: relê e regrava o que mudou. Devolve quantos clipes foram corrigidos."""
    fixos = 0
    for k in range(1, tl.GetTrackCount('video') + 1):
        for it in tl.GetItemListInTrack('video', k) or []:
            antes = foto.get((nfc(it.GetName()), it.GetStart(), it.GetEnd()))
            if not antes or it.GetFusionCompCount(): continue
            mudou = False
            for p, v in antes.items():
                agora = it.GetProperty(p)
                if isinstance(v, (int, float)) and isinstance(agora, (int, float)) and abs(agora - v) > max(0.01, abs(v) * 0.01):
                    it.SetProperty(p, v); mudou = True
            fixos += mudou
    if fixos: print(f'{nome[:45]}: Pan/Tilt/Zoom de {fixos} clipe(s) mudou no .drt e foi regravado', flush=True)
    return fixos


def pontos_zoom(dur, f0, f1, quanto, entra, sai, seco=False):
    """[(quadro, escala)] de um zoom: parado → sobe até f0+entra → segura → desce até f1 (ou corta seco em f1)"""
    f0 = max(0, f0); f1 = min(dur - 1, f1); topo = min(f0 + entra, f1)
    pts = [(f0, 1.0), (topo, quanto)] if f0 > 0 else [(0, 1.0), (max(topo, 1), quanto)]
    if seco:
        if f1 > pts[-1][0] + 1: pts += [(f1 - 1, quanto), (f1, 1.0)]
    else:
        desce = max(pts[-1][0], f1 - sai)
        if desce > pts[-1][0]: pts.append((desce, quanto))
        if f1 > pts[-1][0]: pts.append((f1, 1.0))
    return pts


# ---------- linha de comando ----------
def _opt(a, nome, n=1, padrao=None, tipo=float):
    if nome not in a: return padrao
    i = a.index(nome); v = [tipo(x) for x in a[i + 1:i + 1 + n]]; del a[i:i + 1 + n]
    return v[0] if n == 1 else v


def main():
    a = sys.argv[1:]
    if not a or a[0] in ('-h', '--help'):
        print(__doc__); return
    limite(int(os.environ.get('RESOLVE_LIMITE', 300)))
    cmd = a.pop(0); comps = _opt(a, '--comps', tipo=str)
    r, pm, p = resolve(); assert p, 'nenhum projeto aberto'
    tl = timeline(p, a[0]); F = fps(tl); s0 = tl.GetStartFrame()
    if cmd == 'lista':
        print(f'{p.GetName()} | {tl.GetName()} | {F} fps | {tl.GetSetting("timelineResolutionWidth")}x{tl.GetSetting("timelineResolutionHeight")}')
        for tipo in ('video', 'audio'):
            for k in range(1, tl.GetTrackCount(tipo) + 1):
                its = tl.GetItemListInTrack(tipo, k) or []
                fu = sum(1 for i in its if tipo == 'video' and i.GetFusionCompCount())
                print(f'  {tipo[0].upper()}{k} {tl.GetTrackName(tipo, k)}: {len(its)} clipes' + (f', {fu} com Fusion' if fu else ''))
        return
    if not comps:
        comps = Path(os.environ.get('TMPDIR', '/Volumes/SSD/CIBO/tmp')) / 'comps'
    comps = Path(comps); marca = time.strftime('%H%M%S')
    if cmd == 'zoom':
        entra = _opt(a, '--entra', padrao=0.5); sai = _opt(a, '--sai', padrao=0.8); cx = _opt(a, '--cx', padrao=0.5); cy = _opt(a, '--cy', padrao=0.5)
        seco = '--seco' in a; a = [x for x in a if x != '--seco']
        fx, t0, t1, quanto = a[1], float(a[2]), float(a[3]), float(a[4])
        it = clipe_em(tl, fx, t0); ini = it.GetStart() - s0
        pts = pontos_zoom(it.GetDuration(), round(t0 * F) - ini, round(t1 * F) - ini, quanto, round(entra * F), round(sai * F), seco)
        lido = zoom(it, pts, comps / f'zoom_{marca}.comp', (cx, cy))
        print(f'zoom no Fusion de "{it.GetName()[:40]}": quadros {[f for f, _ in pts]} escalas {lido}, motion blur 360°')
    elif cmd == 'entra-sai':
        esc = _opt(a, '--escala', padrao=1.06); bl = _opt(a, '--blur', padrao=20); px = _opt(a, '--px', n=4)
        W, H = int(tl.GetSetting('timelineResolutionWidth')), int(tl.GetSetting('timelineResolutionHeight'))
        pivo = ((px[0] + px[2] / 2) / W, 1 - (px[1] + px[3] / 2) / H) if px else (0.5, 0.5)
        for n, it in enumerate(itens(tl, a[1]), 1):
            entra_sai(it, comps / f'peca_{marca}_{n:02d}.comp', pivo, esc, bl)
        print(f'entrada/saída no Fusion em {n} clipes da faixa {a[1]}')
    else:
        sys.exit(f'comando desconhecido: {cmd}')
    salva(pm)


if __name__ == '__main__':
    main()
