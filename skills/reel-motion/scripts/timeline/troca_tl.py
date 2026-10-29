# apaga do projeto aberto a timeline dada (para reimportar o pacote corrigido)
import sys, DaVinciResolveScript as d
p = d.scriptapp('Resolve').GetProjectManager().GetCurrentProject()
tls = [p.GetTimelineByIndex(i + 1) for i in range(p.GetTimelineCount())]
alvo = [t for t in tls if t.GetName() == sys.argv[1]]
print(p.GetName(), 'apagada' if alvo and p.DeleteTimelines(alvo) else 'não achei', sys.argv[1])
