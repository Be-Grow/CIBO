#!/usr/bin/env python3
"""Regra do CIBO para timelines no DaVinci (19/10/2026, pedido do editor "aplica cor nas camadas pra me ajudar a organizar"):
cada clipe ganha a cor do seu tipo e cada faixa o nome do tipo que domina nela. A API não muda cor de FAIXA, só de clipe.
O tipo vem do nome do clipe e da pasta do arquivo no pacote (07_davinci/<nome>/…).
uso: resolve_cores.py "NOME DA TIMELINE" […]   (projeto aberto no Resolve; sem nome = todas as timelines do projeto)"""
import re, sys
sys.path.append("/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules")
import DaVinciResolveScript as dvr

# tipo → (cor do clipe no Resolve, nome da faixa). Mesma tabela em client-router/references/regras/davinci.md
CORES = {
    'camera':     ('Blue',      'CÂMERA bruto'),
    'fundo_cam':  ('Navy',      'CÂMERA fundo desfocado'),
    'cam_ref':    ('Navy',      'CÂMERA renderizada (ref.)'),
    'mov_zoom':   ('Orange',    'MOV punch/zoom (Fusion)'),
    'mov_split':  ('Apricot',   'MOV tela dividida (Fusion)'),
    'midia':      ('Teal',      'MÍDIA / B-roll'),
    'painel_bg':  ('Purple',    'PAINEL fundo'),
    'painel':     ('Violet',    'PAINEL partes'),
    'etapa':      ('Violet',    'PAINEL etapa'),
    'tag':        ('Pink',      'ETIQUETAS'),
    'titulo':     ('Yellow',    'TÍTULOS / gancho / tarja'),
    'legenda':    ('Lime',      'LEGENDA (frase)'),
    'burn':       ('Tan',       'BURNS'),
    'extra':      ('Beige',     'EXTRAS'),
    'capa':       ('Brown',     'CAPA'),
    'a_camera':   ('Blue',      'ÁUDIO câmera (ref.)'),
    'a_voz':      ('Green',     'VOZ'),
    'a_trilha':   ('Olive',     'TRILHA'),
    'a_sfx':      ('Chocolate', 'SFX'),
}


def tipo(it, faixa):
    n = it.GetName() or ''; mpi = it.GetMediaPoolItem()
    fp = (mpi.GetClipProperty('File Path') if mpi else '') or ''
    if faixa == 'audio':
        return 'a_voz' if re.search(r'/voz(__[^/]*)?\.wav$', fp) else 'a_trilha' if fp.rsplit('/', 1)[-1].startswith('trilha') else 'a_sfx' if '/sfx/' in fp \
            else 'a_camera' if '/01_sources/' in fp or not fp else 'a_sfx'
    if re.match(r'(punch|zoom) ', n): return 'mov_zoom'
    if n.startswith('tela dividida'): return 'mov_split'
    if '/01_sources/' in fp or n.startswith('bruto'): return 'camera'
    if 'fundo_desfocado' in fp: return 'fundo_cam'
    if re.search(r'/camera(__[^/]*)?\.mov$', fp) or n.startswith('câmera'): return 'cam_ref'
    if '/paineis_fundo/' in fp or '/painel_fundo' in fp: return 'painel_bg'
    if '/legenda/' in fp: return 'legenda'
    if '/burns/' in fp: return 'burn'
    if re.search(r'/capa(__[^/]*)?\.mov$', fp): return 'capa'
    b = fp.rsplit('/', 1)[-1]
    for pre, t in (('painel_', 'painel'), ('step_', 'etapa'), ('tag_', 'tag'), ('titulo_', 'titulo'), ('kw_', 'titulo'), ('cartao', 'titulo')):
        if b.startswith(pre): return t
    if '/midia' in fp or '/extras/' in fp: return 'midia' if '/midia' in fp else 'extra'
    return 'extra'


def aplica(tl):
    feitos = {}
    for faixa in ('video', 'audio'):
        for k in range(1, tl.GetTrackCount(faixa) + 1):
            cont = {}
            for it in tl.GetItemListInTrack(faixa, k) or []:
                t = tipo(it, faixa); it.SetClipColor(CORES[t][0]); cont[t] = cont.get(t, 0) + 1
            if cont:
                t = max(cont, key=cont.get); tl.SetTrackName(faixa, k, CORES[t][1]); feitos[t] = feitos.get(t, 0) + sum(cont.values())
    return feitos


if __name__ == '__main__':
    r = dvr.scriptapp("Resolve"); p = r.GetProjectManager().GetCurrentProject()
    tls = [p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1)]
    for tl in [t for t in tls if not sys.argv[1:] or t.GetName() in sys.argv[1:]]:
        f = aplica(tl); print(f'{tl.GetName()[:45]}: ' + ', '.join(f'{k} {v}' for k, v in sorted(f.items())), flush=True)
