<!--
Seção Python do AGENTS.md / CLAUDE.md, da skill python-on-rails.
Colar junto com o modelo da arquitetura-ai-first (que traz o ciclo TDD, a refatoração e as
fronteiras). Curto e imperativo: cada linha é relida a cada query. Apagar o que não se aplica.
-->

## Python

- Ambiente: `uv`. Dependência entra com `uv add` (ou `uv add --dev`), nunca `pip install`.
  Dependência nova exige justificativa no relatório: o que faz que a stdlib não faz, quem mantém.
  Confira o nome exato do pacote antes de adicionar.
- Portão: `make check`. Rode antes de dizer "pronto" e mostre a saída. O hook Stop roda o mesmo.
- Proibido mexer em `[tool.ruff]`, `[tool.basedpyright]`, `[tool.pytest]`, `[tool.importlinter]`
  ou acrescentar ignore/exclude/linha de base. Regra parece errada? Diga no relatório e pare.
- Supressão só com regra e motivo na mesma linha:
  `# pyright: ignore[reportX]  # motivo: <por quê>` · `# noqa: S603  # motivo: <por quê>`.
  `cast` também é supressão. Antes de suprimir, tente corrigir o tipo.

### Tipos e dados

- Toda função anotada. Proibido `Any`; `object` quando o tipo é realmente qualquer coisa.
- Proibido `dict` solto atravessando funções. Miolo: `@dataclass(frozen=True, slots=True)`.
  Borda (JSON, HTTP, env, arquivo): modelo pydantic ou `TypeAdapter`, validado na entrada.
- `Any` de biblioteca (ex.: `json.loads`) para na borda: valide antes de passar adiante.
- Conjunto fechado de casos: `Enum` + `match` com `case _: assert_never(x)`.
- Dinheiro em `Decimal` ou centavos `int`, nunca `float`. Data com fuso (`datetime.now(UTC)`).

### Erros

- Exceção de domínio própria (`class PedidoVazioError(ValueError)`), com o valor recebido e o
  esperado na mensagem.
- Proibido `except Exception`, `except:` e `except ...: pass`. Capture o tipo específico.
- Relançar com `raise NovoErro(...) from erro`. Nunca trocar exceção por `None` ou `{}` silencioso.

### Config e log

- Só `<pacote>/config.py` lê variável de ambiente, uma vez, na partida. O resto recebe o objeto.
- Segredo como `SecretStr`. Nunca em log, mensagem de erro ou teste.
- `logging.getLogger(__name__)`, nunca `print` fora da camada de interface (CLI).
- Log com fatos nomeados: `log.info("pedido fechado", extra={"pedido_id": id, "total": t})`.

### Testes

- pytest. Fake de borda (relógio, rede, disco) é uma classe tipada que cumpre o `Protocol` e
  guarda o que recebeu, injetada. `Mock` reprova no portão (`reportAny`): não suprima para usar.
- Nunca trocar por dublê o que está definido no módulo sob teste.
- Teste funcional: `@pytest.mark.e2e`, roda com `make e2e`. O da história em curso leva
  `@pytest.mark.xfail(raises=AssertionError, reason="FT em curso: <história>")`, um por vez.
- Sem `time.sleep` em teste. Esperar com `expect` do Playwright ou um helper com prazo constante.
- Hypothesis onde a regra vale para toda entrada (cálculo, parser, ida e volta de serialização).
- Warning em teste é erro (`filterwarnings = error`): corrija a causa, não filtre.
