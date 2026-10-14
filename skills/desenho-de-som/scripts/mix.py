#!/usr/bin/env python3
"""Mixa trilha + SFX a partir de uma folha de deixas (JSON), alinhando cada SFX pelo PICO no corte
(o whoosh "passa" no corte, não começa nele), normaliza e confere se a subida não engole o impacto.

Uso: mix.py DEIXAS.json SAIDA.wav
DEIXAS.json:
{
  "dur": 17, "lufs": -16, "tp": -1.5, "fade_out": 0.7,
  "impacto": 11.75,                      # opcional: confere subida x impacto
  "musica": {"arquivo": "...mp3", "inicio_trilha": 20.8, "ganho": -2, "fade_out": [15.5, 1.5],
             "automacao": [[11.65, 0], [11.8, 6]],   # trilha sobe 6 dB no impacto e fica (dB, linear entre pontos)
             "remover": [[30.6, 31.459]]},          # tempo da TRILHA: encurta a pausa em 1 batida (música volta antes)
  "sfx": [
    {"arquivo": "...whoosh.wav", "pico_em": 1.5, "ganho": -3},       # pico do som cai em 1,5 s
    {"arquivo": "...reverse.wav", "fim_em": 1.5, "trim": 0.3},        # reverse/riser: termina no corte
    {"arquivo": "...boom.mp3", "ataque_em": 11.75, "ganho": 3},       # 1º transiente cai no corte
    {"arquivo": "...pad.wav", "em": 0.0, "dur": 3.2, "trim": 1.75}    # início literal
  ]
}
Para cada deixa: "trim" corta o começo do arquivo e "dur" limita a duração. Use "nota" para lembrar o porquê.
"""
import json, os, subprocess, sys
import numpy as np

SR = 8000


def load(f, trim=0.0, dur=None):
    cmd = ['ffmpeg', '-v', 'error', '-ss', str(trim)] + (['-t', str(dur)] if dur else []) + ['-i', f, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32)


def env(x, win=0.05):
    w = int(SR * win); n = max(len(x) // w, 1)
    return 20 * np.log10(np.sqrt((x[:n * w].reshape(n, w) ** 2).mean(1)) + 1e-9)


def inicio(d):
    trim, dur = d.get('trim', 0), d.get('dur')
    if 'em' in d: return d['em'], None
    x = load(d['arquivo'], trim, dur)
    if 'fim_em' in d: return d['fim_em'] - len(x) / SR, None
    e = env(x)
    if 'pico_em' in d:
        p = float(np.argmax(e)) * 0.05 + 0.025
        return d['pico_em'] - p, p
    if 'ataque_em' in d:
        k = int(np.argmax(e > e.max() - 12))
        return d['ataque_em'] - k * 0.05, k * 0.05
    raise SystemExit(f'deixa sem tempo: {d}')


cfg = json.load(open(sys.argv[1])); out = sys.argv[2]
D = cfg['dur']
cmd = ['ffmpeg', '-v', 'error', '-y']; fl = []; k = 0
m = cfg.get('musica')
if m:
    ini = m.get('inicio_trilha', 0)
    rem = sorted(m.get('remover', []))  # [[a, b], ...] em tempo da TRILHA: encurta pausa/respiro (crossfade de 40 ms)
    cmd += ['-ss', str(ini), '-t', str(D + sum(z - y for y, z in rem) + 1), '-i', m['arquivo']]
    fo = m.get('fade_out')
    auto = ''
    if m.get('automacao'):  # [[t, dB], ...] linear entre pontos; antes do 1º = 0 dB, depois do último = último
        pts = [(0.0, 0.0)] + [tuple(p) for p in m['automacao']]
        ex = f"{10 ** (pts[-1][1] / 20):.5f}"
        for (t0, g0), (t1, g1) in reversed(list(zip(pts, pts[1:]))):
            l0, l1 = 10 ** (g0 / 20), 10 ** (g1 / 20)
            seg = f"{l0:.5f}" if t1 <= t0 else f"({l0:.5f}+({l1 - l0:.5f})*(t-{t0})/{t1 - t0:.4f})"
            ex = f"if(lt(t,{t1}),{seg},{ex})"
        auto = f",volume='{ex}':eval=frame"
    src = '[0:a]'
    if rem:
        cuts = [0.0] + [v - ini for ab in rem for v in ab] + [None]
        parts = []
        for q in range(0, len(cuts), 2):
            t0, t1 = cuts[q], cuts[q + 1]
            fl.append(f"[0:a]atrim=start={t0}" + (f":end={t1 + 0.04}" if t1 is not None else '') + f",asetpts=PTS-STARTPTS[m{q}]")
            parts.append(f'[m{q}]')
        acc = parts[0]
        for q, pt in enumerate(parts[1:]):
            fl.append(f"{acc}{pt}acrossfade=d=0.04[mx{q}]"); acc = f'[mx{q}]'
        src = acc
    fl.append(f"{src}aformat=sample_rates=48000:channel_layouts=stereo,atrim=0:{D},volume={m.get('ganho', 0)}dB{auto}" +
              (f",afade=t=out:st={fo[0]}:d={fo[1]}" if fo else '') + f"[s0]")
    k = 1
for d in cfg['sfx']:
    st, p = inicio(d)
    trim = d.get('trim', 0)
    if st < 0: trim, st = trim - st, 0.0  # começa antes do vídeo: corta o começo
    cmd += ['-ss', f'{trim:.3f}'] + (['-t', str(d['dur'])] if d.get('dur') else []) + ['-i', d['arquivo']]
    fl.append(f"[{k}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={d.get('ganho', 0)}dB,adelay={int(st * 1000)}:all=1[s{k}]")
    nome = d['arquivo'].split('/')[-1][:38]
    print(f'  {st:6.2f}s  {nome:38s}' + (f' (pico a {p:.2f}s do início)' if p is not None else ''))
    k += 1
fl.append(''.join(f'[s{i}]' for i in range(k)) + f"amix=inputs={k}:normalize=0,apad,atrim=0:{D},"
          f"afade=t=out:st={D - cfg.get('fade_out', 0.7)}:d={cfg.get('fade_out', 0.7)}[out]")
pre = out + '.pre.wav'
cmd += ['-filter_complex', ';'.join(fl), '-map', '[out]', '-c:a', 'pcm_f32le', pre]
subprocess.run(cmd, check=True)
# loudness: limitador + ganho medido, ajustado 2x (loudnorm de passada única erra até 1 dB em trecho curto com impacto)
I_, TP = cfg.get('lufs', -16), cfg.get('tp', -1.5)
lim = f"alimiter=limit={10 ** ((TP - 0.5) / 20):.4f}:attack=2:release=60:level=false"


def lufs(af):
    e = subprocess.run(['ffmpeg', '-i', pre, '-af', f'{af},ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float([l for l in e.splitlines() if l.strip().startswith('I:')][-1].split()[1])


g = I_ - lufs(lim)
for _ in range(2):
    g += I_ - lufs(f'{lim},volume={g:.2f}dB,{lim}')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', pre, '-af', f'{lim},volume={g:.2f}dB,{lim},aresample=48000', '-c:a', 'pcm_s24le', out], check=True)
os.remove(pre)

r = subprocess.run(['ffmpeg', '-i', out, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
I = [l.strip() for l in r.splitlines() if l.strip().startswith(('I:', 'Peak:'))][-2:]
print('  ' + ' | '.join(I))
e = env(load(out), 0.1)
if 'impacto' in cfg:
    t = cfg['impacto']; i = int(t * 10)
    sub = e[max(0, i - 20):i - 1].max(); hit = e[i:i + 4].max()
    print(f'  subida máx {sub:.0f} dB x impacto {hit:.0f} dB' + ('  AVISO: subida alta demais, abaixe reverse/riser' if sub >= hit - 1 else '  ok'))
print('  perfil 0,1 s:')
for j in range(0, len(e), 20):
    print(f'  {j / 10:5.1f} ' + ' '.join(f'{v:3.0f}' for v in e[j:j + 20]))
