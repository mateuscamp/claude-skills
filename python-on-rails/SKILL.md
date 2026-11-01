---
name: python-on-rails
description: Trilhos AI-first para projeto Python escrito por agente - o que vale em todo projeto (uv com lock, ruff, basedpyright estrito, pytest com TDD, portão único `make check` no agente, no hook Stop e no CI, dados tipados, erros explícitos, config validada na partida, logging, uv audit, supressão só com motivo), o padrão com desvio declarado (src/, domínio puro com import-linter), o que se decide por projeto (concorrência, Hypothesis, formato de log) e as referências de FastAPI e Django. Use sempre que o projeto for Python maior que um script - novo, existente ou auditoria - e quando o assunto for pyproject, uv, ruff, basedpyright, pyright, ty, Any, type ignore, noqa, pytest, Hypothesis, portão, make check, pydantic, dict solto, except amplo, mock, teste funcional, e2e, variável de ambiente, logging, print, vulnerabilidade, import-linter, asyncio, FastAPI, Django ou "o agente desligou a regra para passar". Complementa a arquitetura-ai-first (método, ADR, TDD) e a code-audit (auditoria).
---

# Python on Rails

Python aceita quase tudo: `dict` em vez de tipo, `except Exception: pass`, `Any`, `print`
esquecido, dependência instalada por fora. Para uma pessoa isso é flexibilidade. Para um agente
é um atalho, porque ele quer o verde e o Python deixa chegar lá sem resolver o problema. Esta
skill fecha esses atalhos com ferramentas que reprovam, e não com conselho que o agente esquece
na próxima sessão.

O método (drivers, ADR, fitness function, ciclo TDD, refatoração, modelo de `AGENTS.md`) fica na
skill **arquitetura-ai-first**. A auditoria de PR e de issue, inclusive a conferência do teste
visto falhar, fica na **code-audit**. Aqui fica só o que é de Python: qual ferramenta cumpre cada
regra, com qual configuração, e como o agente fecha o ciclo sozinho.

Arquivos desta skill:
- `assets/pyproject-trilho.toml`: a configuração de ruff, basedpyright, pytest e import-linter,
  validada. Colar no `pyproject.toml`.
- `assets/Makefile` e `scripts/portao.sh`: o portão único. `scripts/hook_portao.sh`: o hook Stop.
- `assets/AGENTS-python.md`: a seção Python do `AGENTS.md`, com as regras que o agente relê.
- `references/`: lidas sob demanda (tabela no fim).

## O critério: o que vira trilho

Uma regra vira **trilho** quando protege contra um erro *do agente*. Esses erros são os mesmos
em qualquer domínio: engolir exceção, usar `Any`, desligar a regra que reclamou, testar depois.
Uma regra fica como **decisão do projeto** quando depende *do domínio*: o que o sistema faz,
para quem, em que escala. No meio fica o **padrão com desvio**, que vale por omissão mas tem
casos legítimos de saída, e cada saída é declarada num ADR.

Ao propor regra nova para esta skill, aplique o mesmo teste. Se a regra só faz sentido em parte
dos projetos, ela não é trilho. Se não dá para conferir por ferramenta, ela vai para o
`AGENTS.md` e para a code-audit, não para o portão.

## Quando usar

"Maior que um script" quer dizer qualquer um destes: mais de um módulo, vida maior que uma
semana, outra pessoa ou outro agente vai mexer, ou o código vai ter teste. Script de uma tarde,
de um arquivo só, não precisa do portão, e a cerimônia não se paga.

## Procedimento

**Projeto novo**
1. `uv init --package <nome>`, que já cria `src/`, `.python-version` e `pyproject.toml`.
   Use a versão estável mais nova do Python que as dependências suportam.
2. `uv add --dev ruff basedpyright pytest import-linter`. Ferramenta entra no lock, não no
   sistema: duas máquinas rodam a mesma versão e dão o mesmo veredito.
3. Colar `assets/pyproject-trilho.toml`, copiar `assets/Makefile` e `scripts/` e registrar o
   hook Stop (instrução no topo de `scripts/hook_portao.sh`).
4. Colar `assets/AGENTS-python.md` no `AGENTS.md` do projeto, junto com o modelo da
   arquitetura-ai-first.
5. Primeiro ciclo: um teste vermelho visto falhar na asserção, o verde, `make check` e commit.
   O portão aprovado no commit inicial é a linha de base; a partir dela, só se anda no verde.
6. FastAPI ou Django: ler a referência correspondente antes do passo 3.

**Projeto existente**
1. Medir antes de mudar: rodar cada etapa do portão e contar as reprovações por regra.
2. Não corrigir tudo de uma vez. Ligar o portão com linha de base: `basedpyright
   --writebaseline` congela os erros atuais e reprova só os novos. No ruff, `ruff check
   --add-noqa` marca os existentes; depois acrescente `# motivo: legado, ver ADR-<n>` a cada
   marca, no mesmo commit. A linha de base é um desvio declarado, com ADR e prazo.
3. A dívida baixa por arquivo que a tarefa já toca, nunca num commit de "limpeza geral".

**Auditoria**: conferir o projeto contra os trilhos abaixo, um a um, e listar o que falta. Os
desvios não declarados entram como achado, e os declarados se conferem contra o ADR.

## Trilhos: sempre, em todo projeto

| Trilho | Quem reprova |
|---|---|
| uv, `pyproject.toml`, `uv.lock` versionado e `.python-version`. Nada de `pip install` solto nem `requirements.txt` à mão | `uv lock --check` no portão |
| ruff format e ruff check, com a lista de regras do asset | portão |
| basedpyright no modo `recommended`, com `failOnWarnings`. Sem `Any`, sem `dict`/`list` sem parâmetro de tipo | portão |
| Supressão só com regra nomeada e motivo na mesma linha: `# pyright: ignore[regra]  # motivo: ...` | ruff `PGH`, basedpyright e grep do portão |
| pytest com TDD visto falhar, xfail estrito e warning virando erro. O ciclo está na arquitetura-ai-first | portão, code-audit |
| Portão único: `make check` no agente, no hook Stop e no CI, o mesmo comando. Os testes funcionais (`e2e`) ficam no `make e2e`, obrigatório no CI | hook Stop, CI |
| Dados tipados: nenhum `dict` solto atravessando funções. Borda com validação, miolo com `dataclass(frozen=True, slots=True)` | basedpyright (`reportAny`, `reportUnknown*`) |
| Erros explícitos: exceção de domínio própria, sem `except` amplo, `raise from`, `match` exaustivo com `assert_never` | ruff `BLE`, `S110`, `TRY` e basedpyright |
| Config lida num lugar, na partida, validada num objeto tipado. Segredo como `SecretStr`, nunca no log | revisão: só um módulo lê o ambiente |
| `logging` no lugar de `print` fora da camada de interface | ruff `T20`, `LOG`, `G` |
| Dependência com vulnerabilidade conhecida reprova. Sem `eval`/`pickle` em dado externo. Dependência nova só com justificativa | `uv audit` no portão, ruff `S` |
| O agente nunca afrouxa o portão para passar | code-audit, `AGENTS.md` |

Os exemplos de código de cada trilho estão em `references/padroes-de-codigo.md`.

## Padrão com desvio declarado

Vale por omissão. Sair dele é legítimo, mas exige ADR com o motivo e o que se perde.

- **Layout `src/`**: os testes rodam contra o pacote instalado, não contra a pasta corrente.
  Desvio típico: framework com layout próprio (Django).
- **Domínio puro**: a regra de negócio não importa infra, config nem biblioteca de borda, e
  relógio, rede e disco entram injetados por `typing.Protocol`. O contrato do import-linter no
  asset reprova a violação. Desvio típico: script de cola, CLI de uma função, CRUD que é quase
  só o framework.
- **pydantic na borda e dataclass no miolo**: a biblioteca da borda (pydantic, msgspec, attrs)
  pode mudar; o que não muda é ter validação na borda.

## Decisão do projeto

A skill dá o guia de escolha (`references/desvios-e-decisoes.md`), e o projeto registra a
escolha em ADR:

- **Concorrência**: asyncio, threads ou processos. `references/concorrencia.md`, lida só quando
  o projeto usa alguma das três.
- **Hypothesis**: onde o teste por propriedade compensa (cálculo, parser, serialização de ida e
  volta).
- **Formato do log**: JSON num serviço, texto numa CLI para humano.
- **Aplicação ou biblioteca**: muda a versão mínima do Python e o que se publica.
- **Framework, banco, ORM**: decisão arquitetural, pela arquitetura-ai-first. Para FastAPI e
  Django, os trilhos ganham regras próprias em `references/fastapi.md` e `references/django.md`.

## Em estudo, fora do portão: ty

O ty (Astral) é o candidato a type checker mais rápido. Ele só vira trilho depois de passar no
procedimento de `references/estudo-ty.md`: rodar em paralelo ao basedpyright e perguntar
primeiro se *preserva* o que o basedpyright pega e depois se *acrescenta* algo.

## Regras invioláveis para o agente

1. **Não declarar pronto sem `make check` verde**, e mostrar a saída dele no relatório.
2. **Nunca afrouxar o portão para passar**: não editar `[tool.ruff]`, `[tool.basedpyright]`,
   `[tool.pytest]` nem `[tool.importlinter]`, e não acrescentar `ignore`, `per-file-ignores`,
   `exclude` ou linha de base. Se a regra parece errada, dizer no relatório e parar. Mudança no
   portão é decisão humana, com ADR.
3. **Supressão é a última saída**: antes, tentar corrigir o tipo. Se suprimir, nomear a regra e
   escrever o motivo. `cast` também é supressão e segue a mesma regra.
4. **`Any` vindo de biblioteca para na borda**: validar (`TypeAdapter`, modelo pydantic) ou
   envolver numa função tipada. Não deixar o `Any` vazar para dentro.
5. **Dependência nova só com justificativa** no relatório: o que ela faz que a biblioteca padrão
   não faz e quem a mantém. Conferir o nome exato antes de `uv add`, porque pacote de nome
   parecido é ataque conhecido.
6. **Teste visto falhar na asserção antes do código** (arquitetura-ai-first). `ImportError` não
   é vermelho.

## Referências

Ler sob demanda, nunca todas de uma vez:

| Arquivo | Ler quando |
|---|---|
| `references/padroes-de-codigo.md` | Escrever ou revisar código: dados tipados, erros, config, logging, domínio puro |
| `references/desvios-e-decisoes.md` | Sair de um padrão ou tomar uma decisão de projeto |
| `references/testes.md` | Teste funcional, marcador `e2e`, dublê, `Mock`, Playwright, teste sumido da coleta |
| `references/concorrencia.md` | O projeto usa ou vai usar asyncio, threads ou processos |
| `references/fastapi.md` | Projeto FastAPI |
| `references/django.md` | Projeto Django |
| `references/estudo-ty.md` | Avaliar o ty ou outro type checker |
