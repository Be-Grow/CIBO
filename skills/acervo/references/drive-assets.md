# Assets no Drive: estrutura fixa (editor, 23/11/2026)

Todos os editores sobem os assets de edição para a MESMA estrutura numa pasta compartilhada do Drive, `CIBO Assets`. O Drive
para computador aparece como disco no Mac e no Windows, então a CIBO lê dali direto: `acervo.py drive-define` aponta a pasta neste
computador (uma vez), `acervo.py drive-indexa` cataloga sem copiar e `acervo.py get` copia para o projeto só o que for usado.
O catálogo guarda o caminho RELATIVO a `CIBO Assets`, então vale igual no Mac e no Windows.

```
CIBO Assets/
  _global/                         serve para qualquer cliente
    burns/                         film burns e vazamentos de luz usados nas trocas
    transicoes/                    transições prontas (vídeo com alfa ou pacotes)
    sfx/
      cliques/   whoosh/   impactos/   risers/   pops/   ui/   ambiente/
    trilhas/
      animada/   calma/   corporativa/   emocional/   tensa/   inspiradora/
    luts/                          .cube
    overlays/                      grão, poeira, texturas, molduras
    fontes/                        fontes livres para qualquer cliente (com a licença ao lado)
    templates/                     capas, cartões "seguir", lower thirds (.drfx, .setting, .psd, .png)
  clientes/
    <Nome do Cliente>/             o mesmo nome do cadastro ou um apelido dele (ex.: "Michelle Gil")
      logo/                        PNG com fundo transparente, versão clara e escura
      fontes/                      fontes da marca + licença
      cores/                       manual da marca, paleta
      capas/                       capas aprovadas (exemplos)
      sfx/   trilhas/   burns/     kit próprio, se o cliente tiver
      templates/                   cartões e lower thirds do cliente
      referencias/                 vídeos de referência aprovados
```

Regras para quem sobe:
- **Nome do arquivo diz o que é**, minúsculo, com hífen: `whoosh-rapido-01.wav`, `piano-suave-90bpm.mp3`, `burn-laranja-curto.mov`.
- **Trilha e stock com licença**: um `.txt` com o mesmo nome ao lado (`piano-suave-90bpm.txt`: fonte, autor, licença).
- **Nada solto**: arquivo fora dessas pastas não entra no catálogo (o `drive-indexa` lista o que está fora do lugar).
- **Identidade de cliente só na pasta dele**: logo, fonte e cor de um cliente nunca em `_global`.
- **Não apagar nem renomear o que a CIBO já usou** sem avisar: o catálogo aponta pelo caminho (rode `drive-indexa` de novo depois).
- Bruto de gravação e entregas NÃO vão aqui: o bruto entra pela arena, a entrega vai para a pasta do cliente (com o OK do editor).

Como a CIBO usa: antes de perguntar por um asset, `acervo.py find` (inclui o Drive); escolhido, `acervo.py get ID --to PROJ --client C`
(copia e registra o uso, para não repetir trilha/stock no mesmo cliente). Rode `drive-indexa` no começo do dia de trabalho ou quando o
editor avisar que subiu coisa nova.
