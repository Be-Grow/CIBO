# Correção direto na timeline do Resolve (regra do CIBO, 29/10/2026)

Editor (29/10/2026, Andreia): "a gente não tinha combinado na demanda da Fernanda que ajuste seria mais rápido na timeline e
pacotes seriam apenas componentes únicos que precisam de mudança?" — e "isso deve subir pra CIBO… o que eu quero fazer
agora em diante".

**Regra:** depois do primeiro pacote importado, correção é na timeline pela API. Nunca refaça o pacote inteiro nem crie
`rNN` novo por causa de um ajuste. Se uma camada precisa mudar (legenda de uma frase, um painel, a câmera), renderize só ela
(`--so-el`, `davinci.py` só da parte) e troque o clipe (`MediaPoolItem.ReplaceClip` ou arquivo com nome novo: arquivo
trocado no mesmo caminho fica em cache).

Kit nascido na demanda da Fernanda (IFB Black, 27/10/2026). Os scripts acham o projeto pelo próprio caminho
(`__file__.rsplit('/04_work/')`): **copie para `PROJ/04_work/` e rode de lá.** `corta_trecho`, `poe_capa` e
`organiza_pool` ainda têm nome do projeto IFB/v7 no código: revise antes de usar.

| Ajuste | Script |
|---|---|
| Tirar um trecho [A,B) de uma timeline sem render (endFrame exclusivo) | `corta_trecho.py` (usa `fx_sem_sobrepor`) |
| Emendas: fim engolido / começo cortado / respiro < 0,22 s, pelo sinal | `audita_emendas.py` → `corrige_emendas.py` |
| Trechos pelo sinal num vídeo de roteiro (silêncio ≥ 0,5 s) | `segs_sinal.py` |
| Desliga o áudio da câmera, Pan medido, sincronia | `ajusta_resolve.py`, `desliga_a1.py` |
| Faixas de áudio importadas trocadas (decide pelo conteúdo) | `faixas_audio.py` |
| "Media Offline" por zoom sobreposto à tela dividida | `fx_sem_sobrepor.py` |
| Deslocar movimentos do Fusion depois de tirar quadros | `move_fx.py` |
| Trocar SFX no projeto aberto (ReplaceClip) | `troca_pop.py` |
| Capa (1 quadro, faixa CAPA no topo, quadro 0) | `poe_capa.py`, `capa_render.py` |
| Organizar o Media Pool | `organiza_pool.py` |
| Apagar uma timeline para reimportar (último recurso) | `troca_tl.py` |

Na demanda da Andreia de 29/10, sem este kit: juntar emendas e trocar o enquadramento viraram três pacotes inteiros
(r11/r12, r13→r14), ~20 min de Resolve a mais. O jeito certo era estender os clipes nas emendas e mover burns/SFX na
timeline, e um `ReplaceClip` da câmera.
