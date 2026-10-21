---
name: acervo
description: Biblioteca de assets do CIBO (burns, cliques, SFX, trilhas, fontes, logos, cartões, LUTs) — acha, copia e registra uso, guarda o que o editor apontar. Use sempre que o job precisar de um asset ou o editor mandar um.
---

# Acervo

O editor teve que apontar várias vezes onde estavam os mesmos arquivos (cliques, film burn,
cartão do Instagram, trilhas). Isso acabou: todo asset tem endereço no catálogo, e a regra é
**buscar no acervo antes de perguntar**.

Script: `~/.claude/skills/acervo/scripts/acervo.py` (só biblioteca padrão + ffmpeg).

## Onde fica

- Biblioteca: **lugar fixo escolhido pelo editor**, gravado em `~/.cibo/acervo.json`. Neste Mac:
  `/Volumes/SSD/CIBO Acervo` (o Mac tem 256 GB; o editor prefere o SSD). O catálogo
  (`catalog.json`) fica dentro dela e anda junto; uma cópia de segurança fica em
  `~/.cibo/catalog_backup.json`.
- **Primeira vez numa máquina** (`ACERVO_SEM_BIBLIOTECA`): pergunte ao editor onde a biblioteca
  deve ficar, com a sugestão de um disco externo, e rode `acervo.py init CAMINHO`. Pergunta uma
  vez só.
- **Editor pediu para mudar de lugar**: `acervo.py move-library NOVO`. Copia, confere e passa a
  usar o novo; a cópia antiga só é apagada depois que o editor confirmar.
- **SSD desconectado** (`ACERVO_INACESSIVEL`): peça para conectar. Não saia caçando cópias soltas
  pelo disco.

Dois tipos de item:
- `lib`: copiado para dentro da biblioteca (`<tipo>/<cliente|_global>/arquivo`). Tudo o que o
  editor aponta ou manda entra assim.
- `ref`: indexado onde já está, sem copiar (bibliotecas grandes do SSD, assets das skills).
  Se o arquivo mudar de pasta, `check` reencontra pelo hash.

## Uso no job

```bash
A=~/.claude/skills/acervo/scripts/acervo.py
python3 $A find clique                      # achar (palavras, --type, --client)
python3 $A find burn --type filmburn
python3 $A path sfx-click-lens              # caminho absoluto para um script
python3 $A get filmburn-pack --segment 7 --to 03_assets/fx   # copia e registra no projeto
```

- `get` copia para o projeto e anota em `07_manifests/assets_usados.md` (ID, origem, licença).
  Use `get` em vez de apontar o arquivo do acervo direto no job quando o projeto vai ser
  arquivado ou entregue.
- Pacotes com vários efeitos separados por preto (`filmburn-pack`, 19 burns com SFX): `segments
  ID` detecta os trechos; `--segment N` entrega um só.
- **O editor apontou ou mandou um arquivo de asset**: rode `acervo.py add ARQ --type ... --client
  ... --tags ... --note "como usar"` na mesma hora. A nota guarda o jeito de usar ("baixo,
  ~-20 dBFS", "uma batida por vez"). Use `--id` curto para os favoritos.
- Correção de metadados: `acervo.py edit ID --client _global --add-tags favorito --note ...`.
- Licença: preencha `--license`. Itens com origem YouTube ou licença não verificada não entram em
  cliente com política de stock (Content Hub) sem confirmação.

## Manutenção

- `acervo.py check`: confere todos os caminhos e religa pelo hash o que mudou de pasta dentro das
  raízes indexadas. Rode no começo de um job grande e depois de reorganizar o SSD.
- `acervo.py dupes`: arquivos repetidos (mesmo hash). Ao achar cópias de um mesmo asset espalhadas
  pelas skills, aponte o código para o ID do acervo em vez de copiar mais uma vez.
- Pasta nova de assets no SSD: `acervo.py index PASTA --tags ...`.

## Já catalogado (12/10/2026)

635 itens: `Músicas edicao`, `audio EFXs`, `Projeto premiere` (AMBIENTAÇÃO, IMPACTO, RISERS, HITS,
ATMOSFERA, WHOOSHS), `fx edicao` (film burns, Clientes begrow), assets de todas as skills,
trilhas Mixkit da palestra do João, Cal Sans. Favoritos: `filmburn-pack` (o pacote de burns com
SFX que o editor mais usa; é o mesmo arquivo de `content-hub/assets/film_burn_transitions.mp4`),
`sfx-click-lens`, `sfx-camera-click`, `avatar-joao-campos-insta`.
