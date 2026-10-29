# corrige as emendas que o audita_emendas reprova: fim engolido → saída vai até a voz acabar (+0,05 s);
# fala apertada → respiro de ~0,35 s (estica a saída no silêncio do bruto, senão antecipa a entrada).
# Grava segs.json (rNN e rNNh), soma MARCOS no props.py (tempo ORIGINAL) e desloca camera_moves no reel.json
# uso: corrige_emendas.py r02 r03 …
import json, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audita_emendas import carrega, voz, silencio, pontuacao
from comum import desloca
for R in sys.argv[1:]:
    src = json.load(open(f'{R}/reel.json'))['src'].split('/')[-1].replace('.MP4', '')
    x, sr = carrega(R); S = json.load(open(f'{R}/segs.json')); WS = pontuacao(src); t = 0; novos = []
    for i in range(len(S) - 1):
        a, b = S[i]; c = S[i + 1][0]; te = t + b - a; d0 = 0.0
        if voz(x, sr, b, b + 0.08):
            nb = b
            while nb < b + 0.6 and voz(x, sr, nb, nb + 0.06): nb += 0.01
            nb = min(nb + 0.05, c - 0.01); d0 += nb - b; b = nb
        if voz(x, sr, c - 0.08, c):
            nc = c
            while nc > c - 0.4 and voz(x, sr, nc - 0.06, nc): nc -= 0.01
            nc = max(nc - 0.04, b + 0.01); d0 += c - nc; c = nc
        ult = [w for w in WS if a <= w['start'] <= b]
        resp = silencio(x, sr, b, -1) + silencio(x, sr, c, +1)
        if ult and ult[-1]['word'].strip()[-1:] in '.?!' and resp < 0.3:
            falta = 0.35 - resp; mais = min(falta, max(0, silencio(x, sr, b, +1) - 0.03)); b += mais; d0 += mais; falta -= mais
            if falta > 0: menos = min(falta, max(0, silencio(x, sr, c, -1) - 0.03)); c -= menos; d0 += menos
        if d0 > 0.005: novos.append((round(te, 3), round(d0, 3)))
        S[i][1] = round(b, 3); S[i + 1][0] = round(c, 3); t += S[i][1] - a - d0
    if not novos: print(R, 'nada a corrigir'); continue
    pp = open(f'{R}/props.py').read(); m = re.search(r'^MARCOS = (\[.*\])$', pp, re.M); ant = eval(m.group(1)) if m else []
    orig = [(round(tc - sum(d for t0, d in ant if t0 < tc), 3), d) for tc, d in novos]   # tempo atual → tempo original
    tot = ant + orig; soma = round(sum(d for _, d in orig), 3)
    for D in (R, R + 'h'):
        if not os.path.isdir(D): continue
        json.dump(S, open(f'{D}/segs.json', 'w'))
        s = open(f'{D}/props.py').read()
        if 'MARCOS = ' in s: s = re.sub(r'^MARCOS = \[.*\]$', f'MARCOS = {tot}', s, flags=re.M)
        else:
            s = s.replace("import json, sys, os\n", f"import json, sys, os\nMARCOS = {tot}\n", 1)
            s = re.sub(r'^(from comum import [^\n]*)$', r'\1, desloca', s, count=1, flags=re.M)
            s = re.sub(r"^props\['burns'\] = burns\(W, \[([^\]]*)\]\)$",
                       r"props = {**desloca({k: v for k, v in props.items() if k != 'captions'}, MARCOS), 'captions': props['captions']}  # emendas refeitas 27/10\nprops['burns'] = burns(W, [x + sum(d for t0, d in MARCOS if x > t0) for x in [\1]])", s, count=1, flags=re.M)
        s = re.sub(r'"duration": round\(([^,]*?) \+ 0\.6, 3\)', lambda m: f'"duration": round({m.group(1)} + {soma} + 0.6, 3)', s, count=1)
        assert 'desloca({k' in s, D
        open(f'{D}/props.py', 'w').write(s)
        r = json.load(open(f'{D}/reel.json')); r['camera_moves'] = desloca(r['camera_moves'], orig); json.dump(r, open(f'{D}/reel.json', 'w'), ensure_ascii=False, indent=1)
    print(R, 'emendas corrigidas', novos, '+', soma, 's')
