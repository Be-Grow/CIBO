# Histórias do Porto → XML para o DaVinci

Modelo usado no EP 06 (18/10/2026). Copie os três scripts para `04_work/historias_daniel/work/` do episódio,
troque `STORIES` (nome, manchete, capa, painéis, janelas sem música, SFX, bipes) e `MASTER` em `componentes.py`.

    cd <historia> && python3 ../stage_caps.py <historia>     # legenda animada + punch-in (precisa kinetic/blocks_<historia>.json)
    python3 componentes.py <historia>                         # painéis, legenda com alfa, sombra, fade, trilha, capa, xml_cfg.json
    python3 xml_resolve.py <historia>                         # PROJETO - <nome>.xml

Antes: edit.json (keeps/seams/total), kinetic/words_<historia>.json e kinetic.yaml (destaques), como no EP 06.
Depois: importe num projeto de teste e renderize em baixa antes de entregar (regras em client-router/references/regras-transversais.md,
seção "DaVinci Resolve pela API").
