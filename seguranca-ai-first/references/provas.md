# Provas do piso: correção e teste de cada atalho

Exemplos em Python, porque foi onde a medição rodou. Os nomes (`financas`, `Lancamento`,
`ArquivoGrandeDemais`) são do exemplo; troque pelos do projeto. Em projeto com a python-on-rails,
os testes que sobem processo ou navegador levam o marcador `e2e`.

## 1. Arquivo de fora: parse em processo filho

O pai nunca importa a biblioteca de parse. Com import-linter, um contrato `forbidden` do módulo
do pai para `pypdf` e `openpyxl` mantém isso.

```python
# importador.py (o pai: tem o banco e o segredo)
import subprocess
import sys
import tempfile
from pathlib import Path

from pydantic import TypeAdapter

TETO_ENTRADA = 20 * 1024 * 1024
TETO_SAIDA = 5 * 1024 * 1024
TEMPO_PAREDE_S = 30
LANCAMENTOS = TypeAdapter(list[Lancamento])


def comando_do_parser(arquivo: Path) -> tuple[list[str], dict[str, str]]:
    """Pura: o teste confere o comando e o ambiente sem rodar nada."""
    comando = [sys.executable, "-I", "-m", "financas.parser_isolado", str(arquivo)]
    return comando, {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}


def ler_de_fora(arquivo: Path) -> list[Lancamento]:
    if arquivo.stat().st_size > TETO_ENTRADA:
        raise ArquivoGrandeDemais(arquivo)
    comando, ambiente = comando_do_parser(arquivo)
    with tempfile.TemporaryFile() as saida:
        try:
            fim = subprocess.run(  # noqa: S603  # motivo: comando montado acima, sem shell
                comando, env=ambiente, stdout=saida, stderr=subprocess.DEVNULL,
                timeout=TEMPO_PAREDE_S, check=False,
            )
        except subprocess.TimeoutExpired as erro:
            raise ParserEstourou(arquivo, "tempo") from erro
        if fim.returncode != 0:
            raise ParserEstourou(arquivo, f"código {fim.returncode}")
        saida.seek(0)
        dados = saida.read(TETO_SAIDA + 1)
    if len(dados) > TETO_SAIDA:
        raise ParserEstourou(arquivo, "saída grande demais")
    return LANCAMENTOS.validate_json(dados)
```

```python
# parser_isolado.py (o filho: sem segredo, sem banco, com teto)
import json
import resource
import sys
from pathlib import Path

TETOS = (
    (resource.RLIMIT_AS, 768 * 1024 * 1024),   # memória
    (resource.RLIMIT_CPU, 10),                 # segundos de CPU; o pai mede o tempo de parede
    (resource.RLIMIT_FSIZE, 5 * 1024 * 1024),  # o stdout é arquivo: a saída também tem teto
    (resource.RLIMIT_NOFILE, 64),
    (resource.RLIMIT_CORE, 0),                 # nada de core dump com o conteúdo lido
)


def main() -> None:
    for recurso, teto in TETOS:
        resource.setrlimit(recurso, (teto, teto))  # soft e hard: o filho não sobe de volta
    from financas.leitura import ler_arquivo  # a biblioteca de parse entra depois do teto

    lancamentos = ler_arquivo(Path(sys.argv[1]))
    json.dump([lancamento.para_dict() for lancamento in lancamentos], sys.stdout)


if __name__ == "__main__":
    main()
```

Sem rede, quando a máquina tem `bwrap`: prefixe o comando com
`bwrap --unshare-all --die-with-parent --ro-bind / / --dev /dev --proc /proc --tmpfs /tmp`.
O `/` só de leitura ainda deixa o parser ler a `$HOME`; sem rede ele não tem para onde mandar,
mas pode embutir o que leu no JSON. Para fechar isso, monte só `/usr`, o venv e o arquivo.

```python
def test_filho_nasce_sem_o_segredo(tmp_path: Path) -> None:
    comando, ambiente = comando_do_parser(tmp_path / "nota.pdf")
    assert set(ambiente) <= {"PATH", "LANG"}
    assert "-I" in comando


def test_arquivo_grande_recusado_antes_do_parse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    grande = tmp_path / "grande.pdf"
    with grande.open("wb") as arquivo:
        arquivo.truncate(TETO_ENTRADA + 1)  # esparso: não ocupa disco

    def nao_chame(*_: object, **__: object) -> None:
        raise AssertionError("o parser foi chamado")

    monkeypatch.setattr(subprocess, "run", nao_chame)
    with pytest.raises(ArquivoGrandeDemais):
        ler_de_fora(grande)
```

Teste de ponta, um por formato: gere no teste um arquivo que estoura o teto (planilha com
milhões de células repetidas, que comprime para poucos KB) e espere `ParserEstourou`, não
traceback nem processo pendurado.

## 2. Permissão só do dono

```python
import os
import sqlite3
import stat
from pathlib import Path


def main() -> None:
    os.umask(0o077)  # primeira linha do ponto de entrada, antes de qualquer arquivo
    ...


def abrir_banco(caminho: Path) -> sqlite3.Connection:
    caminho.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if caminho.exists():
        for arquivo in (caminho, *(caminho.with_name(caminho.name + s) for s in ("-wal", "-shm", "-journal"))):
            if arquivo.exists() and stat.S_IMODE(arquivo.stat().st_mode) & 0o077:
                arquivo.chmod(0o600)  # ou recusar, se a pessoa preferir saber
    else:
        caminho.touch(mode=0o600, exist_ok=False)
    return sqlite3.connect(caminho)
```

```python
def test_banco_novo_so_do_dono(tmp_path: Path) -> None:
    abrir_banco(tmp_path / "financas.db").close()
    assert stat.S_IMODE((tmp_path / "financas.db").stat().st_mode) == 0o600


def test_banco_aberto_e_corrigido(tmp_path: Path) -> None:
    caminho = tmp_path / "financas.db"
    caminho.touch()
    caminho.chmod(0o644)
    abrir_banco(caminho).close()
    assert stat.S_IMODE(caminho.stat().st_mode) == 0o600
```

A prova que pega o resto (cópia bruta, download, exportação): rodar o programa de ponta a ponta
num diretório temporário e conferir **tudo** o que ele criou.

```python
for criado in pasta_de_dados.rglob("*"):
    assert stat.S_IMODE(criado.stat().st_mode) & 0o077 == 0, criado
```

## 3. Navegador: conferir o processo vivo

```python
navegador = playwright.chromium.launch(headless=False, chromium_sandbox=True)
```

O mesmo argumento vale em `launch_persistent_context`. O Playwright fala com o navegador por
pipe; não acrescente `--remote-debugging-port`.

```python
import os
import re
from pathlib import Path


def cmdlines_descendentes(raiz: int) -> list[str]:
    pais: dict[int, int] = {}
    linhas: dict[int, str] = {}
    for processo in Path("/proc").iterdir():
        if not processo.name.isdigit():
            continue
        try:
            estado = (processo / "stat").read_text()
            linha = (processo / "cmdline").read_bytes()
        except OSError:
            continue  # o processo acabou entre a listagem e a leitura
        pid = int(processo.name)
        pais[pid] = int(estado.rsplit(")", 1)[1].split()[1])  # depois do nome vem estado e ppid
        linhas[pid] = linha.replace(b"\0", b" ").decode(errors="replace")

    def desce_da_raiz(pid: int) -> bool:
        while pid > 1:
            pid = pais.get(pid, 0)
            if pid == raiz:
                return True
        return False

    return [linhas[pid] for pid in pais if desce_da_raiz(pid)]


PORTA_FIXA = re.compile(r"--remote-debugging-port=(?!0\b)\d+")


def test_navegador_sobe_com_sandbox() -> None:
    with sync_playwright() as playwright:
        navegador = abrir_navegador(playwright)  # a função de produção, não um launch do teste
        try:
            linhas = cmdlines_descendentes(os.getpid())
        finally:
            navegador.close()
    assert any("chrom" in linha.lower() for linha in linhas), "navegador não achado"
    for linha in linhas:
        assert "--no-sandbox" not in linha, linha
        assert "--remote-allow-origins" not in linha, linha
        assert not PORTA_FIXA.search(linha), linha
```

Se o teste reprova porque o navegador não sobe com sandbox (container, namespace de usuário
desligado), o conserto não é tirar o argumento: é relatar e perguntar.

## 4. Segredo de ferramenta local

```python
import getpass

from keyring.backends import SecretService


def ler_token(servico: str, usuario: str) -> str:
    cofre = SecretService.Keyring()  # escolhido no código: o keyringrc.cfg da máquina não decide
    token = cofre.get_password(servico, usuario)
    if token is None:
        token = getpass.getpass("Token da API: ")
        cofre.set_password(servico, usuario, token)
    return token
```

Falha de acesso ao cofre (sessão sem Secret Service, cofre trancado) vira erro com a instrução
para a pessoa, nunca a troca silenciosa por arquivo.

Conferências, no portão ou no teste:

```sh
# exemplo de comando com segredo na documentação
rg -n -i '\b[A-Z0-9_]*(SENHA|PASSWORD|PASSWD|TOKEN|SECRET|SEGREDO|API_?KEY|CHAVE)[A-Z0-9_]*=[^ $]' README.md docs/
# segredo lido do ambiente, ou chaveiro sem backend escolhido
rg -n -i 'environ.*(senha|password|token|secret|chave)' src/
rg -n 'keyring\.(get|set)_password' src/
```

```python
def test_cli_nao_recebe_segredo() -> None:
    ajuda = criar_parser().format_help()
    assert not re.search(r"--(senha|password|token|secret|chave)", ajuda, re.IGNORECASE)
```

Cada `rg` deve sair sem nenhuma linha. Quando a variável de ambiente for legítima (segredo que a
plataforma injeta num serviço), a linha leva o motivo, como qualquer supressão.
