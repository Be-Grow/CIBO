#!/usr/bin/env python3
"""Status de todos os reels de um projeto num comando só (antes: 2-4 comandos ps/tail/ls por "como tá?", 55 na sessão
da Priscilla). Mostra, por reel: última etapa concluída (pelos arquivos), o que está rodando, a entrega e a prévia;
e avisa órfão do motor (esbuild/Chrome com pai 1) e SSD fora.
uso: status.py PROJ"""
import os, subprocess, sys, time
from pathlib import Path

P = Path(sys.argv[1]); WK = P / '04_work'
if not WK.exists():
    sys.exit(f'projeto não encontrado ({P}): SSD desconectado?')
ps = [l for l in subprocess.run(['ps', '-eo', 'pid=,ppid=,etime=,stat=,command='], capture_output=True, text=True).stdout.splitlines()
      if '/bin/zsh -c' not in l and 'uv run' not in l]   # sem os embrulhos do shell (contavam em dobro)
hm = lambda f: time.strftime('%H:%M', time.localtime(f.stat().st_mtime)) if f.exists() else '—'
for r in sorted(d.name for d in WK.iterdir() if d.is_dir() and (d / 'reel.json').exists()):
    W = WK / r
    etapas = [(n, f) for n, f in (('voz', W / 'edit_mfa.json'), ('legenda', W / 'blocos.json'), ('props', WK / 'public' / r / 'props.json'),
                                  ('camera', WK / 'public' / r / 'camera.mov'), ('mix', W / 'mix.wav'), ('final', W / 'video2.mp4')) if f.exists()]
    ult = max(etapas, key=lambda e: e[1].stat().st_mtime) if etapas else None
    rod = [l.split(None, 4) for l in ps if f'{P.name}' in l and f' {r} ' in l and 'reel.py' in l]
    rod = ', '.join(f"{x[4].split(f' {r} ')[1].split()[0]} há {x[2]}{' (pausado)' if x[3].startswith('T') else ''}" for x in rod) or '—'
    nome = next(iter(__import__('json').load(open(W / 'reel.json')).get('name', r).split(' - ', 1)[1:]), r)
    ent = next(P.glob(f'06_deliverables/{r[1:]} -*.mp4'), None)
    prev = next(P.glob(f'05_qa/previas/{r[1:]} -*.mp4'), None)
    print(f"{r} {nome[:34]:34} | última etapa: {ult[0] + ' ' + hm(ult[1]) if ult else '—':15} | rodando: {rod:22} | "
          f"prévia {hm(prev) if prev else '—'} | entrega {hm(ent) if ent else '—'}")
orf = [l for l in ps if l.split(None, 2)[1:2] == ['1'] and 'reel-motion/node_modules' in l]
if orf:
    print(f'ATENÇÃO: {len(orf)} órfão(s) do motor comendo CPU (o próximo render encerra; ou: kill -9 {" ".join(l.split()[0] for l in orf)})')
pes = [('(pausado) ' if l.split(None, 4)[3].startswith('T') else '') + l.split(None, 4)[4][-60:] for l in ps if any(k in l for k in ('camera.py', 'remotion render', 'wt.py', 'face_track'))]
print(f'trabalhos pesados agora: {len(pes)}' + (' → ' + ' | '.join(pes) if pes else ''))
