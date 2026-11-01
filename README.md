# Claude Code skills

Skills I wrote and use daily with [Claude Code](https://claude.com/claude-code) (and Codex), mostly
for building games and software where **the agent writes the code and a person is the scarce
resource**.

The thread running through them: an agent's bottleneck is not how much code it writes, but how
much of its own work it can *prove* without a human saying "run it and tell me if it looks right".
So each skill turns a class of silent failures (the game that works, but not as intended; the
test that always passes; the architectural boundary that erodes in three sessions) into something
the agent can check by itself, before it says "done".

Every lesson in them is dated and traced to the project where it was measured (CampCrawler,
flipper-boom, Boomlitude and others), not copied from a style guide.

> The skills themselves are written in **Portuguese**. This page is in English so you can tell
> what each one does; see the [Portuguese summary](#resumo-em-português) below.

## The skills

### Games built by agents

| Skill | What it does |
|---|---|
| [`jogos-ai-first`](jogos-ai-first/SKILL.md) | Engine-agnostic decision method: the zero rule (the bottleneck is what only a person can verify), engine choice, project start by stop gates, refutable experiments with stop criteria fixed in advance, risk matrix and the agent's decision box. The code and verification patterns live in each engine skill; ADRs and fitness functions in depth, in `arquitetura-ai-first`. Grounded in a measured study of one agent building the same mobile game in Godot, Unity and Defold. |
| [`ai-first-godot`](ai-first-godot/SKILL.md) | Godot 4: engine-free domain in `RefCounted`, a single input adapter, seeded RNG, JSON event logs, and a verification gate that imports, compiles everything, runs the specs and reads the log instead of trusting the exit code. |
| [`ai-first-defold`](ai-first-defold/SKILL.md) | Defold: pure-Lua domain, engine-free test suite on LuaJIT and Lua 5.x, LuaLS, `bob` builds, robot-driven runs, Automation Bridge and editor API scripts. |
| [`ai-first-love`](ai-first-love/SKILL.md) | LÖVE (love2d): the scene as a **draw list**, so visual bugs become data the agent can test (layout invariants, pixel sampling, per-frame replay and diff), plus a custom `love.run`, headless passes under Xvfb and Android notes. |

The engine skills share two single-source lesson files ([`gerais-de-jogo.md`](gerais-de-jogo.md)
and [`gerais-de-lua.md`](gerais-de-lua.md)) that [`distribuir.py`](distribuir.py) copies into
each skill and checks for drift, with its own test suite in [`tests/`](tests/).

### Software engineering

| Skill | What it does |
|---|---|
| [`arquitetura-ai-first`](arquitetura-ai-first/SKILL.md) | Architecture decisions for agent-built backends and full-stack apps: drivers before technology, module boundaries drawn from subdomains and bounded contexts, trade-off analysis, numbered ADRs, each decision turned into an executable fitness function in CI and a rule in `AGENTS.md`, including TDD and refactoring with an agent. |
| [`code-audit`](code-audit/SKILL.md) | Audits PRs, local diffs and bug reports with verifiable evidence; evidence outranks the author's description, even when the author is another agent. Fixing is a separate mode that requires explicit approval. |
| [`python-on-rails`](python-on-rails/SKILL.md) | Rails for agent-written Python: what holds in every project (uv with a lockfile, a fixed ruff rule set, strict basedpyright that fails on warnings, pytest with tests seen failing first, a single `make check` gate shared by the agent, the Stop hook and CI, typed data, explicit errors, config validated at startup, dependency audit, suppressions only with a written reason), what is a default with a declared exit (`src/` layout, a pure domain enforced by import-linter), what each project decides, and FastAPI and Django references, all measured on throwaway projects. |

### Fiction editing

| Skill | What it does |
|---|---|
| [`revisao-de-capitulo`](revisao-de-capitulo/SKILL.md) | Structural diagnosis of a finished chapter: open scaffolding notes, real-world fact checks, scene-by-scene function in the arc, and a keep / rewrite / cut decision. Never rewrites the author's prose. |
| [`revisao-de-livro`](revisao-de-livro/SKILL.md) | Second pass over a whole book's chapter reviews, looking for what only exists *between* chapters: unpaid promises, shifting internal rules, characters who vanish, the reader's engagement curve. |

## Using them

Each folder with a `SKILL.md` is a self-contained skill. To use one in Claude Code, put the folder
in `~/.claude/skills/`:

```sh
git clone https://github.com/mateuscamp/claude-skills.git
cp -r claude-skills/ai-first-godot ~/.claude/skills/
```

How the repository itself is maintained (branches, generated copies, the Codex links) is in
[`CONTRIBUTING.md`](CONTRIBUTING.md).

## Credits

- `jogos-ai-first` and `arquitetura-ai-first` distill their decision method from *Fundamentals of
  Software Architecture* and *Software Architecture: The Hard Parts* (Richards, Ford, Sadalage,
  Dehghani).
- The layered-testing references of `arquitetura-ai-first` and `python-on-rails` (double-loop TDD,
  the test pyramid, test doubles, functional tests) adapt *Test-Driven Development with Python*,
  3rd edition (Harry Percival), freely readable at obeythetestinggoat.com.
- The domain reference of `arquitetura-ai-first` (subdomain types, ubiquitous language, bounded
  contexts, context map, the tactical decision tree and the test shape per pattern) adapts
  *Learning Domain-Driven Design* (Vlad Khononov).
- `code-audit` adapts the `pr-audit`, `iss-audit` and `github-resolution` rules described in an
  article by Fabio Akita; it is an adaptation, not a copy of the original files.

## License

[GNU AGPL-3.0](LICENSE).

## Resumo em português

Skills próprias do Claude Code, escritas em português e usadas no dia a dia. Quatro são de jogo
feito por agente (`jogos-ai-first`, que é o método, e uma por motor: Godot, Defold e LÖVE), três
de engenharia (`arquitetura-ai-first`, `code-audit` e `python-on-rails`) e duas de revisão de ficção
(`revisao-de-capitulo` e `revisao-de-livro`). A ideia comum é fazer o agente provar sozinho o que
hoje só uma pessoa consegue verificar. Cada lição traz a data e o projeto em que foi medida. A
operação do repositório está no [`CONTRIBUTING.md`](CONTRIBUTING.md).
