# Django

Ler ao começar ou auditar um projeto Django. Os trilhos valem, mas o Django é o caso que mais
exige ajuste: ele tem layout próprio, gera código e não traz tipos. Cada ajuste abaixo é um
desvio declarado e já vem com o motivo.

**Medido em 2026-11-01** (projeto do `startproject`, uma app com modelo e teste de banco, verde
no portão e no `manage.py check`): Django 6.1, django-stubs 6.1, pytest-django 4.14, Python 3.13.
As regras marcadas *(prática)* não foram medidas aqui.

## Dependências

```bash
uv init --app --name <projeto> .
uv add django
uv add --dev ruff basedpyright pytest pytest-django django-stubs import-linter
uv run django-admin startproject config .
```

Sem o `django-stubs`, o basedpyright vê quase tudo do Django como `Unknown` e o portão reprova
em massa. Ele é obrigatório, com a mesma versão principal do Django.

## Ajustes no asset `pyproject-trilho.toml` (desvio de layout, um ADR)

```toml
[tool.ruff]
src = ["."]
extend-exclude = ["**/migrations/**"]   # código gerado: a checagem é o makemigrations

[tool.ruff.lint.per-file-ignores]
"**/tests.py" = ["S101", "PLR2004", "ANN401"]
"**/test_*.py" = ["S101", "PLR2004", "ANN401"]

[tool.basedpyright]
include = ["config", "<apps>", "manage.py"]
exclude = ["**/migrations"]

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings"
python_files = ["tests.py", "test_*.py"]
testpaths = ["<apps>"]
```

Sem `python_files`, o pytest não coleta o `tests.py` que o `startapp` cria e diz "no tests ran",
com código de saída diferente de zero.

## Arquivos que o Django gera: corrigir uma vez, na criação

O `startproject` e o `startapp` geram código que reprova no portão. Corrija tudo no primeiro
commit, à mão, em vez de excluir os arquivos da checagem:

| Arquivo | Reprova por | Correção |
|---|---|---|
| `config/settings.py` | `SECRET_KEY` no código (`S105`), `TEMPLATES` sem tipo | `SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]`, `DEBUG = os.environ.get("DJANGO_DEBUG") == "1"`, `ALLOWED_HOSTS: list[str]`, `TEMPLATES: list[dict[str, object]]` |
| `config/asgi.py`, `wsgi.py` | retorno de `setdefault` ignorado | `_ = os.environ.setdefault(...)` |
| `manage.py` | sem anotação, import dentro da função | import no topo, `def main() -> None` |
| `<app>/apps.py` | `name` sem anotação | `name: str = "<app>"` |
| `<app>/admin.py`, `views.py` | import não usado | esvaziar até ter uso |

O `settings.py` lendo o ambiente cumpre o trilho de config na partida: sem a variável, o Django
nem sobe. O teste também precisa dela, por variável no CI ou por um `config/settings_teste.py`
apontado no `DJANGO_SETTINGS_MODULE` do pytest *(prática)*.

## Modelos tipados

```python
from __future__ import annotations

from typing import ClassVar, override

from django.db import models


class Produto(models.Model):
    nome: models.CharField[str, str] = models.CharField(max_length=100)
    preco_centavos: models.PositiveIntegerField[int, int] = models.PositiveIntegerField()

    objects: ClassVar[models.Manager[Produto]] = models.Manager()

    @override
    def __str__(self) -> str:
        return self.nome
```

- **Campo anotado com o genérico do stub** (`CharField[str, str]`: tipo que entra e tipo que
  sai). Sem a anotação, o basedpyright reprova o campo como parcialmente desconhecido.
- **`from __future__ import annotations` no Python 3.13**: sem ele, `CharField[str, str]` quebra
  na importação (`TypeError: type 'CharField' is not subscriptable`), porque o Django não é
  genérico em tempo de execução. No 3.14 a avaliação adiada é o padrão e a linha deve sobrar
  (não medido). A alternativa é `django_stubs_ext.monkeypatch()` no settings.
- **`objects` declarado** com `ClassVar[models.Manager[Modelo]]`, para as consultas saírem
  tipadas.
- **`@override` no `__str__`** e em todo método herdado.
- `class Meta` com lista mutável dispara o `RUF012`: `per-file-ignores` só no `models.py` que
  precisar *(prática)*.

## Domínio puro no Django

É o lugar onde o desvio é mais comum, e ele é legítimo. Um CRUD com admin é quase só framework:
declare o desvio no ADR e não force camadas vazias. Quando aparecer regra de negócio não trivial
(cálculo, máquina de estado, política), ela sai para um pacote `dominio/` sem `django`,
conferido pelo import-linter, e os modelos e as views passam a chamá-lo *(prática)*. O gatilho
para essa extração vai escrito no ADR do desvio.

## Testes

- `pytest-django` com `@pytest.mark.django_db` só nos testes que tocam o banco. O teste de
  regra de domínio não precisa de banco, e isso é o sinal de que a regra está no lugar certo.
- Fixture de dados criada no teste, não por `fixtures/*.json` compartilhado *(prática)*.
- E-mail: a fixture `mailoutbox`, não patch. O settings precisa de `MAILERS` no Django 6.1, ou
  o aviso de depreciação reprova o teste. Teste funcional com `live_server`: `references/testes.md`.
