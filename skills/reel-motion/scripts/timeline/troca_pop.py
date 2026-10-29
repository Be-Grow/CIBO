# editor 27/10/2026: "pop" tira a seriedade → clique. Gera NN_click-*__rNN.wav ao lado de cada NN_pop-*__rNN.wav
# (mesma duração, clique no início) e troca a mídia dos clipes no projeto aberto (ReplaceClip), renomeando
import glob, subprocess, os, unicodedata, DaVinciResolveScript as d
nfc = lambda s: unicodedata.normalize("NFC", s)
P = __file__.rsplit('/04_work/', 1)[0]; K = '/Volumes/SSD/CIBO Acervo/sfx/_global/'
TROCA = {'pop-1': 'click-soft', 'pop-2': 'click-mouse', 'select-1': 'click-soft-2'}   # select-1: editor 27/10 'esse som não dá'
novo = {}
for f in [g for k in TROCA for g in glob.glob(f'{P}/07_davinci/*/sfx/*{k}__*.wav')]:
    k = next(x for x in TROCA if x in f); g = f.replace(k, TROCA[k])
    dur = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f], capture_output=True, text=True).stdout.strip()
    if not os.path.exists(g):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', K + TROCA[k] + '.wav', '-ac', '1', '-ar', '48000', '-af', f'apad,atrim=0:{dur}', g], check=True)
    novo[nfc(f)] = g
print(len(novo), 'cliques gerados')
p = d.scriptapp('Resolve').GetProjectManager().GetCurrentProject()
def todos(f): return (f.GetClipList() or []) + [c for s in (f.GetSubFolderList() or []) for c in todos(s)]
ok = 0
for c in todos(p.GetMediaPool().GetRootFolder()):
    fp = nfc(c.GetClipProperty('File Path') or '')
    if fp in novo and c.ReplaceClip(novo[fp]):
        c.SetClipProperty('Clip Name', os.path.basename(novo[fp])); ok += 1
print(ok, 'clipes trocados no projeto', p.GetName())
