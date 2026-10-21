# reel-motion — fonte, legenda, recorte e RAM

Movido do SKILL.md em 20/10/2026 (carregar sob demanda). Conteúdo preservado sem cortes.

## Bruto multicâmera (episódio já editado + câmeras originais)

Quando a fonte é o episódio editado e o editor manda o bruto, a **imagem vem do bruto e o áudio continua o do episódio**
(já nivelado). Assim um corte com foco no apresentador nunca cai num plano de reação da convidada.
1. Identifique cada arquivo (quadro + duração) e os duplicados (mesmo tamanho e mesmo hash de começo/fim).
2. `acha_trechos.py EP_16k.wav sync/epXX.json rNN/segs.json … -- BRUTO1 BRUTO2` casa cada trecho no bruto (envelope 10 ms + forma de onda).
   O close da convidada casa com score ~0,98; o aberto ~0,85; trecho < 1,5 s pode dar falso positivo.
3. `aplica_mapa.py rNN/ sync/epXX.json` grava `video_map` no reel.json (trecho curto que destoa herda o offset dos vizinhos).
   Corte do convidado: monte o `video_map` à mão (pergunta do apresentador no aberto, resposta no close).
4. `reel.py PROJ rNN camera` usa o `video_map` (recorte 9:16 em `raw_cx` ou `cx` por trecho).
Também ficam aqui: `props_base.py` (props de um reel a partir das partes do corte) e `sfx_auto.py` (SFX e cliques a partir do props).

## Texto da legenda

- `edit_fix` só para palavra que o Whisper **inventou** na emenda ("porque", "E aí") ou ouviu claramente errado
  ("te porrando" → "te empurrando"). Variação de fala ("de"/"com", "tava"/"estava") fica como o modelo grande ouviu:
  no 01 do João a legenda cruzada (large-v3) derrubou duas trocas minhas.
- Correção pontual depois do render: `trecho A B` refaz só aqueles segundos.

## Recorte e qualidade

- `camera: crop` trava a altura inteira da fonte (608×1080 em 1080p). Nunca close mais apertado
  (regra transversal "sem zoom além da escala nativa"; o João reclamou em 09/10/2026).

## RAM (Mac de 16 GB)

- Um trabalho pesado por vez quando há Whisper rodando. Quadros de vídeo longo: um `ffmpeg -ss T -frames:v 1`
  por quadro, nunca `fps=1/60` decodificando o episódio inteiro.
