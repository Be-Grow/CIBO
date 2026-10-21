# Regras transversais — Regras editoriais de todo corte

- **Fala limpa** (skill `fala-limpa`): só a voz de quem fala, sem hesitação, sem palavra
  final cortada. Antes da legenda e de novo no QA.
- **Legenda fiel à fala.** Reproduza como foi dito, inclusive erro de português do
  convidado; corrija só o erro do transcritor (palavra trocada, termo técnico, nome próprio).
  (Thomas)
- **Legenda abaixo do queixo**, nunca sobre boca ou rosto. Meça o queixo ao longo do bloco
  inteiro, incluindo o auge de zoom. Se não couber, corrija o enquadramento, não a legenda.
  (Thomas, Katia, Bombordo, Malu)
- **Pente-fino de legenda com modelo grande** (`large-v3`, ou a versão 8-bit se faltar
  RAM), independente do que gerou a legenda: skill `legenda-cruzada`. Termos que o Whisper
  erra: zeólita ("ódio"), Bombordo ("Bom Bordo"), adsorve ("absorve").
- **O enquadramento só muda onde a câmera corta.** Um `cropx` por plano de câmera, nunca
  por trecho mantido. Um salto de 46 px numa emenda de áudio foi lido como "deslize".
  Prefira o quadro parado à câmera virtual que persegue o rosto. (Rodrigo, Dr. Energia)
- **Sem zoom digital além da escala nativa.** Gravação em 1080p não aguenta ampliação: o
  recorte de câmera usa a escala nativa (608×1080 para 9:16; o plano aberto entra inteiro no
  16:9) e o ken-burns do motor fica desligado (`ZOOM_AMT=0`) quando a fonte já é 1080p ou
  escura. Se o falante aparece pequeno no plano aberto, use o aberto, não um "close" ampliado.
  Rode `video-delivery-safety-check` (nitidez contra a fonte) antes de entregar. (João/Begrow:
  "a qualidade já não tá perfeita e você ainda dá esse close no João", 09/10/2026)
  Única exceção: tirar marca queimada de terceiros (logo da transmissão no rodapé) com um
  recorte até ~9% mais baixo (`crop_h` no `podcast-reels`). Nunca `delogo`/borrão ("ao invés
  de aplicar um blur estranho", João Campos, 12/10/2026).
- **Burn no final: vídeo acaba seco e o burn passa do fim, sobre preto.** Como numa timeline
  com a trilha do vídeo e a do efeito por cima, terminando depois dela. O pico do burn cai no
  último quadro do vídeo; nada de fade nem de congelar a imagem. No `podcast-reels`:
  `scripts/burn_end.py`. Vale para qualquer cliente que use burn na saída. (podLilian, 09/10/2026)
- **Saída é decisão por cliente** (editor, 20/10/2026, opção "regra por cliente"): padrão **seco**; fade só onde foi aprovado.
  reel-motion: bloco `"saida"` do tema (`{"tipo": "fade", "dur": 0.9}` em Andreia, Priscilla e João Campos; seco em Growth
  Leaders e em todo tema novo), `reel.json "saida"` sobrepõe num reel. Bombordo, Autismo Cast e Content Hub: fade de 0,42 s
  aprovado continua; `"saida": "seco"` no clipe ou `SAIDA=seco` tira o fade. Cliente novo: pergunte no briefing só se ele
  pedir fade.
- **Todo corte vertical leva trilha**, mesmo sem pedido. Biblioteca própria no SSD:
  `/Volumes/SSD/Music/Sound/Músicas edicao` e `/Volumes/SSD/Music/Projeto premiere/`
  (AMBIENTAÇÃO, IMPACTO, RISERS, HITS, ATMOSFERA, WHOOSHS). Escolha e nível pela skill
  `talking-head-music`. A biblioteca mistura faixas comerciais protegidas: para cliente,
  só o que tem direito de uso claro. (Rodrigo)
- **Render: deixe o hardware escolher.** Rode com `VENC=auto` (perfil da
  `video-render-optimizer`, testado de novo a cada 10 renders) e uma codificação só (`overlays`,
  `BURN_END_INLINE`). Nunca recodifique o MP4 entregue para pôr cartão ou burn. ("demora
  muito", 12/10/2026)
- **Ritmo e som de referência** (6 reels de criadores; `kurbaitaev/ghost-editor` e
  `kmilo93sd/agent-video-editor`, 12/10/2026): ~95% das transições são corte seco; plano médio
  de ~3 s; algo novo na tela a cada 5–7 s em Reels; SFX 0,4–0,9 a cada 10 s, nos grafismos e
  não nos cortes; zoom/punch-in só quando a fala motiva (no máximo ~3 por reel, nunca em todo
  corte); pausa entre frases de 200–300 ms em Reels. O que o cliente já aprovou vale mais que
  a referência (ex.: trilha −16 a −20 dB sob a voz no João).
- **Asset ripado do YouTube** (efeito, meme, música) serve para Instagram e TikTok, mas pode
  bloquear o vídeo por Content ID no YouTube: avise se o destino incluir YouTube.
- **Loudness por ganho fixo medido**, nunca `loudnorm` dinâmico no mix ou na voz: ele
  levanta a trilha nas pausas até ficar mais alta que a voz. (Dr. Energia)
- **Clique (SFX de ênfase): sempre os dois sons do usuário**, `/Volumes/SSD/Music/Sound/Músicas edicao/click lens.wav` e `~/CIBO/skills/fernanda-produto/assets/camera_click.mp3`, alternados. Nunca o clique sintetizado ("click ridículo", 12/10/2026). Já é o padrão do `clicks.py` da podcast-reels.
- **SFX só onde há mudança visual real** (entrada, saída e troca de referência), nunca no
  burn de abertura ou fechamento. Música e SFX em faixas separadas no arquivo editável.
  (Fernanda)
- **Zoom no vídeo**: keyframes estilo Premiere Easy Ease (cubic-bezier 0.33,0,0.67,1), sem
  mola nem overshoot, escala em espaço log, motion blur de 360°, segurar no nível do zoom.
  (Bombordo, Malu)
- **Capa**: a pessoa de frente, olhos abertos, sorriso ou boca fechada, nunca no meio da
  palavra, e pode vir de qualquer momento do episódio. Olhe a folha de contatos rotulada com
  o tempo real antes de escolher. Título e degradê só na parte de baixo, nunca sobre o
  rosto. A capa tem um frame só. (Bombordo, Katia, Dr. Energia)
  Close de rosto olhando para a câmera vence gesto: braço erguido, apontar, sorriso de pé em
  plano aberto e dedo entrando na borda foram "horríveis"; "de rosto tá ótimo". Varra a
  gravação inteira (`podcast-reels/scripts/cover_scan.py`), não pegue o primeiro quadro bom.
  (João Campos, 12/10/2026)
- **Cartão "Seguir"/@ do Instagram: a foto é a do perfil atual**, pedida ao usuário ou
  baixada do perfil, nunca um quadro do vídeo ("meteu uma foto aleatória", João Campos).
  Confira o @ no próprio Instagram.
- **Cortar bastidores**: conversa com a equipe, contagem, "deixa eu gravar outra", no começo
  e no fim. (Fernanda, Katia)

- **A voz de quem sopra a fala nunca entra** (equipe/videomaker atrás da câmera, ~15–30 dB abaixo): escolha de
  take pelo nível (`reel-motion/scripts/checa_takes.py`) antes da legenda ("isso devia ter sido cortado", 13/10/2026).
- **Corte nunca no meio da palavra nem antes de a frase acabar.** A transcrição do Whisper adianta o início
  das palavras: serve para conferir o FIM do corte, não o começo. `reel.py … revisa` junta energia + Whisper,
  gaguejada, etiquetas e olhar, e roda sozinho antes do final (pegou 4 dos 5 erros que passaram no 05 da Priscilla).
- **Gráfico e etiqueta só com o que a pessoa diz naquele trecho** ("mandioca, milho e tofu… ela não fala isso").
- **Olhada para o lado/para baixo no fim do take:** corte antes ou cubra com o burn; se ela segue falando, mantém.

- **Formato por conteúdo, não um formato para tudo**: para cada corte, pense qual formato está performando e
  serve àquele conteúdo (só legenda, motion, imagem real da marca citada como gancho de feed) e proponha com visão de
  editor ("nem tudo igual, testar outros formatos", Priscilla, 14/10/2026).
- **Trilha é opcional em conteúdo orgânico**; quando entra, nunca acima da voz e com BPM casado com o ritmo da fala.

Volta ao checklist: [`_checklist.md`](_checklist.md).
