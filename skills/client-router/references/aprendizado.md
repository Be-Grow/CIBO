# Processo de aprendizado da CIBO (23/11/2026)

Editor: "a CIBO precisa ter um processo de aprendizado muito bem definido, saber quando criar uma nova skill, quando melhorar, e
sempre ir atualizando o aprendizado". Este arquivo é a regra. Quem roda é a CIBO, por baixo; o editor só conversa.

## 1. De onde vem o aprendizado (sinais)

| Sinal | Exemplo | Quando aparece |
|---|---|---|
| Correção do editor | "comeu o final da palavra", "legenda menor" | durante o job |
| Ajuste do editor no DaVinci | `guarda_editor.py` mostra que ele encurtou a abertura | antes de refazer a timeline |
| Resposta ao "o que você mudaria?" | "capa com o rosto maior" | depois da entrega |
| Material de cliente | logo, fontes, referências, perfis | cliente novo ou marca mudou |
| Script feito no job | um recap, um efeito, um conserto que não existia | durante o job (fica na pasta do projeto) |
| Erro que a CIBO percebe sozinha | checador falhou, render quebrou, retrabalho | durante o job |

## 2. Para onde vai: a árvore de decisão

Pergunte nesta ordem; a primeira resposta "sim" decide o destino.

1. **É gosto ou proibição de UM cliente?** ("ela odeia amarelo", "capa com rosto") → **lição** do cliente: `licao.py add`.
2. **É a identidade visual de um cliente?** (logo, fonte, cor, estilo de capa/legenda) → **tema** do cliente: `aprende.py`.
3. **É erro da CIBO?** → **correção registrada** com padrão: `feedback.py add --padrao`. Na 2ª vez do mesmo padrão → **trava**
   na skill da etapa (código que barra o erro, com teste). Voltou COM trava → conserte a trava.
4. **É um jeito melhor de fazer algo que uma skill JÁ cobre?** (técnica nova, parâmetro melhor, script de job que resolve uma
   etapa existente) → **melhoria da skill** daquela etapa: SKILL.md + script + teste de regressão.
5. **É um tipo de trabalho que NENHUMA skill cobre?** (recap de evento, aula, carrossel) → **candidata** a formato ou skill.
   Registre (`aprendizado.py registra --destino candidata --tipo <nome>`) e faça no job, guardando o script.
6. **Nada disso** (caso único, acaso do material) → **nada**; não vale regra. Registre só se o editor insistir.

## 3. Quando criar uma skill nova (e quando não)

Uma candidata vira **skill nova** só quando TODAS valem:

- **Repetiu:** o mesmo tipo de trabalho apareceu em 2 jobs ou mais (de preferência de clientes diferentes);
- **Não cabe em nenhuma skill:** lida a descrição das skills, nenhuma cobre a entrada e a saída desse trabalho (se cabe, é melhoria);
- **Tem etapa própria:** entrada, saída e critério de pronto próprios, que dá para testar;
- **Não é de cliente:** cliente nunca ganha skill (é tema + rubrica + lições no motor, decisão "um motor só" de 14/11/2026).

Se é um tipo de VÍDEO que o motor padrão monta com outra estrutura (recap, aula, depoimento), vira **formato do reel-motion**, não
skill. Skill nova é para especialidade nova (ex.: SEO, relatório, foto, transcrição de aula).

Nunca: skill por cliente, cópia de motor, skill para um caso único, skill nova que repete o que outra já faz.

### Quando melhorar uma skill

- erro repetido (trava), técnica melhor, script de job que resolve uma etapa existente, ou regra que o editor deu 2 vezes;
- uma melhoria por vez, fora de produção, com teste (`tests/regressao.py` ou teste próprio) antes de commitar;
- se a skill ficou grande ou confusa para a CIBO usar certo, dividir também é melhoria (descrição clara de quando usar).

### Quando aposentar

Skill sem uso há 60 dias e sem cliente ativo, ou coberta por outra → proponha apagar (fica no histórico do git). Ex.: Katia e Autismo
Cast (apagadas em 14/11/2026).

## 4. O ritmo (sempre atualizando)

| Quando | O que a CIBO faz sozinha |
|---|---|
| No turno da correção | registra (lição, correção ou candidata) no mesmo turno; nunca edita skill no meio da produção |
| Fim de cada job | `aprendizado.py colhe PROJ`: lista os scripts criados no job e as correções do job; classifica cada um pela árvore e registra |
| Toda semana | `aprendizado.py revisao`: pauta com o que virou trava, melhorias abertas, candidatas que repetiram (vira skill/formato) e o que está velho |
| Ao aplicar | faz a mudança fora de produção, com teste, commita e marca o item como feito: `aprendizado.py feito ID` |

O registro é `references/aprendizado.jsonl` (uma linha por decisão: data, sinal, destino, skill, tipo, motivo, status). Ele anda com
o repositório, então o que a CIBO aprende numa máquina chega nas outras pelo git.
