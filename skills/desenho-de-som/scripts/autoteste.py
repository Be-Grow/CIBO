#!/usr/bin/env python3
"""Autoteste do desenho-de-som com áudio sintético (determinístico, sem arquivos externos).
Rode depois de mexer em analisa_trilha.py ou mix.py:  python3 autoteste.py
Trilha falsa: batida de 0,6 s (100 BPM) sobre ruído, pausa de 12 a 14,5 s e impacto forte em 14,6 s.
Confere batida, pausa, impacto, offset sugerido, alinhamento por pico/fim/ataque e a loudness da mix.
"""
import json, os, re, subprocess, sys, tempfile, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 44100
tmp = tempfile.mkdtemp(prefix='cibo_som_')
fails = []


def wav(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype('<i2').tobytes())


def check(nome, ok, info=''):
    print(('ok   ' if ok else 'FALHA') + f' {nome} {info}')
    if not ok: fails.append(nome)


rng = np.random.default_rng(7)
t = np.arange(int(SR * 20)) / SR
trilha = 0.05 * rng.standard_normal(len(t))
for b in np.arange(0, 20, 0.6):
    i = int(b * SR); n = int(0.08 * SR)
    trilha[i:i + n] += 0.6 * np.exp(-np.arange(n) / (0.015 * SR)) * np.sin(2 * np.pi * 80 * np.arange(n) / SR)
trilha[int(12 * SR):int(14.6 * SR)] *= 0.01
i = int(14.6 * SR); n = int(1.0 * SR)
trilha[i:i + n] += 0.95 * np.exp(-np.arange(n) / (0.25 * SR)) * rng.standard_normal(n)
wav(f'{tmp}/trilha.wav', trilha)

out = subprocess.run([sys.executable, f'{HERE}/analisa_trilha.py', f'{tmp}/trilha.wav', '--alvo', '10'], capture_output=True, text=True).stdout
beat = float(re.search(r'batida ([0-9.]+)s', out).group(1))
check('batida', abs(beat - 0.6) < 0.02, f'{beat:.3f}s (esperado 0,600)')
m = re.search(r'(\d+\.\d+)-\s*(\d+\.\d+)s \([0-9.]+s\)\s+->\s+impacto (\d+\.\d+)s', out)
check('pausa e impacto', bool(m) and abs(float(m.group(1)) - 12) < 0.3 and abs(float(m.group(3)) - 14.6) < 0.1,
      m.group(0) if m else 'não achou')
off = re.search(r'offset ([0-9.]+)s', out)
check('offset sugerido', bool(off) and abs(float(off.group(1)) - 4.6) < 0.1, off.group(0) if off else '')

# SFX falsos com pico/fim/ataque conhecidos
n = int(0.6 * SR); env = np.sin(np.pi * np.arange(n) / n) ** 4  # pico em 0,3 s
wav(f'{tmp}/whoosh.wav', 0.5 * env * rng.standard_normal(n))
n = int(1.0 * SR); wav(f'{tmp}/riser.wav', 0.3 * (np.arange(n) / n) ** 3 * rng.standard_normal(n))
n = int(0.8 * SR); pre = int(0.2 * SR)
boom = np.zeros(n); boom[pre:] = 0.9 * np.exp(-np.arange(n - pre) / (0.12 * SR)) * rng.standard_normal(n - pre)
wav(f'{tmp}/boom.wav', boom)
deixas = {'dur': 8, 'lufs': -16, 'tp': -1.5, 'fade_out': 0.5, 'impacto': 6.0,
          'sfx': [{'arquivo': f'{tmp}/whoosh.wav', 'pico_em': 2.0}, {'arquivo': f'{tmp}/riser.wav', 'fim_em': 6.0, 'ganho': -12},
                  {'arquivo': f'{tmp}/boom.wav', 'ataque_em': 6.0}]}
json.dump(deixas, open(f'{tmp}/d.json', 'w'))
out = subprocess.run([sys.executable, f'{HERE}/mix.py', f'{tmp}/d.json', f'{tmp}/mix.wav'], capture_output=True, text=True).stdout
st = [float(x) for x in re.findall(r'^\s+([0-9.]+)s\s', out, re.M)]
check('whoosh pelo pico', len(st) == 3 and abs(st[0] - 1.7) < 0.06, f'início {st[0] if st else "?"} (esperado 1,70)')
check('riser pelo fim', len(st) == 3 and abs(st[1] - 5.0) < 0.01, f'início {st[1] if len(st) > 1 else "?"} (esperado 5,00)')
check('boom pelo ataque', len(st) == 3 and abs(st[2] - 5.8) < 0.06, f'início {st[2] if len(st) > 2 else "?"} (esperado 5,80)')
lufs = re.search(r'I:\s+(-?[0-9.]+) LUFS', out)
check('loudness no alvo', bool(lufs) and abs(float(lufs.group(1)) + 16) < 0.6, lufs.group(0) if lufs else '')
check('subida abaixo do impacto', 'ok' in out.split('subida')[-1].split('\n')[0] if 'subida' in out else False)

# automação da trilha: ruído constante, +6 dB a partir de 3 s
wav(f'{tmp}/musica.wav', 0.05 * rng.standard_normal(int(SR * 7)))
json.dump({'dur': 6, 'lufs': -20, 'tp': -1.5, 'fade_out': 0.2, 'sfx': [],
           'musica': {'arquivo': f'{tmp}/musica.wav', 'inicio_trilha': 0, 'automacao': [[3.0, 0], [3.05, 6]]}}, open(f'{tmp}/a.json', 'w'))
subprocess.run([sys.executable, f'{HERE}/mix.py', f'{tmp}/a.json', f'{tmp}/a.wav'], capture_output=True, check=True)
with wave.open(f'{tmp}/a.wav') as w:
    raw = w.readframes(w.getnframes()); sr = w.getframerate(); ch = w.getnchannels()
y = np.frombuffer(raw, np.uint8).reshape(-1, 3)
y = (y[:, 0].astype(np.int32) | (y[:, 1].astype(np.int32) << 8) | (y[:, 2].astype(np.int32) << 16))
y = np.where(y >= 1 << 23, y - (1 << 24), y)[::ch] / float(1 << 23)
lv = lambda t0, t1: 20 * np.log10(np.sqrt((y[int(t0 * sr):int(t1 * sr)] ** 2).mean()))
dlt = lv(3.3, 5.0) - lv(1.0, 2.8)
check('automação da trilha (+6 dB em 3 s)', abs(dlt - 6) < 0.8, f'{dlt:+.1f} dB')

# remover trecho da trilha: silêncio até 3 s e ruído depois; removendo [1, 2] o ruído entra em 2 s
mus = np.zeros(int(SR * 8)); mus[int(SR * 3):] = 0.1 * rng.standard_normal(int(SR * 5))
wav(f'{tmp}/musica2.wav', mus)
json.dump({'dur': 6, 'lufs': -20, 'tp': -1.5, 'fade_out': 0.2, 'sfx': [],
           'musica': {'arquivo': f'{tmp}/musica2.wav', 'inicio_trilha': 0, 'remover': [[1.0, 2.0]]}}, open(f'{tmp}/r.json', 'w'))
subprocess.run([sys.executable, f'{HERE}/mix.py', f'{tmp}/r.json', f'{tmp}/r.wav'], capture_output=True, check=True)
with wave.open(f'{tmp}/r.wav') as w:
    raw = w.readframes(w.getnframes()); sr = w.getframerate(); ch = w.getnchannels()
y = np.frombuffer(raw, np.uint8).reshape(-1, 3)
y = (y[:, 0].astype(np.int32) | (y[:, 1].astype(np.int32) << 8) | (y[:, 2].astype(np.int32) << 16))
y = np.where(y >= 1 << 23, y - (1 << 24), y)[::ch] / float(1 << 23)
onset = np.argmax(np.abs(y) > 0.01) / sr
check('remover trecho da trilha (entra em 2,0 s)', abs(onset - 2.0) < 0.06, f'{onset:.2f}s')

print('\nTUDO OK' if not fails else f'\n{len(fails)} FALHA(S): {fails}')
sys.exit(1 if fails else 0)
