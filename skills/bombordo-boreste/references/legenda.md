# Bombordo — reenquadramento e legenda (passe de ritmo, só o que é ouvido)

Movido do SKILL.md em 20/10/2026 (carregar sob demanda). Conteúdo preservado sem cortes.

## Reenquadramento: um recorte por plano de camera

`face_crop.py` decide **um recorte por plano de camera**, nunca por trecho
mantido. Fechar o recorte a cada `keep` foi um bug real com defeito visivel: dois
keeps do mesmo plano recebem medianas de rosto diferentes porque o falante se
mexeu, o `cropx` pula dezenas de pixels numa emenda onde a camera nunca cortou, e
o video entregue desliza de lado. A deteccao de cena tambem roda na junção entre
dois keeps, entao um corte de camera que caiu dentro do trecho descartado
continua sendo detectado.

**Regra: `cropx` so muda onde a camera corta.** A unica excecao e trocar de
falante dentro de um plano aberto, e so quando a troca cai exatamente sobre uma
emenda que ja muda quem fala. Antes de renderizar, confira que toda mudanca de
`cropx_timeline` coincide com um corte de camera.

## O passe de ritmo das legendas

Este motor e o mesmo da `podcast-reels`, e correcoes precisam ser propagadas nos
dois sentidos. O passe `ritmo()` (blocos que piscam sao esticados, pedem tempo
emprestado ao vizinho ou fundem, e **nunca** sao descartados) veio de la; o
`cropx_timeline` foi daqui para la. O codigo antigo terminava com um
`[o for o in out if o['e']-o['s']>0.18]` que apagava em silencio legendas
espremidas pelo de-overlap, sumindo com falas inteiras sem deixar rastro em
relatorio nenhum.

## Legenda so mostra o que e ouvido

O mapeamento de cue para trecho mantido exige sobreposicao **relativa**, nao um
limiar absoluto: acima de 85% do cue o texto vai inteiro; abaixo disso vao so as
palavras proporcionais ao trecho ouvido; se nao sobra nada, o atomo e descartado.
Com o limiar absoluto antigo, 0,13 s de um cue bastavam para jogar a frase
inteira na tela com o audio dela cortado fora.
