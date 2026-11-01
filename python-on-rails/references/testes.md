# Testes em Python: camadas, dublês e teste funcional

Ler quando o projeto tiver teste funcional (navegador ou servidor vivo), dublê de
qualquer tipo, ou quando a suíte começar a ficar lenta. O método (ciclo duplo,
pirâmide, dublê como desvio, erro deliberado) está na arquitetura-ai-first, em
`references/testes-em-camadas.md`; aqui fica só a tradução para pytest.

**Medido em 2026-11-01** com Python 3.13.13, pytest 9.2, pytest-django 4.14,
Django 6.1, basedpyright 1.40.2 e ruff 0.17.3, com o asset
`pyproject-trilho.toml`. As regras marcadas *(não medido)* vêm do livro de
Percival (*TDD with Python*, 3ª ed.) e da documentação, sem medição aqui.

## O marcador `e2e` e os dois alvos

O asset registra o marcador `e2e`, o `make check` roda `pytest -m "not e2e"` e o
`make e2e` roda `pytest -m e2e`. Teste funcional ganha `@pytest.mark.e2e`.

- **O marcador precisa estar registrado.** Com `--strict-markers` e sem a linha
  `markers` no `[tool.pytest.ini_options]`, o `pytest -m "not e2e"` não roda
  nenhum teste e sai com código 4. Projeto que copia o `portao.sh` novo copia
  também essa linha.
- `make e2e` sem nenhum teste `e2e` sai com código 5 ("no tests ran"). Projeto
  sem teste funcional não chama o alvo, nem no CI.
- O hook Stop roda o `make check` (`--rapido`), sem os funcionais. Eles rodam no
  CI e antes do commit que fecha a história. É desvio declarado do portão único
  (arquitetura-ai-first, "Onde cada camada roda").

## O teste funcional em curso

```python
@pytest.mark.e2e
@pytest.mark.xfail(raises=AssertionError, reason="FT em curso: história <n>, <nome>")
def test_visitante_cria_lista_e_volta_a_ela(pagina: Page) -> None:
    ...
```

Medido, com o `xfail_strict = true` do asset:

| O teste | Resultado |
|---|---|
| falha na asserção | `XFAIL`, a suíte segue verde |
| falha com `NameError`, `ImportError` ou erro de servidor | `FAILED`: `raises=AssertionError` só aceita a falha de asserção |
| passa | `FAILED [XPASS(strict)]`: obriga a tirar a marca no mesmo commit |

Sem `raises=AssertionError`, qualquer erro vira `XFAIL` e o teste funcional pode
ficar quebrado por motivo errado sem ninguém ver. Um teste em curso por vez, e
nunca num teste unitário.

## Dublês e o portão

- **O `Mock` comum reprova no portão.** Todo atributo de `mock.Mock()` e de
  `mock.create_autospec(...)` é `Any`, e o basedpyright avisa `reportAny` em
  cada acesso. Com `failOnWarnings`, isso inclui o `call_args` que se usa para
  conferir a chamada. O trilho já empurra para o dublê tipado: uma classe fake
  que cumpre o `Protocol` da borda e guarda o que recebeu.

  ```python
  @dataclass
  class CarteiroFalso:
      enviados: list[tuple[str, str]] = field(default_factory=list)

      def enviar(self, destino: str, texto: str) -> None:
          self.enviados.append((destino, texto))
  ```

  Com o fake tipado, o erro de digitação na conferência é erro de tipo.
- **Não suprimir o `reportAny` para usar `Mock`.** Se o projeto declarar o
  desvio (borda de terceiro sem `Protocol` viável), vale o que foi medido:
  - `carteiro.enviar.asssert_called_with(...)` (três "s") **passa sempre**. O
    Python só barra os prefixos `assert`, `assret`, `asert`, `aseert` e `assrt`.
    Conferir com `assert m.call_args == mock.call(...)`, ou usar
    `create_autospec`, que levanta `AttributeError` em qualquer nome errado.
  - `mock.patch("pacote.modulo.nome_errado")` levanta `AttributeError ... does
    not have the attribute`. Isso não é vermelho, é teste que não rodou.
  - O patch mira onde o nome é **procurado**: `pacote.modulo_sob_teste.cliente`,
    o nome que o módulo importou da borda. O proibido é trocar o que está
    **definido** no próprio módulo sob teste.
- **Dublê do framework antes de patch.** No Django com pytest-django, a fixture
  `mailoutbox` captura o e-mail enviado. Medido: ela funciona no Django 6.1, mas
  o settings precisa declarar `MAILERS`. Sem isso, o `send_mail` emite
  `RemovedInDjango2028Warning`, e o `filterwarnings = error` reprova o teste:

  ```python
  MAILERS = {"default": {"BACKEND": "django.core.mail.backends.smtp.EmailBackend"}}
  ```

## Teste sumido da coleta

Medido: `_test_x` e `xtest_x` não são coletados nem acusados por nenhuma
ferramenta. `DONT_test_x` também some da coleta, e só o ruff acusa, por acaso
(`N802`, nome com maiúscula). O grep por `skip`/`xfail` não vê nenhum dos três.
No CI, compare a contagem com a da base do PR:

```bash
uv run --locked pytest --collect-only -q | tail -1   # "<n> tests collected in ..."
```

A contagem caiu e o PR não apaga teste de forma declarada: reprova.

## Teste funcional com navegador *(não medido)*

- **Playwright no lugar do Selenium** do livro, pelo `pytest-playwright`. O
  `expect(locator).to_have_text(...)` já espera até o prazo dele, e isso dispensa
  o laço de espera feito à mão. Onde ainda precisar de espera própria, um helper
  só, com o prazo numa constante.
- **Servidor vivo:** fixture `live_server` do pytest-django. Ela pede sozinha o
  `transactional_db` (lido no código do pytest-django 4.14): o servidor roda em
  outra thread e não vê a transação do teste, então o dado é gravado de fato e
  o banco é esvaziado depois de cada teste. É mais lento que o `django_db`, um
  motivo a mais para poucos funcionais.
- **Captura na falha:** o `pytest-playwright` guarda captura de tela e trace com
  `--screenshot only-on-failure --tracing retain-on-failure`. No CI, publicar a
  pasta `test-results/` como artefato.
- **Sessão pré-autenticada:** só o teste de login percorre o login real. Os
  outros criam a sessão direto (no Django, `client.force_login` e o cookie
  copiado para o contexto do navegador, ou o `storage_state` do Playwright).
- **Objeto de página:** uma classe por página com os localizadores e as ações.
  Nenhum seletor repetido entre testes.

## Dados de teste

- Um helper com nome descritivo cria os dados no próprio teste
  (`criar_lista_com_itens(...)`), sem fixture em JSON (`django.md`). JSON quebra
  quando o schema muda e esconde qual campo importa para o teste.
- Objeto de modelo **não salvo** quando o teste não precisa do banco: fica sem
  `django_db` e roda mais rápido *(não medido)*.
- Regra de negócio presa ao ORM sobe primeiro para um método do modelo com nome
  de domínio (`Lista.criar_com_item(...)`). É o degrau antes do pacote `dominio/`
  do `django.md` *(não medido)*.
