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
