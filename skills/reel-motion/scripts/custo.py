#!/usr/bin/env python3
"""Custo de produção por reel, medido no registro da sessão do Claude Code: turnos, imagens lidas, comandos, erros,
tokens de saída e leitura de cache, entre o primeiro e o último comando que cita o reel. Serve para a revisão de
eficiência pedida pelo editor a cada reel finalizado (14/10/2026).
uso: custo.py SESSAO.jsonl rNN [rNN…]      (marcadores: o nome da pasta do reel, ex. r06, e pastas de fonte opcionais com --fonte x12)"""
import json, re, sys
from datetime import datetime

f = sys.argv[1]; alvos = [a for a in sys.argv[2:] if not a.startswith('--')]
fontes = sys.argv[sys.argv.index('--fonte') + 1].split(',') if '--fonte' in sys.argv else []
ev = []
for l in open(f):
    try:
        m = json.loads(l)
    except ValueError:
        continue
    if m.get('type') != 'assistant':
        continue
    msg = m.get('message', {}); u = msg.get('usage', {}) or {}
    tools = [c for c in msg.get('content', []) if isinstance(c, dict) and c.get('type') == 'tool_use'] if isinstance(msg.get('content'), list) else []
    ev.append((m.get('timestamp'), u, tools))
for r in alvos:
    pad = re.compile(r'(\b|/)(' + '|'.join([re.escape(r)] + [re.escape(x) for x in fontes]) + r')\b')
    idx = [i for i, (_, _, t) in enumerate(ev) if any(pad.search(json.dumps(c.get('input', {}), ensure_ascii=False)) for c in t)]
    if not idx:
        print(r, 'sem registros'); continue
    a, b = idx[0], idx[-1]
    turn = b - a + 1
    imgs = sum(1 for _, _, t in ev[a:b + 1] for c in t if c['name'] == 'Read' and re.search(r'\.(jpg|png)$', c['input'].get('file_path', '')))
    cmds = sum(1 for _, _, t in ev[a:b + 1] for c in t if c['name'] == 'Bash')
    out = sum((u.get('output_tokens') or 0) for _, u, _ in ev[a:b + 1]); cr = sum((u.get('cache_read_input_tokens') or 0) for _, u, _ in ev[a:b + 1])
    t0 = datetime.fromisoformat(ev[a][0].replace('Z', '+00:00')); t1 = datetime.fromisoformat(ev[b][0].replace('Z', '+00:00'))
    print(f'{r}: {turn} turnos, {cmds} comandos, {imgs} imagens, {out/1000:.0f} mil tokens de saída, {cr/1e6:.1f} M de leitura de cache, '
          f'{(t1 - t0).total_seconds()/60:.0f} min de relógio (inclui espera e outros reels em paralelo)')
