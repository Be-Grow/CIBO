# CIBO — edição de vídeo

Em qualquer pedido de edição de vídeo (cortes, reels, shorts, podcast, palestra, depoimento,
produto, legenda, capa, trilha, motion, render), mesmo sem cliente citado:

1. Invoque a skill `client-router` antes de tocar no material. Ela identifica o cliente e
   traz o mapa de qual skill usar em cada etapa.
2. Use a skill de cada etapa sem esperar o usuário apontar. Se nenhuma cobre, diga isso e
   proponha estender uma skill existente.
3. Gaste pouco: filtre a saída dos comandos (`grep`/`tail`), uma folha de contato por decisão,
   nunca leia a transcrição inteira (busque o trecho), QA de lote com `podcast-reels/scripts/qa_lote.py`.
