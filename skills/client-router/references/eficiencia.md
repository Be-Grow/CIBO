# Eficiência de tokens por job

Estimativa: tokens ≈ bytes/3,6. Medidor: `scripts/carga.py` (refaça a tabela com ele depois de mexer em SKILL/referência).

## Fase 0 — linha de base (20/10/2026, antes de qualquer mudança)

Sessões reais (`custo.py` e leitura das chamadas de ferramenta):
- Andreia (`d965b52a`, 83 MB): r01–r04 ~1 600–2 000 turnos, 55 imagens e ~1,5–1,8 M tokens de saída **cada**
  (janelas sobrepostas: os reels andaram em paralelo), ~400–470 M de leitura de cache por reel. Leitura de cache é o
  custo dominante: cada turno relê o contexto inteiro, então carga fixa × turnos é a alavanca.
- Arquivos de skill mais relidos: `regras-transversais.md` (3x por sessão em Andreia, João e Bombordo), `reel-motion/SKILL.md`
  (2x), `client-registry.md` (2x), `davinci.py` (4x, 8k), `Reel.tsx` (3x, 7k), `reel.py` (15k), e SKILL de outro cliente
  (`bombordo-boreste` na sessão do João, `priscilla-daher` na da Andreia).

Carga por pedido (o que o router manda ler + skills do mapa):

| Item | tokens (bytes/3,6) |
|---|---|
| CLAUDE.md + memória | 1.4k |
| descrições de skills | 4.1k |
| client-router SKILL | 2.4k |
| regras-transversais | 7.1k |
| client-registry.md | 3.5k |
| **carga comum** | **18.5k** |

| Pedido típico | arquivos abertos além da carga comum | antes |
|---|---|---|
| 1 cliente novo (reel-motion) | reel-motion, briefing-criativo, acervo, fala-limpa, talking-head-music, lettering-motion | 37.5k |
| 2 Bombordo | bombordo-boreste, briefing-criativo, acervo, fala-limpa, talking-head-music | 33.3k |
| 3 Katia | katia, podcast-reels, briefing-criativo, fala-limpa, talking-head-music | 32.4k |
| 4 só legenda | caption-quality-gate, legenda-cruzada | 21.2k |
| 5 correção pontual (reel-motion) | reel-motion | 27.7k |

Coluna "depois" e relatório final: fase 4.

## Depois (fases 1–3, 21/10/2026; medido com `scripts/carga.py`, bytes/3,6)

| Carga | Antes | Depois | Meta |
|---|---|---|---|
| Carga comum (CLAUDE.md, memória, descrições, router, registro) | 18,5k | 9,4k | — |
| Descrições das skills | 4,1k | 1,9k | ≤2,5k ✓ |
| 1 cliente novo (reel-motion) | 37,5k | 21,7k | ≤15k de carga fixa: não atingida (falta enxugar briefing/acervo/fala-limpa) |
| 2 Bombordo | 33,3k | 18,7k | ≤22k ✓ |
| 3 Katia (inativa) | 32,4k | 20,1k | — |
| 4 só legenda | 21,2k | 12,0k | — |
| 5 correção pontual (reel-motion) | 27,7k | 12,2k | — |

O que moveu (nada apagado):
- **Fase 1:** seções dos SKILL.md foram para `references/` com índice e gatilho, o histórico datado para `historico.md` e as regras transversais viraram `regras/` + `_checklist.md`.
- **Fase 2:**
  - o DaVinci é o padrão, com exceções temporárias (Content Hub e podcast-reels genérico em MP4 até existir o adaptador; piloto Content Hub no `todo.md`);
  - as lições gerais do Resolve ficaram só em `regras/davinci.md`;
  - a receita de 10 etapas ficou só no reel-motion.
- **Fase 3:**
  - `saida_curta.py` em 19 scripts: até 15 linhas no terminal, log completo em `05_qa/logs/`; em erro, o caminho do log e 20 linhas;
  - seção "Sessão" no CLAUDE.md;
  - o symlink `mg/node_modules` saiu do git.

O que não mexi:
- Bombordo × motor-comum: as seções diferem (regras próprias do cliente) e ficam como estão até o editor decidir.
- Katia e Autismo Cast: inativos, a pedido do editor.
- malu-cortes (3,4k) e content-hub (2,7k): o resto do texto é o fluxo que todo job desses clientes lê; mover só trocaria uma leitura por outra.
- 3.2 `resolve_resumo.py`, 3.3 teto de imagens, 3.4 subagentes: ficam para depois, porque o `fila_davinci`/`qa_resolve` já terminam em linha curta e subagente não mostrou ganho medido.
