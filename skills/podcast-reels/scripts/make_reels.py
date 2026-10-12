#!/usr/bin/env python3
"""Entry point. Usage:  JOB=job.json python3 make_reels.py [clip ...]"""
import os,sys,json,subprocess
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
JOBF=os.environ['JOB']; JOB=json.load(open(JOBF))
os.environ.setdefault('WORK',JOB.get('work','./work'))
os.environ.setdefault('SRCDIR',JOB['srcdir'])
os.environ.setdefault('FONT',JOB.get('font',os.path.join(HERE,'..','assets','CalSans-Regular.ttf')))
os.environ.setdefault('FILMBURN',JOB.get('filmburn',os.path.join(HERE,'..','assets','filmburn_blue.mp4')))
if JOB.get('logo'): os.environ.setdefault('LOGO',JOB['logo'])
B=os.environ['WORK']; os.makedirs(B,exist_ok=True)
subprocess.run([sys.executable,os.path.join(HERE,'plan.py')],check=True,env=os.environ)
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
    json.dump(_ST,open(STAMP,'w'),indent=1); print(name,'built',flush=True); return True

def run(k):
    P=json.load(open(os.path.join(B,'plan.json'))); c=P[k]
    # fingerprint the caption DATA before render_caps decorates it with PIL objects
    CAPS=fp([{a:b for a,b in x.items() if a!='items'} for x in c['caps']])
    stage(f'caps:{k}',   fp(CAPS,JOB.get('style'),os.environ.get('BAND_Y'),os.environ.get('CAP_CY')), [f'{B}/caps_{k}_rgb.mp4',f'{B}/caps_{k}_a.mp4'],
          lambda: RC.render(c,f'{B}/caps_{k}'))
    stage(f'clicks:{k}',  fp([x['s'] for x in c['caps'] if x.get('any')]), f'{B}/clicks_{k}.wav',
          lambda: CK.build(c,f'{B}/clicks_{k}.wav'))
    cutkey=fp(c['keeps'],c['cropx'],c.get('cropx_timeline'),c.get('cropx_interp'),c['src'],os.environ.get('FORMAT'))
    if c.get('crop_h'): cutkey=fp(cutkey,c['crop_h'])   # so entra quando usado: caches antigos seguem validos
    recut=stage(f'cut:{k}', cutkey, f'{B}/A_{k}.mp4', lambda: render.passA(c,f'{B}/A_{k}.mp4'))
    stage(f'intro:{k}',   cutkey, f'{B}/I_{k}.mp4', lambda: render.make_intro(f'{B}/A_{k}.mp4',f'{B}/I_{k}.mp4'))
    horiz=os.environ.get('FORMAT')=='16x9'   # YouTube: sem capa no 1o frame (thumbnail sobe a parte)
    if not horiz: stage(f'cover:{k}',   fp(cutkey,c['headline'],c['cover_t'],c.get('cover_src'),c.get('cover_src_t'),c.get('cover_src_x'),c.get('cover_style')), f'{B}/capa_{k}.png',
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
                           JOB.get('preset'),JOB.get('crf'),JOB.get('extra_v'),c.get('burn_at'),c.get('voice_af'),c.get('music'),c.get('mix'),os.environ.get('BURN_OUT'),os.environ.get('BAND_Y'),os.environ.get('FORMAT')), out, _final)
    print(k,'DONE ->',out,flush=True)
for k in (sys.argv[1:] or list(JOB['clips'])): run(k)
