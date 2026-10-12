#!/usr/bin/env python3
"""Entry point. Usage:  JOB=job.json python3 make_reels.py [clip ...]"""
import os,sys,json,subprocess
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
JOBF=os.environ['JOB']; JOB=json.load(open(JOBF))
# PROFILE (opt-in): perfil de cliente, `<skill do cliente>/assets/profile.json`. Prioridade:
# env explicito > job.json > perfil > padrao do motor. "env" vira variavel de ambiente;
# "job" vira padrao do job ({SKILL} = pasta da skill do cliente; `fix` e `emph` somam).
_pf=os.environ.get('PROFILE') or JOB.get('profile')
if _pf:
    _sd=os.path.dirname(os.path.dirname(os.path.abspath(_pf)))
    _sub=lambda v: v.replace('{SKILL}',_sd) if isinstance(v,str) else v
    _P=json.load(open(_pf))
    for _k,_v in _P.get('env',{}).items(): os.environ.setdefault(_k,_sub(str(_v)))
    _J=dict(JOB); _pj=_P.get('job',{})
    _J['fix']=list(JOB.get('fix',[]))+[list(x) for x in _pj.get('fix',[])]
    _J['emph']=' '.join(x for x in (JOB.get('emph',''),_pj.get('emph','')) if x)
    for _k,_v in _pj.items():
        if _k not in ('fix','emph'): _J.setdefault(_k,_sub(_v))
    JOB=_J; os.makedirs(JOB.get('work','./work'),exist_ok=True)
    JOBF=os.path.join(JOB.get('work','./work'),'.job_com_perfil.json')
    json.dump(JOB,open(JOBF,'w'),ensure_ascii=False,indent=1); os.environ['JOB']=JOBF   # plan.py le daqui
if os.environ.get('CAP_BAND_Y') and not os.environ.get('BAND_Y'): os.environ['BAND_Y']=os.environ['CAP_BAND_Y']
# CAP_PRESET (opt-in): estilo de legenda pelo tipo de conteudo (oneshot-video captions.md, 12/10/2026).
# Valores explicitos no env ganham. Mudou de preset num corte ja planejado: REPLAN=1.
_PRESETS={'veredito':dict(CAP_CHARS='12',MAX_MERGE_CHARS='16',CAP_BASE='92',CAP_EMPH='118',EMPH_MAX='0.2'),   # opiniao forte, gancho, < 40 s
          'historia':dict(CAP_CHARS='22',MAX_MERGE_CHARS='26',CAP_BASE='70',CAP_EMPH='90',EMPH_MAX='0.15'),   # caso, "o que aconteceu"
          'aula':dict(CAP_CHARS='30',MAX_MERGE_CHARS='36',CAP_BASE='62',CAP_EMPH='78',EMPH_MAX='0.2')}        # explicacao, argumento
if os.environ.get('CAP_PRESET') in _PRESETS:
    for _k,_v in _PRESETS[os.environ['CAP_PRESET']].items(): os.environ.setdefault(_k,_v)
os.environ.setdefault('WORK',JOB.get('work','./work'))
os.environ.setdefault('SRCDIR',JOB['srcdir'])
os.environ.setdefault('FONT',JOB.get('font',os.path.join(HERE,'..','assets','CalSans-Regular.ttf')))
os.environ.setdefault('FILMBURN',JOB.get('filmburn',os.path.join(HERE,'..','assets','filmburn_blue.mp4')))
if JOB.get('logo'): os.environ.setdefault('LOGO',JOB['logo'])
B=os.environ['WORK']; os.makedirs(B,exist_ok=True)
# filho do modo paralelo: o pai ja rodou o plano (rodar de novo em paralelo corromperia o plan.json)
if os.environ.get('_CIBO_CHILD')!='1': subprocess.run([sys.executable,os.path.join(HERE,'plan.py')],check=True,env=os.environ)
import render, cover, clicks as CK, render_caps as RC
def sh(c):
    r=subprocess.run(c,shell=True,capture_output=True,text=True)
    if r.returncode: print(r.stderr[-2500:]); raise SystemExit(1)
STAMP=os.path.join(B,'.stamps.json')
_ST=json.load(open(STAMP)) if os.path.exists(STAMP) else {}
def fp(*parts):
    import hashlib
    return hashlib.sha1(json.dumps(parts,sort_keys=True,default=str).encode()).hexdigest()[:16]
def stage(name,key,out,fn):
    """run fn() only if its fingerprint or its output changed"""
    outs=out if isinstance(out,list) else [out]
    if _ST.get(name)==key and all(os.path.exists(o) for o in outs):
        print(name,'cached',flush=True); return False
    fn(); _ST[name]=key
    # grava com trava e junta com o que esta no disco: cortes em paralelo (PARALLEL) dividem
    # este arquivo e um apagaria o registro do outro
    import fcntl
    with open(STAMP+'.lock','w') as lk:
        fcntl.flock(lk,fcntl.LOCK_EX)
        cur=json.load(open(STAMP)) if os.path.exists(STAMP) else {}
        cur[name]=key; _ST.update(cur)
        json.dump(cur,open(STAMP,'w'),indent=1)
    print(name,'built',flush=True); return True

# opcoes de capa do perfil entram no cache so quando usadas (caches antigos seguem validos)
_CX=[os.environ.get('COVER_Y'),os.environ.get('COVER_BAR')] if (os.environ.get('COVER_Y') or os.environ.get('COVER_BAR')) else []
def run(k):
    P=json.load(open(os.path.join(B,'plan.json'))); c=P[k]
    # fingerprint the caption DATA before render_caps decorates it with PIL objects
    CAPS=fp([{a:b for a,b in x.items() if a!='items'} for x in c['caps']])
    _CAPX=[os.environ.get('CAP_BASE'),os.environ.get('CAP_EMPH')] if (os.environ.get('CAP_BASE') or os.environ.get('CAP_EMPH')) else []
    stage(f'caps:{k}',   fp(CAPS,JOB.get('style'),os.environ.get('BAND_Y'),os.environ.get('CAP_CY'),*_CAPX), [f'{B}/caps_{k}_rgb.mp4',f'{B}/caps_{k}_a.mp4'],
          lambda: RC.render(c,f'{B}/caps_{k}'))
    stage(f'clicks:{k}',  fp([x['s'] for x in c['caps'] if x.get('any')]), f'{B}/clicks_{k}.wav',
          lambda: CK.build(c,f'{B}/clicks_{k}.wav'))
    cutkey=fp(c['keeps'],c['cropx'],c.get('cropx_timeline'),c.get('cropx_interp'),c['src'],os.environ.get('FORMAT'))
    if c.get('crop_h'): cutkey=fp(cutkey,c['crop_h'])   # so entra quando usado: caches antigos seguem validos
    # VENC/PASSA_DIRECT so entram quando usados: caches antigos seguem validos
    if os.environ.get('VENC') or os.environ.get('PASSA_DIRECT'): cutkey=fp(cutkey,os.environ.get('VENC'),os.environ.get('PASSA_DIRECT'))
    recut=stage(f'cut:{k}', cutkey, f'{B}/A_{k}.mp4', lambda: render.passA(c,f'{B}/A_{k}.mp4'))
    stage(f'intro:{k}',   cutkey, f'{B}/I_{k}.mp4', lambda: render.make_intro(f'{B}/A_{k}.mp4',f'{B}/I_{k}.mp4'))
    horiz=os.environ.get('FORMAT')=='16x9'   # YouTube: sem capa no 1o frame (thumbnail sobe a parte)
    if not horiz: stage(f'cover:{k}',   fp(cutkey,c['headline'],c['cover_t'],c.get('cover_src'),c.get('cover_src_t'),c.get('cover_src_x'),c.get('cover_style'),*_CX), f'{B}/capa_{k}.png',
          lambda: cover.build(c,f'{B}/A_{k}.mp4',f'{B}/capa_{k}.png'))
    basename=c.get('filename',k)
    out=os.path.join(JOB.get('outdir',B),f'{basename}.mp4'); os.makedirs(os.path.dirname(out) or '.',exist_ok=True)
    def _final():
        # grava num .part e so renomeia no fim: um render morto no meio nao pode deixar
        # um MP4 truncado com o nome final, que o cache depois aceita como pronto.
        part=out[:-4]+'.part.mp4'
        render.final(c,f'{B}/A_{k}.mp4',f'{B}/I_{k}.mp4',part,cover=None if horiz else f'{B}/capa_{k}.png',
                     preset=JOB.get('preset','veryfast'),crf=JOB.get('crf',21),
                     extra=JOB.get('extra_v',''))
        os.replace(part,out)
        if horiz: return
        import shutil; shutil.copy(f'{B}/capa_{k}.png',os.path.join(JOB.get('outdir',B),f'CAPA - {basename}.png'))
    # cover_src/_t/_x entram aqui tambem: sem eles, trocar o frame da capa refazia o PNG
    # mas o MP4 ficava em cache com a capa antiga no primeiro quadro.
    stage(f'final:{k}', fp(cutkey,CAPS,c['headline'],c['cover_t'],c.get('cover_src'),c.get('cover_src_t'),c.get('cover_src_x'),c.get('cover_style'),os.environ['FILMBURN'],
                           JOB.get('preset'),JOB.get('crf'),JOB.get('extra_v'),c.get('burn_at'),c.get('voice_af'),c.get('music'),c.get('mix'),os.environ.get('BURN_OUT'),os.environ.get('BAND_Y'),os.environ.get('FORMAT'),*_CX,
                           *([c.get('overlays'),os.environ.get('BURN_END_INLINE'),os.environ.get('BURN_END_LIMIT'),os.environ.get('BURN_END_BT709'),os.environ.get('VT_MBPS')] if (c.get('overlays') or os.environ.get('BURN_END_INLINE')) else [])), out, _final)
    print(k,'DONE ->',out,flush=True)
KS=sys.argv[1:] or list(JOB['clips'])
# PARALLEL=N|auto (opt-in): um processo por corte, N de cada vez. `auto` usa o numero que o
# perfil de hardware calcula pela RAM (video-render-optimizer, CIBO_MAX_PARALLEL).
_par=os.environ.get('PARALLEL','1')
if _par=='auto':
    _par=os.environ.get('CIBO_MAX_PARALLEL')
    if not _par:
        try:
            _hp=os.path.join(HERE,'..','..','video-render-optimizer','scripts','hw_profile.py')
            _par=json.loads(subprocess.run([sys.executable,_hp,'env','--json'],capture_output=True,text=True,timeout=900).stdout)['CIBO_MAX_PARALLEL']
        except Exception: _par='1'
_par=max(1,int(_par))
if _par>1 and len(KS)>1 and os.environ.get('_CIBO_CHILD')!='1':
    import time
    env=dict(os.environ,_CIBO_CHILD='1',PARALLEL='1')
    fila=list(KS); vivos={}; falhas=[]
    while fila or vivos:
        while fila and len(vivos)<_par:
            k=fila.pop(0); vivos[k]=subprocess.Popen([sys.executable,os.path.abspath(__file__),k],env=env,
                                                     stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        for k,p in list(vivos.items()):
            if p.poll() is not None:
                out=p.stdout.read(); vivos.pop(k)
                for l in out.splitlines():
                    if any(x in l for x in ('built','cached','DONE','Error','Traceback','AVISO')): print(f'[{k}] {l}',flush=True)
                if p.returncode: falhas.append(k); print(f'[{k}] FALHOU (saida {p.returncode})\n'+out[-1500:],flush=True)
        time.sleep(0.5)
    if falhas: sys.exit(f'falharam: {falhas}')
else:
    for k in KS: run(k)
