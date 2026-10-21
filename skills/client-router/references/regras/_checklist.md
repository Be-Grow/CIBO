# Checklist das regras transversais (todo cliente)

Leia só este arquivo no começo do job; abra a fase atual quando chegar nela. Detalhe, exemplo e origem estão no link.

**Regra geral do CIBO (21/10/2026):** conferência no DaVinci é no preview do editor, sempre: sem render e sem exportar quadro pelo Resolve para conferir; render só quando ele pedir. Capa com 1 quadro, sempre. Detalhe em [davinci.md](davinci.md).

**Antes** — [antes.md](antes.md)
- Briefing antes de editar; grafia de todo nome que vai para a tela confirmada.
- Procure skill, asset (`acervo`, nunca pergunte onde está), efeito em `assets/` e `fontes-externas.md` antes de criar.
- Pergunte se o editor já tem os tempos escolhidos; som e trilha com prévia no trecho real antes do render.
- Execute você mesmo, em primeiro plano; entregue o resultado antes da análise.
- Correção do editor vai para o registro (`feedback.py add`); motor só sobe ao CIBO com `tests/regressao.py check`.
**Durante** — [durante.md](durante.md)
- Economia de tokens: baixe/transcreva só a minutagem pedida; uma sessão por lote, estado em disco; `lote.py` para filas.
- Temporários no SSD (`TMPDIR`), nunca apague os de job em andamento; no máximo 2–3 ffmpeg 4K em paralelo.
- Progresso e tempo restante sem ser perguntado; pode instalar a biblioteca certa.
- Ajuste pontual só no trecho apontado; valide o caminho difícil primeiro, pequeno.
- Bruto longo com silêncio/repetição: Whisper com `--condition-on-previous-text False`.
- Toda espera em segundo plano tem tempo limite e sai no erro; zsh: variável sempre entre aspas.
- Pergunte o que o editor quis dizer antes de investigar.
**DaVinci** — [davinci.md](davinci.md)
- **Vai pro Resolve pela API (`fila_davinci.py`) sem perguntar; prévia e aprovação do piloto também no Resolve, nunca prévia longa no Remotion.** Abra `davinci.md` inteiro antes do pacote: as lições da Andreia valem para todo cliente (João 21/10/2026: "eu preciso ficar te ensinando novamente").
- Pacote DaVinci é o padrão (exceções temporárias em MP4, sem adaptador job.json→pacote: Content Hub, podcast-reels genérico; Katia e Autismo inativos); projeto NOVO para validar.
- XML do FCP7, render pela API, AAC 64 kb/s, `SetLUT` só da pasta do sistema, arquivo trocado no mesmo caminho fica em cache;
  render no Deliver H.264 limitado a 25.000 kb/s.
- Lições da Andrea: FPS da fonte, nome único por pacote, nunca encadear ciclos de .drt, bins e cores.
**Editoriais** — [editoriais.md](editoriais.md)
- Fala limpa (`fala-limpa`); a voz de quem sopra a fala nunca entra; corte nunca no meio da palavra nem da frase.
- Legenda fiel à fala, abaixo do queixo, pente-fino com modelo grande.
- Enquadramento só muda onde a câmera corta; sem zoom digital além da escala nativa; zoom em Easy Ease, sem mola nem overshoot.
- Saída por cliente (padrão seco; burn no final passa do fim sobre preto).
- Todo corte vertical leva trilha (orgânico pode ir sem); loudness por ganho fixo medido; ritmo e som de referência.
- Clique: os dois sons do usuário; SFX só onde há mudança visual real; asset ripado do YouTube: avise se o destino incluir YouTube (Content ID).
- Gráfico e etiqueta só com o que a pessoa diz naquele trecho; formato por conteúdo, não um para tudo.
- Olhada para o lado no fim do take: corte antes ou cubra com o burn; corte os bastidores.
- Capa (grid 3:4 do feed) e cartão Seguir com a foto atual do perfil.
- Render: deixe o hardware escolher (`VENC=auto`).
**Entrega** — [entrega.md](entrega.md)
- Nomes `NN - HEADLINE` e `CAPA - …`; pastas legíveis de relance; uma versão por vídeo.
- Transcrição sempre com tempo; não diga que está bom antes de olhar; abra a pasta no Finder ao terminar.
**Depois de uma correção** — [pos-correcao.md](pos-correcao.md)
- A lição vai para a skill no mesmo turno; causa no motor = conserte o motor; código compartilhado entra como opção por chave e o outro cliente sai idêntico.
- Suba para o CIBO (commit e push) no mesmo turno.
