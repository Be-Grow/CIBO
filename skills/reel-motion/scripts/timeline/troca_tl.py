# apaga do projeto aberto a timeline dada (para reimportar o pacote corrigido)
# DeleteTimelines é do MediaPool, não do Project (Project.DeleteTimelines é None na API: 'NoneType' object is not callable,
# Andreia cortesMesaRadionica 06/11/2026). Rode de um arquivo (.py), não por heredoc: pelo stdin a API devolveu None nos métodos.
import sys, unicodedata, DaVinciResolveScript as d
nfc = lambda s: unicodedata.normalize('NFC', s)
p = d.scriptapp('Resolve').GetProjectManager().GetCurrentProject()
alvo = []
for i in range(1, p.GetTimelineCount() + 1):
    t = p.GetTimelineByIndex(i)
    if t and nfc(t.GetName()) == nfc(sys.argv[1]):
        alvo.append(t)
print(p.GetName(), 'apagada' if alvo and p.GetMediaPool().DeleteTimelines(alvo) else 'não achei', sys.argv[1])
