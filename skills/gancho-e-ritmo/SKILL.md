---
name: gancho-e-ritmo
description: Nota criativa 0–10 com justificativa (gancho 3 s, tempo morto, densidade, variação, ênfase, final) a partir do props/SRT, sem render. Use em todo reel antes do render e ao comparar ganchos.
---

# Gancho e ritmo

Checagem de **qualidade criativa** (as outras checagens do CIBO são técnicas). É uma pré-seleção legível que o editor pode
derrubar, não um juiz: a nota aponta onde olhar, e o olho do editor decide.

## Uso

```bash
# reel-motion (já roda dentro de `reel.py PROJ rNN revisa` e `final`)
python3 scripts/gancho_ritmo.py --props public/rNN/props.json --segs rNN/segs.json --reel rNN/reel.json \
        --tema ~/.claude/skills/reel-motion/temas/<cliente>.json [--json rNN/work/gancho_ritmo.json]
# qualquer corte com SRT (podcast-reels, bombordo, katia…): só fala, legenda e final
python3 scripts/gancho_ritmo.py --srt corte.srt --dur 62.4 [--tema …]
```

Saída: uma linha por critério (nota + motivo com tempo), a média ponderada e os dois critérios para mexer primeiro.
Código 2 = abaixo do limiar. No `reel.py final` isso **para** o render; o editor libera com `GANCHO_OK=1` (decisão dele).

## Critérios

| Critério | O que mede | Perde nota quando |
|---|---|---|
| gancho 3 s | primeira palavra, palavras nos 3 s, tipo (pergunta, número, contraste, história, afirmação), tela muda, título de gancho | começa depois de 0,4 s, abre com muleta ("então", "é", "olha"), nada muda na tela, nenhuma frase fecha em 6 s |
| tempo morto | pausas de fala > 0,6 s e o maior trecho sem mudança na tela | pausa > 1 s, tela parada além de `max_parado` |
| densidade | mudanças de tela por 10 s (emendas, layout, burn, painel, item, palavra-chave, movimento de câmera) | fora de `alvo_eventos_10s` |
| variação | desvio dos intervalos entre mudanças (CV) e fala/s por bloco; movimentos de câmera iguais seguidos | CV < 0,3 (mecânico), > 40 % dos blocos fora de ±35 % da fala, > 3 movimentos iguais seguidos |
| ênfase | fração de palavras em destaque; destaque em palavra vazia isolada; bloco inteiro destacado | fora da faixa `enfase` |
| final | última palavra, ponto final, cauda depois da fala | termina em conectivo ("e", "porque"), sem ponto, cauda < 0,25 s (palavra engolida) ou > 2,5 s |

Pesos padrão: gancho 2, tempo morto 1,5, final 1,5, demais 1. Critério sem dado (ex.: variação num SRT curto) não entra na média.

## Por cliente (tema)

```json
"qualidade": {"limiar": 6, "alvo_eventos_10s": [1.5, 4], "max_parado": 6, "enfase": [0.08, 0.28], "pesos": {"gancho": 2}}
```

Calibre pelo último piloto aprovado: os aprovados têm que passar com folga. A rubrica de cada cliente (gancho, ritmo,
legibilidade, identidade: o que foi aprovado e o que reprova) fica em `<skill do cliente>/references/rubrica.md` ou, para
cliente só com tema, em `reel-motion/references/clientes/<cliente>/rubrica.md`. Leia a rubrica junto com o relatório: a nota
mede o ritmo; a rubrica diz o que é certo para aquele cliente.
Andreia (20/10/2026): r01–r04 deram 8,3–9,4; ênfase aprovada chega a 34 %, então o tema dela usa `enfase` [0.1, 0.35].

## Ao ler o relatório

- Mexa só nos dois critérios apontados; não reedite o que tirou ≥ 8.
- Gancho baixo: troque o começo (`podcast-reels` → "Escolha dos momentos", `variacoes_gancho.py`), não invente texto.
- Tela parada longa: um item de painel, palavra-chave ou punch no meio (veja `reel-motion` "variação"), nunca SFX solto.
- Final baixo: confira com `fala-limpa` se a palavra final foi engolida antes de mexer no corte.

Fontes das ideias (só ideias; supoclip é AGPL): `client-router/references/fontes-externas.md`, rodada de 20/10/2026.
