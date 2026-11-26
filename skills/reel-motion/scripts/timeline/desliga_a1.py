# desliga a faixa de áudio de referência da câmera (pelo NOME, a ordem muda entre timelines) nas timelines dadas
import os as _ro, sys as _rs; _rs.path.insert(0, _ro.path.join(_ro.path.dirname(_ro.path.realpath(__file__)), '../../../_shared')); import resolve_env  # noqa: E401,F401  (API do Resolve em Mac/Windows)
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
__import__('sys').path.insert(0, __import__('os').path.join(__import__('os').path.dirname(__import__('os').path.realpath(__file__)), '..')); import fusion_kit as _K; _K.salva(pm)
