import json,re,sys
W=sys.argv[1]
ws=[w for w in json.load(open(f'{W}/edit_mfa.json'))['segments'][0]['words'] if w['word'].strip()!='%']
N=lambda s: re.sub(r'[^0-9a-zà-ÿ]','',s.lower())
lines=[l.rstrip('\n') for l in open(f'{W}/blocos_manual.txt') if l.strip()]
out=[];i=0
for L in lines:
    toks=L.split(' '); target=len(N(L.replace('*',''))); acc=0; grp=[]
    while i<len(ws) and acc<target:
        grp.append(ws[i]); acc+=len(N(ws[i]['word'])); i+=1
    # palavras do bloco (texto da legenda) com tempo distribuido pelas palavras do audio
    hl=[]; plain=[]
    for t in toks:
        h=t.startswith('*') or t.endswith('*') or (hl and hl[-1] and t.endswith('*'))
        plain.append(t)
    # marca destaque: trechos entre * *
    words=[];inside=False
    for t in toks:
        # destaque pode fechar antes da pontuação: "*pai*." / "*cuidar*?"
        st=t.startswith('*'); en=bool(re.search(r'\*[.,;:!?…]*$',t))
        if st: inside=True
        words.append({'t':t.replace('*',''),'hl':inside})
        if en: inside=False
    # tempo de cada palavra da legenda: casa por ordem com as palavras do audio do grupo
    gi=0
    for w in words:
        if gi<len(grp):
            w['s']=round(grp[gi]['start'],3); w['e']=round(grp[gi]['end'],3)
            # "22%" pode ser 2 tokens no audio
            if N(w['t'])!=N(grp[gi]['word']) and gi+1<len(grp) and N(w['t'])==N(grp[gi]['word']+grp[gi+1]['word']):
                w['e']=round(grp[gi+1]['end'],3); gi+=1
            gi+=1
        else:
            w['s']=w['e']=round(grp[-1]['end'],3)
    out.append({'s':round(grp[0]['start'],3),'e':round(grp[-1]['end'],3),'words':words,'audio':' '.join(g['word'].strip() for g in grp)})
for k in range(len(out)-1):
    nx=out[k+1]['s']
    if out[k]['e']>nx: out[k]['e']=nx
    for w in out[k]['words']:
        w['e']=min(w['e'],nx); w['s']=min(w['s'],w['e'])
for k,b in enumerate(out):
    flag='' if N(' '.join(w['t'] for w in b['words']))==N(b['audio']) else '   <-- difere: '+b['audio']
    print(k,f"{b['s']:.2f}-{b['e']:.2f}",' '.join(('*' if w['hl'] else '')+w['t'] for w in b['words']),flag)
print('sobrou',len(ws)-i,'palavras')
json.dump(out,open(f'{W}/blocos.json','w'),ensure_ascii=False,indent=1)
