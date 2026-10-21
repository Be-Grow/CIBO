# podcast-reels — render e projeto editável

Movido do SKILL.md em 20/10/2026 (carregar sob demanda). Conteúdo preservado sem cortes.

## Render padrão (rápido) e opções

Comece todo job assim (detalhes no item 46 do histórico):

```bash
taskpolicy -B -t 0 -l 0 -p $$          # em background o macOS usa os núcleos lentos
export JOB=job.json ZOOM_AMT=0 BURN_OUT=0 VENC=auto PASSA_DIRECT=1 PARALLEL=auto \
       BURN_END_INLINE=1 BURN_END_LIMIT=0.84 BURN_END_BT709=1
~/.claude/skills/podcast-reels/.venv/bin/python3 scripts/make_reels.py corte01 | grep -E "built|DONE|Error"
```

| Chave | Onde | O que faz |
|---|---|---|
| `VENC=auto` | env | encoder escolhido pelo perfil de hardware (`video-render-optimizer`); falhou → x264 |
| `PASSA_DIRECT=1` | env | recorte direto no ffmpeg (só com `ZOOM_AMT=0`) |
| `BURN_END_INLINE=1` | env | burn de saída sobre preto dentro do `final()` (+`BURN_END_LIMIT`, `BURN_END_BT709`) |
| `overlays` | clipe | `.mov` com alpha (Remotion) + SFX opcional, na mesma codificação |
| `crop_h` | clipe | recorte mais baixo para tirar logo de terceiros do rodapé |
| `cropx_timeline`, `cropx_interp` | clipe | enquadramento por plano / seguindo a pessoa no palco |
| `cover_src`, `cover_src_t`, `cover_src_x` | clipe | capa de qualquer momento da gravação |
| `voice_af`, `music`, `mix` | clipe | cadeia da voz; trilha com ducking (`duck_ratio` 3, `duck_threshold` 0.1, `music_db` −18 em fala contínua) |
| `burn_at`, `nosnap`, `cover_style` | clipe | burn no meio; emenda sem snap; estilo de capa (`lpa`) |
| `REPLAN=1` | env | refaz o plano de legendas (senão `captions_<clip>.json` manda) |
| `PARALLEL=auto` | env | vários cortes ao mesmo tempo (número pela RAM, perfil de hardware); 7 cortes: 400 → 236 s |
| `PROFILE` / `profile` | env / job | perfil de cliente (`<skill>/assets/profile.json`): `env` + padrões do job; env > job > perfil |
| `COVER_Y`, `COVER_BAR=0` | env | altura da manchete na capa; tira a barra azul (perfis) |
| `CAP_PRESET` | env | estilo de legenda pelo conteúdo: `veredito` (opinião forte, gancho, < 40 s: 1–3 palavras, letra 92), `historia` (caso contado: ~22 caracteres, letra 70), `aula` (explicação: até 30 caracteres, letra 62); padrão = 18 caracteres, letra 74. Liga também `EMPH_MAX` (1 destaque por bloco, em ≤ 15–20% dos blocos). Trocar num corte já planejado: `REPLAN=1` |
| `CAP_CHARS`, `CAP_BASE`, `CAP_EMPH`, `EMPH_MAX` | env | os ajustes finos que os presets usam |

**Clientes neste motor:** `podcast-reels` (genérico, João Campos) e `katia` (perfil). Bombordo,
Autismo Cast e Content Hub ainda têm motor próprio (recursos a migrar: `impact_pulses`,
`long_moves`, `punch`, saída com fade, letterings, B-roll); receberam as correções de travamento.
Movimento e variação, para todos esses motores: `reel-motion/scripts/movimento.py planeja --formato podcast` gera
`impact_pulses`/`long_moves` no formato que os renders já leem, e `confere --clip clip.json [--sfx …]` aplica o orçamento
de variação (nenhum cliente foi migrado: o render de cada um continua o mesmo).

Trilha: escolha com `talking-head-music` (por corte, com offset). Fim do corte: vídeo acaba seco
e o burn passa do fim sobre preto, nunca fade.

## Projeto editável (Premiere Pro / DaVinci Resolve) — só sob pedido

`JOB=job.json scripts/projeto_nle.py [corte01 ...] [--master ORIGINAL] [--clicks 'x_{k}.wav']` grava
`<outdir>/Projetos editáveis/PROJETO - <nome>.xml` + `.srt` + LEIAME. Um XML do Final Cut 7 serve aos
dois programas: V1 trechos sobre o original com Movimento (keyframes do `cropx_timeline`), V2 film
burn em modo Tela, V3 `overlays`, A1/A2 voz, A3/A4 trilha no nível do job, A5 cliques, marcador em
cada emenda. Sem o quadro da capa e sem o ducking (feito no render). Ofereça sempre na entrega;
gere só se o editor pedir. Pendente: confirmar a importação no Premiere e no Resolve com o editor
(o primeiro teste está em `joãoCortes/05_qa/projetos_teste`).
