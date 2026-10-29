# confere/corrige as faixas de áudio pelo CONTEÚDO (não pelo nome): faixa com o bruto .MP4 = câmera (desliga),
# faixa com voz__*.wav = VOZ (liga); renomeia certo. O Resolve às vezes importa com os nomes trocados (02, 27/10/2026)
import sys, DaVinciResolveScript as d
p = d.scriptapp('Resolve').GetProjectManager().GetCurrentProject()
for i in range(p.GetTimelineCount()):
    t = p.GetTimelineByIndex(i + 1); p.SetCurrentTimeline(t); mud = []
    for k in range(1, t.GetTrackCount('audio') + 1):
        it = t.GetItemListInTrack('audio', k) or []
        m = it[0].GetMediaPoolItem().GetName() if it else ''
        if m.upper().endswith('.MP4'):
            if t.GetTrackName('audio', k) != 'ÁUDIO câmera (ref.)' or t.GetIsTrackEnabled('audio', k): mud.append(f'A{k} câmera')
            t.SetTrackName('audio', k, 'ÁUDIO câmera (ref.)'); t.SetTrackEnable('audio', k, False)
        elif m.startswith('voz__'):
            if t.GetTrackName('audio', k) != 'VOZ' or not t.GetIsTrackEnabled('audio', k): mud.append(f'A{k} voz')
            t.SetTrackName('audio', k, 'VOZ'); t.SetTrackEnable('audio', k, True)
    print(t.GetName(), '→ corrigido: ' + ', '.join(mud) if mud else '→ ok')
