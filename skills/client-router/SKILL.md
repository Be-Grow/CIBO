---
name: client-router
description: Ponto de entrada de toda edição de vídeo do CIBO — identifica o cliente, isola identidade e assets e traz o mapa de qual skill usar em cada etapa. Use antes de qualquer outra skill de edição, com ou sem cliente citado.
---

# Client Router

O CIBO edita para vários clientes, e cada um tem um fluxo de edição diferente — mesmo quando o motor por baixo é compartilhado. Duas skills de clientes distintos podem ter nascido do mesmo código (`bombordo-boreste` e `podcast-reels` são o mesmo motor com defaults e assets próprios), mas isso não significa que os arquivos são intercambiáveis. Identidade de cliente é definida pelos assets, pela fonte, pela trilha e pelas regras editoriais daquele cliente específico, não pelo motor de render.

## Mapa de skills por etapa (use sem o usuário pedir)

| Etapa | Skill |
|---|---|
| Cliente e skill de corte | `client-router` (esta) |
| Decisões de estilo, aprovação do mapa e do piloto | `briefing-criativo` |
| Qualquer asset (burn, clique, SFX, trilha, fonte, logo, cartão, foto) | `acervo` — busque antes de perguntar; o que o editor apontar entra com `add` |
| Pastas do projeto (início e fim) | `video-project-structure` |
| Bruto do Drive **sem minutagem** (precisa transcrever para achar os trechos) | só o áudio: `yt-dlp -F <link>` (só lista) e, se houver o formato `140` (m4a só áudio), `yt-dlp -f 140 -o <proj>/01_sources/<nome>_audio.m4a <link>`; depois, os trechos de vídeo com `trecho_drive.py`. **Nunca** `ffmpeg -map 0:a` pelo proxy: o MP4 é intercalado e puxa o arquivo inteiro (17/11/2026: 1,4 GB para tirar 78 MB de áudio, editor: "era mais fácil baixar o vídeo"). Sem `140`: avise e baixe o arquivo inteiro de uma vez |
| Bruto grande no Drive (demanda com minutagem): baixar **só os trechos**, nunca o arquivo inteiro | `scripts/trecho_drive.py <link> --saida <proj>/01_sources --trecho "03=00:42:58-00:44:32" …` (proxy de Range fechado + `ffmpeg -c copy`, folga 5 s, confere áudio×vídeo; `--info` só mede) |
| Bruto longo com bastidores/retakes | `limpeza-gravacao-bruta` |
| Transcrição de aula/live longa | `transcricao-aulas` |
| Escolha dos momentos (portão, começo/fim) | `podcast-reels` → "Escolha dos momentos" + `scripts/checa_cortes.py` |
| Fala: outra voz, hesitação, palavra engolida | `fala-limpa` |
| Trilha por corte | `talking-head-music`; trilha nova (acervo → Openverse CC0/CC BY): `busca-trilha` |
| B-roll / referência em tela | `semantic-broll-validator` (sentido) + `busca-stock` (acervo → Pixabay → Pexels, folha, nota, download catalogado) |
| Cartão Seguir, título, lower third, legenda animada | `lettering-motion` (+ `anthropic-skills:motion-graphics`) |
| **Motor padrão de edição do CIBO** (fluxo da Andreia, 20/10/2026): fala/talking head de cliente novo ou sem skill própria, reel com motion em tela dividida, versão 16:9 | `reel-motion` — seção "Padrão de edição do CIBO" (10 etapas, do briefing ao QA do render); um tema `temas/<cliente>.json` por cliente; nunca copie o motor para o projeto |
| Vinheta, intro, abertura, logo animada | `vinheta-marca` (template Remotion 16:9/4K) |
| Som conduzido por música (vinheta, teaser, motion): trilha medida, cortes na batida, SFX pelo pico | `desenho-de-som` |
| Encoder e velocidade de render | `video-render-optimizer` (`VENC=auto`) |
| Qualidade criativa (gancho 3 s, tempo morto, ritmo, ênfase, final): nota 0–10 antes do render | `gancho-e-ritmo` (já roda no `reel.py revisa`/`final`; em SRT para os outros motores) |
| Legenda: pente-fino | `caption-quality-gate` |
| Legenda: retranscrição cruzada | `legenda-cruzada` |
| Checagem final do MP4 | `video-delivery-safety-check` (`podcast-reels/scripts/qa_lote.py` no lote, `audio_qa.py` no som) |
| Referência de estilo mandada pelo editor | `briefing-criativo/scripts/analisa_referencia.py` |
| Tempo exato de palavra (legenda, emendas) | `fala-limpa/scripts/alinha_mfa.py` (MFA no SSD) |
| Podcast só de áudio | `lettering-motion/scripts/audiograma.py` |
| Teste A/B de ganchos | `podcast-reels/scripts/variacoes_gancho.py` |
| Render final (padrão: no DaVinci do editor — camadas + XML, validar em projeto NOVO, sem render queimado) | `reel-motion` `scripts/fila_davinci.py` (pacote → projeto organizado → Fusion/cores → `qa_resolve`), depois do render do editor `qa_render.py`; FCP7: `bombordo-boreste/scripts/historias_xml/`; regras em `references/regras-transversais.md` → "DaVinci Resolve pela API" |
| Projeto Premiere (só sob pedido) | `podcast-reels/scripts/projeto_nle.py` |
| Entrega no Drive (com links) | `scripts/entrega_drive.py` desta skill. **Nada sobe sem o OK do editor** (trava, 23/11/2026): 1º rode sem `--aprovado` (mostra e grava o plano), mostre ao editor os arquivos e o destino e PERGUNTE; só com a resposta dele rode `--aprovado "<palavras dele>"`. Mudou arquivo ou destino, mostre de novo. Nunca reaproveite OK antigo |
| Correção do editor | Formato do editor (23/11/2026): **vídeo, minutagem, código de 3 números do elemento (está no nome do clipe no DaVinci) e o erro** → `scripts/feedback.py add --proj PASTA --reel rNN --codigo 214 --tempo 00:12 --texto "…"` (cliente, categoria e skill saem do `codigos.json`; minutagem fora do elemento = confirme o código). Sem código, `feedback.py add` normal, no mesmo turno (o padrão do erro é sugerido; confirme ou passe `--padrao`). Aviso **VIRA TRAVA** = anote em `todo.md` "Viram trava"; **A TRAVA FALHOU** = a correção é na trava. Revisão semanal: `feedback.py repetidos` |
| **Aprendizado (sempre)** | Regra em `references/aprendizado.md`: árvore de decisão (lição, tema, trava, melhoria, candidata, nada), quando criar skill nova (repetiu em 2+ jobs, nenhuma skill cobre, etapa própria, não é de cliente; tipo de vídeo = formato do reel-motion) e quando aposentar. Fim de todo job: `scripts/aprendizado.py colhe PROJ` e registre cada script/correção (`registra`). Toda semana ou quando o editor pedir revisão: `aprendizado.py revisao` (inclui o `feedback.py repetidos`). Feito com teste: `aprendizado.py feito ID` |
| Cor de fotos | `foto-evento-cor` |
| SEO / thumb do episódio / demanda ClickUp | `seo-youtube-podcast` e, **logo em seguida e sempre**, `clickup-thumb-podcast` (SEO pronto = demanda criada; nunca esperar pedido) |

## Um motor só (decisão do editor, 14/11/2026)

O destino de todo cliente ativo é o `reel-motion` com tema próprio (`temas/<cliente>.json`): conserto no motor chega a todos.
Bombordo e Content Hub migram **no próximo job real de cada um, um por sessão** (roteiro em `/Volumes/SSD/CIBO/repo/todo.md`); até lá seguem na skill
atual. Não crie skill-cópia de motor para cliente novo: tema + rubrica. Katia e Autismo Cast foram apagados (inativos; estão no histórico do git).

## Workflow

1. **Identifique o cliente antes de tocar em qualquer material.** Use o que o usuário disse, o nome do podcast/marca citado no SRT, ou o nome da pasta do projeto. Se não houver sinal claro, **pergunte ao usuário** — nunca infira o cliente pela localização física de um arquivo compartilhado (ver `references/client-registry.md`).
2. **Rode `scripts/detect_client.py "<pasta, marca ou trecho de SRT>"`**: imprime só a linha do cliente (skill, fonte, identidade, SFX, engine, fonte de verdade). Nunca leia o `references/client-registry.md` inteiro; abra-o só para editar a linha de um cliente.
3. **Leia as lições e a rubrica do cliente antes de editar**: `python3 scripts/licao.py ler <cliente>` (lições do editor,
   mais novas primeiro, e o caminho da `rubrica.md`). Lição vale mais que o padrão do motor; se uma contradiz o brief, pergunte.
4. **Rode o `briefing-criativo` antes de editar**: pergunte ao editor só as decisões artísticas e de estilo que o perfil do cliente não responde, grave `07_manifests/brief.md` e siga os pontos de aprovação (mapa de cortes, piloto).
5. **Delegue todo o trabalho à skill do cliente identificado.** Não copie fonte, logo, filmburn, SFX, `client-content-bible.md` ou convenção de capa de um cliente para o job de outro, mesmo que os arquivos estejam acessíveis no mesmo volume ou pasta compartilhada.
6. **Se o material não pertencer a nenhum cliente com skill própria:** use o motor padrão `reel-motion` (fluxo da Andreia, editor 20/10/2026: "gostaria que fosse o padrão de edição da CIBO") com um tema novo `temas/<cliente>.json` montado no briefing; `podcast-reels` só se o editor pedir aquele estilo (Cal Sans, clique, burn azul). Cliente recorrente ganha tema, rubrica e lições no motor (passo 7), nunca skill própria. Nunca force os assets/identidade de um cliente existente num material que não é dele.
7. **Cliente novo e aprendizado de estilo: quem roda é você, nunca o editor** (editor, 23/11/2026: "eu não quero que os usuários
   tenham que digitar ou rodar comandos"). Ele só conversa; você reconhece pelo contexto e roda `scripts/aprende.py` por baixo:

   | O editor diz algo como… | Você faz (sem mostrar o comando) |
   |---|---|
   | "cliente novo: Fulana", "vamos começar a editar a Fulana" (e ela não está no registro) | `aprende.py "Fulana" --novo --alias "@perfil,apelido"` e pede o material da seção 3.3 do guia, em português |
   | manda/aponta arquivo, pasta, link de perfil ou fala um gosto do cliente ("ela odeia amarelo") | `aprende.py <cliente> --de <arquivos/pasta/links/"frase">` (copia para a entrada, o original fica onde está, e analisa) |
   | "olha o projeto do DaVinci da Fulana" (um .drp ou um projeto que já está no DaVinci) | `aprende.py <cliente> --de ARQ.drp` ou `--de "davinci:Pasta/Projeto"` (lê pela API com `le_davinci.py`: camadas, títulos Text+, cortes, zoom, trilhas, SFX; devolve o projeto do editor) |
   | "olha o material da Fulana", "o que você aprendeu dela?" | `aprende.py <cliente>`; resuma a ficha em até 5 linhas, sem caminho nem nome de chave, e pergunte se aprova |
   | "aprovado", "pode aplicar", "aprovado menos as cores/legenda/fontes" | `aprende.py <cliente> --aplica [--sem theme.colors,theme.caption,theme.fonts]` e avise que o próximo vídeo é piloto |
   | "a cliente mudou a marca", "material novo da Fulana" | mesmo caminho do `--de` |
   | "minha arena é a pasta X" (a arena é SÓ a porta de entrada; o editor aponta, a CIBO não cria nem mexe nela) | `arena.py define X` (uma vez por computador) |
   | "tem demanda nova na arena", "pega a demanda da Fulana" | `arena.py lista` → confirme qual → `arena.py recebe DEMANDA [--cliente C]`: cria o projeto na organização da CIBO (`arena.py projetos`) e copia o material; daí em diante trabalhe só no projeto |

   Pedidos e proibições da ficha viram `licao.py add` no mesmo turno da aprovação. Nunca no meio de produção. Não crie skill para o
   cliente. O Drive é só para material de edição (baixar efeitos e subir o vídeo pronto): nunca crie pasta de trabalho, fila ou
   aprendizado nele. Use `video-project-structure` para auditar a organização de pastas do projeto desse cliente.
8. **A CIBO mora no SSD, numa cópia só (editor, 14/11/2026: "a cibo deve ficar no meu ssd").** O repositório é `/Volumes/SSD/CIBO/repo`
   e cada skill em `~/.claude/skills/<nome>` é só o ponteiro que o Claude Code exige para a pasta `repo/skills/<nome>`. Editou a skill = editou
   o repositório: não existe mais cópia para sincronizar. **Correção do editor só está feita depois do commit e push** no mesmo turno
   (20/10/2026: "eu pedi pra gravar lá, como não gravou"), sem levar arquivos em teste de outra sessão. Nada da CIBO no disco interno.
9. **Regras transversais (valem para todo cliente): leia só `references/regras/_checklist.md`** e abra o arquivo da fase
   atual (`regras/antes|durante|davinci|editoriais|entrega|pos-correcao.md`) quando chegar nela. Em resumo: procure a skill e o asset antes de fazer; `fala-limpa` em todo corte de fala; legenda fiel à fala e abaixo do queixo; um crop por plano de câmera; todo corte com trilha; nomes `NN - HEADLINE` e `CAPA - …`; uma versão por vídeo; transcrição sempre com tempo; não dizer que está bom sem olhar; abrir a pasta no fim; correção do usuário vira atualização da skill (e do CIBO) no mesmo turno.
10. **Antes de entregar**, confirme que nome de pasta, capa, fonte, música e legendas não vazaram identidade de outro cliente — isso vale mesmo dentro de um único job com múltiplos convidados ou formatos.
11. **Depois de cada entrega, faça UMA pergunta: "O que você mudaria?"** Só essa, sem lista de opções, uma vez por entrega.
    Grave a resposta com `python3 scripts/licao.py add <cliente> "<resposta>" --projeto <pasta> [--reel rNN]` e leve ao
    `/Volumes/SSD/CIBO/repo` no mesmo turno. "Nada" também é resposta (grave). Se a resposta for correção de skill, ela também vai para o
    `feedback.py add` e para a skill. Lição repetida em dois jobs sobe para a `rubrica.md` do cliente.
