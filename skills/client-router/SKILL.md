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
| Fala: outra voz, hesitação, palavra engolida | `fala-limpa` |
| Trilha por corte | `talking-head-music` |
| B-roll / referência em tela | `semantic-broll-validator` |
| Cartão Seguir, título, lower third, legenda animada | `lettering-motion` (+ `anthropic-skills:motion-graphics`) |
| Encoder e velocidade de render | `video-render-optimizer` (`VENC=auto`) |
| Legenda: pente-fino | `caption-quality-gate` |
| Legenda: retranscrição cruzada | `legenda-cruzada` |
| Checagem final do MP4 | `video-delivery-safety-check` (`podcast-reels/scripts/qa_lote.py` no lote) |
| Cor de fotos | `foto-evento-cor` |
| SEO / thumb do episódio / demanda ClickUp | `seo-youtube-podcast`, `clickup-thumb-podcast` |

## Workflow

1. **Identifique o cliente antes de tocar em qualquer material.** Use o que o usuário disse, o nome do podcast/marca citado no SRT, ou o nome da pasta do projeto. Se não houver sinal claro, **pergunte ao usuário** — nunca infira o cliente pela localização física de um arquivo compartilhado (ex.: a trilha da Katia vem do mesmo pool de música da Content Hub/SEBRAE, mas isso não faz o job ser da Content Hub — ver `references/client-registry.md`).
2. **Consulte `references/client-registry.md`** para mapear o cliente à skill certa e às suas marcas de identidade (fonte, logo, SFX, engine de origem, fonte de verdade). Rode `scripts/detect_client.py "<texto>"` como apoio quando quiser testar um nome de pasta, marca ou trecho de SRT contra os clientes conhecidos.
3. **Rode o `briefing-criativo` antes de editar**: pergunte ao editor só as decisões artísticas e de estilo que o perfil do cliente não responde, grave `07_manifests/brief.md` e siga os pontos de aprovação (mapa de cortes, piloto).
4. **Delegue todo o trabalho à skill do cliente identificado.** Não copie fonte, logo, filmburn, SFX, `client-content-bible.md` ou convenção de capa de um cliente para o job de outro, mesmo que os arquivos estejam acessíveis no mesmo volume ou pasta compartilhada.
5. **Se o material não pertencer a nenhum cliente com skill própria:** use `podcast-reels` como fallback genérico, ou pare e pergunte ao usuário se deve nascer uma skill nova para esse cliente. Nunca force os assets/identidade de um cliente existente num material que não é dele.
6. **Ao nascer um cliente novo**, crie a skill seguindo a estrutura das demais (`SKILL.md`, `scripts/`, `references/client-content-bible.md`, `references/asset-source-catalog.md`, `assets/` com fonte/logo/SFX próprios) e adicione uma linha em `references/client-registry.md`. Use `video-project-structure` para auditar a organização de pastas do projeto desse cliente.
7. **Regras transversais (valem para todo cliente): leia `references/regras-transversais.md`.** Em resumo: procure a skill e o asset antes de fazer; `fala-limpa` em todo corte de fala; legenda fiel à fala e abaixo do queixo; um crop por plano de câmera; todo corte com trilha; nomes `NN - HEADLINE` e `CAPA - …`; uma versão por vídeo; transcrição sempre com tempo; não dizer que está bom sem olhar; abrir a pasta no fim; correção do usuário vira atualização da skill (e do CIBO) no mesmo turno.
8. **Antes de entregar**, confirme que nome de pasta, capa, fonte, música e legendas não vazaram identidade de outro cliente — isso vale mesmo dentro de um único job com múltiplos convidados ou formatos.
