# organiza o Media Pool do projeto aberto: 00 TIMELINES/{9x16,16x9} · 01 BRUTO · 02 MÍDIA POR VÍDEO/<vídeo>/<tipo>;
# clipe repetido (mesmo arquivo) sem uso em timeline sai do pool (o arquivo no disco fica). uso: organiza_pool.py [--aplica]
import sys, re, DaVinciResolveScript as d
AP = '--aplica' in sys.argv
p = d.scriptapp('Resolve').GetProjectManager().GetCurrentProject(); mp = p.GetMediaPool(); root = mp.GetRootFolder()
def todos(f):
    out = [(c, f) for c in (f.GetClipList() or [])]
    for s in f.GetSubFolderList() or []: out += todos(s)
    return out
def pasta(pai, nome):
    for s in pai.GetSubFolderList() or []:
        if s.GetName() == nome: return s
    return mp.AddSubFolder(pai, nome) if AP else None
def tipo(caminho):
    n = caminho.rsplit('/', 1)[-1].lower()
    if n.startswith('voz__'): return '1 VOZ'
    if n.startswith('trilha__'): return '2 TRILHA'
    if '/sfx/' in caminho: return '3 SFX'
    if '/legenda/' in caminho: return '4 LEGENDA'
    if '/burns/' in caminho: return '6 BURNS'
    if n.startswith('capa'): return '7 CAPA'
    return '5 GRAFISMOS'
itens = todos(root); por_arq = {}
for c, f in itens:
    if c.GetClipProperty('Type') == 'Timeline': continue
    por_arq.setdefault(c.GetClipProperty('File Path') or c.GetName(), []).append(c)
sobra = []
for arq, cs in por_arq.items():
    if len(cs) > 1:
        cs.sort(key=lambda c: -int(c.GetClipProperty('Usage') or 0))
        sobra += [c for c in cs[1:] if int(c.GetClipProperty('Usage') or 0) == 0]
destino = {}   # (caminho de pastas) → clipes
for c, f in itens:
    if c in sobra: continue
    if c.GetClipProperty('Type') == 'Timeline':
        destino.setdefault(('00 TIMELINES', '16x9' if '(16x9)' in c.GetName() else '9x16'), []).append(c); continue
    arq = c.GetClipProperty('File Path') or ''
    if '/01_sources/' in arq: destino.setdefault(('01 BRUTO',), []).append(c); continue
    m = re.search(r'/07_davinci/([^/]+)/', arq)
    pac = m.group(1) if m else 'OUTROS'; base = re.sub(r' v7(\.1)?$', '', re.sub(r' \(16x9\)$', '', pac))
    fmt = ('16x9' if '(16x9)' in pac else '9x16') + (' v7.1' if 'v7.1' in pac else ' v7 (antiga)' if pac.endswith('v7 (16x9)') else '')
    destino.setdefault(('02 MÍDIA POR VÍDEO', base, fmt, tipo(arq)), []).append(c)
print('timelines:', sum(len(v) for k, v in destino.items() if k[0] == '00 TIMELINES'), '| repetidos sem uso p/ tirar:', len(sobra),
      '| vídeos:', len({k[1] for k in destino if k[0] == '02 MÍDIA POR VÍDEO'}), '| clipes que ficam:', sum(len(v) for v in destino.values()))
if not AP: [print('  ', '/'.join(k), len(v)) for k, v in sorted(destino.items()) if k[0] != '02 MÍDIA POR VÍDEO' or k[3] == '1 VOZ']; sys.exit()
if sobra: print('tirados do pool:', mp.DeleteClips(sobra))
for k, cs in destino.items():
    f = root
    for n in k: f = pasta(f, n)
    mp.MoveClips(cs, f)
vazias = [s for s in root.GetSubFolderList() if s.GetName() not in ('00 TIMELINES', '01 BRUTO', '02 MÍDIA POR VÍDEO') and not todos(s)]
if vazias: print('pastas vazias apagadas:', [s.GetName() for s in vazias], mp.DeleteFolders(vazias))
print('ok')
