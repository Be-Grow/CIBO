#!/usr/bin/env python3
"""Checa as props do reel antes do render (regras do piloto da Priscilla).
uso: checa_props.py props.json edit_mfa.json sfx.json
- toda troca de painel dentro da tela dividida tem burn (tr=burn + burn no instante) e SFX
- animação de dado termina antes da troca (barra, carimbo, risco, logo)
- painel de cima sem vazio > 2,5 s sem nada entrando (painéis de vídeo contam como movimento)
- entrada/saída da tela dividida não corta palavra; SFX em toda troca de layout
"""
import json,sys,re
P=json.load(open(sys.argv[1])); W=[w for w in json.load(open(sys.argv[2]))['segments'][0]['words'] if w['word'].strip()!='%']
S=json.load(open(sys.argv[3])) if len(sys.argv)>3 else []
err=[]
near=lambda t,L,tol=0.08: any(abs(t-x)<tol for x in L)
burns=[b['t'] for b in P.get('burns',[])]; sfx=[e['t'] for e in S]
pan=P['panels']
def times(o):
    if isinstance(o,dict):
        for k,v in o.items():
            if isinstance(v,(int,float)) and (k.endswith('At') or k=='at'): yield v
            else: yield from times(v)
    elif isinstance(o,list):
        for v in o: yield from times(v)
for a,b in zip(pan,pan[1:]):
    if abs(a['e']-b['s'])<0.05:
        if b.get('tr')!='burn' or not near(b['s'],burns): err.append(f"{b['s']:.2f} troca {a['type']}→{b['type']} sem burn")
        if not near(b['s'],sfx,0.15): err.append(f"{b['s']:.2f} troca sem SFX")
for p in pan:
    end=[]
    for x in p.get('bars',[]): end.append(('barra',x['dropAt']+x.get('dropDur',0.9)))
    if p.get('stampAt'): end.append(('carimbo',p['stampAt']+0.22))
    if p.get('strike'): end.append(('risco',p['strike']['strikeAt']+0.35))
    if p.get('logo',{}).get('outAt'): end.append(('logo',p['logo']['outAt']+0.45))
    if p.get('pushAt'): end.append(('destaque',p['pushAt']+0.5))
    for k,t in end:
        if t>p['e']-0.15: err.append(f"{p['e']:.2f} {k} termina em {t:.2f}, depois da troca")
    if p['type'] not in ('media','stat'):
        ev=sorted([p['s']]+[t for t in times(p) if p['s']<=t<=p['e']]+[t for t in burns if p['s']<=t<=p['e']])
        for x,y in zip(ev,ev[1:]+[p['e']]):
            if y-x>2.5:
                # sugere as palavras de conteúdo ditas no vazio (onde encaixar a etiqueta), para não reler a transcrição
                sug=[f"{w['word'].strip(' ,.?!')}@{w['start']:.2f}" for w in W if x+0.6<w['start']<y-0.6 and len(w['word'].strip(' ,.?!'))>=5][:5]
                err.append(f"{x:.2f}-{y:.2f} painel {p['type']} parado {y-x:.1f}s  → palavras: {' '.join(sug)}")
# etiquetas: passar da borda direita (largura estimada) ou ficar baixa demais no painel invertido (interface do Instagram cobre)
for p in pan:
    inv = any(g.get('inv') and g['s'] <= p['s'] < g['e'] for g in P['split'])
    for g in p.get('tags', []):
        sz = g.get('size', 28); larg = len(str(g['text'])) * sz * 0.68 + sz * 1.8 + 22
        x = g.get('x'); y = g.get('y', 0)
        if x is not None and x + larg > 1050:
            err.append(f"{g['at']:.2f} etiqueta '{g['text']}' passa da borda direita (x {x} + ~{larg:.0f} px): use x ≤ {int(1040 - larg)}")
        if not inv and y > 770:   # painel normal: legenda centrada em y≈862 (splitH−78); pílula de ~52 px abaixo de 770 encosta nela (09, 10)
            err.append(f"{g['at']:.2f} etiqueta '{g['text']}' em y {y}: fica sobre a legenda (use ≤ 770)")
        if inv and y > 690:
            err.append(f"{g['at']:.2f} etiqueta '{g['text']}' em y {y} no painel invertido: fica sob a interface do Instagram (use ≤ 690)")
# etiquetas sobrepostas entre si (mesma faixa de y, faixas de x se cruzam, as duas visíveis juntas até o fim do painel): 08, "MERCADO LIVRE · SHOPEE" × "LANÇAR UMA MARCA"
for p in pan:
    tg = [g for g in p.get('tags', []) if 'y' in g]
    def faixa(g):
        sz = g.get('size', 28); larg = len(str(g['text'])) * sz * 0.68 + sz * 1.8 + 22
        x = g['x'] if g.get('x') is not None else (1080 - larg) / 2
        return x, x + larg
    for i1 in range(len(tg)):
        for i2 in range(i1 + 1, len(tg)):
            a1, a2 = tg[i1], tg[i2]
            if abs(a1['y'] - a2['y']) < 44:
                (x1, x2), (y1, y2) = faixa(a1), faixa(a2)
                if x1 < y2 - 8 and y1 < x2 - 8:
                    err.append(f"{max(a1['at'], a2['at']):.2f} etiquetas '{a1['text']}' e '{a2['text']}' se sobrepõem (y {a1['y']}/{a2['y']}, x {x1:.0f}-{x2:.0f} × {y1:.0f}-{y2:.0f})")
# etiqueta tem que vir da fala: palavras de conteúdo da etiqueta ditas até 8 s antes/depois (05: "mandioca, milho, tofu" de outro take)
import unicodedata
nz = lambda t: ''.join(ch for ch in unicodedata.normalize('NFD', t.lower()) if unicodedata.category(ch) != 'Mn')
for p in pan:
    for g in p.get('tags', []):
        ws = [w for w in re.findall(r'[a-zà-ÿ]{4,}', nz(str(g['text'])))]
        perto = ' '.join(nz(w['word']) for w in W if abs(w['start'] - g['at']) < 8)
        faltam = [w for w in ws if w[:5] not in perto]
        if ws and len(faltam) == len(ws):
            err.append(f"{g['at']:.2f} etiqueta '{g['text']}': ela não diz isso por perto (confira se não veio de outro take)")
for g in P['split']:
    for t in (g['s'],g['e']):
        w=[x['word'].strip() for x in W if x['start']+0.05<t<x['end']-0.05]
        if w: err.append(f"{t:.2f} troca de layout no meio de '{w[0]}'")
        if not near(t,sfx,0.15): err.append(f"{t:.2f} troca de layout sem SFX")
print('\n'.join(err) if err else 'OK: nenhuma pendência'); sys.exit(1 if err else 0)
