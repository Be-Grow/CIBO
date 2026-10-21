# Regras transversais — Antes de começar

- **Som e trilha com prévia no trecho real antes do render.** Trilha alta ou de clima errado e SFX que
  oscilam entre "falta" e "feliz demais" são as correções mais repetidas do CIBO (11 de trilha em 68, João,
  Priscilla, Andrea, LPA, Bombordo). Monte 2–3 opções de 10 s no ponto onde entram, já niveladas, e só renderize
  depois da escolha.
- **Grafia de todo nome que aparece na tela** (lower, capa, rodapé) confirmada no briefing, com a fonte
  (perfil, contrato). "Andreia" no cadastro virou "Andrea" depois de 8 renders.

- **Briefing antes de editar** (`briefing-criativo`). O fluxo estava automático demais: a IA
  decidia gancho, capa, cartão, trilha e cliques sozinha e o editor só via no render. Pergunte
  o que o perfil do cliente não responde, com opções do histórico, registre o brief e peça
  aprovação no mapa de cortes e no piloto. ("a ia deveria questionar o editor para que o
  máximo de detalhes seja fornecido", 12/10/2026)
- **Antes de criar algo novo, veja `references/fontes-externas.md`**: o que já foi avaliado de
  terceiros, o que entrou e o que está pendente.
- **Procure a skill antes de fazer.** "Procura skill ao invés de tentar fazer algo que já
  tá resolvido pela skill, faça isso sempre." Rodar um script solto de dentro da pasta de uma
  skill não conta: o valor está no SKILL.md, com as convenções e as falhas conhecidas. Se
  falta uma opção, estenda a skill e avise, em vez de escrever uma versão paralela. (Dr.
  Energia; Fernanda)
- **Asset: busque no `acervo`, nunca pergunte onde está.** `acervo.py find` antes de qualquer
  outra coisa; quando o editor apontar ou mandar um arquivo, `acervo.py add` na hora, com nota
  de uso. Biblioteca fixa em `/Volumes/SSD/CIBO Acervo` ("já tive que apontar inúmeras vezes
  onde ela deveria buscar os mesmos arquivos", 12/10/2026).
- **Procure o efeito em `assets/` antes de criar.** Quando o cliente pede outra cor, tinja o
  asset (`hue=h=...`, `colorchannelmixer` em `format=gbrp`) em vez de recriar o efeito: o
  burn-in feito do zero com `geq` custou dois renders no Dr. Energia.
- **Pergunte se o usuário já tem os tempos escolhidos** antes de fazer seleção editorial de
  um bruto longo ("na vdd eu tenho tempos escolhidos"). (Malu)
- **Execute você mesmo, em primeiro plano.** Não delegue o entregável principal a um fork em
  segundo plano respondendo "te aviso quando terminar". (Bombordo)
- **Entregue o resultado antes da análise.** Rode o pedido principal primeiro (mesmo numa
  amostra de 2–3 arquivos), mostre, e só depois faça triagem e diagnóstico. (fotos CONFEA)

Volta ao checklist: [`_checklist.md`](_checklist.md).
