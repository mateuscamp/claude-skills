# Padrões de código

Ler ao escrever ou revisar código Python num projeto com os trilhos. Cada seção traz a regra, o
porquê para o agente e o exemplo. Todo exemplo daqui passou no portão do asset em 2026-11-01.

## Índice

- [Dados tipados](#dados-tipados)
- [Erros explícitos](#erros-explícitos)
- [Config validada na partida](#config-validada-na-partida)
- [Logging](#logging)
- [Domínio puro](#domínio-puro)
- [Supressão](#supressão)
- [O que o portão pega que o agente não espera](#o-que-o-portão-pega-que-o-agente-não-espera)

## Dados tipados

`dict[str, Any]` atravessando funções é o maior gerador de bug silencioso em código escrito por
agente: a chave errada vira `KeyError` em produção ou, pior, `None` com `.get()`. O tipo é a
especificação que o agente não consegue ignorar, porque o basedpyright reprova.

```python
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Item:
    nome: str
    preco: Decimal
    quantidade: int
```

- **Miolo**: `dataclass(frozen=True, slots=True)`. `frozen` impede a mutação escondida, e
  `slots` impede atributo criado por erro de digitação.
- **Borda** (JSON, HTTP, env, arquivo): pydantic `BaseModel` ou `TypeAdapter`. É ali que a
  entrada não confiável vira tipo.
- **`TypedDict`**: só quando o formato é imposto de fora e precisa continuar sendo `dict`.
- **`json.loads` devolve `Any`**, e o basedpyright reprova (`reportAny`) quando esse valor
  escapa. Valide na hora: `TypeAdapter(list[Item]).validate_json(texto)`.

## Erros explícitos

Quando o verde demora, o atalho do agente é `try/except Exception: pass` ou devolver `{}`. O
programa "funciona" e o defeito some do log.

```python
from enum import Enum, auto
from typing import assert_never


class PedidoVazioError(ValueError):
    """Pedido sem itens não tem total."""


class Cupom(Enum):
    NENHUM = auto()
    FRETE_GRATIS = auto()


def total(itens: list[Item], cupom: Cupom, frete: Decimal) -> Decimal:
    if not itens:
        msg = f"pedido sem itens; esperado ao menos 1, recebido {len(itens)}"
        raise PedidoVazioError(msg)
    bruto = sum((i.preco * i.quantidade for i in itens), Decimal(0))
    match cupom:
        case Cupom.NENHUM:
            return bruto + frete
        case Cupom.FRETE_GRATIS:
            return bruto
        case _:
            assert_never(cupom)
```

- Exceção própria, herdando da exceção padrão mais próxima, com o valor recebido e o esperado.
- `match` com `assert_never`: quando alguém acrescenta um caso ao `Enum`, o basedpyright aponta
  todo `match` que não o trata.
- Relançar com `raise ... from erro`, para a causa original aparecer no traceback.
- Na borda (rota HTTP, comando de CLI), a exceção de domínio vira resposta. Esse é o único
  lugar onde se captura amplo, e é para registrar e responder, nunca para engolir.

## Config validada na partida

`os.environ["X"]` espalhado pelo código quebra uma hora depois da partida, no primeiro uso, com
`KeyError` ou `None`. Validar tudo na partida faz o erro aparecer no primeiro segundo, com o nome
da variável que falta.

```python
from typing import ClassVar

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_prefix="APP_", frozen=True
    )

    url_banco: str
    chave_api: SecretStr
    porta: int = 8000
```

- Um módulo só (`config.py`) lê o ambiente. O objeto é criado no ponto de entrada e passado
  adiante; ninguém mais importa `os.environ`.
- `SecretStr` aparece como `**********` em `repr` e em log. O valor só sai com
  `.get_secret_value()`, no ponto exato de uso.
- `model_config` precisa da anotação `ClassVar[...]`, senão o basedpyright reprova
  (`reportUnannotatedClassAttribute`).
- Sem pydantic, uma `dataclass` com uma função `carregar_config() -> Config` cumpre o trilho. O
  trilho é validar na partida, não a biblioteca usada.

## Logging

O agente lê log para saber o que aconteceu. `print` não tem nível, não tem origem e se mistura
com a saída do programa.

- `log = logging.getLogger(__name__)` em cada módulo. A configuração (nível, formato, destino)
  fica num lugar só, no ponto de entrada.
- Fato com campo nomeado: `log.info("pedido fechado", extra={"pedido_id": p.id})`. Nada de
  f-string na mensagem (ruff `G004`), porque a mensagem fixa é o que se busca com grep.
- `log.exception(...)` dentro do `except`, para levar o traceback.
- Formato (JSON ou texto) é decisão do projeto: ver `desvios-e-decisoes.md`.
- `print` só na camada de interface (CLI), com `per-file-ignores` para `T201` naquele módulo,
  declarado.

## Domínio puro

A regra de negócio que lê relógio, rede ou disco por conta própria só se testa devagar ou de
forma instável, e o TDD morre. Com a dependência injetada, o teste passa um fake e roda em
milissegundos.

```python
from datetime import datetime
from typing import Protocol


class Relogio(Protocol):
    def agora(self) -> datetime: ...


def vencido(prazo: datetime, relogio: Relogio) -> bool:
    return relogio.agora() > prazo
```

- O domínio define o `Protocol`, e a infra o implementa. A seta nunca inverte.
- O contrato do import-linter no asset reprova `dominio` importando `infra`, `config` ou
  biblioteca de borda. Acrescente ao contrato as bibliotecas de borda do projeto.
- Fronteira que não aparece na árvore de diretórios não é fronteira (arquitetura-ai-first).

## Supressão

Toda supressão é uma afirmação: "aqui a ferramenta está errada". Sem motivo escrito, a próxima
sessão não sabe se a afirmação ainda vale.

```python
resultado = subprocess.run(cmd, check=True)  # noqa: S603  # motivo: cmd é lista fixa, sem entrada do usuário
valor = lib.coisa()  # pyright: ignore[reportUnknownVariableType]  # motivo: lib sem stubs, ver issue 12
```

- `# type: ignore` está desligado (`enableTypeIgnoreComments = false`). Só vale
  `# pyright: ignore[regra]`, que diz qual regra está calando.
- O portão reprova qualquer `noqa`, `pyright: ignore` ou supressão de arquivo sem `motivo:` na
  mesma linha.
- Supressão desnecessária também reprova (`reportUnnecessaryTypeIgnoreComment`, ruff `RUF100`).

## O que o portão pega que o agente não espera

Medido nos projetos de teste da skill, em 2026-11-01:

- `**modelo.model_dump()` para montar outro modelo: o resultado é `Any` e o basedpyright
  reprova. Passe os campos nomeados.
- `json.loads`, `requests.Response.json()` e afins devolvem `Any`: valide antes de usar.
- Atributo de classe sem anotação (`model_config`, `name` de `AppConfig`): reprova se a classe
  não for `@final`.
- Método que sobrescreve outro sem `@override` (`typing.override`): reprova.
- Valor de retorno ignorado (`reportUnusedCallResult`): atribua a `_` quando for intencional.
- Biblioteca que depreciou algo: com `filterwarnings = error`, o teste reprova no dia em que a
  depreciação chega. Foi assim que o TestClient do Starlette 1.10 mostrou que o `httpx` deu
  lugar ao `httpx2` (ver `fastapi.md`).
