# Malu — biblioteca curada de SFX

Movido do SKILL.md em 20/10/2026 (carregar sob demanda). Conteúdo preservado sem cortes.

## SFX: biblioteca curada da Malu

Substitui o whoosh e o clique fixos da `fernanda-produto`. A biblioteca fica em `assets/sfx/` desta skill e é reaproveitada em todos os cortes da Malu.

- **Categorias**: whoosh suave (zoom e entrada de referência), swish curto (texto), riser (antes do gancho ou da punchline), impacto suave e grave (revelação de número), pop ou clique discreto (palavra-chave), brilho (produto) e foley ligado à imagem (água caindo no copo, pó, respiração).
- **Fontes**: Freesound (só CC0), Pixabay e Mixkit. Confira a licença de cada arquivo e registre fonte, URL e licença em `assets/sfx/licencas.csv`. Se precisar de chave de API, peça ao usuário.
- **Seleção**: baixe de 4 a 6 candidatos por categoria e filtre por análise: sem ruído de fundo, sem voz (rode o Whisper para conferir), ataque limpo, duração compatível.
- **Aprovação**: como você não consegue ouvir, monte uma audição (vídeo com cada candidato numerado na tela) para o usuário aprovar a biblioteca **uma única vez**. Só os aprovados entram em `assets/sfx/`.
- **Uso**: o pico do whoosh cai no ponto mais rápido do movimento; SFX nunca por cima de consoante da fala; nunca o mesmo arquivo duas vezes seguidas; foley só quando a imagem justifica; em média 1 SFX a cada 3 a 5 s. `sfx_db: -8` é o ponto de partida; `whoosh_post: 0.1` e `click_lead: 0.3` continuam valendo (a fala dela volta colada nos cortes).
