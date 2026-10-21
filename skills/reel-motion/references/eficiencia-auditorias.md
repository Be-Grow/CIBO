# reel-motion — auditorias de eficiência e validação dos checadores

Movido do SKILL.md em 20/10/2026 (carregar sob demanda). Conteúdo preservado sem cortes.

## Eficiência (auditoria de 14/10/2026, medida na sessão da Priscilla)

A sessão dos reels 01–05 teve 1.575 turnos do agente para ~62 mensagens do editor; 529 M tokens de leitura de cache
(cada turno relê todo o contexto), 98 imagens lidas e 55 comandos só de status. O custo cresce com **turnos × contexto**,
então o que mais economiza é fazer menos turnos e não encher o contexto.
- **Status:** `scripts/status.py PROJ` responde "como tá?" num comando (etapas por reel, o que roda, pausados, órfãos, SSD).
  Não encadeie ps/tail/ls; espere a notificação do trabalho em segundo plano em vez de consultar.
- **Um comando por decisão:** encadeie as etapas que não pedem julgamento (props → mix → prévia → folhas) num comando só.
- **Imagens:** cada imagem lida fica no contexto e é relida em todo turno. Leia folha só onde há decisão visual
  (capa, painéis antes da prévia); o resto é checador: `checa_props`, `checa_takes`, `hesita.py` (ééé e repetição),
  `olhar.py`, legenda cruzada, `qa_paineis --video`.
- **Takes:** `scripts/takes.py src_large.json src_16k.wav` (só a voz dela; tentativas superadas resumidas com ~ — não esconda:
  no 05 o take bom era o "superado" 2 vezes).
- **Um trabalho pesado por vez com Whisper rodando**; renders com 2 abas (`--concurrency=2`). Máximo: 1 render + 1 câmera.
- **Câmera:** sai direto em 1080 (`out_size`; warp continua em 4K). Medido em 20 s: 407 s → 356 s, 2,55 GB → 0,36 GB,
  PSNR 47 dB / SSIM 0,992 contra o proxy antigo. Planos iguais ao job anterior: enquadramentos reaproveitados, sem face_track.
- **Robustez:** render com limite de tempo (12 s por segundo de vídeo, mín. 6 min) e 1 nova tentativa; trava por etapa
  (`work/.trava_<etapa>`) impede duas câmeras no mesmo arquivo; órfãos do motor (esbuild/Chrome com pai 1) são encerrados
  antes de cada render — dois ficaram 4 h a ~280% de CPU. Encerrar render: mate o grupo (`os.killpg`), nunca só o npm.
- **Mudou trecho (gaguejada, take trocado) depois das props:** `scripts/retempo.py segs_antigo segs_novo props.py sfx.json reel.json`
  recalcula os tempos; confira à mão o que caiu em take vindo de outro ponto da fonte (o remapeador joga para a emenda).
- **Ajuste pontual:** `trecho A B`, `capa`, `audio`, `entrega` — nunca render inteiro para mudança localizada.
- **Reel já entregue:** não regere a câmera dele (mesmo com imagem equivalente). No 05 a câmera nova tinha o zoom alguns px diferente
  nos punches (15% dos quadros < 35 dB contra a antiga, nitidez igual); um `trecho` depois emendaria duas câmeras e pularia.

- **Melhorias dos extras 06–10 (14/10/2026):**
  - `capa_cand.py FONTE folha.jpg T1 T2…` monta os candidatos de capa já no recorte de feed (rosto detectado, cabeça em
    y≈600); `--grava T rNN/capa_feed.png` grava o escolhido. Capa saiu de 3–5 turnos para 1 folha + 1 comando.
  - `checa_props.py` sugere as palavras ditas em cada vazio do painel e pega: etiqueta passando da borda direita
    (largura estimada, um pouco conservadora), abaixo de y 690 em painel invertido, abaixo de y 770 em painel normal
    (encosta na legenda) e duas etiquetas sobrepostas na mesma faixa. Pegou 4 defeitos em reels já entregues (06, 08, 09, 10).
  - Conversa livre (entrevista): voz dela a −17/−30 dB, equipe −38/−42 → `"takes_min": -34` no reel.json. Ela olha para
    quem pergunta, quase nunca para a câmera: capa com olho aberto e boca fechada aceita olhar de lado (máx. 2 folhas).
  - `hesita.py` dá falso positivo onde o texto do Whisper difere do alinhado; confirme com transcrição literal do trecho.
  - Quando o editor delega a revisão, pule a prévia: `final` direto + `qa_paineis --video <entrega>`; o que estiver
    errado sai por `trecho`. Encadeie mix → camera → final → folhas num comando por reel.
  - `checa_takes.py` também acusa corte no meio da fala (voz volta forte em até 0,35 s depois do corte): pegou o
    "marketplace" cortado e o "Depois" solto do 05; em conversa livre dá aviso nos cortes de propósito, confira cada um.
  - `checa_props.py` acusa etiqueta com palavras que ela não diz em ±8 s (o "mandioca, milho, tofu" do 05 veio de outro take).
  - **Fila de espera:** nunca `while pgrep -f "trecho"` — o próprio comando contém o texto e espera a si mesmo para sempre
    (três filas ficaram 4 h paradas, 14/10/2026). Encadeie em sequência num comando só, ou espere a trava `work/.trava_<etapa>` sumir.
  - `custo.py SESSAO.jsonl rNN` mede turnos/imagens/tokens por reel (revisão de eficiência a cada reel).
  - Encerrar o `reel.py` agora leva o render junto (o render roda em grupo próprio).

  Validado no estado antigo do 05: pegou marketplace, "Depois" solto, "seis por cen|to" e "mandioca, milho, tofu".
  O Whisper adianta o início das palavras: serve para conferir o FIM do corte, não o início.
  O aviso de olhar tem falso positivo (1:18 do 05 estava olhando a câmera): é lista para conferir numa tira, não verdade.

- Custo: o contexto por turno é o que mais pesa (844 mil/turno no fim da sessão). Um lote por sessão; o estado mora no disco
  (`status.py`, reel.json, segs.json), não na conversa.
