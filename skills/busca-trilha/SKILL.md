---
name: busca-trilha
description: Busca trilha de fundo para vídeos de fala — acervo primeiro, depois Openverse (só CC0 e CC BY) e Freesound (CC0, opcional) — a partir de um briefing (mood, energia, BPM, sem vocal), mede cada candidata (loudness, BPM, energia em 1–4 kHz, onde ela briga com a voz), descarta o que o cliente já usou, gera prévia de 10 s sob a voz real, sugere trecho/offset e cataloga a escolhida no acervo com o crédito. Use quando a talking-head-music precisar de trilha nova ou o acervo não tiver uma que sirva.
---

# busca-trilha

Chamada pela `talking-head-music` (critério e mixagem ficam lá). Regra transversal: **som com prévia no trecho real
antes do render** — a trilha errada foi a correção mais repetida do CIBO (João, Priscilla, Andrea, LPA, Bombordo).

## Licenças (conferidas em 20/10/2026)

- **Só CC0 e CC BY.** BY-SA obrigaria o vídeo a sair com licença aberta; BY-ND proíbe obra derivada (trilha sob fala é
  derivada); NC proíbe uso comercial. O filtro `license_type=commercial` do Openverse inclui by-nd: a busca usa
  `license=cc0,by` e confere item a item.
- **CC BY exige crédito** (título, autor, link, licença) na descrição do post: o relatório e a `baixa` imprimem a linha
  pronta, e ela fica no `meta.credito` do acervo. Avise o editor.
- Freesound: só CC0; sem OAuth2 só sai a prévia HQ (mp3 ~128 kb/s) — diga isso ao editor.
- Item do acervo sem licença registrada fica de fora (registre com `acervo.py edit ID --license …`).
- ElevenLabs (música gerada) é plano B desligado: só com pedido do editor e os termos do plano conferidos.

## Fluxo

```
PY=~/.claude/skills/busca-trilha/.venv/bin/python; BT=~/.claude/skills/busca-trilha/scripts/busca_trilha.py
```

1. **Brief** `07_manifests/trilha_brief.json`: `cliente`, `mood`, `energia`, `bpm` [min, max] (metade e dobro também
   valem), `queries` em inglês (gênero + instrumento + clima: "calm piano ambient"), `duracao_min`, `evitar`.
   Tire do `brief.md` do job e do perfil do cliente.
2. **Busca**: `$PY $BT busca BRIEF 05_qa/trilha` — fora: vocal nas tags, termo evitado, curta, já usada pelo cliente,
   energia em 1–4 kHz > 15 %, BPM fora da faixa. Fica com as 5–8 melhores (menos banda de voz, menos dinâmica).
   Baixa as candidatas inteiras para medir (~2–3 min para 12).
3. **Relatório**: `relatorio DIR --md 07_manifests/trilha_candidatas.md`.
4. **Prévia**: `previa DIR N --voz PROJ/…/voz.wav --em S` — 10 s com a trilha 18,5 dB abaixo da voz (o gap da Priscilla;
   use o do cliente). Mande 2–3 prévias ao editor e espere a escolha.
5. **Corte**: `corte DIR N --dur D [--alvo T]` — roda a `analisa_trilha.py` da `desenho-de-som` (BPM, pausas, acentos,
   offset para o impacto cair em T).
6. **Baixa**: `baixa DIR N --proj PROJ` — `acervo add` (tipo `musica`, cliente `stock`, `meta` com fonte, id, autor,
   página, crédito, BPM, banda de voz) e `get --client` para `03_assets/trilha/` (registra o uso).

## Notas

- Rede (curl, cache de 24 h, nova tentativa em 429/5xx, modo simulado) vem de `busca-stock/scripts/rede.py`; as medidas
  de `talking-head-music/scripts/analyze_music.py`.
- Teste: `~/CIBO/tests/regressao.py check --engine busca-trilha`.
