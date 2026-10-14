---
name: desenho-de-som
description: Desenhe o som de vídeos editados sobre música — mede a trilha (BPM, pausas, impactos, acentos), escolhe o trecho e o offset para o impacto cair no momento-chave, casa os cortes com a batida, escolhe SFX no acervo para cada transição e alinha cada um pelo pico (whoosh passa no corte, reverse/riser termina no corte, boom ataca no corte), mixa com a subida abaixo do impacto e normaliza. Use em vinhetas, intros, aberturas, teasers, reels de motion e qualquer edição em que trilha e SFX conduzem o ritmo; não use para trilha de fundo sob fala (isso é talking-head-music).
---

# Desenho de som

Aprovado pelo editor na vinheta LPA (13/10/2026): "o motion e a escolha do SFX junto com a música
ficou muito bom". A v1 (6 s, só SFX) foi reprovada por falta de música marcante e de SFX.
Caso completo: `references/deixas_vinheta_lpa.json`.

## Fluxo

1. **Trilha marcante, medida antes de editar.** Busque no acervo (`acervo.py find epic`, `trailer`,
   `cinematic`, `inspiring`) e meça 2–3 candidatas:
   `python3 scripts/analisa_trilha.py TRILHA --alvo <segundo do momento-chave>`
   Prefira a que tem **pausa longa (≥ 2 s) seguida de impacto**: a pausa vira o suspense e o impacto, a revelação.
   O script devolve o offset (`inicio_trilha`) e onde cai o 1º acento. Trilhas medidas: `references/trilhas.md`.
2. **Grade de batidas.** Corte = batida (`1º acento + n × batida`). Troca de plano a cada 2 batidas, palavra
   ou cartão a cada batida, mudança de bloco a cada 4. Passe esses tempos para o motion (ex.: `vinheta-marca/config.ts`).
3. **Um SFX por evento visual, nunca em todo corte de fala:**
   | Evento | SFX (acervo `sfx/_global`) | Alinhamento |
   |---|---|---|
   | cold open → 1º corte | `reverse-cymbal-2s` + `whoosh-reverse-1s` | `fim_em` / `pico_em` no corte |
   | painel/cartão entrando | `whoosh-short` + `impact-soft-1` baixo | `pico_em` / `ataque_em` |
   | troca de plano | `whoosh-short` (-6 dB) | `pico_em` |
   | mudança de bloco (tela cheia) | `Swoosh Transition SFX 20` + `impact-soft-3` | `pico_em` / `ataque_em` |
   | palavra/título na tela | `whoosh-soft` (-10 dB) | `pico_em` |
   | energia cai (pausa da música) | `downlifter-2s` | `em` no início da pausa |
   | suspense até a revelação | `Reverse Cinematic Boom` (-11 dB) + `riser-short-2s` (-12 dB) | `fim_em` no impacto |
   | revelação (logo/CTA) | `Cinematic Boom` (+3 dB) + `impact-soft-1` | `ataque_em` no impacto |
   | brilho/shine | `sweep-long` (**-18 dB**: mais alto soa como "a música subindo" 2 s depois da logo) | `pico_em` no meio do brilho |
4. **Folha de deixas JSON → mix.** Vinheta no padrão aprovado: gere as deixas direto dos tempos (os mesmos do `config.ts`):
   `python3 scripts/deixas_vinheta.py --trilha T --inicio-trilha 20.8 --batida 0.859 --primeiro 1.5 --pausa 8.5 --impacto 11.75 --dur 17 > deixas.json`
   (reproduz a mix aprovada da LPA com correlação de 0,97). Outros formatos: escreva o JSON à mão a partir da tabela acima.
   Depois: `python3 scripts/mix.py deixas.json som.wav`. O script mede o pico de cada SFX e
   o posiciona sozinho; normaliza (padrão -16 LUFS no mix.py, -14 nas deixas de vinheta; -1,5 dBTP; limitador + ganho medido, bate o alvo com ±0,2 dB) e imprime o perfil a cada 0,1 s.
5. **A subida fica abaixo do impacto.** Com `"impacto"` no JSON o script compara; se aparecer AVISO, abaixe
   reverse/riser (na LPA: boom reverso de -4 → -11 dB, riser -8 → -12, boom +3). Impacto no máximo, ~6 dB acima da subida.
6. **A trilha tem que crescer JUNTO com a revelação, não depois.** Muita trilha de trailer cai para um trecho mais
   baixo logo após o impacto. Meça a trilha sozinha depois do impacto; se ela cair, use `"automacao": [[impacto-0.1, 0], [impacto+0.05, 5]]`
   na música (+5 dB a partir da logo), comece o fade final da música só no último 1,5 s e mixe em **-14 LUFS**, para o começo não perder
   força com a normalização. Confira o perfil por segundo antes x depois: o começo ±2 dB, o pós-impacto +4 dB ou mais.
   (Cliente LPA, 14/10/2026: "a música demora a aumentar quando a logo aparece; deveria aumentar em 12 s, não em 13 s".)
7. Mux com o vídeo (`-c:a aac -b:a 320k` no MP4, `pcm_s24le` no master ProRes). Não diga que o som está bom
   sem medir: perfil + LUFS são a prova; peça ao editor para ouvir.

## Regras

- Música sem copyright (Infraction, Shamaluev, KeysofMoon...): confira a licença no nome/descrição.
- SFX alinhado pelo **pico** (whoosh), pelo **fim** (reverse, riser) ou pelo **ataque** (boom, impacto), nunca pelo início do arquivo.
- Não empilhe dois sons longos no mesmo papel: um reverse + um riser baixo bastam.
- A música começa no cold open baixa (o trecho antes do 1º acento) e o fade final dura 2,4 s até o fim do vídeo.
- Registre no acervo (`acervo.py add`) toda trilha ou SFX novo que o editor aprovar, e anote as medições em `references/trilhas.md`.

## Autoteste

`python3 scripts/autoteste.py` (áudio sintético; ~20 s). Rode depois de mexer em `analisa_trilha.py` ou `mix.py`;
confere batida, pausa, impacto, offset, alinhamento por pico/fim/ataque, loudness e subida x impacto.
