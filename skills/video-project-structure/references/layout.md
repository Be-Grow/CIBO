# Layout e política de armazenamento

```text
Projeto/
├── 01_sources/
│   ├── masters/
│   ├── audio/
│   └── proxies/
├── 02_transcripts/
├── 03_assets/
│   ├── brand/
│   ├── fonts/
│   ├── music/
│   ├── sfx/
│   ├── vfx_overlays/
│   ├── stock_local_only/
│   └── licenses/
├── 04_work/
├── 05_qa/
├── 06_deliverables/
└── 07_manifests/
```

## Drive de skills/assets do cliente

Permitido, quando a licença autorizar:

- skills e scripts;
- logo, identidade e fontes;
- SFX;
- música;
- VFX, FSX, overlays e transições reutilizáveis;
- previews leves, licenças e manifestos.

Proibido:

- gravações brutas e masters;
- áudio bruto de entrevista;
- proxies;
- vídeos stock/B-roll;
- caches/intermediários;
- entregas finais, salvo destino de entrega separado e pedido explícito.

Quando uma licença proibir redistribuição do asset bruto, armazene no Drive apenas título, autor, fonte, URL, licença, hash esperado e comprovante.

## Nomes

Use nomes descritivos e estáveis. Para assets: `tipo_descricao_fundo_resolucao_fps_fonte_id.ext`. Para entregas: `NN - HEADLINE.ext`. Não use `final_final`, `novo`, `teste2` ou arquivos soltos na raiz.

## Limpeza de projeto (lição joao "ep 26", 04/11/2026)

- **Só limpe projeto fechado.** Antes de apagar `04_work/` ou `01_sources/`, confira se toda entrega existe e abre no
  `ffprobe`. No "ep 26" do joao, o r05 e o r06 estavam sem MP4: o `.mov` do r05 tinha 822 bytes (render interrompido)
  e o `status.py` não acusou nada.
- **`04_work/_bundle/rNN` que sobrou indica render que morreu** (o bundle é apagado ao sair). Dá para apagar se nenhum
  render estiver rodando, porque o próximo render recria o bundle.
- **`04_work/_pub` é hard link de `04_work/public`.** O `du` mostra GB, mas apagar libera quase nada. Meça o espaço
  real antes de prometer ganho (`find <pasta> -type f -links 1`).
- **Uma cópia só do edit do editor.** Na ingestão ele vai para `01_sources/`. Se precisar de remux, confira o vídeo
  (`ffmpeg -i X -map 0:v:0 -c copy -f md5 -`) e fique com um arquivo só. No "ep 26" havia 5 GB repetidos (original
  solto na raiz e remux em `01_sources/`).
- **Nome da pasta = episódio real.** A pasta "ep 26" guardava o EP27 (Antônio Veras), com arquivos `ep27_*`. Corrija o
  nome na ingestão; depois que a timeline do DaVinci aponta para o caminho, renomear quebra os links.
