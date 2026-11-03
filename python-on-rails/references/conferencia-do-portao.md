# Conferência do portão

Ler quando o `conferir_trilho` reprovar e o motivo não estiver claro, ao adotar os trilhos num
projeto, ou quando alguém propuser framework, CLI ou pacote para esta skill.

## O que é

`scripts/conferir_trilho.py` compara o projeto com `assets/pyproject-trilho.toml` e reprova o que
afrouxa. Ele mora na pasta da skill e **nunca se copia**: o `portao.sh` o chama lá, e sem ele o
portão não aprova. Só a biblioteca padrão, sem rede e sem escrever nada. Não aceita argumento, e
nenhuma flag, variável de ambiente ou comentário desliga uma regra.

| Saída | Veredito | Quem age |
|---|---|---|
| 0 | `aprovado` | Ninguém |
| 1 | `conserte` | O agente conserta o que é `[agente]` e roda de novo |
| 2 | `indeterminado` | Não deu para julgar: fora do git, TOML inválido, sem `pyproject.toml`. Nunca aprova |
| 3 | `pare` | O agente relata o que é `[humano]` e para. Decisão humana |

O `make` troca qualquer falha por 2. Por isso a última linha da saída sempre diz o veredito.

## Regras

| Id | Dono | Reprova quando |
|---|---|---|
| CFG001 | agente | Há `ruff.toml` ou `.ruff.toml` em qualquer pasta, ou na raiz `pyrightconfig.json`, `pytest.ini`, `.pytest.ini`, `pytest.toml`, `.pytest.toml`, `.importlinter`, seção de pytest em `tox.ini` ou `setup.cfg`, seção `[importlinter]` em `setup.cfg`. Olha o disco, não o git, e pula as pastas que o ruff pula |
| CFG002 | humano | Há linha de base do basedpyright |
| CFG003 | humano | Há `pyproject.toml` aninhado com `[tool.*]`: pode ser outro projeto |
| GAT001 | humano | ruff afrouxado: prefixo fora de `select`, `ignore` ou `per-file-ignores` em regra do trilho, exclusão além de `.claude` e `.venv`, `include`, complexidade maior, regra de ambiente apagada, `ban-relative-imports` mudado, ou chave fora da lista das neutras, como `extend` e limites do pylint |
| GAT002 | humano | basedpyright afrouxado: modo fora de `recommended` e `all`, `failOnWarnings` falso, `enableTypeIgnoreComments` não falso, `report*` enfraquecido, `exclude`, `ignore`, `include` que tira `src` ou `tests`, ou chave fora da lista das neutras, como `executionEnvironments` |
| GAT003 | humano | pytest afrouxado: `xfail_strict`, `filterwarnings` (inclusive ação abreviada, como `i::`), `--strict-*`, `addopts` que esconde teste ou troca a configuração (`-W`, `-o`, `-c`), ou `norecursedirs` e `python_files` e afins |
| GAT004 | humano | Falta uma etapa no `portao.sh`, fora de comentário, ou ela está neutralizada (`\|\| true`, `--exit-zero`, `--ignore`, config que não é o `pyproject.toml`), ou o `check` do `Makefile` não roda o `portao.sh`. Sem `portao.sh`, confere o `Makefile` |
| GAT005 | humano | Não há contrato `forbidden` guardando `<pacote>.dominio` (chave `padrao.dominio-puro`), falta um módulo do asset em `forbidden_modules` (camada interna só se o projeto a tiver), ou há `ignore_imports` |
| AMB001 | agente | `uv.lock` fora do git |
| AMB002 | agente | `.python-version` ausente ou fora do git |
| AMB003 | agente | `pythonVersion` difere de `.python-version` e do piso de `requires-python` |
| AMB004 | agente | `requirements*.txt` no git que o `uv export` não gerou |
| SUP001 | agente | Supressão sem motivo, em `.py` e `.pyi`, rastreados ou novos, inclusive `cast` e `no_type_check` |
| SUP002 | agente | `skip` que não diz o motivo |
| DES001 | humano | Item do registro aponta ADR ausente, fora do projeto ou não aceito |
| DES002 | agente | Item do registro não casa com nada |

Só afrouxar reprova. `select = ["ALL"]`, modo `all`, linha mais curta, mais módulos proibidos no
contrato e opções extras no `addopts` passam. Marcador `e2e`, layout `src/`, concorrência,
Hypothesis e formato de log são decisão do projeto, e nenhuma regra os toca. O `per-file-ignores`
só conta em regra do trilho: `D` e `INP001` passam.

## O que ela não vê

| Assunto | Quem cuida |
|---|---|
| Ambiente lido fora do config | ruff `TID251`, no asset |
| Lock desatualizado | `uv lock --check` |
| `Any`, `print`, `except` amplo, `eval`, supressão inútil | ruff e basedpyright |
| `dict` solto, `frozen`, `SecretStr`, `datetime.now` no domínio, teste visto falhar, justificativa de dependência, qualidade do motivo | code-audit |

## O limite

Tirar a chamada do juiz de dentro do `portao.sh` não reprova ali: quem foi removido não pode
reclamar. Por isso há dois caminhos de fora:

- **`scripts/hook_juiz.sh`**, hook Stop do usuário, registrado uma vez por máquina em
  `~/.claude/settings.json` (instrução no topo dele). Roda o juiz em todo repositório que o adotou,
  sem passar pelo portão. A adoção se lê do histórico do git, então apagar a chamada ou o
  `portao.sh` não a desfaz. Repositório que nunca adotou não é julgado.
- **O CI do asset**, que chama o juiz direto.

O que continua passando: uma sessão de Codex ou de outra máquina não tem o hook; na segunda parada
seguida ele libera, para não prender a sessão em laço; e quem escreve em `~/.claude/settings.json`
o desliga. O modelo de ameaça é o agente que quer o verde, não um adversário: um ADR forjado ou um
workflow editado passam. Dentro do repositório não existe âncora contra quem escreve no
repositório, e o hook é a âncora fora dele.

## A decisão: skill com juiz externo, sem framework e sem CLI

Medido em 2026-11-03 em 7 projetos adotantes, com ruff 0.17.3 e basedpyright 1.40.2. As 11 formas
testadas de afrouxar o portão passavam caladas. O drift entre os projetos era quase todo adaptação
com ADR, e não atraso: 2 iguais ao `main`, 1 um commit atrás, 3 adaptados, 1 sem o script. Em dois
dias, a etapa de supressão tinha sido reescrita em três lugares.

| Opção | Por que não |
|---|---|
| Framework de runtime | Não há o que compartilhar em runtime: todo trilho age em tempo de desenvolvimento |
| CLI instalável fixada no lock | Pacote, release e nome para manter. O nome é um risco: `rails` é Ruby no treino do agente, e `rails` e `python-on-rails` no PyPI são outros pacotes |
| `new` e `drift` | `new` serviria a no máximo 3 dos 7, e o verde dele exigiria um teste que ninguém viu falhar. `drift` trata adaptação como problema |
| Copier | Pede repositório próprio com tag PEP 440: num monorepo copia tudo ou não grava `_commit`. O update escreve no projeto, e aqui o caso é conferir |
| Só regra escrita e etapa em bash | Regra se esquece. Etapa em bash no projeto o agente edita, e comparar TOML por sentido não cabe nela |
| Script copiado em cada projeto | Melhor que nada, mas fica ao alcance do agente e o conserto volta a ser colado à mão |
| Só o portão chamando o juiz | Não vê a própria remoção: faltava quem rodasse o juiz de fora, daí o hook do usuário |

Ganha: o juiz fica fora da área que o réu edita, e o conserto chega a todos sem colar nada.
Perde: uma mudança no script ou no asset pode reprovar vários projetos no mesmo dia, e o portão
depende da skill instalada na máquina. No CI o juiz vem de um commit fixo, então lá a mudança é
explícita.

Reabrir se: precisar rodar onde a skill não pode estar instalada, ou se um projeto precisar de
versões diferentes do juiz por muito tempo.
