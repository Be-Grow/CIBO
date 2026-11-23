#!/usr/bin/env python3
"""Consulta a documentação do DaVinci Resolve instalada no Mac ANTES de tentar no escuro (regra do editor, 23/11/2026:
"quando a CIBO fica com dúvida sobre como usar o DaVinci, ela deve consultar a docs").

Duas fontes, as duas locais e da mesma versão do Resolve instalado:
  api     README da API de scripting (Resolve, Project, MediaPool, Timeline, TimelineItem…: funções, argumentos, retorno,
          propriedades de clipe, opções de render/importação). Dúvida de script = aqui primeiro.
  manual  Manual do Resolve (PDF, ~4 mil páginas): como uma função da interface funciona (Fusion, Fairlight, Color,
          legendas, render). O texto é extraído uma vez para ~/.cache/cibo/ e reaproveitado.

uso: doc_resolve.py api TERMO [TERMO…]        linhas que citam TODOS os termos, com a classe de cada uma (até 25)
     doc_resolve.py api --classe Timeline     todas as funções de uma classe
     doc_resolve.py manual TERMO [TERMO…]     páginas que citam todos os termos, com um trecho (até 12)
     doc_resolve.py manual --pagina N         o texto de uma página (só depois de achar a página certa)
Saída curta de propósito: busque, ache a linha/página, leia só ela. Se as duas fontes não resolverem, aí sim procure na
web (fórum da Blackmagic) e anote o achado em client-router/references/regras/davinci.md."""
import re, subprocess, sys
from pathlib import Path

API = Path('/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/README.txt')
PDF = Path('/Applications/DaVinci Resolve/DaVinci Resolve Manual.pdf')
CACHE = Path.home() / '.cache' / 'cibo' / 'resolve_manual.txt'
CLASSES = ('Resolve', 'ProjectManager', 'Project', 'MediaStorage', 'MediaPool', 'Folder', 'MediaPoolItem', 'Timeline',
           'TimelineItem', 'Gallery', 'GalleryStillAlbum', 'Graph', 'ColorGroup')


def api(termos, classe=None):
    if not API.exists(): sys.exit(f'README da API não encontrado: {API} (Resolve instalado?)')
    linhas = API.read_text(errors='replace').splitlines()
    atual, saida = 'Geral', []
    for i, l in enumerate(linhas):
        if l.strip() in CLASSES and i + 1 < len(linhas): atual = l.strip()
        elif i + 1 < len(linhas) and set(linhas[i + 1].strip()) == {'-'} and l.strip(): atual = l.strip()
        if classe:
            if atual == classe and l.strip(): saida.append(l.rstrip())
        elif all(t.lower() in l.lower() for t in termos):
            saida.append(f'[{atual}] l.{i + 1}: {l.strip()}')
    if not saida: print('nada na API com ' + ' + '.join(termos or [classe]) + '; tente outro termo ou `manual`'); return
    for l in saida[:25 if not classe else 200]: print(l[:220])
    if len(saida) > 25 and not classe: print(f'… mais {len(saida) - 25}: refine com outro termo')


def texto_manual():
    if not CACHE.exists():
        if not PDF.exists(): sys.exit(f'manual não encontrado: {PDF}')
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        print('extraindo o texto do manual (uma vez só, ~1 min)…', flush=True)
        subprocess.run(['pdftotext', '-layout', str(PDF), str(CACHE)], check=True)
    return CACHE.read_text(errors='replace').split('\f')


def manual(termos, pagina=None):
    pags = texto_manual()
    if pagina:
        t = pags[pagina - 1] if 0 < pagina <= len(pags) else ''
        print('\n'.join(l.rstrip() for l in t.splitlines() if l.strip())[:6000]); return
    achou = [(n, p) for n, p in enumerate(pags, 1) if all(t.lower() in p.lower() for t in termos)]
    if not achou: print('nada no manual com ' + ' + '.join(termos)); return
    for n, p in achou[:12]:
        flat = re.sub(r'\s+', ' ', p); k = flat.lower().find(termos[0].lower())
        print(f'p.{n}: …{flat[max(0, k - 90):k + 150]}…')
    if len(achou) > 12: print(f'… {len(achou)} páginas no total: refine com mais um termo')


a = sys.argv[1:]
if not a or a[0] not in ('api', 'manual'): sys.exit(__doc__)
if a[0] == 'api':
    api([x for x in a[1:] if not x.startswith('--') and x not in a[a.index('--classe') + 1:a.index('--classe') + 2]] if '--classe' in a else a[1:],
        a[a.index('--classe') + 1] if '--classe' in a else None)
else:
    manual(a[1:] if '--pagina' not in a else [], int(a[a.index('--pagina') + 1]) if '--pagina' in a else None)
