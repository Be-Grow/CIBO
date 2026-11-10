#!/usr/bin/env python3
"""Esquema dos painéis tirado do próprio código (mg/src/reel/panels.tsx), sem tabela à mão para desatualizar (10/11/2026).
Para cada tipo do registro PANELS: campos que o componente lê (p.campo) e quais são OBRIGATÓRIOS — tempo usado direto em
ramp(t, p.campo…) sem valor padrão (`??`) nem teste de existência. Um tempo desses faltando dá NaN e o painel nem renderiza
(strike sem line2At, YT 01 da Priscilla).
uso: esquema.py            → lista os tipos e campos        esquema.py props.json → valida (saída 1 se faltar obrigatório)"""
import json, re, sys
from pathlib import Path

TSX = Path(__file__).resolve().parent.parent / 'mg/src/reel/panels.tsx'
COMUNS = {'type', 's', 'e', 'tr', 'tags', 'step', 'hideCapsFrom', 'inv'}


def esquema():
    src = TSX.read_text()
    reg = dict(re.findall(r'(\w+): (Panel\w+)', src[src.index('PANELS'):]))            # tipo → componente
    corpos = {m.group(1): m for m in re.finditer(r'^const (Panel\w+)\b', src, re.M)}
    ini = sorted(m.start() for m in re.finditer(r'^(const|export|function|type|interface) ', src, re.M))
    out = {}
    for tipo, comp in reg.items():
        if comp not in corpos:
            continue
        a = corpos[comp].start(); b = next((x for x in ini if x > a), len(src)); corpo = src[a:b]
        campos = set(re.findall(r'\bp\.(\w+)', corpo))
        # obrigatório = tempo lido num `const … = ramp(t, p.campo` do topo do componente (roda sempre), sem valor padrão
        topo = '\n'.join(l for l in corpo.splitlines() if re.match(r'  const ', l))
        obr = {c for c in re.findall(r'ramp\(t,\s*p\.(\w+)', topo) if not re.search(rf'\bp\.{c}\s*(\?\?|!==|===|&&|\|\||\?[^.?:])', corpo)}
        tempos = {c for c in campos if c.endswith('At')}
        out[tipo] = {'campos': sorted(campos), 'obrigatorios': sorted(obr - COMUNS), 'tempos': sorted(tempos), 'solto': '...p' in corpo or '(p as any)' in corpo}
    return out


def valida(props):
    E = esquema(); erros, avisos = [], []
    for i, p in enumerate(props.get('panels') or []):
        t = p.get('type')
        if t not in E:
            erros.append(f"painel {i} ({p.get('s', 0):.1f} s): tipo '{t}' não existe (tipos: {', '.join(sorted(E))})"); continue
        for c in E[t]['obrigatorios']:
            if not isinstance(p.get(c), (int, float)):
                erros.append(f"painel {i} ({t}, {p.get('s', 0):.1f} s): falta o tempo `{c}` (sem ele o painel não renderiza)")
        if not E[t]['solto']:
            for c in sorted(set(p) - set(E[t]['campos']) - COMUNS):
                avisos.append(f"painel {i} ({t}): campo `{c}` não é lido por esse painel (erro de digitação? campos: {', '.join(E[t]['campos'])})")
    return erros, avisos


if __name__ == '__main__':
    if len(sys.argv) < 2:
        for t, e in sorted(esquema().items()):
            print(f"{t:10} obrigatórios: {', '.join(e['obrigatorios']) or '—':28} campos: {', '.join(e['campos'])}")
        sys.exit(0)
    er, av = valida(json.load(open(sys.argv[1])))
    for l in er + [f'aviso: {a}' for a in av]:
        print(l)
    sys.exit(1 if er else 0)
