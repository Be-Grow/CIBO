#!/usr/bin/env python3
"""Barra take da equipe: a voz de quem sopra o roteiro fica a -30..-50 dB, a da apresentadora a -13..-20.
uso: checa_takes.py segs.json fonte_16k.wav [--min -22]
Mede o p90 do nível (janelas de 100 ms, ignorando silêncio) de cada trecho e de cada pedaço de 2 s dentro dele (janela com voz e p90 < -28 dB = suspeita)."""
import json,subprocess,sys,numpy as np
S=json.load(open(sys.argv[1])); src=sys.argv[2]; MIN=float(sys.argv[sys.argv.index('--min')+1]) if '--min' in sys.argv else -25   # trecho curto dela no fim da frase chega a -24 (Priscilla 03); equipe fica em -30/-50
def frames(a,b):
    x=np.frombuffer(subprocess.run(['ffmpeg','-v','error','-ss',str(a),'-to',str(b),'-i',src,'-f','s16le','-ac','1','-'],capture_output=True).stdout,np.int16)/32768
    return [20*np.log10(np.sqrt(np.mean(x[i:i+1600]**2))+1e-9) for i in range(0,len(x)-1600,1600)]
bad=0
for a,b in S:
    f=frames(a,b); v=[x for x in f if x>-60]
    p=np.percentile(v,90) if v else -99
    sub=[(a+k*0.1,[x for x in f[k:k+20] if x>-60]) for k in range(0,len(f),20)]
    low=[f"{t:.1f}" for t,w in sub if len(w)>=8 and np.percentile(w,90)<MIN-3]   # janela de 2 s com voz só no nível da equipe
    flag=p<MIN or low
    bad+=bool(flag)
    print(f"{a:.2f}-{b:.2f} p90 {p:.1f} dB" + (f"  <-- VOZ BAIXA (equipe?) em {', '.join(low) or 'todo o trecho'}" if flag else ""))
# corte no meio da palavra: voz forte logo antes E logo depois da borda (05: "marketplace" e "seis por cen|to", 14/10/2026)
def nivel(a, b):
    f = [x for x in frames(a, b) if x > -90]
    return max(f) if f else -99
for k, (a, b) in enumerate(S):
    if nivel(b, b + 0.35) > -28:   # a voz volta forte logo depois do corte: a fala continuava (pausa entre sílabas engana)
        print(f"{a:.2f}-{b:.2f} corte no FIM no meio da palavra (voz continua depois de {b:.2f})"); bad += 1
    if nivel(a - 0.35, a) > -28:
        print(f"{a:.2f}-{b:.2f} corte no INÍCIO no meio da palavra (voz antes de {a:.2f})"); bad += 1
# fim do corte dentro de uma palavra pela transcrição do Whisper (o MFA às vezes encurta a última palavra: "seis por cen|to" no 05)
import os
tx = os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), 'src_large.json')
if os.path.exists(tx):
    ww = [w for sg in json.load(open(tx))['segments'] for w in sg.get('words', [])]
    for a, b in S:
        for w in ww:
            if w['start'] + 0.05 < b < w['end'] - 0.05 and (w['end'] - b) > 0.08:
                print(f"{a:.2f}-{b:.2f} corte no FIM antes do fim de '{w['word'].strip()}' (Whisper: termina {w['end']:.2f})"); bad += 1; break
print('OK' if not bad else f'{bad} trecho(s) para ouvir'); sys.exit(1 if bad else 0)
