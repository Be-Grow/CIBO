# pós-importação: desliga o som da câmera (pelo nome), aplica Pan medido em quadros do Resolve e confere a sincronia
# uso: ajusta_resolve.py "TIMELINE" PAN [segs.json]   (PAN "-" = não mexe; unidade da API ≈ 14 px na vertical)
import sys, json, DaVinciResolveScript as d
pm = d.scriptapp('Resolve').GetProjectManager(); p = pm.GetCurrentProject(); nome, pan = sys.argv[1], sys.argv[2]
t = next(p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1) if p.GetTimelineByIndex(i).GetName() == nome)
p.SetCurrentTimeline(t)                                   # SetTrackEnable/SetProperty só pegam com a timeline ativa
for k in range(1, t.GetTrackCount('audio') + 1):
    t.SetTrackEnable('audio', k, 'câmera' not in t.GetTrackName('audio', k).lower())
cam = next(k for k in range(1, t.GetTrackCount('video') + 1) if 'câmera' in t.GetTrackName('video', k).lower())
it = t.GetItemListInTrack('video', cam)
if pan != '-':
    for x in it: x.SetProperty('Pan', float(pan))
fps = float(t.GetSetting('timelineFrameRate'))
segs = [s[0] for s in json.load(open(sys.argv[3]))] if len(sys.argv) > 3 else []
print(nome, '| áudio:', [(t.GetTrackName('audio', k), t.GetIsTrackEnabled('audio', k)) for k in range(1, t.GetTrackCount('audio') + 1)],
      '| pan', round(it[0].GetProperty('Pan'), 2), '| desvio:', [round(x.GetLeftOffset() / fps - s, 2) for x, s in zip(it, segs)])
pm.SaveProject()
