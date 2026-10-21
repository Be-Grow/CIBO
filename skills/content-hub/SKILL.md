---
name: content-hub
description: Crie cortes verticais 9:16 para Reels, TikTok e Shorts da Content Hub, com identidade, seleção editorial, tratamento de áudio e transições próprios deste cliente. Use somente em trabalhos da Content Hub.
---

# Content Hub → Cortes verticais

Produza cortes finalizados a partir de vídeos master e seus SRTs, sem misturar identidade ou arquivos de outros clientes.

## Resumo rápido

As ~12 decisões que mais mudam o resultado, condensadas dos 4 documentos de referência. Use isto no dia a dia com um cliente já conhecido; leia o documento completo linkado quando o job for o primeiro desta skill, algo estiver ambíguo, ou o resumo não cobrir o caso.

- **Identidade** ([brand-profile.md](references/brand-profile.md)): logo `assets/logo_content_hub_transparent.png`; laranja `#FF7400` como acento (nunca fundo dominante) + azul `#000249`/`#002C7B`; Montserrat ExtraBold/Black em caixa alta; film burn oficial `assets/film_burn_clean.mp4` em toda troca real de cena.
- **Capa**: pessoa centralizada (sem cortar olhos/queixo/testa), glow laranja leve, painel editorial azul assimétrico na base, barra laranja, headline curta, logo do lado oposto ao rosto. Nunca repita a composição de outro cliente — comparar contra o registro de assinaturas antes de aprovar.
- **Lettering**: popup curto em card no canto inferior esquerdo/área negativa, nunca como legenda ampliada. Card responsivo, fonte no tamanho mínimo legível, overflow determinístico é proibido (frase cortada já foi feedback real).
- **Split-screen**: B-roll no topo, talking head embaixo em escala natural, sem headline entre os painéis; blur estreito + borda azul semitransparente só abaixo. Entrada/saída sempre com film burn oficial — fade já foi rejeitado explicitamente.
- **B-roll** ([media-policy.md](references/media-policy.md)): valide pelo sentido completo da fala via `semantic-broll-validator`, nunca por palavra-chave isolada; sem candidato forte, prefira talking head ou lettering.
- **Música**: escolha por corte (não por convidado/episódio), brief emocional, 3–5 candidatas, ducking sob a voz; prioridade é emoção/impacto sem perder inteligibilidade.
- **Render**: prioridade `speed` — GPU só quando qualidade e bitrate passarem no teto do perfil (ver `video-render-optimizer`).
- **Fontes de stock aprovadas**: Pexels, Pixabay, Coverr, Mixkit (manual), Wikimedia; ProductionCrate/Videvo só com licença individual confirmada. Nunca YouTube/filmes/séries/pacotes piratas. Pexels falha em queries longas — tente 1–2 palavras de sentido amplo antes de descartar.
- **Entrega**: uma pasta por nome do convidado; ver [regra de entrega por gravação](#regra-de-entrega-por-gravação) abaixo.
- **Drive** ([asset-source-catalog.md](references/asset-source-catalog.md)): `02 - Assets` é a fonte canônica — sincronize antes de renderizar e confira `assets/ASSETS_MANIFEST.md`. Nunca suba stock bruto, masters ou proxies no Drive de skills/assets.
- **Rejeições conhecidas** ([client-content-bible.md](references/client-content-bible.md)): sem fade no split, sem B-roll genérico, sem capa parecida com Bombordo e Boreste, sem áudio metálico/exposição escura/saturação excessiva.

## Antes de editar

1. Confirme que o trabalho é da Content Hub. Não use esta skill para Autismo Cast ou Bombordo e Boreste.
2. No primeiro job de um cliente novo (ou sempre que o Resumo rápido acima não cobrir a decisão), leia os 4 documentos de referência por completo: [brand-profile.md](references/brand-profile.md), [media-policy.md](references/media-policy.md), [client-content-bible.md](references/client-content-bible.md) e [asset-source-catalog.md](references/asset-source-catalog.md). Atualize a bíblia e o catálogo quando aprender algo novo — eles são memória canônica do cliente e acompanham a skill no Drive.
3. Leia o SRT como transcrição agrupada em blocos de aproximadamente 15 s. Escolha os momentos pelo texto antes de revisar imagem e enquadramento.
4. Identifique entrevistador e convidados pelo fluxo da conversa. Os cortes priorizam a fala e a imagem dos convidados; mantenha perguntas apenas quando forem necessárias para contexto.
5. Verifique os assets entregues para o job. Nunca reutilize logo, patrocinador, vinheta, música, headline ou referência visual de outro cliente.
6. Antes de renderizar, sincronize `Content Hub/02 - Assets` do Drive com `assets/` local e confira `assets/ASSETS_MANIFEST.md`. O Drive é a fonte canônica dos assets reutilizáveis deste cliente; não use arquivos homônimos de outras skills.
7. Audite a estrutura com `video-project-structure`. Fontes, trabalho, QA, entregas e manifests precisam estar separados; não mova caminhos ativos sem atualizar jobs.

## Regra de entrega por gravação

Quando o usuário pedir cortes das gravações SEBRAE, produza **dois cortes por gravação válida**, ignorando testes ou arquivos corrompidos/curtíssimos. Cada corte deve ter gancho nos primeiros 3 s, uma ideia autônoma e conclusão semântica. Leia pelo menos os 10–20 s seguintes da transcrição antes de fechar o fim.

Organize as entregas em uma pasta por nome do convidado. Se uma gravação tiver mais de um convidado, arquive cada corte sob o participante que protagoniza o trecho. Não use nomes genéricos quando a identidade puder ser confirmada pela gravação, transcrição ou materiais do projeto.

Use 35–60 s como faixa normal e adapte ao pensamento completo. Um bom corte da Content Hub ensina, demonstra, provoca, mostra bastidor ou comprova resultado com clareza e autoridade.

## Pipeline

O job é controlado por `job.json`; veja `assets/job.example.json`.

Na primeira utilização em uma máquina nova, crie `.venv` e instale `requirements.txt`. FFmpeg e FFprobe também precisam estar disponíveis no sistema.

1. Defina `src`, `master_in`, `headline`, `cover_t` e `keeps` para cada corte.
2. Remova repetições, falsos começos e silêncios, preservando orações inteiras. As bordas internas são ajustadas automaticamente ao silêncio.
3. Rode `face_crop.py` e revise a prévia. Use `cropx_timeline` por plano; não siga o rosto quadro a quadro.
4. Detecte as trocas reais de câmera. Use o asset oficial `assets/film_burn_clean.mp4` de forma seletiva, com seu SFX abaixo da voz. Todo split-screen deve entrar e sair escondido por um film burn curto; não use fade e não use film burn para esconder corte semântico ruim.
5. Defina `letterings` independentes para números, conceitos e frases-chave. Defina `broll` somente depois de validar a relação com a frase completa e seu contexto. O layout padrão usa o B-roll no topo e desloca o talking head para baixo, preservando escala natural e rosto/tronco.
6. Revise uma amostra curta ou contact sheet antes do render final.
7. Renderize:

```bash
JOB=job.json ~/.claude/skills/content-hub/.venv/bin/python3 \
  ~/.claude/skills/content-hub/scripts/make_reels.py
```

## Assets e licenças

Mantenha em `Content Hub/02 - Assets` apenas transições, overlays, SFX, fontes, logo, música aprovada e manifestos de origem/licença. B-roll de estoque fica separado por projeto e nunca é confundido com overlay reutilizável. Para SFX externos, aceite automaticamente somente CC0; CC BY exige créditos anexos; rejeite CC BY-NC. Itens cuja licença não permita redistribuição ficam apenas referenciados no manifesto e são baixados da fonte oficial para o job, sem re-hospedagem no Drive compartilhado.

## Revisão e entrega

Cada corte entrega o MP4 com a mesma capa como primeiro frame, `CAPA - <nome>.png` em 1080×1920 e os timecodes `HH:MM:SS:FF` de entrada e saída no master. A capa é obrigatória e deve ser visualmente revisada. Confira o MP4, a headline em caixa alta, Montserrat, logo, frame zero, trilha de áudio escolhida e todos os film burns de troca de cena.

Depois de todo render final, rode `caption-quality-gate` com cobertura de 100% dos blocos e `video-delivery-safety-check`. Valide também 100% dos popups no início/meio/fim e confronte o texto com o job. Um vídeo com erro, baixa qualidade ou divergência do job é bloqueado mesmo que o FFmpeg tenha terminado. Ao encerrar a demanda, rode novamente `video-project-structure`, atualize bíblias/catálogos/manifests e suba ao Drive as skills e assets reutilizáveis necessários. Nunca envie bruto/master/proxy ou vídeo stock ao Drive de skills/assets; música/SFX/VFX/overlays só sobem quando a licença permitir, caso contrário sobe apenas a referência legal.

Quando o usuário pedir organização no Google Drive, mantenha a estrutura descrita no perfil da marca. Uploads e alterações no Drive exigem autorização da tarefa atual; a skill não presume permissão permanente.

## Referências (abra só quando o gatilho bater)

| Arquivo | Abra se |
|---|---|
| `references/audio.md` | decidir a camada de áudio (tratamento, trilha, mixagem) |
| `references/regras-visuais.md` | enquadramento, legenda, transições, letterings, B-roll, encode |
| `references/brand-profile.md` | cores, fontes e logo |
| `references/media-policy.md` | usar mídia de terceiros ou B-roll |
| `references/client-content-bible.md` | tom e seleção editorial |
| `references/asset-source-catalog.md` | de onde vem cada asset |
| `references/historico-falhas.md` | algo falhou: falhas conhecidas |
