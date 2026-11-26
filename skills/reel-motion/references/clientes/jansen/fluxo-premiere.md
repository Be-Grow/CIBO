# Jansen Automóveis: fluxo de edição lido do Premiere (26/11/2026)

Fonte: projeto do editor `21.11 CARROS.prproj` (Drive `JANSEN/NOVEMBRO/21.11/VÍDEOS/CACHE`), lido com `le_premiere.py`
(candidata #21). Sete vídeos de carro (Spin Premier, T-Cross Highline, Golf Comfortline, S10 WT, Hilux SRX Plus, Mobi Like,
Nivus Highline), 4K vertical 2160×3840 a 30 fps, 28 a 32 s cada. Brutos Sony 3840×2160 com rotação 90 (C18xx.MP4) e proxies.
Cliente ainda **não cadastrado** no registro (falta a ficha aprovada pelo editor; as artes de feed/stories são da skill
`jansen-artes-carros`).

| Camada no Premiere | O que é | No DaVinci (reel teste 26/11/2026) |
|---|---|---|
| V1 | 9–10 tomadas por carro, 2–3 s, ângulos baixos e detalhes (frente com logo e placa JANSEN, roda, lanterna, interior); metade em câmera lenta (56–95 %); Warp Stabilizer em quase todas (sequências aninhadas) | `SetSpeed({'Percentage': N})` + Optical Flow + `Stabilize()` |
| V2 | MOGRT "Spinning One": ficha do carro, uma linha por tomada, Clash Grotesk Semibold branca, caixa alta, sombra projetada. 1ª tomada = modelo (no alto), 2ª = ano e motor ("2025 - 1.8", embaixo), depois itens e km ("RODAS DE LIGA LEVE", "119 MIL KM RODADOS") | ProRes 4444 com alfa, entrada girando em 8 quadros |
| V3/V4 | Camada de ajuste de ~8 quadros em cada corte: Brilho/Contraste e Brilho de borda com 3 keyframes + Lumetri (o "flash") | clipe de flash com alfa, 9 quadros, 2 quadros antes do corte |
| V5 | Camada de ajuste do vídeo todo com Lumetri (cor) | **falta**: valores do Lumetri não lidos ainda |
| V6 | Assinatura `JANSEN_outro_4K_9x16.mp4` (~5,7 s usados de 7 s) com dissolve | mesma mídia no fim da V1 |
| A1 | `@WySFX Shutter Sound 07` em cada flash (+ `Cinematic acents`) | obturador -8 dB em cada corte |
| A2/A3 | Impactos "Cinematic acents" e trilha de corrida/drift (Pixabay: 331music, gr0za, vaitsez, tatamusic, lnplusmusic) | trilha -10 dB |

Assets: fonte no acervo (`fonte-clashgrotesk-semibold`, cliente jansen); SFX em `D:\EDIÇÃO\NOVO\@WySFX Pack SFX` (acervo, junção
EDIÇÃO); trilhas e assinatura em `Downloads` do editor (copiar para `03_assets` do job).
Projeto de referência: `D:\CIBO\Projetos\Jansen\2026-11-26 Reel teste carros` (scripts em `04_work`: `gera_camadas.py`,
`monta_resolve.py`, `acabamento_resolve.py`) e projeto "Jansen - Reel teste carros" em BeGrow/Jansen no DaVinci.
