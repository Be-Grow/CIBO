#!/usr/bin/env python3
"""Gera a folha de deixas padrão (aprovada na vinheta LPA) a partir dos tempos da trilha — os mesmos
que vão no config.ts da vinheta-marca. Saída pronta para mix.py.

Uso: deixas_vinheta.py --trilha T.mp3 --inicio-trilha 20.8 --batida 0.859 --primeiro 1.5 \
       --pausa 8.5 --impacto 11.75 --dur 17 [--palavras 3] [--brilho-depois 1.6] > deixas.json
Os SFX vêm do acervo (sfx/_global + Músicas edicao); troque um caminho no JSON se o editor pedir outro som.
"""
import argparse, json

G = '/Volumes/SSD/CIBO Acervo/sfx/_global/'
M = '/Volumes/SSD/Music/Sound/Músicas edicao/'
SWOOSH = '/Volumes/SSD/Music/Projeto premiere/Copiado_Raul Lamarca/Swoosh Transition SFX 20.wav'

ap = argparse.ArgumentParser()
ap.add_argument('--trilha', required=True); ap.add_argument('--inicio-trilha', type=float, required=True)
ap.add_argument('--batida', type=float, required=True); ap.add_argument('--primeiro', type=float, required=True)
ap.add_argument('--pausa', type=float, required=True); ap.add_argument('--impacto', type=float, required=True)
ap.add_argument('--dur', type=float, default=17); ap.add_argument('--palavras', type=int, default=3)
ap.add_argument('--brilho-depois', type=float, default=2.2, help='s entre o impacto e o meio do brilho')
ap.add_argument('--lufs', type=float, default=-14)
ap.add_argument('--subida-musica', type=float, default=5, help='dB que a trilha sobe no impacto (0 = sem automação)')
a = ap.parse_args()

b = lambda n: round(a.primeiro + n * a.batida, 3)
wide = b(4)
setc = b(4 + max(a.palavras, 1))
s = []
add = lambda f, nota, **k: s.append({'arquivo': f, **k, 'nota': nota})
add(G + 'reverse-cymbal-2s.wav', 'cold open cresce até o 1º acento', fim_em=a.primeiro)
add(G + 'whoosh-reverse-1s.wav', 'puxa para o 1º corte', pico_em=a.primeiro, ganho=-4)
add(G + 'whoosh-short.wav', 'painéis entram', pico_em=a.primeiro, ganho=-3)
add(G + 'impact-soft-1.wav', 'painéis assentam', ataque_em=a.primeiro, ganho=-4)
add(G + 'whoosh-short.wav', 'troca dos painéis', pico_em=b(2), ganho=-6)
add(SWOOSH, 'tela cheia', pico_em=wide, ganho=-6)
add(G + 'impact-soft-3.wav', 'tela cheia assenta', ataque_em=wide, ganho=-6)
for k in range(1, a.palavras):
    add(G + 'whoosh-soft.wav', f'palavra {k + 1}', pico_em=b(4 + k), ganho=-10)
add(G + 'whoosh-short.wav', 'painéis de novo', pico_em=setc, ganho=-5)
add(G + 'downlifter-2s.wav', 'energia cai na pausa', em=a.pausa, ganho=-6)
sub = round(min(3.2, a.impacto - a.pausa), 2)
add(M + 'Reverse Cinematic Boom Sound effect [9qVvCEeECsA].mp3', 'subida baixa, abaixo do impacto',
    fim_em=a.impacto, trim=round(4.95 - sub, 2), dur=sub, ganho=-11)
add(G + 'riser-short-2s.wav', 'tensão final', fim_em=a.impacto, ganho=-12)
add(M + 'Cinematic Boom - sound effect - [High quality] [RNDmV_sZpUk].mp3', 'revelação da logo', ataque_em=a.impacto, ganho=3)
add(G + 'impact-soft-1.wav', 'corpo do impacto', ataque_em=a.impacto, ganho=0)
add(G + 'sweep-long.wav', 'brilho: bem baixo, senão soa como a música subindo 2 s depois da logo', pico_em=round(a.impacto + a.brilho_depois, 2), ganho=-18)

out = {'dur': a.dur, 'lufs': a.lufs, 'tp': -1.5, 'fade_out': 0.7, 'impacto': a.impacto,
       'musica': {'arquivo': a.trilha, 'inicio_trilha': a.inicio_trilha, 'ganho': -2, 'fade_out': [round(a.dur - 1.5, 2), 1.5],
                 # a trilha cai depois do impacto: sobe +5 dB junto com a logo, mix em -14 LUFS para o começo não perder força (pedido da cliente LPA, 14/10/2026)
                 'automacao': [[round(a.impacto - 0.1, 2), 0], [round(a.impacto + 0.05, 2), a.subida_musica]]},
       'sfx': s}
print(json.dumps(out, ensure_ascii=False, indent=1))
