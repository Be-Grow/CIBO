#!/usr/bin/env python3
"""Recalcula os tempos de um reel quando os trechos mudam (gaguejada cortada, take trocado) — sem reescrever à mão.

uso: retempo.py segs_antigo.json segs_novo.json ARQ [ARQ…]
  ARQ: rNN/props.py, rNN/sfx.json, rNN/reel.json (camera_moves)
Cada tempo editado antigo vira tempo na fonte (pelos trechos antigos) e volta para tempo editado novo
(pelos trechos novos). Tempo que caía num pedaço removido vai para a emenda. Só mexe em números com ponto decimal
entre 0 e a duração antiga (preços, posições x/y e contagens inteiras ficam). Guarda cópia ARQ.antes_retempo.
"""
import json, re, shutil, sys

old = json.load(open(sys.argv[1])); new = json.load(open(sys.argv[2]))
def starts(S):
    st = [0.0]
    for a, b in S:
        st.append(st[-1] + b - a)
    return st
so, sn = starts(old), starts(new)
DUR = so[-1]


def remap(t):
    if t <= 0 or t > DUR + 1.0:
        return t
    if t >= DUR:                       # cauda depois da última fala
        return round(sn[-1] + t - DUR, 2)
    k = next(i for i in range(len(old)) if so[i] <= t < so[i + 1])
    src = old[k][0] + t - so[k]
    for j, (a, b) in enumerate(new):
        if a - 1e-6 <= src <= b + 1e-6:
            return round(sn[j] + src - a, 2)
    # caiu num pedaço removido: vai para a emenda mais próxima
    best = min(range(len(new)), key=lambda j: min(abs(src - new[j][0]), abs(src - new[j][1])))
    a, b = new[best]
    return round(sn[best] if abs(src - a) < abs(src - b) else sn[best + 1], 2)


num = re.compile(r'(?<![\w.])(\d{1,3}\.\d{1,3})(?![\w.])')
for f in sys.argv[3:]:
    shutil.copy2(f, f + '.antes_retempo')
    txt = open(f).read()
    if f.endswith('reel.json'):
        c = json.loads(txt)
        for m in c.get('camera_moves', []):
            for key in ('t', 'until'):
                if key in m:
                    m[key] = remap(m[key])
        json.dump(c, open(f, 'w'), ensure_ascii=False, indent=1)
    else:
        n = 0
        def sub(m):
            global n
            v = float(m.group(1))
            if v < 0.3 or v > DUR + 1.0:
                return m.group(1)
            n += 1
            return f'{remap(v):.2f}'.rstrip('0').rstrip('.') if '.' in f'{remap(v):.2f}' else f'{remap(v)}'
        open(f, 'w').write(num.sub(sub, txt))
        print(f'{f}: {n} tempos recalculados')
print(f'duração {DUR:.2f} → {sn[-1]:.2f}')
