# Regras transversais — Depois de uma correção do usuário

- **A lição vai para a skill no mesmo turno**, não só para a memória: SKILL.md, bíblia do
  cliente, script ou checagem automática. Se a falha passou pelo QA, acrescente a checagem
  que faltou ao portão. Diga qual skill mudou.
- **Se a causa está no motor da skill, conserte o motor** (e procure o mesmo defeito no lote
  todo), não só os arquivos do job.
- **Código compartilhado entre clientes** (motor da Fernanda usado pela Malu; `face_crop.py`
  do Bombordo usado pelo Dr. Energia): mudança entra como opção por chave no job, e o outro
  cliente precisa sair idêntico (`framemd5` num trecho de 5 s, ou checksum da pasta).
- **Suba para o CIBO** (`~/CIBO`, `git@github.com:Be-Grow/CIBO.git`): copie a skill,
  confira o diff, atualize o README se a skill for nova, commit e push. Nada vai para
  `~/.codex/skills`.

Volta ao checklist: [`_checklist.md`](_checklist.md).
