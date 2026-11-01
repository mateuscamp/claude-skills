# claude-skills

A operação completa está no `CONTRIBUTING.md`; aqui fica só o que o agente faz sem perguntar.

- A fonte de toda skill é o `main` deste repositório. `~/Documentos/Skills` é cópia gerada pelo
  `distribuir.py`, nunca editada à mão, e é de lá que o autor sobe os zips no claude.ai.
- Mudança entra num ramo, numa worktree em `~/.cache/claude-skills-wt/<ramo>`. Push e PR esperam
  o sim do autor.
- Depois de cada merge, o agente roda, sem pedir ao autor, e relata a saída do `--check`:

  ```sh
  git -C ~/.claude/skills pull --ff-only
  ~/.claude/skills/distribuir.py
  ~/.claude/skills/distribuir.py --check
  ```

- O autor só sobe zip no claude.ai quando o agente dá o sinal: `--check` em "tudo em dia"
  e nenhum PR da mesma skill ainda aberto. O sinal nomeia os zips que mudaram.
- Mudança local no `main` trava o pull: ela vai para um ramo próprio, nunca é descartada.
