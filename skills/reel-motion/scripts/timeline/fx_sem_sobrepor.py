# "Media Offline" no Resolve quando a camada de zoom (Fusion, V3) se sobrepõe à de tela dividida (Fusion, V4) — achado 27/10/2026.
# Apara cada zoom na borda da tela dividida (termina quando ela começa / começa quando ela acaba), apaga as camadas de ajuste
# da timeline e recria com o resolve_fx (sem render). uso: fx_sem_sobrepor.py "NOME DA TIMELINE" […]  (pacote = 07_davinci/<nome>)
import json, os, sys, subprocess, DaVinciResolveScript as d
P = __file__.rsplit('/04_work/', 1)[0]; FX = os.path.expanduser('~/.claude/skills/reel-motion/scripts/resolve_fx.py')
p = d.scriptapp('Resolve').GetProjectManager().GetCurrentProject()
def apara(m):
    ss = [(c['inicio'], c['inicio'] + c['dur']) for c in m['camadas'] if c['tipo'] == 's']; out, n = [], 0
    for c in m['camadas']:
        if c['tipo'] == 'z':
            for a, b in ss:
                i, f = c['inicio'], c['inicio'] + c['dur']
                if not (i < b and f > a): continue
                n += 1
                if i < a: c['kf'] = [k for k in c['kf'] if k[0] < a - i]; c['dur'] = a - i
                else: c['kf'] = [[k[0] - (b - i)] + k[1:] for k in c['kf'] if k[0] >= b - i]; c['inicio'] = b; c['dur'] = f - b
            if c['dur'] <= 1 or not c['kf']: continue
        out.append(c)
    m['camadas'] = out; return n
for nome in (sys.argv[1:] if __name__ == '__main__' else []):
    m = json.load(open(f'{P}/07_davinci/{nome}/movimentos.json', encoding='utf-8')); n = apara(m)
    if not n: print(f'{nome}: sem sobreposição'); continue
    g = f'{P}/04_work/tmp/fx/{nome}'; os.makedirs(g, exist_ok=True); json.dump(m, open(f'{g}/movimentos.json', 'w', encoding='utf-8'), ensure_ascii=False)
    t = [p.GetTimelineByIndex(i + 1) for i in range(p.GetTimelineCount()) if p.GetTimelineByIndex(i + 1).GetName() == nome][0]; p.SetCurrentTimeline(t)
    aj = [it for k in range(1, t.GetTrackCount('video') + 1) for it in (t.GetItemListInTrack('video', k) or []) if not it.GetMediaPoolItem() and it.GetFusionCompCount()]
    t.DeleteClips(aj, False)
    r = subprocess.run(['/opt/homebrew/bin/python3.14', FX, g], capture_output=True, text=True)
    print(f'{nome}: {n} sobreposição(ões) aparada(s); {len(aj)} camadas refeitas →', (r.stdout.strip().splitlines() or ['?'])[-1][-60:])
