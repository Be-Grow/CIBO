#!/usr/bin/env python3
"""Fila do fluxo DaVinci do CIBO para um lote (nasceu do fila_davinci.sh + vigia_resolve.sh do projeto da Andreia, 19/10/2026):
para cada reel, um por vez: capa → pacote (`reel.py … davinci`) → importação no projeto do job no Resolve (`resolve_render.py`
com SEM_RENDER=1) → movimentos no Fusion (`resolve_fx.py`, se o pacote tem movimentos.json; já aplica as cores) ou só as cores
(`resolve_cores.py`) → bins organizados (`resolve_projeto.py organiza`) → `qa_resolve.py` na timeline.
Sem render final: ele é do editor no Resolve (regra do CIBO). Depois que ele renderizar: `qa_render.py PROJ`.
Para antes de um reel se o SSD tiver < 8 GB livres (o SSD lotou na Andreia) e apaga as camadas inteiras que o pacote já
fatiou (legenda, fundo do painel: GB que o Resolve não usa).
uso: fila_davinci.py PROJ "Nome do projeto no Resolve" "BeGrow/<Cliente>" r01 r01h r02 …"""
if __name__ == '__main__':   # saída curta + log completo em 05_qa/logs (client-router/scripts/saida_curta.py)
    import os as _o, sys as _s; _s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.realpath(__file__)), '../../client-router/scripts')); import saida_curta; saida_curta.curta()
import json, os, shutil, subprocess, sys, time
from pathlib import Path

a = sys.argv[1:]
P, NOME, PASTA, REELS = Path(a[0]).resolve(), a[1], a[2], a[3:]
S = Path(__file__).resolve().parent; PY = sys.executable
os.environ['TMPDIR'] = str(P / '04_work' / 'tmp'); (P / '04_work' / 'tmp').mkdir(parents=True, exist_ok=True)
os.environ.setdefault('RESOLVE_SCRIPT_API', '/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting')
os.environ.setdefault('RESOLVE_SCRIPT_LIB', '/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so')
LOG = open(P / '05_qa' / 'fila_davinci.log', 'a')


def diz(m):
    print(m, flush=True); LOG.write(m + '\n'); LOG.flush()


def roda(cmd, limite, env=None):
    """API do Resolve sempre com limite de tempo (travou o DaVinci do editor sem ele)"""
    r = subprocess.run(['perl', '-e', f'alarm {limite}; exec @ARGV', *map(str, cmd)], capture_output=True, text=True, env=env)
    return r.returncode, (r.stdout + r.stderr).strip().splitlines()


res = []
for R in REELS:
    livre = shutil.disk_usage('/Volumes/SSD').free / 1e9
    if livre < 8:
        diz(f'PAREI antes de {R}: só {livre:.0f} GB livres no SSD'); break
    t0 = time.time(); nome = json.load(open(P / '04_work' / R / 'reel.json'))['name']; pac = P / '07_davinci' / nome
    diz(f'== {R} {time.strftime("%H:%M")} ({livre:.0f} GB livres)')
    if not json.load(open(P / '04_work' / R / 'reel.json')).get('grosso'):   # aula no grosso: sem capa (Remotion)
        roda([PY, S / 'reel.py', P, R, 'so_capa'], 900)
    c, out = roda([PY, S / 'reel.py', P, R, 'davinci'], 7200)
    diz('   ' + next((l for l in reversed(out) if 'pacote DaVinci' in l or 'rror' in l), f'saída {c}')[:160])
    if c:
        res.append(f'ERRO {R} pacote'); continue
    for f in ('legenda', 'painel_fundo'):
        for x in (pac / '_camadas').glob(f'{f}__*.mov'):
            x.unlink()
    c, out = roda([PY, S / 'resolve_render.py', NOME, PASTA, P / '06_deliverables', pac], 1800, {**os.environ, 'SEM_RENDER': '1'})
    diz('   resolve: ' + ' | '.join(out[-2:])[:200])
    if not c:
        fx = (pac / 'movimentos.json').exists()
        c, out = roda([PY, S / ('resolve_fx.py' if fx else 'resolve_cores.py'), *([pac] if fx else [])], 1800)
        diz(f"   {'fusion' if fx else 'cores'}: " + (out[-1] if out else f'saída {c}')[:160])
        roda([PY, S / 'resolve_projeto.py', 'organiza'], 300)
    c2, out2 = roda([PY, S / 'qa_resolve.py', nome], 300)
    diz('   qa_resolve: ' + ' | '.join(out2)[:300])
    res.append(f"{'ok ' if not (c or c2) else 'ERRO'} {R} {(time.time() - t0) / 60:.0f} min, {sum(f.stat().st_size for f in pac.rglob('*') if f.is_file()) / 1e9:.1f} GB")
diz('\n'.join(['== resumo'] + res))
