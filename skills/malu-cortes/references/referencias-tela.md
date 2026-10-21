# Malu — referências em tela

Movido do SKILL.md em 20/10/2026 (carregar sob demanda). Conteúdo preservado sem cortes.

## Referências

- Busque no **Pexels, Pixabay e Mixkit**, sempre em inglês e com descritores visuais: *close up, slow motion, macro, soft natural light, shallow depth of field*.
- Baixe de 5 a 8 candidatos por trecho, monte uma folha de contatos com 3 frames de cada e dê nota (`semantic-broll-validator`) para: relação com a fala, estética cinematográfica, cor compatível com o estúdio (quente e suave), recorte 9:16 e movimento dentro do plano.
- **Recuse**: cara de banco de imagem (gente sorrindo para a câmera, fundo branco), marca d'água, texto na imagem, imagem escura ou estourada, baixa resolução.
- Literal para coisas concretas, metáfora visual para ideias abstratas.
- **Inserts do próprio master em 4K**: só quando o recorte for grande (o copo na mão, as mãos). O card com os pacotes Turi-Ita da estante foi reprovado (região pequena, fica mole).
- Aplique o tratamento de cor e o grão do kit de motion e conforme para 29,97 fps.
- Tela dividida: `ref_push: 0.06` (push lento no painel), `shift: 1150`.
- **Entrega em Full HD** (1080×1920, ~12 Mb/s: `out_size: [1080, 1920]`, `vbitrate: "12M"`), não em 4K. O processamento interno continua em 4K; o usuário pediu "exporta em fullhd somente" quando o render 4K demorou.
- **Resolução decide o layout**: tela cheia só com fonte 4K (1080p ampliaria 3,6× no 4K); 1080p e 720p vão em tela dividida ou card. O Mixkit gratuito tem muito vídeo só em 720p.
- Na tela cheia a legenda ganha faixa escura em degradê atrás (automática na camada): o dourado some sobre stock claro.
