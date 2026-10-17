# Skills do Claude Code

Skills próprias, carregadas de `~/.claude/skills/`.

- `ai-first-defold`: boas práticas AI-first e portão de verificação para jogos em Defold.
- `ai-first-godot`: o mesmo para Godot 4.
- `ai-first-lua`: o mesmo para jogo em Lua com LÖVE (em construção; por ora só
  `references/gerais-de-jogo.md`, sem `SKILL.md`).
- `code-audit`: auditoria de PRs, diffs e issues com evidência verificável.

O `.gitignore` é lista de permissão: skill nova só entra acrescentando a linha dela.

## Gerais de jogo: uma fonte, uma cópia por skill de motor

- Lição de jogo que vale em qualquer engine se edita só em `gerais-de-jogo.md`, na raiz. Cada
  skill sai num zip próprio, então carrega a cópia dentro dela, em
  `<skill>/references/gerais-de-jogo.md`; a cópia nunca se edita à mão.
- As skills que recebem a cópia são a constante `GENERAL_LESSONS_SKILLS` do `distribuir.py`
  (hoje `ai-first-defold`, `ai-first-godot` e `ai-first-lua`); skill de motor nova entra nela.
- Depois de editar a fonte, na worktree do ramo, regrave as cópias e faça commit das quatro:

  ```sh
  W=~/.cache/claude-skills-wt/<ramo>
  $W/distribuir.py --repo $W --copiar-gerais
  ```

- O `--copiar-gerais` recusa o checkout que está no ref (o `main` da pasta compartilhada), e o
  `--check` reprova cópia ausente ou diferente da fonte no ref.

## Uma fonte só: o `main`

- A fonte de toda skill é o `main` deste repositório. O resto é gerado dele e nunca se edita à
  mão: as cópias de `~/Documentos/Skills` e o que sobe delas para o claude.ai.
- Nenhum projeto guarda cópia de skill: o projeto cita a skill pelo nome ou pelo caminho em
  `~/.claude/skills/`.

## A pasta `~/.claude/skills` fica no `main`

- Toda sessão local do Claude Code carrega o ramo que estiver em checkout aqui, e o Codex vê o
  mesmo pelos links. Trocar o ramo da pasta troca as skills de todas as sessões abertas.
- Lição nova entra num ramo numa worktree fora do `/tmp` (o `/tmp` desta máquina é tmpfs e some
  no reboot):

  ```sh
  git -C ~/.claude/skills fetch
  git -C ~/.claude/skills worktree add ~/.cache/claude-skills-wt/<ramo> -b <ramo> origin/main
  ```

- Commit na worktree; push e PR esperam o sim do autor. Depois do merge:

  ```sh
  git -C ~/.claude/skills pull --ff-only
  git -C ~/.claude/skills worktree remove ~/.cache/claude-skills-wt/<ramo>
  ```

## `distribuir.py`

Gera as cópias de `~/Documentos/Skills` a partir do `main`, só com a biblioteca padrão do Python:

- `<skill>.zip` e `<skill>.skill/<skill>/` para cada pasta com `SKILL.md`, e o
  `code-audit-skill.md`;
- o que difere vai antes para `<nome>.antigo`, e o `<nome>.antigo` que já existia sai (mesmo
  feito à mão); nenhuma outra entrada de Documentos é tocada.

```sh
~/.claude/skills/distribuir.py           # depois de cada merge no main
~/.claude/skills/distribuir.py --check   # antes de subir um zip no claude.ai
```

O `--check` só lê e sai com 1 listando cada problema:

- cópia de Documentos diferente do `main`, ou ausente;
- cópia `<skill>/references/gerais-de-jogo.md` ausente ou diferente do `gerais-de-jogo.md`, as
  duas lidas no `main` (seção "Gerais de jogo", acima);
- `~/.claude/skills` fora do `main` ou com mudança local;
- `main` atrás do `origin/main` (o ref local, sem rede: rode `git fetch` antes);
- skill sem o link do Codex (abaixo);
- `description` acima de 1.024 caracteres, onde o Codex corta.

`--repo`, `--ref`, `--destino` e `--links` trocam os caminhos padrão, para provar o script numa
cópia.

## Codex: um link por skill em `~/.agents/skills`

- O Codex não lê `~/.claude/skills` nem `.claude/skills`. Ele acha a skill por
  `~/.agents/skills/<skill>`, um symlink para `~/.claude/skills/<skill>`:

  ```sh
  ln -s ~/.claude/skills/<skill> ~/.agents/skills/<skill>
  ```

- Um link por skill, nunca a pasta inteira: o link de `~/.agents/skills` para `~/.claude/skills`
  arrasta o `synced/` do app e duplica skills.
- Skill nova ganha o link junto com a linha no `.gitignore`; o `--check` cobra o link.
