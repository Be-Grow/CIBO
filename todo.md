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

- [ ] **davinci.py `transf()`: fonte que não é 1 px = 1 px da timeline** (cobrado 6×: 19/10, 30/10, 01/11, 06/11, 09/11, 12/11). O Resolve encaixa a
      fonte pela largura; Zoom = (VH/RH)/(VW/RW) e posição dividida pelo mesmo excesso, com `track`, com `crops` e em 720p (`joao/blueTreeCortes`:
      zoom 1,18519 + `track_dv.json`). Hoje é contorno à mão em cada job. Validar com clipe de teste no Resolve, no molde de `tests/fusion_kit_teste.py`.
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
