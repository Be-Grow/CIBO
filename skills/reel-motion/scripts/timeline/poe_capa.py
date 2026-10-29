# capa (1 quadro) no quadro 0 de cada timeline vertical, faixa própria no topo "CAPA"; JPG na pasta do vídeo no Media Pool
import glob, os, re, unicodedata, DaVinciResolveScript as d
P = __file__.rsplit('/04_work/', 1)[0]; nfc = lambda s: unicodedata.normalize('NFC', s)
p = d.scriptapp('Resolve').GetProjectManager().GetCurrentProject(); mp = p.GetMediaPool(); root = mp.GetRootFolder()
def sub(f, n):
    for s in f.GetSubFolderList() or []:
        if s.GetName() == n: return s
    return mp.AddSubFolder(f, n)
for i in range(p.GetTimelineCount()):
    t = p.GetTimelineByIndex(i + 1); n = nfc(t.GetName())
    if '(16x9)' in n and not any(os.path.exists(f'{P}/06_deliverables/CAPA - {n}.mov') for _ in [0]): continue
    base = re.sub(r' v7(\.1)?$', '', n); jpg = [f for f in glob.glob(f'{P}/06_deliverables/CAPA - *.mov') if nfc(os.path.basename(f))[7:-4] in (n, base)]
    if not jpg: print(n, 'sem capa'); continue
    jpg = sorted(jpg, key=lambda f: -len(f))[0]   # "… v7" antes de "…"
    p.SetCurrentTimeline(t)
    velhas = [it for k in range(1, t.GetTrackCount('video') + 1) for it in (t.GetItemListInTrack('video', k) or []) if it.GetName().lower().startswith('capa')]
    if velhas: t.DeleteClips(velhas, False)
    capa_ja = [it for it in (t.GetItemListInTrack('video', t.GetTrackCount('video')) or []) if it.GetName().startswith('CAPA')]
    if capa_ja: print(n, 'já tem capa'); continue
    pasta = sub(sub(sub(root, '02 MÍDIA POR VÍDEO'), re.sub(r' \(16x9\)$', '', base)), '16x9' if '(16x9)' in n else '9x16'); mp.SetCurrentFolder(sub(pasta, '7 CAPA'))
    ja = [c for c in (mp.GetCurrentFolder().GetClipList() or []) if c.GetName() == os.path.basename(jpg)]
    it = ja[0] if ja else mp.ImportMedia([jpg])[0]
    k = t.GetTrackCount('video')
    if t.GetTrackName('video', k) != 'CAPA': t.AddTrack('video'); k += 1; t.SetTrackName('video', k, 'CAPA')
    nv = mp.AppendToTimeline([{'mediaPoolItem': it, 'startFrame': 0, 'endFrame': 1, 'mediaType': 1, 'trackIndex': k, 'recordFrame': t.GetStartFrame()}])
    print(n, '→ capa no V%d' % k, 'ok' if nv else 'FALHOU', nv[0].GetDuration() if nv else '')
