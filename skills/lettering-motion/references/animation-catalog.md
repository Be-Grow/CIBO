# Catálogo de animações e árvore de decisão

## Presets de entrada (Pillow + `easing.py`)

| Preset | `direction` | `ease` | Quando usar |
|---|---|---|---|
| `slide_up_fade` | `up` | `ease_out_cubic` | Padrão para legenda/lettering entrando por baixo, desacelerando até a posição final |
| `slide_down_fade` | `down` | `ease_out_cubic` | Headline/título entrando por cima |
| `slide_left_fade` / `slide_right_fade` | `left` / `right` | `ease_out_cubic` | Card lateral, popup de canto, comparação lado a lado |
| `pop_back` | — (sem slide, só `scale` de 0.74→1.0) | `ease_out_back` | Ênfase pontual sem deslocamento — já era o padrão antigo, continua válido quando não há necessidade de direção |
| `bounce_in` | qualquer | `ease_out_bounce` | Uso raro — CTA/gancho que precisa de energia extra; não usar em legenda corrida (cansa) |

Distância padrão: 30–50 px para legenda/lettering em 1080×1920 (proporcional ao tamanho do elemento; maior que isso lê como exagero na tela pequena de um celular). Duração padrão: 5–8 frames a 30 fps (~180–260 ms) — mais rápido que isso não dá tempo de perceber a direção, mais lento que isso atrasa a leitura.

## Combinando slide com o que já existe

`scale` (pop-in) e `entrance()` (slide+fade) não são mutuamente exclusivos: dá pra aplicar os dois na mesma tile (slide traz a posição, scale dá o peso de entrada). Mas não empilhe mais de dois efeitos no mesmo elemento — legenda que desliza, aparece, cresce e ainda balança compete com a leitura da fala, que é sempre prioridade (ver hierarquia editorial em `video-delivery-safety-check/references/final-checklist.md`).

## Árvore de decisão: Pillow × Remotion

```
É legenda corrida (bloco a bloco da fala)?
├── Sim → Pillow + easing.py, dentro do motor de legenda.
└── Não. É um grafismo que entra na tela (card, @, lower third, título, número, CTA)?
    └── Sim → Remotion (anthropic-skills:motion-graphics), template em
              assets/remotion-template, render ProRes 4444 com alpha e
              overlay numa passada separada (scripts/overlay_card.sh).
```

A versão anterior desta árvore mandava evitar Remotion ("só se virar padrão recorrente"). Virou: o motion em Pillow foi reprovado ("um pouco ruinzinha") e o pipeline Remotion já está instalado e validado neste Mac.
