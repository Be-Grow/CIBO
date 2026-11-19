# CIBO — a fazer

Pendências de 12/10/2026 (detalhes em `skills/client-router/references/fontes-externas.md`).

- [ ] **Migrar Bombordo, Autismo Cast e Content Hub para o motor único** (`podcast-reels` + perfil),
      um cliente por sessão. Levar os recursos próprios como opções: `impact_pulses`, `long_moves`,
      `punch`, saída com fade/preto/SFX (decidido 20/10/2026: saída por cliente, padrão seco; ver regras-transversais),
      mixagem própria, legenda cinética, chamada (Bombordo); letterings e B-roll (Content Hub).
      Proteção: `tests/regressao.py check` antes de cada push.
- [ ] **Confirmar a importação do projeto editável** no Premiere Pro e no DaVinci Resolve
      (`joãoCortes/05_qa/projetos_teste`); ajustar keyframes/modo Tela se vierem errados.
- [ ] **Legenda "diálogo"** (duas pessoas, lados opostos) e **"epígrafe"** no `render_caps`.
- [ ] **Costuras por velocidade** (zoom-through, rack-focus) — reelmimic `cut-the-curve`.
- [ ] **Triagem de takes por visão** para gravações com vários takes (Katia) — Fagan1024/smart-video-editor.

- [ ] **Adaptador `job.json` → pacote DaVinci** para os motores de podcast (Content Hub, podcast-reels genérico), hoje em
      "padrão atual: MP4" (exceção temporária, decisão do editor 20/10/2026). Katia e Autismo Cast ficam fora: o editor
      disse que não são clientes ativos.
      Cliente piloto: **Content Hub** (cliente ativo com mais entrega em ffmpeg: lotes SEBRAE, render próprio).
      Escopo estimado. O adaptador lê do `job.json` `srcdir`, `work` e `outdir`; por clipe, lê `src`, `keeps` (emendas),
      `cropx`/`cropx_timeline`/`cropy`/`cropy_steps`/`zoom_steps`, `impact_pulses`/`long_moves` (movimento), `caps`,
      `caption_base_y`, `letterings`, `click_times`, `music`/`mix`, `broll`, `grade`, `filmburn`, `saida`, `cover_t`
      e `headline`.
      Gera, no formato do `davinci.py` e com sufixo do clipe:
      - voz e trilha em WAV, separadas;
      - legenda e letterings como PNG/ProRes 4444 com alfa;
      - burn e clique como faixas próprias;
      - crop e zoom como transform/keyframe na timeline (FCP7 XML);
      - capa PNG.
      Em seguida, `fila_davinci.py`/`resolve_render.py` montam o projeto, e `qa_resolve.py` + `qa_render.py` conferem.
      Estimativa: 1 script novo (~300 linhas) + 1 sessão de piloto com o editor. Migrar um cliente por sessão, com
      `tests/regressao.py check`, e perguntar ao editor antes de trocar o padrão.

- [ ] reel-motion `so_capa` falha calado com `camera_davinci` (sem `camera.mov`) e a `fila_davinci` segue sem capa (Andreia 29/10/2026). Usar o quadro do bruto (`frame_file`) quando não houver camera.mov e parar a fila se a capa falhar.
- [ ] reel-motion: `zoom` com bruto horizontal em timeline vertical escala 1,78× a mais (scaleToFit do Resolve). Corrigir `davinci.py transf()` ou compor o vertical antes automaticamente (Andreia/Vanessa 29/10/2026).
- [ ] Generalizar o kit `reel-motion/scripts/timeline/` (tirar IFB/v7 de corta_trecho, poe_capa, organiza_pool; receber PROJ por argumento em vez de copiar para 04_work).
- [ ] **`status.py` acusar render quebrado** (lição joao "ep 26", 04/11/2026): marcar reel sem MP4 em `06_deliverables`,
      `.mov`/`.mp4` com menos de 1 MB e `04_work/_bundle/rNN` que sobrou. O r05 e o r06 ficaram sem entrega sem alerta.

## Anotado no YT 01 da Priscilla (09/11/2026) — corrigir depois do job
- reel-motion `e_davinci`: renderiza a camada inteira `legenda` mesmo com `captions: []` (vídeo sem legenda = ProRes 4444 vazio de 8 min). Pular quando não há legenda. Contornei com um MOV de 1 quadro no lugar.
- reel-motion `mix.py`: trilha não faz loop; vídeo longo (YouTube) precisa de trilha longa. Fiz à mão com acrossfade (`y01/trilha_lofi-tea_longa.wav`).
- Fonte = timeline do editor: criar `le_timeline.py` (lê V1 pela API → segs.json) e detector de retakes por frase (o "bruto limpo" tinha 42 grupos de retake).
- Bordas: régua relativa ao nível da voz + perfil em volta do corte; o MFA em janela curta dá alarme falso.

## Colheita de 14/11/2026 (antes de apagar a mídia do SSD) — por ordem de quantas vezes o editor cobrou

Material bruto: `colheita/2026-11-14/` (556 scripts, notas e configs de job). Feito no dia: `fusion_kit.py`, `bordas.py`, trava do
"Untitled Project" no `resolve_render.py`, `so_capa` só com `capa`, recusa de `camera_moves` sem `camera_fusion`, teste `tests/fusion_kit_teste.py`.

- [x] **Posição no Resolve** (cobrado 6×): lei medida com render e corrigida no `davinci.py` (`"posicao_resolve": "auto"`), 14/11/2026.
      Falta: fonte girada (layout calibrado em cima do erro; só com piloto novo) e o caminho `job.json` da Priscilla 4K.
- [ ] **Migrar Bombordo e Content Hub para o `reel-motion`** (decisão do editor 14/11/2026): no próximo job real de cada um, um por sessão.
      Tema `temas/<cliente>.json` + rubrica; levar como opção do motor o que é só deles (Bombordo: legenda cinética, chamada, `impact_pulses`;
      Content Hub: letterings, B-roll). Depois do job aprovado, apagar a skill-cópia. Substitui a pendência de 12/10 "motor único = podcast-reels".
- [ ] **`bordas.py` como trava** (corte em cima da voz, cobrado 10×): hoje é aviso no `reel.py cortes`. Depois de 2 jobs medindo falso alarme,
      virar pendência do selo `cortes`. Levar o mesmo conferidor aos motores de podcast (`podcast-reels`, `bombordo-boreste`).
- [ ] **Trocar `dvr.scriptapp` por `fusion_kit` nos scripts do motor** (`resolve_*.py`, `scripts/timeline/*.py`, `qa_resolve.py`): uma conexão, uma trava de
      salvar, um limite de tempo. O kit `timeline/` ainda tem IFB/v7 fixo (pendência antiga).
- [ ] **rastreio.py**: lê tudo na memória (32 min = 15 GB, morreu) e pega o maior rosto (foto no telão, técnico de som). Ler em fluxo e seguir por
      continuidade + largura máxima: `colheita/…/joao/blueTreeCortes/04_work/rastreio_palco.py`.
- [ ] **monta_props.py**: `"burns": "inicio_fim"` para reel só com legenda (`…/blueTreeCortes/04_work/burns_inicio_fim.py`); burn em cada troca de
      câmera + whoosh nos zooms para corte sem painel (`…/fernandaBen/podcastAngelica/04_work/scripts/transicoes.py`).
- [ ] **Zooms pelas palavras em destaque** quando não há painel (`…/podcastCast06/04_work/scripts/zooms.py`: punch a cada ≥ 6 s, vão > 12 s preenchido):
      levar para `movimento.py planeja`.
- [ ] **checa_takes "corte no meio da palavra"** dispara em toda borda de palestra (sala com eco): medir o vale (≤ −40 dB por 20 ms) antes de acusar.
- [ ] **blocos.py** casa por contagem de letras: correção que junta palavras desalinha (`…/blueTreeCortes/04_work/texto_legenda.py`).
- [ ] **Painéis**: `PanelSides` exige `lineAt` e `accent`; `PanelTimeline`/`PanelChecklist` ignoram `titleAt`; checklist `size` passa pela escala 0,62 do tema.
- [ ] `camera_moves` só vale para câmera `face` (punch no `crop` é ignorado calado); `"fps": 30` não evitou a cópia 29,97 (GL 05/11).
- [ ] Tema `growth-leaders` sem bloco `sfx`; capa no estilo dos posts oficiais virar layout `post` no `Capa.tsx`.
- [ ] **Limpeza de episódio longo no Resolve** (Angélica 12/11, "nesses podcasts maiores vc sempre faz cagada"): os 13 scripts de
      `…/podcastAngelica/04_work/limpeza_episodio/04_work/` (turnos, planos, monta_cortes, conserta_ep, itens_tl) são o fluxo que funcionou; levar para a `limpeza-gravacao-bruta`.
- [ ] **Troca de QR/cartão em aula** (`…/fernandaBen/colocarNovoQrCode/04_work/scripts/`, 33 scripts): fluxo inteiro só existe no job; virar skill ou seção da `fernanda-produto`.

## 16/11/2026 — Podcast ELZA (fernandaBen/podcastElza)
- ffprobe 8 repete a linha de `stream=` quando o arquivo tem stream group (master do Drive): corrigido no reel-motion (width/height e r_frame_rate; antes convertia o bruto 30p inteiro para 29,97 à toa). Falta revisar: content-hub/cover.py, limpeza-gravacao-bruta/renderizar_cortes.py, podcast-reels/cover.py e burn_end.py, vinheta-marca/{autoteste,entrega,clipes}.py.
- reel.py tem o whisper-large-v3-mlx fixo: avisar (e oferecer o turbo) quando o modelo não está no Mac, em vez de baixar 3 GB calado.
- Subir para o motor: 04_work/scripts/crops_planos.py (crops por plano em master multicâmera, YuNet) e punch_sfx.py (padrão Angélica: punch nos destaques + SFX do kit).
- render_tls.py (Angélica) usado de novo no episódio: vira script do motor.
- Burns nas trocas (Fernanda): transicoes.py (Angélica) e burns_timeline.py (Elza) viram etapa do motor para corte sem painel; hoje o pacote só leva burn de painel.
- cibo-auto helium: a extensão Claude (claude-in-chrome) cria a PRÓPRIA janela/aba no space ativo, não usa a janela que o cibo-auto abriu no space da automação (editor 16/11: 'tu foi abrir o helium lá em outro space'). Depois de tabs_context(createIfEmpty), mover a janela nova com yabai para o space da automação; ideal: cibo-auto mover qualquer janela Helium nova da sessão.

- 16/11/2026 (Podcast Sabrina): TRAVA pedida — `reel.py capa` deve recusar sem print/frame do editor (correção repetida: "eu ja deixei isso claro mil vezes"). capa_cand.py gira por padrão (--rot clock), errado para master 16:9 de podcast.
- 16/11/2026 (Podcast Sabrina): timeline de EPISÓDIO criada no projeto dos cortes nasce 1080x1920 (padrão do projeto) — editor: "pq a timeline ficou vertical pro clipe horizontal?". Script de timeline de episódio (podcastSabrina/04_work/scripts/ep_timeline.py) precisa SetSetting useCustomSettings + 1920x1080; idem rascunho do Text+ no resolve_insta (Elza). Levar ep_timeline + resolve_insta + burns_timeline + crops_planos + punch_sfx para o motor.
- 16/11/2026 (Podcast Sabrina): fila_davinci troca a timeline atual a cada corte e "fecha" a do episódio que o editor está vendo ("pq vc fechou a timeline do meu podcast inteiro"): ao fim da fila, reabrir todas as timelines do projeto com a do episódio na frente.
- 16/11/2026: resolve_insta.py: AppendToTimeline do composto recém-criado falha na mesma execução; endFrame deve ser dur-1; repetir depois funciona.
- 16/11/2026: gancho-e-ritmo não vê o "tail" do motion.json (acusa 0 s depois da última palavra) nem os destaques *…* do blocos_manual (0%).

- lettering-motion/reel-motion: legenda palavra a palavra em Pillow alinhar pela LINHA DE BASE (getmetrics + anchor "ls"), nunca centralizar cada palavra pela própria bbox (Michelle 19/11/2026: "tortinha"). Script de referência: michele/04_work/grafismos_v2.py

- regras/davinci.md: documentar lei do Pan no modo scaleToCrop ("Scale full frame with crop"), medida 19/11/2026 com render (TESTE PAN SCALETOCROP): visto = Pan × largura exibida ÷ largura da timeline (4K 16:9 em 1080x1920: 3,16). Diferente da lei conform none (Pan × arquivo ÷ timeline). Ref.: michele/04_work/resolve/edita_v3.py
- reel-motion: montagem de recap (vídeos+fotos+flares) pela API virou script de job (michele/04_work/resolve/monta_recap.py, edita_v2/v3.py): subir ao motor como "recap" (fotos como sequência de links, LUT por plano, zoom Fusion alternado)

- regras/davinci.md: clipe com Fusion comp + Pan no Inspector = faixa preta (o Fusion recebe o quadro já recortado pelo input sizing e o Pan desloca a saída). Reenquadrou com Pan? zoom NÃO vai no Fusion do clipe. DeleteFusionCompByName devolveu False: recolocar o clipe (DeleteClips + AppendToTimeline com GetLeftOffset). Com Fusion o Pan lido cai para 1/4. Medido 19/11/2026 (Michelle).

- regras/davinci.md: ciclo de .drt (export/import) MULTIPLICA por 4 o Pan de clipes de vídeo em scaleToCrop (Michelle 19/11/2026: tela preta nos horizontais). Depois de qualquer .drt, reler e regravar Pan. Sequência de imagens não sofre. resolve_cores: voz_mic_v2.wav cai como a_camera e seria DESLIGADA (regex /voz(__)?.wav).
