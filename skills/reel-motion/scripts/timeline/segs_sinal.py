# segs.json pelo SINAL do bruto (o Whisper marcou emendas em cima da voz): silêncio real (janelas de 20 ms abaixo de LIM dB,
# bolhas < 80 ms ignoradas) de pelo menos MIN s vira emenda, deixando PRE s depois da voz e POS s antes dela.
# uso: segs_sinal.py rNN [LIM -46] [MIN 0.5]
import json, sys, wave, numpy as np
R = sys.argv[1]; LIM = float(sys.argv[2]) if len(sys.argv) > 2 else -46; MIN = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
PRE, POS, J = 0.18, 0.12, 0.02
w = wave.open(f'{R}/src_48k.wav'); sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
n = int(len(x) / sr / J); db = np.array([20 * np.log10(np.sqrt(np.mean(x[int(i * J * sr):int((i + 1) * J * sr)] ** 2)) + 1e-9) for i in range(n)])
v = db > LIM
# bolha curta de "voz" dentro do silêncio (estalo, respiro) não conta
i = 0
while i < n:
    if v[i]:
        j = i
        while j < n and v[j]: j += 1
        if j - i < 4: v[i:j] = False
        i = j
    else: i += 1
idx = np.flatnonzero(v); ini, fim = idx[0] * J, (idx[-1] + 1) * J
S = [[max(0, ini - POS), None]]; prev = idx[0]
for k in idx[1:]:
    if (k - prev - 1) * J >= MIN:
        S[-1][1] = (prev + 1) * J + PRE; S.append([k * J - POS, None])
    prev = k
S[-1][1] = min(n * J, fim + 0.35)
S = [[round(a, 2), round(b, 2)] for a, b in S]
json.dump(S, open(f'{R}/segs.json', 'w')); print(R, S, f'{sum(b - a for a, b in S):.2f}s de {n * J:.2f}s')
