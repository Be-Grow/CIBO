# confere TODAS as emendas pelo SINAL de áudio do bruto (o Whisper estica palavras sobre pausas e dá alarme falso):
#  - voz nos 80 ms DEPOIS do ponto de saída = fim de palavra engolido
#  - voz nos 80 ms ANTES do ponto de entrada = começo de palavra cortado
#  - respiro na emenda (silêncio antes + depois) < 0,22 s depois de ponto/interrogação = fala apertada
# uso: audita_emendas.py r01 r02 …      (limiar de voz: −40 dBFS em janelas de 20 ms)
import json, glob, sys, wave, numpy as np
P = __file__.rsplit('/04_work/', 1)[0]
def carrega(R):
    w = wave.open(f'{R}/src_48k.wav'); sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    return x, sr
def db(x, sr, a, b):
    s = x[max(0, int(a * sr)):max(0, int(b * sr))]; return 20 * np.log10(np.sqrt(np.mean(s ** 2)) + 1e-9) if len(s) else -120
def voz(x, sr, a, b, lim=-40):     # alguma janela de 20 ms com voz em [a, b]?
    return any(db(x, sr, t, t + 0.02) > lim for t in np.arange(a, b - 0.019, 0.01))
def silencio(x, sr, t, sentido, lim=-40, maxs=1.5):   # quanto silêncio a partir de t (para trás −1 / frente +1)
    d = 0.0
    while d < maxs and db(x, sr, *(sorted((t + sentido * d, t + sentido * (d + 0.02))))) <= lim: d += 0.01
    return d
def pontuacao(src):
    ws = [w for g in glob.glob(f'{P}/02_transcripts/_palavras/{src}_*.json') for w in json.load(open(g))]
    return sorted(ws, key=lambda w: w['start'])
for R in sys.argv[1:]:
    src = json.load(open(f'{R}/reel.json'))['src'].split('/')[-1].replace('.MP4', '')
    x, sr = carrega(R); S = json.load(open(f'{R}/segs.json')); WS = pontuacao(src); t = 0; prob = []
    for i, (a, b) in enumerate(S):
        te = t + b - a
        if i + 1 < len(S):
            c = S[i + 1][0]
            if voz(x, sr, b, b + 0.08): prob.append(f'{te:6.2f}s fim ENGOLIDO (ainda tem voz depois de {b:.2f})')
            if voz(x, sr, c - 0.08, c): prob.append(f'{te:6.2f}s começo CORTADO (já tem voz antes de {c:.2f})')
            resp = silencio(x, sr, b, -1) + silencio(x, sr, c, +1)
            ult = [w for w in WS if a <= w['start'] <= b]
            if ult and ult[-1]['word'].strip()[-1:] in '.?!' and resp < 0.22:
                prob.append(f'{te:6.2f}s fala APERTADA: {resp:.2f} s de respiro depois de "{ult[-1]["word"].strip()}"')
        t += b - a
    print(f'== {R}: {len(S) - 1} emendas, ' + (f'{len(prob)} problema(s)' if prob else 'OK')); [print('  ', p) for p in prob]
