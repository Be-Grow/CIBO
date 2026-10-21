---
name: busca-stock
description: Busca B-roll de banco para corte de fala — acervo, Pixabay e Pexels — com filtro por slot, nota de naturalidade, top 3 por trecho e download catalogado. Use quando um corte precisar de vídeo de inserção.
---

# busca-stock

Acha B-roll que **parece filmado de verdade e diz o que a fala diz**. O critério de sentido é da
`semantic-broll-validator` (matriz ponderada em `references/semantic-scoring.md` de lá); esta skill faz a busca,
os filtros, as folhas, as notas e o download. Vídeo de inserção só entra com aprovação do editor
(regra da `reel-motion`; o João reprovou B-roll de banco em 13/10/2026).

## Fontes e licenças (conferidas em 20/10/2026)

| Fonte | Acesso | Licença |
|---|---|---|
| acervo | `acervo.py find --sem-uso CLIENTE` | a de cada item (`license`) |
| Pixabay | API, `PIXABAY_API_KEY` | Pixabay Content License: comercial sem crédito; proibido revender sem alterar, marca/logo em produto, uso enganoso ou ofensivo com pessoa reconhecível. API: 100 pedidos/60 s, cache de 24 h obrigatório, sem download em massa, dizer a origem ao mostrar resultados |
| Pexels | aba do Chrome (emissão de chave pausada) | Pexels License: comercial sem crédito; proibido pessoa reconhecível de forma ofensiva, sugerir endosso, revender ou redistribuir em outro banco |

Fonte nova (Mixkit, Coverr…): classe em `scripts/fontes.py`, **só depois de conferir a licença** e dizer qual é ao
editor. Fonte sem licença verificável fica de fora.

Chaves: variável de ambiente ou `~/.cibo/chaves.env` (`NOME=valor`, chmod 600). Nunca em código, commit ou chat.

## Fluxo

```
PY=~/.claude/skills/busca-stock/.venv/bin/python; BS=~/.claude/skills/busca-stock/scripts/busca_stock.py
```

1. **Plano** `07_manifests/broll_plano.json`: um item por trecho (`id`, `inicio`, `fim`, `fala`, `ideia`, `slot`
   `painel`|`cheia`, 3–5 `queries`, `evitar`). Queries em inglês, cena inteira: ator + ação + lugar + função
   ("kid doing homework at kitchen table", nunca "homework"). `$PY $BS checa PLANO` aponta query curta e cena posada.
2. **Pexels** (se for usar): abra o Chrome (regra do CLAUDE.md), navegue para `https://www.pexels.com/`, rode no
   `javascript_tool` a saída de `$PY $BS pexels-js PLANO -n 8`, leia com `get_page_text` e salve em `pexels.json`.
   O retorno do `javascript_tool` corta em ~1000 caracteres: por isso o resultado vai para o corpo da página.
3. **Busca**: `$PY $BS busca PLANO 05_qa/broll --pexels pexels.json` — até 20 candidatos por trecho. Filtros:
   painel aceita horizontal 1080p; tela cheia pede vertical ≥ 1080 de largura ou horizontal 4K; duração ≥ trecho + 1 s;
   fora o que tem termo de `evitar` e o que o cliente já usou (`usos` no acervo).
4. **Quadros**: `$PY $BS quadros 05_qa/broll` — 4 quadros por candidato (das prévias pequenas), uma folha por trecho.
5. **Nota**: com `ANTHROPIC_API_KEY`, `nota DIR` manda cada folha ao `claude-haiku-5-5`. Sem chave, olhe a folha e
   grave `notas.json` (`{"t1": {"3": {"naturalidade": 8, "claim": 4, "funcao": 4, "ator": 4, "literal": 5,
   "emocao": 4, "risco": "…"}}}`), depois `nota DIR --manual notas.json`. Técnica e licença são calculadas.
   Final = 70 % semântica (0–5) + 30 % naturalidade (0–10 ÷ 2). Aprovado: semântica ≥ 4, claim ≥ 4, licença 5,
   naturalidade ≥ 7.
6. **Relatório**: `relatorio DIR --md 07_manifests/broll_candidatos.md` — top 3 por trecho, com página e risco de leitura.
   Mostre ao editor (folha + tabela) e espere a escolha.
7. **Baixa**: `baixa DIR t1 3 --proj PROJ` — arquivo grande (Pexels pela página de download, Pixabay pelo `large`),
   `acervo add` com `--meta` (fonte, id, autor, query, página, nota) e `get --client` (registra o uso e copia para
   `03_assets/broll/`). Na próxima busca do mesmo cliente ele não volta.

## Notas

- O Cloudflare do Pixabay recusa o `urllib` do Python (403): `rede.py` usa o curl, com URL e cabeçalhos pelo stdin.
- A API do Pixabay tem relevância fraca em query longa (traz trem, folhas, campo): por isso a folha + nota, nunca o
  primeiro resultado.
- A página do Pexels lista vídeos relacionados: o snippet filtra pelo id; a duração é conferida no ffprobe da prévia.
- Teste: `~/CIBO/tests/regressao.py check --engine busca-stock` (respostas simuladas com `CIBO_BUSCA_MOCK`, acervo
  isolado com `CIBO_ACERVO_CONF`).
- `scripts/rede.py` é compartilhado com a `busca-trilha`.
