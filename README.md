# Skills do Claude Code

Skills próprias, carregadas de `~/.claude/skills/`.

- `ai-first-defold`: boas práticas AI-first e portão de verificação para jogos em Defold.
- `ai-first-godot`: o mesmo para Godot 4.
- `ai-first-love`: o mesmo para jogo em Lua com LÖVE (12.0 main, lido no fonte; medido no LÖVE
  só o boot, pela R0.1 do CampCrawler).
- `code-audit`: auditoria de PRs, diffs e issues com evidência verificável.
- `jogos-ai-first`: método e governança para jogo escrito por agente, em qualquer engine.
- `arquitetura-ai-first`: decisão de arquitetura em backend ou full stack feito com agentes
  (drivers, trade-off, ADR, fitness function).
- `revisao-de-capitulo` e `revisao-de-livro`: revisão de ficção, por capítulo e depois entre
  capítulos.

As quatro últimas nasceram no claude.ai e foram trazidas da cópia sincronizada (`synced/`) em
18/10/2026; daqui em diante a fonte delas é este `main`.

O `.gitignore` é lista de permissão: skill nova, e arquivo novo da raiz, só entram acrescentando
a linha deles.

## Gerais de jogo: uma fonte, uma cópia por skill de motor

- Lição de jogo que vale em qualquer engine se edita só em `gerais-de-jogo.md`, na raiz. Cada
  skill sai num zip próprio, então carrega a cópia dentro dela, em
  `<skill>/references/gerais-de-jogo.md`; a cópia nunca se edita à mão.
- As skills que recebem a cópia são a constante `GENERAL_LESSONS_SKILLS` do `distribuir.py`
  (hoje `ai-first-defold`, `ai-first-godot` e `ai-first-love`); skill de motor nova entra nela.
- O `armadilhas.md` das skills de motor ficou só com o ponteiro na seção "Gerais de jogo": lição
  geral nunca entra ali.
- Depois de editar a fonte, na worktree do ramo, regrave as cópias, faça commit das quatro e
  confira o commit antes do PR:

  ```sh
  W=~/.cache/claude-skills-wt/<ramo>
  $W/distribuir.py --repo $W --copiar-gerais
  # commit da fonte e das cópias
  $W/distribuir.py --repo $W --check-gerais
  ```

- O `--copiar-gerais` recusa o checkout que está no ref (o `main` da pasta compartilhada) e o HEAD
  desanexado, e desfaz a cópia que virou symlink.
- O `--check-gerais` lê o HEAD de `--repo` (ou o `--ref`) e só confere as Gerais, sem o destino,
  os links e o checkout que o `--check` também cobra. Reprova cópia ausente, diferente da fonte ou
  symlink; cópia numa skill fora da `GENERAL_LESSONS_SKILLS`; item de lista ou subtítulo na seção
  "Gerais de jogo" de um `.md` das skills da lista (a lição escrita no lugar velho, ou a seção
  inteira de volta por um merge com um ramo anterior à fonte única); e item da fonte repetido
  num desses `.md`. O `--check` cobra o mesmo no `main`, e a geração recusa antes de escrever.
- Mudou o `distribuir.py`? Rode os testes, que montam repositórios temporários (só a biblioteca
  padrão, sem rede):

  ```sh
  python3 tests/test_distribuir.py
  ```

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
- se as Gerais de jogo do `main` têm problema (seção acima), lista e recusa sem escrever nada.

```sh
~/.claude/skills/distribuir.py           # depois de cada merge no main
~/.claude/skills/distribuir.py --check   # antes de subir um zip no claude.ai
```

O `--check` só lê e sai com 1 listando cada problema:

- cópia de Documentos diferente do `main`, ou ausente;
- as Gerais de jogo no `main`, como o `--check-gerais` (seção "Gerais de jogo", acima);
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
- Skill nova ganha o link junto com o `SKILL.md`; o `--check` cobra o link de toda pasta com
  `SKILL.md`. Pasta sem ele não é skill para o `distribuir.py` nem para o Codex, e fica sem
  link.
