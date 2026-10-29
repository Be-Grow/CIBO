# tira um trecho [TA,TB) s de uma timeline do v7 SEM render (editor 27/10/2026). endFrame do AppendToTimeline é EXCLUSIVO.
# Depois de rodar: ajusta_resolve.py (Pan), faixas_audio.py e qa_resolve.py — conferir quadros na emenda.
# cópia → divide clipes nos cortes (API) + ripple em todas as faixas → zoom/tela dividida deslocados e sem sobreposição
# (resolve_fx) → apaga a original e a cópia assume o nome. uso: corta_trecho.py "TIMELINE" TA TB
import json, os, sys, subprocess, DaVinciResolveScript as d
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fx_sem_sobrepor import apara
NOME, TA, TB = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]); TMP = NOME + ' (cortando)'
P = __file__.rsplit('/04_work/', 1)[0]; FX = os.path.expanduser('~/.claude/skills/reel-motion/scripts/resolve_fx.py')
r = d.scriptapp('Resolve'); p = r.GetProjectManager().GetCurrentProject(); mp = p.GetMediaPool()
tl = lambda n: [p.GetTimelineByIndex(i + 1) for i in range(p.GetTimelineCount()) if p.GetTimelineByIndex(i + 1).GetName() == n]
o = tl(NOME)[0]; p.SetCurrentTimeline(o); t = o.DuplicateTimeline(TMP); p.SetCurrentTimeline(t)
fps = float(t.GetSetting('timelineFrameRate')); s0 = t.GetStartFrame(); a, b = round(TA * fps), round(TB * fps); A, B = s0 + a, s0 + b
# 1) camadas de ajuste fora (voltam pelo resolve_fx) · 2) divide e marca o trecho · 3) ripple
aj = [it for k in range(1, t.GetTrackCount('video') + 1) for it in (t.GetItemListInTrack('video', k) or []) if not it.GetMediaPoolItem() and it.GetFusionCompCount()]
t.DeleteClips(aj, False); meio, ruim, filler = [], [], {}
for tipo in ('video', 'audio'):
    for k in range(1, t.GetTrackCount(tipo) + 1):
        for it in list(t.GetItemListInTrack(tipo, k) or []):
            st, en = it.GetStart(), it.GetEnd()
            if en <= A or st >= B: continue
            if A <= st and en <= B: meio.append(it); continue
            m = it.GetMediaPoolItem()
            if not m: ruim.append(f'{tipo}{k} {it.GetName()}'); continue
            filler.setdefault(tipo, m); ss = it.GetSourceStartFrame(); props = it.GetProperty() or {}; mt = 1 if tipo == 'video' else 2
            t.SetClipsLinked([it], False); t.DeleteClips([it], False)   # desvincula: senão o Resolve apaga junto o áudio da câmera e as faixas trocam
            for x, y in [(st, A)] * (st < A) + [(max(st, A), min(en, B))] + [(B, en)] * (en > B):
                nv = mp.AppendToTimeline([{'mediaPoolItem': m, 'startFrame': ss + (x - st), 'endFrame': ss + (y - st), 'mediaType': mt, 'trackIndex': k, 'recordFrame': x}])
                if nv:
                    for _ in (1, 2):   # 2 passadas: Scaling antes de Zoom/Pan
                        for kk, vv in props.items():
                            try: nv[0].SetProperty(kk, vv)
                            except Exception: pass
                    if (x, y) == (max(st, A), min(en, B)): meio.append(nv[0])
        if not any(x.GetStart() < B and x.GetEnd() > A for x in (t.GetItemListInTrack(tipo, k) or [])) and filler.get(tipo):
            nv = mp.AppendToTimeline([{'mediaPoolItem': filler[tipo], 'startFrame': 0, 'endFrame': B - A, 'mediaType': 1 if tipo == 'video' else 2, 'trackIndex': k, 'recordFrame': A}])
            if nv: meio.append(nv[0])
print('ripple', len(meio), 'itens:', t.DeleteClips(meio, True), '| não divididos:', ruim)
# 4) movimentos deslocados + aparados → resolve_fx na cópia
m = json.load(open(f'{P}/07_davinci/{NOME}/movimentos.json', encoding='utf-8')); D = b - a; novas = []
for c in m['camadas']:
    i, f = c['inicio'], c['inicio'] + c['dur']
    if f <= a: novas.append(c); continue
    if i >= b: c['inicio'] -= D; novas.append(c); continue
    if a <= i and f <= b: continue
    kf = [[k[0] - (D if i + k[0] >= b else 0)] + k[1:] for k in c['kf'] if not (a <= i + k[0] < b)]
    if i >= a: kf = [[k[0] - (a - i)] + k[1:] for k in kf]; c['inicio'] = a
    c['kf'] = kf; c['dur'] -= min(f, b) - max(i, a); novas.append(c)
m['camadas'] = novas; apara(m); g = f'{P}/04_work/tmp/fx/{TMP}'; os.makedirs(g, exist_ok=True)
json.dump(m, open(f'{g}/movimentos.json', 'w', encoding='utf-8'), ensure_ascii=False)
print((subprocess.run(['/opt/homebrew/bin/python3.14', FX, g], capture_output=True, text=True).stdout.strip().splitlines() or ['?'])[-1][-70:])
# guarda os movimentos novos junto do pacote (próximo ajuste parte daqui)
json.dump(m, open(f'{P}/07_davinci/{NOME}/movimentos.json', 'w', encoding='utf-8'), ensure_ascii=False)
# 5) troca: apaga a original, a cópia assume o nome
o = tl(NOME)[0]; n = tl(TMP)[0]; p.SetCurrentTimeline(n); mp.DeleteTimelines([o]); print('renomeada:', n.SetName(NOME), '| duração', round((n.GetEndFrame() - n.GetStartFrame()) / fps, 2), 's')
