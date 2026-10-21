---
name: client-router
description: Ponto de entrada de todo trabalho de edição de vídeo do CIBO (cortes, reels, shorts, podcast, palestra, depoimento, produto, legenda, capa, trilha, motion, render), com ou sem cliente citado: identifica o cliente e a skill de corte, e traz o mapa de qual skill usar em cada etapa (briefing, estrutura, fala, trilha, motion, legenda, render, QA). Trata cada cliente como fluxo, estilo e assets isolados — nunca mistura fonte, logo, trilha, SFX ou capa entre clientes (Bombordo e Boreste, Content Hub, Katia, Autismo Cast, Dr. Energia, Fernanda, Malu, João Campos). Use antes de qualquer outra skill de edição.
---

# Client Router

O CIBO edita para vários clientes, e cada um tem um fluxo de edição diferente — mesmo quando o motor por baixo é compartilhado. Duas skills de clientes distintos podem ter nascido do mesmo código (`bombordo-boreste`, `autismo-cast` e `podcast-reels` são o mesmo motor com defaults e assets próprios; `katia` é um fork de `podcast-reels`), mas isso não significa que os arquivos são intercambiáveis. Identidade de cliente é definida pelos assets, pela fonte, pela trilha e pelas regras editoriais daquele cliente específico, não pelo motor de render.

## Mapa de skills por etapa (use sem o usuário pedir)

| Etapa | Skill |
|---|---|
| Cliente e skill de corte | `client-router` (esta) |
| Decisões de estilo, aprovação do mapa e do piloto | `briefing-criativo` |
| Qualquer asset (burn, clique, SFX, trilha, fonte, logo, cartão, foto) | `acervo` — busque antes de perguntar; o que o editor apontar entra com `add` |
| Pastas do projeto (início e fim) | `video-project-structure` |
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
| Entrega no Drive (com links) | `scripts/entrega_drive.py` desta skill — simula sem `--confirmo`; confirme o destino |
| Correção do editor | `scripts/feedback.py add` no mesmo turno em que a skill é corrigida; `resumo` mostra onde investir |
| Cor de fotos | `foto-evento-cor` |
| SEO / thumb do episódio / demanda ClickUp | `seo-youtube-podcast` e, **logo em seguida e sempre**, `clickup-thumb-podcast` (SEO pronto = demanda criada; nunca esperar pedido) |

## Workflow

1. **Identifique o cliente antes de tocar em qualquer material.** Use o que o usuário disse, o nome do podcast/marca citado no SRT, ou o nome da pasta do projeto. Se não houver sinal claro, **pergunte ao usuário** — nunca infira o cliente pela localização física de um arquivo compartilhado (ex.: a trilha da Katia vem do mesmo pool de música da Content Hub/SEBRAE, mas isso não faz o job ser da Content Hub — ver `references/client-registry.md`).
2. **Consulte `references/client-registry.md`** para mapear o cliente à skill certa e às suas marcas de identidade (fonte, logo, SFX, engine de origem, fonte de verdade). Rode `scripts/detect_client.py "<texto>"` como apoio quando quiser testar um nome de pasta, marca ou trecho de SRT contra os clientes conhecidos.
3. **Rode o `briefing-criativo` antes de editar**: pergunte ao editor só as decisões artísticas e de estilo que o perfil do cliente não responde, grave `07_manifests/brief.md` e siga os pontos de aprovação (mapa de cortes, piloto).
4. **Delegue todo o trabalho à skill do cliente identificado.** Não copie fonte, logo, filmburn, SFX, `client-content-bible.md` ou convenção de capa de um cliente para o job de outro, mesmo que os arquivos estejam acessíveis no mesmo volume ou pasta compartilhada.
5. **Se o material não pertencer a nenhum cliente com skill própria:** use o motor padrão `reel-motion` (fluxo da Andreia, editor 20/10/2026: "gostaria que fosse o padrão de edição da CIBO") com um tema novo `temas/<cliente>.json` montado no briefing; `podcast-reels` só se o editor pedir aquele estilo (Cal Sans, clique, burn azul). Cliente recorrente ganha skill própria (passo 6) que usa o motor por baixo. Nunca force os assets/identidade de um cliente existente num material que não é dele.
6. **Ao nascer um cliente novo**, crie a skill seguindo a estrutura das demais (`SKILL.md`, `scripts/`, `references/client-content-bible.md`, `references/asset-source-catalog.md`, `assets/` com fonte/logo/SFX próprios) e adicione uma linha em `references/client-registry.md`. Use `video-project-structure` para auditar a organização de pastas do projeto desse cliente.
7. **Correção do editor só está feita depois do commit e push no `~/CIBO`** (20/10/2026: "eu pedi pra gravar lá, como não
   gravou"). Editar só `~/.claude/skills` não basta: copie para `~/CIBO/skills`, confira o diff, commit e push no mesmo turno,
   sem levar arquivos em teste de outra sessão.
8. **Regras transversais (valem para todo cliente): leia `references/regras-transversais.md`.** Em resumo: procure a skill e o asset antes de fazer; `fala-limpa` em todo corte de fala; legenda fiel à fala e abaixo do queixo; um crop por plano de câmera; todo corte com trilha; nomes `NN - HEADLINE` e `CAPA - …`; uma versão por vídeo; transcrição sempre com tempo; não dizer que está bom sem olhar; abrir a pasta no fim; correção do usuário vira atualização da skill (e do CIBO) no mesmo turno.
9. **Antes de entregar**, confirme que nome de pasta, capa, fonte, música e legendas não vazaram identidade de outro cliente — isso vale mesmo dentro de um único job com múltiplos convidados ou formatos.
