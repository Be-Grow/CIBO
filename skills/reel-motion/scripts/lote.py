#!/usr/bin/env python3
"""Fila de etapas em vários reels, uma de cada vez (substitui laços de espera à mão — um `while pgrep -f` esperou a si mesmo
por 4 h, 14/10/2026). Segue para a próxima mesmo se uma falhar e resume no fim.
uso: lote.py PROJ "r06 trecho 43 47.2" "r08 trecho 20.3 24.9" "r10 final" …"""
import os, subprocess, sys, time
P = sys.argv[1]; R = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reel.py')
os.environ.setdefault('TMPDIR', os.path.join(os.environ.get('CIBO_TEMP', os.path.join(os.environ.get('TEMP', '/tmp'), 'CIBO'))))
res = []
for job in sys.argv[2:]:
    t = time.time(); r = subprocess.run([sys.executable, R, P] + job.split(), capture_output=True, text=True)
    ok = r.returncode == 0
    linha = next((l for l in reversed(r.stdout.splitlines()) if 'checagem' in l or 'OK' in l), '')
    res.append(f"{'ok ' if ok else 'ERRO'} {job:28} {time.time() - t:5.0f}s {linha[:80]}" + ('' if ok else ' | ' + (r.stderr or r.stdout).strip().splitlines()[-1][:120]))
    print(res[-1], flush=True)
print('\n'.join(['== resumo'] + res))
