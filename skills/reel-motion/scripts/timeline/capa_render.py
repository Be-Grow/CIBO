"""Tira o SELO (era o cartão da campanha Black: não cabe em conteúdo orgânico), põe a capa (1 quadro, faixa CAPA no topo,
quadro 0; MOV de 10 quadros porque o Resolve não corta 1 quadro de um still) ; render depois com selo_render.py so-render.
uso: capa_render.py"""
import glob, os, sys, unicodedata
from pathlib import Path
sys.path.append('/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules')
import DaVinciResolveScript as dvr
AQ = Path(__file__).resolve().parent.parent; nfc = lambda s: unicodedata.normalize('NFC', s)
r = dvr.scriptapp('Resolve'); p = r.GetProjectManager().GetCurrentProject()
assert p.GetName() == 'Andreia - Demanda Urgente', p.GetName()
mp = p.GetMediaPool(); raiz = mp.GetRootFolder()
capas = next((f for f in raiz.GetSubFolderList() if f.GetName() == '08 CAPAS'), None) or mp.AddSubFolder(raiz, '08 CAPAS')
for i in range(1, p.GetTimelineCount() + 1):
    tl = p.GetTimelineByIndex(i); nome = nfc(tl.GetName()); p.SetCurrentTimeline(tl)
    for k in range(tl.GetTrackCount('video'), 0, -1):
        if tl.GetTrackName('video', k) == 'SELO':
            its = tl.GetItemListInTrack('video', k) or []
            if its: assert tl.DeleteClips(its, False)
            assert tl.DeleteTrack('video', k); print(nome[:30], 'SELO removido')
    if any(tl.GetTrackName('video', k) == 'CAPA' for k in range(1, tl.GetTrackCount('video') + 1)):
        print(nome[:30], 'já tem capa'); continue
    arq = next((f for f in glob.glob(str(AQ / '06_deliverables' / 'CAPA - *.mov')) if nfc(os.path.basename(f))[7:-4] == nome), None)
    if not arq: print(nome[:30], 'sem capa (16:9)'); continue
    mp.SetCurrentFolder(capas); it = mp.ImportMedia([arq])[0]
    assert tl.AddTrack('video'); k = tl.GetTrackCount('video'); tl.SetTrackName('video', k, 'CAPA')
    nv = mp.AppendToTimeline([{'mediaPoolItem': it, 'startFrame': 0, 'endFrame': 1, 'mediaType': 1, 'trackIndex': k, 'recordFrame': tl.GetStartFrame()}])
    assert nv and nv[0].GetDuration() == 1, f'capa {nome}: {nv and nv[0].GetDuration()}'
    nv[0].SetClipColor('Brown'); print(nome[:30], f'capa no V{k}, 1 quadro')
r.GetProjectManager().SaveProject()
