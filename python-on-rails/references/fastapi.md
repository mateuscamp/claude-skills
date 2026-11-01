# FastAPI

Ler ao começar ou auditar um projeto FastAPI. Os trilhos da skill valem inteiros, e o asset
`pyproject-trilho.toml` funciona sem mudança. Este arquivo acrescenta o que é do framework.

**Medido em 2026-11-01** (esqueleto com rota, dependência injetada e dois testes, verde no
portão): fastapi 0.162, starlette 1.10, pydantic 2, Python 3.13. As regras marcadas *(prática)*
são conhecidas do ecossistema, mas não foram medidas aqui.

## Esqueleto

```
src/<pacote>/
  dominio/      regras de negócio, sem fastapi nem pydantic (import-linter reprova)
  infra/        repositório, cliente HTTP, implementação dos Protocols do domínio
  api/          rotas: traduzem HTTP para o domínio e de volta
  config.py     pydantic-settings, lido uma vez
  app.py        cria o FastAPI, liga as rotas e as dependências
tests/
```

Acrescente `"fastapi"` e `"starlette"` à lista `forbidden_modules` do contrato do domínio.

## Dependências

```bash
uv add fastapi "uvicorn[standard]" pydantic-settings
uv add --dev ruff basedpyright pytest import-linter httpx2
```

O `TestClient` do Starlette 1.10 usa o **`httpx2`**; com o `httpx` antigo ele emite
`DeprecationWarning`, e o `filterwarnings = error` do trilho reprova a coleta dos testes. Se a
mensagem for `No module named 'httpx2'`, é isso. Antes de fixar a dependência de teste num
projeto novo, confira no `METADATA` do Starlette instalado qual cliente ele pede.

## Regras

- **Tipo de retorno da rota é o modelo de resposta.** `async def ler(...) -> ItemSalvo:` já
  valida e documenta. Não repetir com `response_model=`, porque duas fontes divergem.
- **Dependência com `Annotated`.** `Repo = Annotated[Repositorio, Depends(repositorio)]` e
  usar `repo: Repo` na rota. Valor padrão `= Depends(...)` esconde o tipo.
- **Teste troca a dependência, não faz patch.** `app.dependency_overrides[repositorio] =
  lambda: fake`, com um fake novo por teste. Nada de `mock.patch` no módulo da rota.
- **Modelo de entrada e de saída separados.** `NovoItem` (sem `id`) e `ItemSalvo` (com `id`).
  Um modelo só para os dois vaza campo interno ou aceita campo que o cliente não deveria mandar.
- **Sem `**modelo.model_dump()`** para montar outro modelo: vira `Any` e o basedpyright reprova.
  Passe os campos nomeados.
- **Restrição no modelo, não na rota.** `Field(min_length=1)`, `Field(ge=0)`: o 422 sai de graça
  e o teste confere.
- **`HTTPException` só na camada `api/`.** O domínio levanta exceção própria. A rota (ou um
  `exception_handler` registrado no `app.py`) traduz para status HTTP *(prática)*.
- **`async def` só se a rota faz `await`.** Rota com I/O síncrono vai em `def` comum, que o
  FastAPI roda em thread. `async def` com chamada bloqueante trava o servidor inteiro *(prática;
  ruff `ASYNC` pega parte)*. Ver `concorrencia.md`.
- **Partida e parada no `lifespan`**, não em `on_event` (depreciado) *(prática)*. A config é
  criada ali e entregue por dependência.
- **Config por dependência.** `def config() -> Config` com cache, injetada como as outras, e
  sobrescrita no teste.

## Exemplo verde no portão

```python
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field


class NovoItem(BaseModel):
    nome: str = Field(min_length=1)
    preco_centavos: int = Field(ge=0)


class ItemSalvo(BaseModel):
    id: int
    nome: str
    preco_centavos: int


class Repositorio:
    def __init__(self) -> None:
        self._itens: dict[int, ItemSalvo] = {}

    def salvar(self, novo: NovoItem) -> ItemSalvo:
        salvo = ItemSalvo(
            id=len(self._itens) + 1, nome=novo.nome, preco_centavos=novo.preco_centavos
        )
        self._itens[salvo.id] = salvo
        return salvo

    def buscar(self, item_id: int) -> ItemSalvo | None:
        return self._itens.get(item_id)


_repositorio = Repositorio()


def repositorio() -> Repositorio:
    return _repositorio


Repo = Annotated[Repositorio, Depends(repositorio)]
app = FastAPI()


@app.post("/itens", status_code=status.HTTP_201_CREATED)
async def criar(novo: NovoItem, repo: Repo) -> ItemSalvo:
    return repo.salvar(novo)


@app.get("/itens/{item_id}")
async def ler(item_id: int, repo: Repo) -> ItemSalvo:
    item = repo.buscar(item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"item {item_id}")
    return item
```

```python
from fastapi.testclient import TestClient

from api.app import Repositorio, app, repositorio


def cliente() -> TestClient:
    novo = Repositorio()
    app.dependency_overrides[repositorio] = lambda: novo
    return TestClient(app)


def test_item_criado_pode_ser_lido() -> None:
    c = cliente()
    criado = c.post("/itens", json={"nome": "caneta", "preco_centavos": 250})
    assert criado.status_code == 201
    assert c.get(f"/itens/{criado.json()['id']}").json()["nome"] == "caneta"


def test_preco_negativo_e_recusado() -> None:
    assert cliente().post("/itens", json={"nome": "x", "preco_centavos": -1}).status_code == 422
```

No projeto real, `Repositorio` mora em `infra/` atrás de um `Protocol` do domínio. Aqui ficou
junto para o exemplo caber numa tela.
