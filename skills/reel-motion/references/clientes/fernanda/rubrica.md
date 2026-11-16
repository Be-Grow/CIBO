# Rubrica — Fernanda Ben, cortes de podcast do Instituto (tema `fernanda`)

Base: cortes aprovados da **Angélica Rosa** (`fernandaBen/podcastAngelica`, r01–r03, 12/11/2026) e da **Inge Weiser**
(`fernandaBen/podcastCast06`, r01–r06, 12/11/2026). Editor (16/11/2026, Podcast ELZA): "quero que os cortes sejam exatamente do
mesmo pique" desses dois e "salva essas configs na CIBO". Vale para todo podcast do Instituto (série do Carlindo no CCI 2026).

## Configuração padrão (reel.json / motion.json)

| Item | Valor |
|---|---|
| Formato | 9:16, 3 cortes por episódio quando a demanda não diz outro número |
| Motor / tema | `reel-motion`, `"tema": "fernanda"`, `"fps": 30` |
| Câmera | `"camera": "crop"` sobre o master multicâmera já cortado: um `crops` `{at, cx}` por plano, altura inteira; `"camera_davinci": true`, `"camera_fusion": true` |
| Movimento | Angélica (mais recente, referência): `punch` a cada ~6–8 s, `in` 0,5 s, segura ~3,85 s, `amount` alternando 0,10 / 0,07. Inge: `camera_cortes.py` (empurra 0,07 + fechado 0,16). Nada de zoom out |
| Motion | **nenhum painel**: `motion.json` = `{"legenda": true, "panels": [], "tail": 3.3}` ("n precisa colocar motion, cortes simples") |
| Legenda | sim, com destaque (MFA + `legenda-cruzada`) |
| Burns | **burn em cada troca de câmera/emenda** (editor 16/11/2026, Podcast ELZA: "senti falta de um burning… não entendi pq não foram adicionados nas transições"): os 4 burns da Angélica (`podcastAngelica/04_work/public/burns`, do filmburn-pack do acervo) tingidos pelo tema, opacidade 0,8, pico na troca, whoosh −12 dB 0,3 s antes. Antes do pacote: `transicoes.py` (Angélica); em timeline já mexida: `podcastElza/04_work/scripts/burns_timeline.py` |
| SFX | kit do acervo `_global` (whoosh-medium-1s, Swoosh 01/04, slide-1, whoosh-short) ~0,1 s antes de cada punch, −12/−16 dB alternando; nunca o mesmo som 3× seguidas |
| Trilha | uma diferente por corte, do acervo (`_global`): Upbeat Travel Event, Lofi Tea, Lofi Lobby, Piano Reflections, Inspiring Orchestral; escolha delegada à IA |
| Fim | ~3,3 s de imagem depois da última fala (`"tail": 3.3`), sem a voz do entrevistador (lição 12/11) |
| Capa | `"capa": {"l1", "l2", "accent", "y": 1150, "footer": "INSTITUTO FERNANDA BEN", "frame_file": "capa_src.png", "grad": "base"}`; quadro escolhido pelo editor; 1 quadro na faixa CAPA da timeline |
| Entrega | pacote DaVinci pela `fila_davinci.py`, projeto "Fernanda - Cortes Podcast <Convidado>" em `BeGrow/Fernanda`, uma timeline por corte, sem render |
| Nomes | `NN - MANCHETE EM CAIXA ALTA`, `CAPA - NN - …` |

## Reprova se
- Corte com voz do entrevistador sobreposta nas bordas (SM Gabriel 09/11) ou última palavra engolida (Cast06 r06).
- Painel/motion que ninguém pediu; trilha igual em todos os cortes; capa sem o quadro do editor.
- Afirmação de saúde forte solta (cura, porcentagem de cura) escolhida como corte.
