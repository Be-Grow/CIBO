#!/usr/bin/env python3
"""Projeto organizado no DaVinci (regra do CIBO, 20/10/2026: "os projetos que são feitos no DaVinci precisam estar sim
organizados"). Abre ou cria o projeto na pasta do cliente, cria os bins por tipo e arruma o Media Pool e as timelines.

  resolve_projeto.py abre     "BeGrow/Bombordo e Boreste" "EP 07 - Izaac Nava"    cria/abre e monta os bins
  resolve_projeto.py organiza                                                     move o que está solto na Master para o bin do tipo
  resolve_projeto.py arvore                                                       imprime a árvore do Media Pool (conferência)

Como módulo: `abre(pasta, nome, fps)`, `bin_(mp, caminho)`, `importa(mp, arquivos, caminho_bin)`, `organiza(p)`, `arvore(p)`.
Pasta de cliente no Project Manager segue a árvore que o editor já usa (BeGrow/<Cliente>/…)."""
import os, sys
sys.path.append("/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules")
import DaVinciResolveScript as dvr

BINS = ['00 TIMELINES', '01 BRUTO', '02 VOZ', '03 TRILHA', '04 SFX', '05 LEGENDA', '06 GRAFISMOS', '07 BURNS', '08 CAPAS',
        '09 REFERÊNCIA']
VID = ('.mp4', '.mov', '.mxf', '.mkv', '.m4v')
AUD = ('.wav', '.mp3', '.aif', '.aiff', '.m4a')
IMG = ('.png', '.jpg', '.jpeg', '.tif', '.tiff')


def resolve():
    r = dvr.scriptapp("Resolve"); assert r, 'DaVinci Resolve não respondeu (abra o Resolve)'
    return r, r.GetProjectManager()


def abre(pasta, nome, fps='30'):
    """Abre (ou cria) `nome` dentro de `pasta` ("BeGrow/Cliente"). Salva o projeto atual antes. Devolve o projeto."""
    r, pm = resolve()
    cur = pm.GetCurrentProject()
    # Projeto sem nome ("Untitled Project"): SaveProject abre o diálogo "Save Current Project" e trava o Resolve
    # do editor (EP 07, 20/10/2026). Só salva projeto com nome.
    if cur and not cur.GetName().startswith('Untitled Project'): pm.SaveProject()
    pm.GotoRootFolder()
    for f in [x for x in pasta.split('/') if x]:
        if f not in (pm.GetFolderListInCurrentFolder() or []): pm.CreateFolder(f)
        assert pm.OpenFolder(f), f'não abriu a pasta {f}'
    novo = nome not in (pm.GetProjectListInCurrentFolder() or [])
    p = pm.CreateProject(nome) if novo else pm.LoadProject(nome)
    assert p, f'projeto {nome} não abriu'
    if novo: p.SetSetting('timelineFrameRate', fps); p.SetSetting('timelinePlaybackFrameRate', fps)
    mp = p.GetMediaPool()
    for b in BINS: bin_(mp, b)
    mp.SetCurrentFolder(mp.GetRootFolder())
    return p


def bin_(mp, caminho):
    """Bin pelo caminho "00 TIMELINES/Cortes 9x16" (cria o que faltar)."""
    f = mp.GetRootFolder()
    for parte in [x for x in caminho.split('/') if x]:
        sub = {s.GetName(): s for s in (f.GetSubFolderList() or [])}
        f = sub.get(parte) or mp.AddSubFolder(f, parte)
    return f


def importa(mp, arquivos, caminho_bin):
    """Importa no bin certo; reaproveita o que já está lá pelo caminho do arquivo."""
    b = bin_(mp, caminho_bin)
    ja = {c.GetClipProperty('File Path'): c for c in (b.GetClipList() or [])}
    falta = [str(a) for a in arquivos if str(a) not in ja]
    if falta:
        mp.SetCurrentFolder(b); mp.ImportMedia(falta)
    return {c.GetClipProperty('File Path'): c for c in (b.GetClipList() or [])}


def tipo_bin(clip):
    fp = (clip.GetClipProperty('File Path') or '').lower(); n = os.path.basename(fp)
    if clip.GetClipProperty('Type') == 'Timeline': return '00 TIMELINES'
    if '/01_sources/' in fp or 'bruto' in n: return '01 BRUTO'
    if n.endswith(AUD):
        return '02 VOZ' if 'voz' in n else '03 TRILHA' if ('trilha' in n or '/music' in fp or '/musica' in fp) else '04 SFX'
    if 'legenda' in fp or 'caption' in n or n.startswith('caps'): return '05 LEGENDA'
    if 'burn' in n: return '07 BURNS'
    if 'capa' in n or 'cover' in n: return '08 CAPAS'
    if '/05_qa/' in fp or 'previa' in n or 'prévia' in n or 'ref' in n: return '09 REFERÊNCIA'
    if n.endswith(IMG) or 'painel' in fp or 'titulo' in n or 'lower' in n: return '06 GRAFISMOS'
    return '01 BRUTO' if n.endswith(VID) else '06 GRAFISMOS'


def organiza(p, formato_timeline=None):
    """Tira tudo da Master: cada clipe vai para o bin do tipo; timelines para 00 TIMELINES[/formato]."""
    mp = p.GetMediaPool(); raiz = mp.GetRootFolder(); movidos = 0
    for c in list(raiz.GetClipList() or []):
        destino = tipo_bin(c)
        if destino == '00 TIMELINES' and formato_timeline: destino += '/' + formato_timeline
        if mp.MoveClips([c], bin_(mp, destino)): movidos += 1
    return movidos


def arvore(p):
    mp = p.GetMediaPool(); out = []
    def anda(f, nivel):
        cl = f.GetClipList() or []
        out.append('  ' * nivel + f'{f.GetName()}/  ({len(cl)} itens)')
        for c in cl: out.append('  ' * (nivel + 1) + '- ' + c.GetName())
        for s in f.GetSubFolderList() or []: anda(s, nivel + 1)
    anda(mp.GetRootFolder(), 0)
    return '\n'.join(out)


if __name__ == '__main__':
    acao = sys.argv[1] if len(sys.argv) > 1 else 'arvore'
    if acao == 'abre':
        p = abre(sys.argv[2], sys.argv[3])
    else:
        p = resolve()[1].GetCurrentProject()
    if acao == 'organiza': print('movidos:', organiza(p))
    print(p.GetName()); print(arvore(p))
