# Regras transversais — Durante o job

- **Toda correção do editor vai para o registro** (`client-router/scripts/feedback.py add
  --cliente --categoria --texto --acao`), além de virar atualização de skill. `feedback.py
  resumo` mostra onde o CIBO mais erra.
- **Mudança em motor de corte só sobe para o CIBO com `~/CIBO/tests/regressao.py check`
  passando.** Diferença intencional: grave de novo com `record` e explique no commit.

- **Economia de tokens** (fluxo longo de várias edições precisa ser sustentável, 12/10/2026):
  saída de comando sempre filtrada (`grep`/`tail`, plano de legendas só com `PLAN_VERBOSE=1`);
  uma folha de contato pequena (≤ 2000 px de largura) por decisão, nunca quadro a quadro;
  transcrição longa nunca lida inteira, só o trecho buscado; QA de lote numa chamada
  (`qa_lote.py`); nada de reler arquivo que acabou de ser escrito. Um projeto por sessão:
  ao trocar de projeto, comece sessão nova (o contexto do anterior só custa).

- **Baixe e transcreva só a minutagem pedida**, com ~10 s de folga de cada lado, nunca o
  episódio inteiro; um Whisper grande por vez ("pra ser mais econômico... transcreve só essa
  minutagem", LPA e Você, 12/10/2026).
- **Temporários no SSD**, na pasta do projeto, nunca no disco de sistema (vive perto de
  100 %). Detalhes e o `taskpolicy` para encode em background: `video-render-optimizer`.
- **No máximo 2–3 ffmpeg em paralelo sobre 4K**, e um Whisper grande por vez: o Mac tem
  16 GB. Se o DaVinci estiver exportando, `nice` e modelo menor. Folha de contato de vídeo longo:
  um `ffmpeg -ss T -frames:v 1` por quadro, nunca `fps=1/60` decodificando o episódio inteiro com o
  Whisper rodando ("cuidado com a ram", 13/10/2026). Chrome só aberto enquanto a extensão é usada.
- **Dê progresso e tempo restante sem ser perguntado** em tarefa longa. "E aí", "falta
  quanto" e "tá editando mesmo?" são sinal de silêncio longo demais.
- **Pode instalar a biblioteca certa** em vez de improvisar ("não precisa fazer gambiarra").

- **Fila de etapas com `reel-motion/scripts/lote.py`**, nunca `while pgrep -f "…"`: o texto procurado está no
  próprio comando, e a fila esperou a si mesma por 4 h (Priscilla, 14/10/2026). Render com limite de tempo e
  grupo de processos; antes de renderizar, mate os órfãos (esbuild/Chrome com pai 1).
- **Uma sessão por lote, com o estado em disco** (`status.py`, `reel.json`, `segs.json`): na sessão da Priscilla
  os turnos por reel caíram 5× depois da 1ª auditoria, mas o contexto por turno subiu de 357 mil para 844 mil
  tokens e comeu o ganho.
- **Ajuste pontual só no trecho apontado** (render parcial ou só o áudio), nunca o vídeo inteiro de novo; e não
  regere a câmera de um reel entregue para um ajuste (a nova sai com outro zoom).
- **Não apague temporários de um job em andamento** sem o editor liberar: servem para o CIBO aprender com a demanda.

- **Leia este arquivo inteiro antes do primeiro comando do job.** No Histórias do Porto do EP 06 (18/10/2026),
  três erros já registrados aqui se repetiram por falta de leitura: espera com `pgrep -f` travada em si mesma,
  whoosh no burn de abertura/fechamento e um clique só em vez dos dois alternados.
- **Valide o caminho difícil primeiro, pequeno, antes de produzir tudo.** No EP 06 o XML inteiro (legenda,
  painéis, trilha) foi gerado antes de testar a importação no Resolve, e cada erro custou uma volta inteira.
  Ordem certa: XML mínimo (V1 + 1 painel + 1 trilha de áudio) → importar e renderizar 1 s → só então o resto.
- **Gravação bruta longa com silêncio ou repetição: Whisper com `--condition-on-previous-text False
  --hallucination-silence-threshold 2` desde a primeira passada.** Sem isso o large-v3 entrou em loop
  ("não! não!") do minuto 3:40 até o fim e precisou de uma segunda passada de 8 min.
- **Toda espera em segundo plano tem tempo limite e sai também no erro** (`timeout 900 …`, ou o loop testa a falha e um
  contador). No EP 06 duas esperas ficaram 20 min presas checando um log de um export que já tinha falhado.
- **zsh não separa variável sem aspas**: `for x in ${=lista}` (ou um array), nunca `for x in $lista`.
- **Pergunte o que o editor quis dizer antes de investigar** quando o tempo citado não existe no vídeo
  (ex.: "3:05" num corte de 2:24 era do bruto).

Volta ao checklist: [`_checklist.md`](_checklist.md).
