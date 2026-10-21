# Bombordo — chamada do episódio

Movido do SKILL.md em 20/10/2026 (carregar sob demanda). Conteúdo preservado sem cortes.

## Chamada do episódio (`scripts/chamada.py`)

O pilar "Episódio da semana" da estratégia pede um corte de chamada: frase mais forte do convidado
nos 3 primeiros segundos, **nome do convidado na tela**, corte no auge e "o resto está no episódio".
Depois do `render` da legenda animada do corte escolhido:

```bash
python3 scripts/chamada.py "<corte>.mp4" --nome "ARTHUR NETO" --sub "Sócio da Alphamar Agência Marítima" \
    --logo <logo_podcast.png> --lt 6.6 10.6 --y 300
```

`--lt` = entrada/saída do nome (logo depois da frase de impacto); `--y` = topo do nome, fora da faixa
da legenda (`cap_cy` ± 210) e do rosto. Guarde antes uma cópia limpa do corte: o script reescreve o
arquivo (uma passada de vídeo, card final de 2,5 s com "Episódio completo: Bombordo e Boreste no YouTube").
Aprovado no EP 04 (Ayrton) e usado no EP 05 (Arthur).
