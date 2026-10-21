---
name: podcast-reels
description: Episódio de podcast + SRT viram cortes 9:16 com legenda Cal Sans, ênfases, clique, burn azul, abertura com zoom e capa. Use quando pedirem cortes, Reels, Shorts ou TikToks de podcast no estilo podcast-reels.
---

# Podcast → Reels

**Local setup:** dependencies (Pillow, numpy) live in a venv at
`~/.claude/skills/podcast-reels/.venv`. Run scripts with
`~/.claude/skills/podcast-reels/.venv/bin/python3 scripts/make_reels.py`, or
`source ~/.claude/skills/podcast-reels/.venv/bin/activate` first, instead of the
bare `python3` shown below. Requires `ffmpeg`/`ffprobe` on PATH (already present
via Homebrew).

Builds finished vertical cuts from a master video + SRT. Everything is driven by one
`job.json`; the scripts do transcription-free caption timing (reused from the SRT),
silence-snapped trimming, caption rendering, audio sweetening and the cover.

## Workflow

> **Entrega — padrão atual: MP4** (exceção temporária ao padrão DaVinci do CIBO, editor 20/10/2026). O render final sai
> pelo ffmpeg (`podcast-reels/references/render-ffmpeg-legado.md`) até existir o adaptador `job.json` → pacote DaVinci.
> Regra: `client-router/references/regras/davinci.md`.


1. **Read the SRT, not the video.** Collapse it into a readable transcript first:
   group cues into ~15 s blocks and print `[start - end] text`. Pick the clips from
   that. Never scrub the video looking for moments.
2. **Identify host vs guest** from conversational flow (who introduces, who asks,
   who answers) and say so before proposing cuts.
3. **Pick moments** with a hook in the first 3 s, one clear idea, and a closing
   punchline or a cliffhanger question. Target 42–55 s of *kept* audio — the trim
   removes 15–25 % of the raw window, so choose a window ~20 % longer.
4. **Write `job.json`** (see `assets/job.example.json`) with, per clip: `src`,
   `master_in` (its IN point in the master, seconds — used to map SRT cues),
   `headline`, `filename` (the delivered basename — never leave this as the clip
   key; deliverables must be named after the headline, e.g.
   `01 - ELEGANCIA NAO E - FICAR INVISIVEL - DEPOIS DOS 50`, matching the cover's
   `CAPA - <filename>.png`), `cropx`, `cover_t`, and `keeps` (list of `[start,end]`
   in *clip-local* seconds).
5. **Run it:**
   ```bash
   JOB=job.json python3 scripts/make_reels.py            # all clips
   JOB=job.json python3 scripts/make_reels.py corte01    # one clip
   ```

## Escolha dos momentos (doutrina)

Onde todo "clipador" automático erra (testes do Opus Clip descartam 13–40% da saída). Adaptado de
`kvrancic/oneshot-video` references/selection.md (MIT), 12/10/2026.

- **Portão:** o momento precisa ter pelo menos um: virada inesperada; opinião forte que alguém
  discutiria ou mandaria para outra pessoa; informação útil para salvar (número, mecanismo,
  resultado, mito derrubado); história com virada, do começo à consequência; frase que se sustenta
  citada sozinha. Bem falado e no tema não basta. Menos cortes, mais fortes.
- **Começo:** a primeira frase faz sentido para um estranho. Pronome sem referência, resposta a
  pergunta não ouvida, "então", "como eu disse" → adiante o começo. **Contexto se conserta
  adiantando o início, nunca cortando o desfecho.**
- **Fim:** depois do desfecho (inclua a risada, a pausa, o "e isso faz pensar"); termine em frase
  completa, nunca em vírgula, "mas" ou gancho para a próxima ideia. Piada é unidade: preparação e
  punchline juntas.
- **Sem distorcer:** juntar dois trechos só se nada entre eles inverte ou relativiza ("mas",
  "porém", "exceto").
- **Cold open:** quando o melhor está depois da metade, abra com a frase-chave (3–8 s), corte para
  o começo e deixe tocar.
- **Ranqueie candidatos entre si** em gancho, completude, desfecho, densidade e público (uma frase
  por eixo, depois nota 1–5); nota absoluta prevê pouco. Nada de dois cortes com a mesma ideia.
- **Duração pelo conteúdo:** frase afiada 15–40 s; opinião com argumento ou história curta
  40–90 s; lista/comparação 90 s–3 min.
- Antes do render: `JOB=job.json scripts/checa_cortes.py` (começo com conectivo, pronome sem
  referência, minúscula no meio da frase, fim em vírgula ou conectivo, duração).

## Referências (abra só quando o gatilho bater)

| Arquivo | Abra se |
|---|---|
| `references/motor-comum.md` | escolher `keeps`, mudar um corte pronto, conferir algo sem render inteiro, regras do motor, entregáveis |
| `references/render-ffmpeg-legado.md` | renderizar o MP4 (padrão atual MP4 deste motor; opções VENC, PARALLEL, overlays) ou gerar projeto Premiere/DaVinci |
| `references/gancho-ab.md` | testar ganchos diferentes para o mesmo corte (`variacoes_gancho.py`) |
| `references/eficiencia.md` | o job está caro em tokens ou turnos |
| `references/historico-falhas.md` | algo falhou: índice de falhas conhecidas e o histórico de cada uma |
