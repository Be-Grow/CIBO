# desliga a faixa de áudio de referência da câmera (pelo NOME, a ordem muda entre timelines) nas timelines dadas
import sys, DaVinciResolveScript as d
pm = d.scriptapp('Resolve').GetProjectManager(); p = pm.GetCurrentProject()
for i in range(1, p.GetTimelineCount() + 1):
    t = p.GetTimelineByIndex(i)
    if t.GetName() not in sys.argv[1:]: continue
    p.SetCurrentTimeline(t)                       # SetTrackEnable só pega com a timeline ativa
    for k in range(1, t.GetTrackCount('audio') + 1):
        cam = 'câmera' in t.GetTrackName('audio', k).lower()
        t.SetTrackEnable('audio', k, not cam)
    print(t.GetName(), [(t.GetTrackName('audio', k), t.GetIsTrackEnabled('audio', k)) for k in range(1, t.GetTrackCount('audio') + 1)])
pm.SaveProject()
