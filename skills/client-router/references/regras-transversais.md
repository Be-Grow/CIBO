# Regras transversais (valem para todo cliente)

Correções que o usuário repetiu em várias sessões e pastas diferentes. Estavam só em
memórias por pasta, que não carregam fora da pasta onde nasceram. Cada regra traz a origem.

## Antes de começar

- **Som e trilha com prévia no trecho real antes do render.** Trilha alta ou de clima errado e SFX que
  oscilam entre "falta" e "feliz demais" são as correções mais repetidas do CIBO (11 de trilha em 68, João,
  Priscilla, Andrea, LPA, Bombordo). Monte 2–3 opções de 10 s no ponto onde entram, já niveladas, e só renderize
  depois da escolha.
- **Grafia de todo nome que aparece na tela** (lower, capa, rodapé) confirmada no briefing, com a fonte
  (perfil, contrato). "Andreia" no cadastro virou "Andrea" depois de 8 renders.

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

- **Leia este arquivo inteiro antes do primeiro comando do job.** No Histórias do Porto do EP 06 (18/10/2026),
  três erros já registrados aqui se repetiram por falta de leitura: espera com `pgrep -f` travada em si mesma,
  whoosh no burn de abertura/fechamento e um clique só em vez dos dois alternados.
- **Valide o caminho difícil primeiro, pequeno, antes de produzir tudo.** No EP 06 o XML inteiro (legenda,
  painéis, trilha) foi gerado antes de testar a importação no Resolve, e cada erro custou uma volta inteira.
  Ordem certa: XML mínimo (V1 + 1 painel + 1 trilha de áudio) → importar e renderizar 1 s → só então o resto.
- **Gravação bruta longa com silêncio ou repetição: Whisper com `--condition-on-previous-text False
  --hallucination-silence-threshold 2` desde a primeira passada.** Sem isso o large-v3 entrou em loop
  ("não! não!") do minuto 3:40 até o fim e precisou de uma segunda passada de 8 min.
- **Toda espera em segundo plano tem tempo limite e sai também no erro** (`timeout 900 …`, ou o loop testa a falha e um
  contador). No EP 06 duas esperas ficaram 20 min presas checando um log de um export que já tinha falhado.
- **zsh não separa variável sem aspas**: `for x in ${=lista}` (ou um array), nunca `for x in $lista`.
- **Pergunte o que o editor quis dizer antes de investigar** quando o tempo citado não existe no vídeo
  (ex.: "3:05" num corte de 2:24 era do bruto).

## DaVinci Resolve pela API (medido no Resolve 20.2.3, EP 06, 18/10/2026)

**Projeto organizado (regra do CIBO, 20/10/2026: "os projetos que são feitos no DaVinci precisam estar sim organizados"):**
todo projeto entregue no Resolve sai arrumado, não só a timeline.
- Project Manager: pasta do cliente na árvore que o editor já usa (`BeGrow/<Cliente>/`) e projeto com o nome do job (`EP 07 - Izaac Nava`), nunca solto na raiz nem "Untitled".
- Media Pool em bins por tipo, na ordem: `01 BRUTO`, `02 VOZ`, `03 TRILHA`, `04 SFX`, `05 LEGENDA`, `06 GRAFISMOS` (painéis, títulos,
  lower, cartões), `07 BURNS`, `08 CAPAS`, `09 REFERÊNCIA` (prévias/renders de conferência) e `00 TIMELINES` com uma sub-bin por
  formato (`Episódio`, `Cortes 9x16`, `Versão 15 min`...). Nada solto na Master.
- Timelines com o nome da entrega (`NN - HEADLINE`, `EPISÓDIO - …`, `15 MIN - …`), faixas nomeadas e clipes coloridos (tabela abaixo).
- Nome de arquivo único por pacote (ver Lições da Andrea) para os bins não misturarem mídia de vídeos diferentes.
- Feito pela API (`MediaPool.AddSubFolder`, `MoveClips`, `pm.CreateFolder`); confira a árvore lendo de volta antes de dizer que está pronto.

**Cores e nomes das camadas (regra do CIBO, 19/10/2026, pedido do editor para organizar a timeline):** toda timeline
entregue no DaVinci sai com cada clipe na cor do seu tipo e cada faixa com o nome do tipo. A API não pinta a faixa,
só o clipe. Aplicar com `reel-motion/scripts/resolve_cores.py` (o `resolve_fx.py` já chama no fim).

| Tipo | Cor do clipe | Nome da faixa |
|---|---|---|
| Câmera (bruto) / áudio da câmera | Blue | CÂMERA bruto / ÁUDIO câmera (ref.) |
| Fundo desfocado, câmera renderizada de referência | Navy | CÂMERA fundo desfocado / CÂMERA renderizada (ref.) |
| Movimento: punch/zoom (clipe de ajuste com Fusion) | Orange | MOV punch/zoom (Fusion) |
| Movimento: troca de tela dividida (ajuste com Fusion) | Apricot | MOV tela dividida (Fusion) |
| Mídia / B-roll | Teal | MÍDIA / B-roll |
| Fundo do painel | Purple | PAINEL fundo |
| Partes do painel (título, itens, linha) e etapa | Violet | PAINEL partes |
| Etiquetas | Pink | ETIQUETAS |
| Títulos, gancho, tarja, palavra-chave | Yellow | TÍTULOS / gancho / tarja |
| Legenda (um bloco por frase) | Lime | LEGENDA (frase) |
| Burns | Tan | BURNS |
| Extras (cartão de marca etc.) | Beige | EXTRAS |
| Capa | Brown | CAPA |
| Voz | Green | VOZ |
| Trilha | Olive | TRILHA |
| SFX | Chocolate | SFX |

**Motor padrão = fluxo da Andreia (20/10/2026, "gostaria que fosse o padrão de edição da CIBO"):** todo job de fala segue
a receita de 10 etapas da `reel-motion` ("Padrão de edição do CIBO"): briefing com tema e grafia dos nomes → fonte (rastreio,
fps automático) → trechos e fala limpa → legenda MFA conferida → motion nascido da fala no perfil do cliente → trilha e SFX
com prévia no trecho real → prévia aprovada → `fila_davinci.py` (pacote com nomes únicos, projeto organizado, Fusion,
cores, `qa_resolve`) → `qa_render` depois do render do editor → correção só do que mudou. Cliente com skill própria
mantém estilo, assets e regras dele; o que muda é a entrega pelo mesmo pacote DaVinci.

**Nada de ffmpeg na entrega (20/10/2026, Bombordo EP 07, segunda vez que o editor cobra):** nem o episódio completo
"só com corte e fade" sai pelo ffmpeg. Todo cliente usa o fluxo DaVinci do `reel-motion` (pacote por camadas, projeto novo
organizado, Fusion nos movimentos, QA na timeline e no render). ffmpeg é só para análise, extração e prévia leve.

**Padrão do CIBO para todo cliente (18/10/2026): o render final é do editor, no DaVinci.** Entregue prévias de
conferência (baixa, rápidas) + pacote com cada camada isolada (câmera, mídia/B-roll, painéis, legenda com alfa,
títulos, cartão final, voz/trilha/SFX em WAV separados) + XML. **Não rode o render final queimado** (CRF baixo,
preset lento): ele custa o maior tempo do job e o editor refaz a cor e o acabamento no Resolve de qualquer jeito.
MP4 pronto para postar só se o editor pedir. Valide importando pela API num **projeto novo com o nome do job**
(ex.: "Growth Leaders – Reels"), nunca no projeto que ele tem aberto (no dia era o do Bombordo e Boreste), e
devolva o projeto anterior ao terminar. ("o DaVinci acaba sendo mais eficiente nessa parte", Bombordo EP 06;
"isso deveria ser na cibo mesmo, no geral", João/Growth Leaders, 18/10/2026)

A API funciona
(`DaVinciResolveScript`, ambiente em `RESOLVE_SCRIPT_API`/`RESOLVE_SCRIPT_LIB`/`PYTHONPATH`).
- **XML do FCP7 no Resolve:** clipe encaixado antes do Movimento; centro relativo ao clipe encaixado;
  `<when>` do keyframe conta do início da mídia (soma o `<in>`); áudio de MP4 numa trilha derruba a
  importação inteira (extraia WAV); cada trilha de áudio vira mono centralizada a −3 dB (voz dual-mono numa
  trilha só +3 dB; estéreo em duas com `audiopan` −1/+1). Gerador validado e detalhes: `bombordo-boreste`
  SKILL.md, seção "XML para o DaVinci". O `projeto_nle.py` antigo ainda tem esses erros.
- **Render:** chame `LoadRenderPreset('H.264 Master')` antes de `SetRenderSettings`. Uma chave inválida
  (ex.: `FrameRate`) faz o `SetRenderSettings` falhar inteiro, e uma configuração antiga presa na Deliver
  gerou MP4 só de áudio duas vezes. Confira o retorno e os streams (`ffprobe`) de todo arquivo.
- **AAC sai a 64 kb/s** e não há chave para o bitrate: renderize também um MOV com `AudioCodec: lpcm` e
  remonte o MP4 com `-c:v copy -c:a aac -b:a 256k`.
- **`SetLUT` só aceita LUT da pasta do sistema** (`/Library/Application Support/Blackmagic Design/DaVinci
  Resolve/LUT`) e precisa de `RefreshLUTList()`; aplique pelo `GetNodeGraph().SetLUT(1, nome)`. A API não
  cria Adjustment Clip.
- **Arquivo trocado no mesmo caminho fica em cache** no Media Pool: para medir de novo, use nome novo.
- **O projeto aberto é do editor:** teste num projeto próprio ("TESTE XML CIBO"), devolva o projeto que
  estava aberto ao terminar, e não reabra/renomeie timeline dele sem avisar. Corte feito pelo editor na
  timeline importada não acompanha a legenda (clipe único): refaça o corte no pipeline e reimporte.

- **Lições da Andrea (20/10/2026, 4 vídeos × 2 formatos; o editor achou os defeitos um por um na tela):**
  - Nunca edite a timeline por ciclos de exportar/importar .drt: o GlobalIn do Fusion sobe e o render falha. Edite o XML do
    backup e importe uma vez (`reel-motion/scripts/resolve_refaz_de_backup.py`).
  - Arquivo de mesmo nome em pacotes diferentes (`voz.wav`, `trilha.wav`, `sfx/*.wav`) vira um item só no Media Pool: o
    vídeo 03 tocou a voz do 01. O `davinci.py` grava todo arquivo com o sufixo do reel (`voz__r01.wav`) desde 20/10/2026;
    pacote antigo: religar com `pacote_certo()`. Gerador de outra skill (XML do Bombordo etc.) faz igual.
  - Clipe recolocado pela API entra com Scaling 0 e sem RotationAngle: copie as propriedades dos irmãos.
  - Importação de XML (EP 07, 20/10/2026): um still PNG no xmeml faz `ImportTimelineFromFile` devolver None para a timeline
    inteira. Capa fora do XML e pela API: `ImportMedia` + `AppendToTimeline` com `startFrame 0, endFrame 1` (endFrame 0 é
    recusado). PNG com número no fim do nome vira sequência de imagens; `pathurl` em NFC não casa com o disco do Mac (use NFD);
    nome igual entre cortes vira um item só. Voz medida em mono: ganho = −16 − I (LUFS).
  - **Antes de dizer "corrigido": `reel-motion/scripts/qa_resolve.py`** (offline, outro pacote, transform diferente entre
    os trechos, GlobalIn) com o render parado, e depois do render `qa_render.py PROJ` (sincronia por trecho, offline, preto),
    nos dois formatos. Conferir só o trecho mexido deixou passar o mesmo defeito na outra versão.
  - Renderize só o que mudou, na ordem que o editor precisa; não refaça os 8 por mudança num só.

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
- **Pacote DaVinci é a entrega padrão** (substitui a regra de 12/10 "só gerar se pedirem"): camadas + XML
  validados num projeto novo, render final com o editor; ver "DaVinci Resolve pela API". Premiere Pro só
  se pedirem. MP4 queimado só se pedirem (ex.: postar direto sem passar pelo Resolve).
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
- **Suba para o CIBO** (`~/CIBO`, `git@github.com:Be-Grow/CIBO.git`): copie a skill,
  confira o diff, atualize o README se a skill for nova, commit e push. Nada vai para
  `~/.codex/skills`.

- **Render no Deliver pela API (19/10/2026):** H.264 com qualidade limitada a **25.000 kb/s** (`SetRenderSettings({'VideoQuality': 25000})`),
  nunca o automático/80.000 do preset. Resolução de cada job = a da timeline. Pedido do editor (Andreia).
