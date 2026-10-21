# Descrições completas das skills (antes do enxugamento de 20/10/2026)
As descrições no frontmatter ficaram com ≤ 250 caracteres para baixar a carga fixa de toda sessão. O texto original de cada uma fica aqui.

## acervo

Biblioteca de assets de edição do CIBO com lugar fixo e catálogo único — film burns, cliques e SFX, trilhas, fontes, logos, overlays, cartões, avatares, LUTs e modelos. Acha qualquer asset pelo nome, tipo, cliente ou tag sem perguntar ao editor onde está, copia para o projeto registrando o uso, guarda o que o editor apontar para nunca mais perguntar, religa pelo hash o que mudou de pasta e acha duplicados. Use sempre que um job precisar de um asset (efeito, som, música, fonte, logo, cartão, foto) e sempre que o editor apontar ou mandar um arquivo de asset.

## bombordo-boreste

Crie cortes verticais 9:16 para Reels, TikTok e Shorts do podcast Bombordo e Boreste, usando o estilo, os assets e o fluxo de edição próprios deste cliente — legenda estática ou animada (kinetic typography palavra por palavra), capa com o convidado sorrindo e legenda abaixo do queixo. Use somente em trabalhos do Bombordo e Boreste.

## briefing-criativo

Antes de editar, levante com o editor as decisões artísticas e de estilo que ainda não estão definidas (objetivo, tom, gancho, legenda, capa, motion, cor, trilha, SFX, entrega), perguntando só o que está em aberto, com opções tiradas do histórico do cliente, e registre tudo num brief do projeto que guia o job. Inclui pontos de aprovação no mapa de cortes e num corte piloto antes do lote. Use no início de todo job de edição de qualquer cliente, logo depois do client-router, e sempre que o pedido não disser o estilo de algo que vai aparecer na tela ou no som.

## busca-stock

Busca B-roll de banco para um corte de fala — acervo primeiro, depois Pixabay (API) e Pexels (aba do Chrome) — com queries de cena inteira, filtro por slot (painel ou tela cheia), resolução e duração, sem repetir o que o cliente já usou, folha de quadros, nota de naturalidade e matriz semântica, relatório com top 3 por trecho e download do escolhido catalogado no acervo. Use sempre que um corte precisar de vídeo de inserção/referência em tela e a semantic-broll-validator mandar buscar.

## busca-trilha

Busca trilha de fundo para vídeos de fala — acervo primeiro, depois Openverse (só CC0 e CC BY) e Freesound (CC0, opcional) — a partir de um briefing (mood, energia, BPM, sem vocal), mede cada candidata (loudness, BPM, energia em 1–4 kHz, onde ela briga com a voz), descarta o que o cliente já usou, gera prévia de 10 s sob a voz real, sugere trecho/offset e cataloga a escolhida no acervo com o crédito. Use quando a talking-head-music precisar de trilha nova ou o acervo não tiver uma que sirva.

## caption-quality-gate

Faça um pente-fino obrigatório nas legendas de vídeos, verificando fidelidade à fala e ao contexto, português, timing, velocidade de leitura, quebras, ênfases, sobreposições e legibilidade no render. Detecta o hardware e usa o caminho mais eficiente para transcrição assistida e extração visual. Use antes do QA final de qualquer vídeo com legendas.

## clickup-thumb-podcast

Crie a demanda de thumb de um episódio de podcast (Pod Acontecer, Bombordo e Boreste, Dr. Energia etc.) direto no ClickUp, na lista ContentHub > Max > Edição, com o nome, a descrição, os responsáveis e o prazo no padrão da equipe. Use sempre logo depois de terminar o SEO de um episódio (sem esperar pedido) e quando o usuário pedir para "subir", "criar" ou "mandar" a demanda da thumb para o ClickUp.

## client-router

Ponto de entrada de todo trabalho de edição de vídeo do CIBO (cortes, reels, shorts, podcast, palestra, depoimento, produto, legenda, capa, trilha, motion, render), com ou sem cliente citado: identifica o cliente e a skill de corte, e traz o mapa de qual skill usar em cada etapa (briefing, estrutura, fala, trilha, motion, legenda, render, QA). Trata cada cliente como fluxo, estilo e assets isolados — nunca mistura fonte, logo, trilha, SFX ou capa entre clientes (Bombordo e Boreste, Content Hub, Katia, Autismo Cast, Dr. Energia, Fernanda, Malu, João Campos). Use antes de qualquer outra skill de edição.

## cortes-youtube-verificados

Baixe e recorte trechos de vídeos do YouTube com yt-dlp e FFmpeg, preservando falas completas e validando obrigatoriamente a minutagem, a correspondência com a fonte e a integridade técnica do arquivo final. Use para cortes horizontais do YouTube; não use para transformar podcasts em Reels verticais com legendas e identidade visual.

## depoimento-vertical-blur

Transforme depoimentos e talking heads horizontais de baixa resolução em vídeos 9:16 com a pessoa em um quadro vertical nítido ocupando toda a largura, blur somente acima e abaixo, legendas queimadas, capa e SRT. Use para Reels, Shorts e TikTok; não use quando o usuário quiser blur nas laterais ou reenquadramento horizontal.

## desenho-de-som

Desenhe o som de vídeos editados sobre música — mede a trilha (BPM, pausas, impactos, acentos), escolhe o trecho e o offset para o impacto cair no momento-chave, casa os cortes com a batida, escolhe SFX no acervo para cada transição e alinha cada um pelo pico (whoosh passa no corte, reverse/riser termina no corte, boom ataca no corte), mixa com a subida abaixo do impacto e normaliza. Use em vinhetas, intros, aberturas, teasers, reels de motion e qualquer edição em que trilha e SFX conduzem o ritmo; não use para trilha de fundo sob fala (isso é talking-head-music).

## fala-limpa

Audite e limpe a fala de cortes de talking head e entrevista antes do render e no QA — detecta e manda cortar outra voz (entrevistador, alguém ao fundo), hesitações ("ééé", "ahn", pausas de pensamento) e palavra final engolida pelo fade. Use em todo corte de fala de qualquer cliente (Fernanda/Malu, podcasts, depoimentos), junto com a skill de corte do cliente.

## fernanda-produto

Edite os vídeos verticais de apresentação de produto da Fernanda (linha Zeo — ZeoBody, ZeoDent etc.) gravados em câmera Sony deitada e em S-Log3, com colorização, suavização de pele, corte de bastidores e gaguejadas, zoom suave, referências do Pexels em tela dividida, burn azul, legenda no estilo Zeo, SFX nas transições e música em faixa separada. Use somente em trabalhos da Fernanda.

## foto-evento-cor

Corrija e nivele a cor de uma série de fotos (evento, palestra, corporativo) seguindo o padrão de correção de cor. O neutro de referência fica com os dois eixos certos, a pele fica na linha de tom de pele do vetorscópio (~123°), com brilho consistente entre fotos da mesma pessoa, e pretos e brancos ficam dentro do limite. Tudo é medido antes e depois, com tabela. Use quando o usuário pedir para ajustar, nivelar, igualar, deixar homogênea ou "acertar a cor" de várias fotos; não use para dar look/estilo (grading) sem antes corrigir.

## gancho-e-ritmo

Nota criativa de um reel ou corte de fala, de 0 a 10 com justificativa, em seis critérios — gancho dos 3 primeiros segundos, tempo morto (pausa de fala e tela parada), densidade de mudanças na tela, variação de ritmo, ênfase de legenda e final — num relatório curto que diz onde mexer primeiro. Roda sem render e sem modelo, a partir do props.json/segs/sfx do reel-motion ou de qualquer SRT. Bloqueia o final só abaixo do limiar do cliente. Use em todo reel antes do render (o `reel.py revisa` e o `final` já rodam), ao comparar versões de gancho e quando o editor perguntar se um corte "está prendendo".

## legenda-cruzada

Verifique a legenda queimada de um vídeo já renderizado transcrevendo o áudio final de novo com um modelo mais forte e independente, e comparando palavra a palavra. Use depois do render e antes da entrega, sempre que houver legenda na tela; especialmente com convidado de sotaque não nativo, termo técnico ou nome próprio.

## lettering-motion

Anime legendas, letterings, cards, lower thirds e CTAs. Legenda palavra a palavra fica em Pillow com curvas de easing nomeadas; grafismo desenhado que entra na tela (cartão Seguir, lower third, título de gancho, número animado, CTA) é feito em Remotion com a skill anthropic-skills:motion-graphics, com template pronto em assets/remotion-template. Use ao criar ou revisar qualquer texto/card animado em qualquer skill de corte.

## limpeza-gravacao-bruta

Encontre e remova de uma gravação bruta longa (podcast, entrevista, live, videocast) os bastidores, pausas, retakes, falhas técnicas, bip de início e os assuntos que a equipe pediu para tirar, com emendas limpas definidas pelo sinal de áudio (início real da voz, sem suspiro, com folga na última palavra) e conferidas no arquivo final. Use quando o usuário perguntar se "pediram pra pausar/cortar algo" numa gravação, pedir para "tirar os bastidores", "limpar o bruto" ou "cortar esses trechos", ou apontar emendas ruins, em qualquer cliente; não use para criar cortes verticais/Reels (isso é a skill de corte do cliente).

## malu-cortes

Edite os cortes verticais 9:16 da Malu (entrevista sobre a linha Zeo/Turi-Ita, câmera Sony em Rec.709, plano aberto com ela sentada e entrevistador fora de quadro) no padrão de Reel de marca premium de bem-estar editado por motion designer sênior — mapa de edição obrigatório, fala limpa, enquadramento por plano com rastreamento de rosto, kit de motion (título de gancho, lower third, números, callouts, cards), legenda Montserrat fina animada palavra por palavra, biblioteca de SFX curada, referências em tela dividida, tela cheia ou card, e pente-fino obrigatório antes do render. Use somente em trabalhos da Malu; o padrão da Fernanda continua na fernanda-produto e o do Bombordo na bombordo-boreste.

## podcast-reels

Turn a long podcast episode plus its SRT into vertical 9:16 Reels/TikTok/Shorts cuts with baseline-aligned Cal Sans captions, emphasis lettering, camera-click SFX, a blue film-burn intro, an eased zoom-out-with-blur opener, and a headline cover. Use when the user asks for "cortes", clips, Reels, Shorts or TikToks from a podcast, or wants captions burned into a vertical clip.

## priscilla-daher

Reels verticais da Priscilla Daher (especialista em categoria e varejo, Mercado Livre e TikTok Shop) — talking head solo com motion em Remotion e tela dividida (painel off-white em cima, ela embaixo), legenda serifada editorial, burn em toda troca de painel. Use para qualquer corte, reel, ajuste ou novo lote dela.

## reel-motion

Motor PADRÃO de edição do CIBO (aprovado no job da Andreia Francomano, 20/10/2026) — reels 9:16 e versões 16:9 de talking head com motion nascido da fala (tela dividida, painel em cima ou ao lado, tela cheia no gancho e nas viradas), legenda palavra a palavra, burn nas trocas, SFX e trilha pelo tema, capa, e entrega como pacote por camadas montado no DaVinci Resolve pela API (projeto novo organizado, movimentos de câmera no Fusion, cores por tipo, QA na timeline e no render). Configurado por tema de cliente e montado com uma biblioteca de componentes Remotion. Use em todo job de edição de fala de cliente novo ou sem skill própria, e em qualquer reel "com motion" (Priscilla, João Campos, Andreia e novos), em vez de copiar o motor para o projeto.

## relatorio-estrategia-social

Produza o relatório mensal de performance de redes sociais (Instagram, TikTok, YouTube) de um cliente e a estratégia de conteúdo do mês seguinte, com diagnóstico por plataforma, leitura cruzada e funil, calendário de pautas pronto para produção, metas e testes — entregue em PDF e com o calendário em planilha. Use quando o usuário pedir relatório de performance, análise de métricas/exports das redes, estratégia ou planejamento de conteúdo do próximo mês, ou calendário editorial baseado em dados de um cliente.

## semantic-broll-validator

Analyze, search, score, and approve B-roll for dialogue-led talking-head videos by matching the complete meaning and narrative function of a speech passage, not isolated keywords. Use when selecting, downloading, replacing, or auditing stock/reference footage, split-screen inserts, or visual examples for Reels, Shorts, ads, interviews, and business content.

## seo-youtube-podcast

Escreva o SEO de YouTube de um episódio de podcast (título, descrição com capítulos, hashtags e tags até 500 caracteres) no modelo já usado pelo cliente e casado com o gancho da thumb, e monte a thumb do episódio quando o cliente tiver template (Pod Acontecer). Use quando o usuário pedir "seo", "título/descrição/tags do YouTube", "tags de busca" ou "thumb do ep" de Pod Acontecer, Bombordo e Boreste, Autismo Cast ou outro podcast.

## talking-head-music

Select, compare, document, and mix background music for dialogue-led talking-head videos, podcast clips, Reels, Shorts, and business content. Use when music must support a speaker's emotion and cadence without reducing intelligibility; do not use for music videos or edits where the song is the primary content.

## transcricao-aulas

Transcreva, organize e resuma gravações longas de aulas, cursos, lives e mentorias (várias horas, muitos arquivos) com rapidez e pouca RAM, sempre com marcação de tempo, separando por aula/módulo/bloco, achando intervalos (café, almoço, manhã/tarde) e entregando numa estrutura pronta para subir no Drive, com sumário. Use quando o usuário pedir transcrição de curso/aula/pós/live, "onde tem intervalo/pausa", "em qual módulo essa aula se encaixa", ou organizar/renomear/juntar/dividir arquivos de aula (Andrea Francomano, Fernanda Ben/IFB e outros).

## video-delivery-safety-check

Execute o checking final obrigatório de um vídeo antes da entrega, confrontando o MP4 com o job esperado e detectando falhas técnicas, visuais, sonoras e editoriais, incluindo baixa qualidade, blur, compressão, exposição, cor, frames pretos/congelados, bitrate, capa, legendas e elementos ausentes. Use após todo render final.

## video-project-structure

Crie e audite uma estrutura fixa para projetos de edição de vídeo, separando fontes, transcrições, assets, trabalho, QA, entregas e manifestos; detecta arquivos soltos, duplicados, nomes inconsistentes e mídia proibida em pacotes de Drive. Use no início e antes do encerramento de todo projeto de vídeo.

## video-render-optimizer

Detecte CPU, GPU e encoders FFmpeg, compare CPU versus aceleração por hardware em uma amostra real e escolha o encoder e o bitrate mais eficientes sem inflar o arquivo nem degradar perceptivelmente a imagem. Use antes de renderizações de edição de vídeo em uma máquina nova ou quando hardware, FFmpeg, resolução, FPS ou perfil de entrega mudarem.

## vinheta-marca

Crie vinhetas, intros e aberturas de marca profissionais (programa, podcast, canal, palestrante) em Remotion a partir do manual de identidade, da logo e de imagens da pessoa — cold open com o nome, painéis verticais com a pessoa no ritmo da música, tela cheia com palavras da marca, linha que vira a revelação, símbolo se desenhando na pausa da trilha e logo completa no impacto, com partículas, brilho e fade. 16:9 em 1080p e 4K, master ProRes. Use quando pedirem vinheta, intro, abertura, sting de logo ou logo animada; o som é feito com a skill desenho-de-som.
