#!/usr/bin/env python3
"""Status de todos os reels de um projeto num comando só (antes: 2-4 comandos ps/tail/ls por "como tá?", 55 na sessão
da Priscilla). Mostra, por reel: última etapa concluída (pelos arquivos), o que está rodando, a entrega e a prévia;
e avisa órfão do motor (esbuild/Chrome com pai 1) e SSD fora.
uso: status.py PROJ"""
if __name__ == '__main__':   # saída curta + log completo em 05_qa/logs (client-router/scripts/saida_curta.py)
    import os as _o, sys as _s; _s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.realpath(__file__)), '../../client-router/scripts')); import saida_curta; saida_curta.curta()
import os, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); import selos, json as _j

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
    _c = _j.load(open(W / 'reel.json')); _m = Path(str(_c.get('music') or ''))
    _e = selos.estado(W, {'cortes': [W / 'segs.json'], 'layout': [WK / 'public' / r / 'props.json'], 'audio': [W / 'segs.json', W / 'sfx.json'] + ([_m] if _m.name and _m.exists() and _m.stat().st_size < 3e8 else []),
                          'pacote': [W / 'segs.json', W / 'sfx.json', WK / 'public' / r / 'props.json']})
    sl = ' '.join(f"{n}{'✓' if e.startswith('ok') else '✗' if e == 'velho' else '·'}" for n, e in _e.items())
    print(f"{r} {nome[:34]:34} | última etapa: {ult[0] + ' ' + hm(ult[1]) if ult else '—':15} | rodando: {rod:22} | "
          f"prévia {hm(prev) if prev else '—'} | entrega {hm(ent) if ent else '—'} | selos {sl}")
orf = [l for l in ps if l.split(None, 2)[1:2] == ['1'] and 'reel-motion/node_modules' in l]
if orf:
    print(f'ATENÇÃO: {len(orf)} órfão(s) do motor comendo CPU (o próximo render encerra; ou: kill -9 {" ".join(l.split()[0] for l in orf)})')
pes = [('(pausado) ' if l.split(None, 4)[3].startswith('T') else '') + l.split(None, 4)[4][-60:] for l in ps if any(k in l for k in ('camera.py', 'remotion render', 'wt.py', 'face_track'))]
print('selos: ✓ vale para os arquivos de agora · ✗ arquivo mudou depois do selo · · nunca passou (cortes → verifica → mix → davinci)')
print(f'trabalhos pesados agora: {len(pes)}' + (' → ' + ' | '.join(pes) if pes else ''))
