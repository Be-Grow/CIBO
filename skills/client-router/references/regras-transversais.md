# Regras transversais (valem para todo cliente)

Correções que o usuário repetiu em várias sessões e pastas diferentes. Estavam só em
memórias por pasta, que não carregam fora da pasta onde nasceram. Cada regra traz a origem.

## Antes de começar

- **Briefing antes de editar** (`briefing-criativo`). O fluxo estava automático demais: a IA
  decidia gancho, capa, cartão, trilha e cliques sozinha e o editor só via no render. Pergunte
  o que o perfil do cliente não responde, com opções do histórico, registre o brief e peça
  aprovação no mapa de cortes e no piloto. ("a ia deveria questionar o editor para que o
  máximo de detalhes seja fornecido", 12/10/2026)
- **Antes de criar algo novo, veja `references/fontes-externas.md`**: o que já foi avaliado de
  terceiros, o que entrou e o que está pendente.
- **Procure a skill antes de fazer.** "Procura skill ao invés de tentar fazer algo que já
  tá resolvido pela skill, faça isso sempre." Rodar um script solto de dentro da pasta de uma
  skill não conta: o valor está no SKILL.md, com as convenções e as falhas conhecidas. Se
  falta uma opção, estenda a skill e avise, em vez de escrever uma versão paralela. (Dr.
  Energia; Fernanda)
- **Asset: busque no `acervo`, nunca pergunte onde está.** `acervo.py find` antes de qualquer
  outra coisa; quando o editor apontar ou mandar um arquivo, `acervo.py add` na hora, com nota
  de uso. Biblioteca fixa em `/Volumes/SSD/CIBO Acervo` ("já tive que apontar inúmeras vezes
  onde ela deveria buscar os mesmos arquivos", 12/10/2026).
- **Procure o efeito em `assets/` antes de criar.** Quando o cliente pede outra cor, tinja o
  asset (`hue=h=...`, `colorchannelmixer` em `format=gbrp`) em vez de recriar o efeito: o
  burn-in feito do zero com `geq` custou dois renders no Dr. Energia.
- **Pergunte se o usuário já tem os tempos escolhidos** antes de fazer seleção editorial de
  um bruto longo ("na vdd eu tenho tempos escolhidos"). (Malu)
- **Execute você mesmo, em primeiro plano.** Não delegue o entregável principal a um fork em
  segundo plano respondendo "te aviso quando terminar". (Bombordo)
- **Entregue o resultado antes da análise.** Rode o pedido principal primeiro (mesmo numa
  amostra de 2–3 arquivos), mostre, e só depois faça triagem e diagnóstico. (fotos CONFEA)

## Durante o job

- **Toda correção do editor vai para o registro** (`client-router/scripts/feedback.py add
  --cliente --categoria --texto --acao`), além de virar atualização de skill. `feedback.py
  resumo` mostra onde o CIBO mais erra.
- **Mudança em motor de corte só sobe para o CIBO com `~/CIBO/tests/regressao.py check`
  passando.** Diferença intencional: grave de novo com `record` e explique no commit.

- **Economia de tokens** (fluxo longo de várias edições precisa ser sustentável, 12/10/2026):
  saída de comando sempre filtrada (`grep`/`tail`, plano de legendas só com `PLAN_VERBOSE=1`);
  uma folha de contato pequena (≤ 2000 px de largura) por decisão, nunca quadro a quadro;
  transcrição longa nunca lida inteira, só o trecho buscado; QA de lote numa chamada
  (`qa_lote.py`); nada de reler arquivo que acabou de ser escrito. Um projeto por sessão:
  ao trocar de projeto, comece sessão nova (o contexto do anterior só custa).

- **Baixe e transcreva só a minutagem pedida**, com ~10 s de folga de cada lado, nunca o
  episódio inteiro; um Whisper grande por vez ("pra ser mais econômico... transcreve só essa
  minutagem", LPA e Você, 12/10/2026).
- **Temporários no SSD**, na pasta do projeto, nunca no disco de sistema (vive perto de
  100 %). Detalhes e o `taskpolicy` para encode em background: `video-render-optimizer`.
- **No máximo 2–3 ffmpeg em paralelo sobre 4K**, e um Whisper grande por vez: o Mac tem
  16 GB. Se o DaVinci estiver exportando, `nice` e modelo menor. Folha de contato de vídeo longo:
  um `ffmpeg -ss T -frames:v 1` por quadro, nunca `fps=1/60` decodificando o episódio inteiro com o
  Whisper rodando ("cuidado com a ram", 13/10/2026). Chrome só aberto enquanto a extensão é usada.
- **Dê progresso e tempo restante sem ser perguntado** em tarefa longa. "E aí", "falta
  quanto" e "tá editando mesmo?" são sinal de silêncio longo demais.
- **Pode instalar a biblioteca certa** em vez de improvisar ("não precisa fazer gambiarra").

- **Fila de etapas com `reel-motion/scripts/lote.py`**, nunca `while pgrep -f "…"`: o texto procurado está no
  próprio comando, e a fila esperou a si mesma por 4 h (Priscilla, 14/10/2026). Render com limite de tempo e
  grupo de processos; antes de renderizar, mate os órfãos (esbuild/Chrome com pai 1).
- **Uma sessão por lote, com o estado em disco** (`status.py`, `reel.json`, `segs.json`): na sessão da Priscilla
  os turnos por reel caíram 5× depois da 1ª auditoria, mas o contexto por turno subiu de 357 mil para 844 mil
  tokens e comeu o ganho.
- **Ajuste pontual só no trecho apontado** (render parcial ou só o áudio), nunca o vídeo inteiro de novo; e não
  regere a câmera de um reel entregue para um ajuste (a nova sai com outro zoom).
- **Não apague temporários de um job em andamento** sem o editor liberar: servem para o CIBO aprender com a demanda.

## Regras editoriais de todo corte

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
- **Todo corte vertical leva trilha**, mesmo sem pedido. Biblioteca própria no SSD:
  `/Volumes/SSD/Music/Sound/Músicas edicao` e `/Volumes/SSD/Music/Projeto premiere/`
  (AMBIENTAÇÃO, IMPACTO, RISERS, HITS, ATMOSFERA, WHOOSHS). Escolha e nível pela skill
  `talking-head-music`. A biblioteca mistura faixas comerciais protegidas: para cliente,
  só o que tem direito de uso claro. (Rodrigo)
- **Render: deixe o hardware escolher.** Rode com `VENC=auto` (perfil da
  `video-render-optimizer`, testado de novo a cada 10 renders) e uma codificação só (`overlays`,
  `BURN_END_INLINE`). Nunca recodifique o MP4 entregue para pôr cartão ou burn. ("demora
  muito", 12/10/2026)
- **Projeto editável: sempre oferecer, só gerar se pedirem.** Na entrega, pergunte se o editor
  quer o projeto para Premiere Pro e/ou DaVinci Resolve (`podcast-reels/scripts/projeto_nle.py`:
  XML do Final Cut 7 que os dois importam, com trechos, reenquadramento, burn, grafismos, voz,
  trilha, cliques, marcadores e `.srt`). ("só deve gerar caso o editor peça, mas sempre deve ser
  fornecida a opção", 12/10/2026)
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

## Entrega

- **Nomes**: `NN - HEADLINE.mp4`, com acentos, numerados pela ordem da fala no episódio, e
  `CAPA - NN - HEADLINE.png` (prefixo, para as capas ficarem agrupadas no Finder). Nunca
  `corte01.mp4`. Troque `"` por `'`.
- **Pastas que ele lê de relance**: poucos níveis, nomes em português (`CORTES/Cortes ep1`),
  sem taxonomia numerada nem manifesto que ele não pediu. Nenhum arquivo temporário na
  árvore final. Rode `video-project-structure` no início e no fim, mas o nome das pastas de
  entrega segue esta regra.
- **Uma versão por vídeo** na pasta de entrega: sobrescreva ao refazer. Nada de v1/v2/final
  acumulando, salvo quando o usuário pedir uma pasta nova (ex.: "v2, sem sobrescrever").
- **Transcrição sempre com tempo** (`[hh:mm:ss - hh:mm:ss] texto` + SRT). Sem tempo, ele
  considera inútil. Skill `transcricao-aulas` para aulas e gravações longas.
- **Não diga que está bom antes de olhar.** O portão automático é piso: rode
  `caption-quality-gate`, `legenda-cruzada` e `video-delivery-safety-check`, olhe as contact
  sheets e **meça de novo depois de cada correção**, porque a correção costuma criar um
  defeito novo. O que não dá para verificar (ouvido, ritmo), diga que não verificou.
- **Abra a pasta no Finder ao terminar** (`open "<pasta>"`). Ele pediu isso em quase toda
  sessão.

- **Capa pensada para o grid do feed (3:4):** título fora do rosto, pessoa mais baixa no quadro, olhos abertos e
  boca fechada, escolhida olhando a imagem (`reel-motion/scripts/capa_cand.py` faz a folha com o recorte pronto).
  A capa nova vai também no quadro 0 do vídeo.

## Depois de uma correção do usuário

- **A lição vai para a skill no mesmo turno**, não só para a memória: SKILL.md, bíblia do
  cliente, script ou checagem automática. Se a falha passou pelo QA, acrescente a checagem
  que faltou ao portão. Diga qual skill mudou.
- **Se a causa está no motor da skill, conserte o motor** (e procure o mesmo defeito no lote
  todo), não só os arquivos do job.
- **Código compartilhado entre clientes** (motor da Fernanda usado pela Malu; `face_crop.py`
  do Bombordo usado pelo Dr. Energia): mudança entra como opção por chave no job, e o outro
  cliente precisa sair idêntico (`framemd5` num trecho de 5 s, ou checksum da pasta).
- **Suba para o CIBO** (`~/CIBO`, `git@github.com:BrunoLucio191/CIBO.git`): copie a skill,
  confira o diff, atualize o README se a skill for nova, commit e push. Nada vai para
  `~/.codex/skills`.
