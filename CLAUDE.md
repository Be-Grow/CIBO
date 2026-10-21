# CIBO — edição de vídeo

Em qualquer pedido de edição de vídeo (cortes, reels, shorts, podcast, palestra, depoimento,
produto, legenda, capa, trilha, motion, render), mesmo sem cliente citado:

1. Invoque a skill `client-router` antes de tocar no material. Ela identifica o cliente e
   traz o mapa de qual skill usar em cada etapa.
2. Use a skill de cada etapa sem esperar o usuário apontar. Se nenhuma cobre, diga isso e
   proponha estender uma skill existente.
3. Asset (burn, clique, trilha, fonte, logo, cartão): busque com a skill `acervo`
   (`acervo.py find`) em vez de perguntar onde está; o que o editor apontar, registre com `add`.
4. Tudo no SSD: em todo Bash do job, `export TMPDIR="<projeto>/04_work/tmp"`. Prévias, testes e
   renders vão para a pasta do projeto no SSD, nunca para `/tmp` ou para o scratchpad.
5. Gaste pouco: filtre a saída dos comandos (`grep`/`tail`), uma folha de contato por decisão,
   nunca leia a transcrição inteira (busque o trecho), QA de lote com `podcast-reels/scripts/qa_lote.py`.
   `feedback.jsonl` nunca é lido inteiro: só `client-router/scripts/feedback.py add` e `feedback.py resumo`.
6. Conferência no DaVinci é no preview do editor, sempre (regra geral do CIBO, 21/10/2026): monte as camadas e avise;
   não renderize nem exporte quadro pelo Resolve para conferir, e render só quando ele pedir. Capa: 1 quadro, sempre.

## Como conversar

- Tom leve e direto, em português, como colega de edição; sem jargão de programação quando não precisa.
- Decisão do editor: 2–3 opções, uma marcada como recomendada e o porquê em uma linha.
- Resumo de etapa ou entrega em até 5 linhas; detalhe só se ele pedir.
- Uma pergunta por vez. Depois de cada entrega, só "O que você mudaria?" (vai para `licoes.md` do cliente).
- Comemore sem exagero quando algo fica bom ("ficou redondo", "passou no QA"), e diga com a mesma clareza o que falhou.

## Sessão (eficiência, 21/10/2026)
- Um cliente/lote por sessão; estado no disco (`status.py`), nunca de memória. `/clear` entre jobs, `/compact` perto de 150 mil tokens.
- Não edite skills no meio de produção; anote e faça depois.
- Nunca abra `.drt`, `.fcpxml` nem `package-lock.json` no contexto; buscas com `--glob '!**/package-lock.json'`.
- Scripts do motor imprimem até 15 linhas e gravam o log completo em `05_qa/logs/` (`client-router/scripts/saida_curta.py`;
  `CIBO_VERBOSO=1` mostra tudo). Em erro: caminho do log + últimas 20 linhas; abra o log só se isso não bastar.
- Uma folha de contato por decisão; nada de prints soltos de quadro.
