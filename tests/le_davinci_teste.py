#!/usr/bin/env python3
"""Teste do client-router/scripts/le_davinci.py (24/11/2026), com o Resolve aberto.
Cria um projeto descartável com um título Text+ (fonte, texto, tamanho e cor conhecidos), exporta em .drp, apaga o projeto,
roda le_davinci.py --drp e confere o que voltou. Devolve o projeto que estava aberto. uso: le_davinci_teste.py"""
import json, subprocess, sys, tempfile, time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'skills/reel-motion/scripts')); sys.path.insert(0, str(REPO / 'skills/client-router/scripts'))
import fusion_kit as K, le_davinci as L   # noqa: E402

PASTA, NOME = 'CIBO teste', f'teste le_davinci {time.strftime("%H%M%S")}'
TEXTO, FONTE, TAM, COR = 'Diagnosticar a dor', 'Arial', 0.08, (1.0, 0.8, 0.2)
r, pm, cur = K.resolve()
ant = cur.GetName() if cur and not cur.GetName().startswith('Untitled Project') else None
if ant: K.salva(pm)
cam_ant = L.caminho_do(pm, ant) if ant else []
tmp = Path(tempfile.mkdtemp(dir='/Volumes/SSD/CIBO/tmp')); drp = tmp / 'teste.drp'; falhas = []
try:
    L.vai_para(pm, [PASTA], cria=True)
    p = pm.CreateProject(NOME); assert p, 'não criou o projeto de teste'
    p.SetSetting('timelineResolutionWidth', '1080'); p.SetSetting('timelineResolutionHeight', '1920')
    mp = p.GetMediaPool(); tl = mp.CreateEmptyTimeline('T1'); p.SetCurrentTimeline(tl)
    it = tl.InsertFusionTitleIntoTimeline('Text+'); assert it, 'não inseriu o Text+'
    t = next(x for x in it.GetFusionCompByIndex(1).GetToolList(False).values() if x.GetAttrs()['TOOLS_RegID'] == 'TextPlus')
    t.SetInput('StyledText', TEXTO); t.SetInput('Font', FONTE); t.SetInput('Size', TAM)
    for k, v in zip(('Red1', 'Green1', 'Blue1'), COR): t.SetInput(k, v)
    K.salva(pm)
    L.vai_para(pm, [PASTA]); pm.CloseProject(p)
    assert pm.ExportProject(NOME, str(drp), False), 'ExportProject falhou'
    pm.DeleteProject(NOME)
finally:
    L.vai_para(pm, cam_ant)
    if ant: pm.LoadProject(ant)
    pm.GotoRootFolder()
    if pm.OpenFolder(PASTA) and not pm.GetProjectListInCurrentFolder():
        pm.GotoRootFolder(); pm.DeleteFolder(PASTA)
    L.vai_para(pm, cam_ant)

out = tmp / 'saida'
res = subprocess.run([sys.executable, str(REPO / 'skills/client-router/scripts/le_davinci.py'), '--drp', str(drp), '--out', str(out)],
                     capture_output=True, text=True, encoding='utf-8', errors='replace')
if res.returncode: falhas.append('le_davinci falhou: ' + res.stdout[-600:] + res.stderr[-600:])
else:
    R = json.loads((out / 'padrao.json').read_text(encoding='utf-8'))
    if not any(FONTE in k for k in R['fontes_titulos']): falhas.append(f'fonte não lida: {R["fontes_titulos"]}')
    if TEXTO not in ' '.join(R['exemplos_texto']): falhas.append(f'texto não lido: {R["exemplos_texto"]}')
    if R['tamanho_titulo_mediana'] is None or abs(R['tamanho_titulo_mediana'] - TAM) > 1e-3: falhas.append(f'tamanho: {R["tamanho_titulo_mediana"]}')
    if '#FFCC33' not in R['cores_texto']: falhas.append(f'cor: {R["cores_texto"]}')
    if '1080x1920' not in ' '.join(R['formatos']): falhas.append(f'formato: {R["formatos"]}')
_, pm2, cur2 = K.resolve()
if ant and (not cur2 or cur2.GetName() != ant): falhas.append(f'não devolveu o projeto do editor ({ant}); aberto: {cur2 and cur2.GetName()}')
pm2.GotoRootFolder()
if 'CIBO leitura' in (pm2.GetFolderListInCurrentFolder() or []) or PASTA in (pm2.GetFolderListInCurrentFolder() or []):
    falhas.append('sobrou pasta temporária no Project Manager')
L.vai_para(pm2, cam_ant)
print('FALHOU:\n- ' + '\n- '.join(falhas) if falhas else f'OK le_davinci: Text+ ({FONTE}, {TAM}, #FFCC33), .drp importado e apagado, projeto do editor devolvido')
sys.exit(1 if falhas else 0)
