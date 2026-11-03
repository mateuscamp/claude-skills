#!/usr/bin/env python3
"""Confere, de fora do projeto, se o portão python-on-rails foi afrouxado.

O `portao.sh` de cada projeto chama este arquivo na pasta da skill, e ele compara o projeto com
`assets/pyproject-trilho.toml`. Ele mora fora do projeto de propósito: o agente que quer o verde
não tem cópia para editar, e conserto aqui chega a todos sem colar nada. Só apertar é livre; o
que afrouxa reprova, a não ser que esteja em `[[tool.trilhos.desvios]]`, com ADR aceito.

Só a biblioteca padrão, sem rede e sem escrever nada. Não há flag, variável de ambiente nem
comentário que desligue uma regra.

Saída: 0 aprovado, 1 o agente conserta, 2 não deu para julgar, 3 pare: decisão humana.
"""

import ast
import io
import os
import re
import shlex
import subprocess
import sys
import tokenize
import tomllib
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

ASSET = Path(__file__).resolve().parents[1] / "assets" / "pyproject-trilho.toml"
PYPROJECT = "pyproject.toml"

AGENTE = "agente"
HUMANO = "humano"
SAIDA_CONSERTE = 1
SAIDA_INDETERMINADO = 2
SAIDA_PARE = 3

# As pastas que o ruff pula por padrão, mais a das worktrees de agente.
PASTAS_FORA = {
    ".claude", ".eggs", ".git", ".mypy_cache", ".nox", ".pytest_cache", ".ruff_cache", ".tox",
    ".venv", "__pycache__", "__pypackages__", "_build", "build", "dist", "node_modules",
    "site-packages", "venv",
}
EXCLUSOES_LIVRES = {".claude", ".venv"}

# Só estas chaves passam sem achado: enumerar as perigosas deixaria passar `extend`, limites do
# pylint e `executionEnvironments`, que levam a configuração para fora do que se confere aqui.
RUFF_NEUTRAS = {
    "cache-dir", "exclude", "extend-exclude", "extend-include", "fix", "force-exclude", "format",
    "include", "indent-width", "line-length", "lint", "namespace-packages", "output-format",
    "preview", "required-version", "respect-gitignore", "show-fixes", "src", "target-version",
    "unsafe-fixes",
}
LINT_NEUTRAS = {
    "exclude", "extend-fixable", "extend-ignore", "extend-per-file-ignores", "extend-select",
    "fixable", "flake8-tidy-imports", "ignore", "isort", "mccabe", "per-file-ignores", "preview",
    "pydocstyle", "select", "task-tags", "unfixable",
}
TIPOS_NEUTRAS = {
    "baselineFile", "enableTypeIgnoreComments", "exclude", "extraPaths", "failOnWarnings", "ignore",
    "include", "pythonPlatform", "pythonVersion", "strict", "typeCheckingMode", "venv", "venvPath",
}

MODOS_DE_TIPOS = {"recommended", "all"}
NIVEIS_FRACOS = {"none", "information", "hint"}
# O pytest aceita a ação abreviada (`i::UserWarning`): compara-se por prefixo.
AVISOS_CALADOS = ("ignore", "default", "always", "all", "module", "once")
ESCONDE_TESTE_EXATO = {"--co", "--collect-only"}
ESCONDE_TESTE_PREFIXO = (
    "--confcutdir", "--config-file", "--deselect", "--ignore", "--override-ini", "--pythonwarnings",
    "--rootdir", "-W", "-c", "-k", "-m", "-o", "-pno:",
)
ESCONDE_DA_COLETA = (
    "collect_imported_tests", "norecursedirs", "python_classes", "python_files", "python_functions",
)
ETAPAS = (
    "uv lock --check",
    "ruff format --check",
    "ruff check",
    "basedpyright",
    "pytest",
    "uv audit",
    "conferir_trilho",
)

CONFIG_EM_QUALQUER_PASTA = {"ruff.toml", ".ruff.toml"}
CONFIG_NA_RAIZ = {
    "pyrightconfig.json",
    "pytest.ini",
    ".pytest.ini",
    "pytest.toml",
    ".pytest.toml",
    ".importlinter",
}
SECOES_EM_INI = {
    "tox.ini": ("[pytest]",),
    "setup.cfg": ("[tool:pytest]", "[importlinter]"),
}
# Na linha da etapa, o que a faz aprovar sem conferir. `--config pyproject.toml`, `-c` e `-p`
# para o mesmo arquivo são legítimos: fixam a fonte da configuração.
NEUTRALIZA = re.compile(
    r"\|\||--exit-zero|--(?:extend-)?(?:ignore|select|exclude)\b|--isolated|--deselect|--skip"
    r"|PYTEST_ADDOPTS=|\s-[kW]\b|(?:--config|\s-[cp])[=\s]+(?!pyproject\.toml)\S"
)

# Medido no ruff 0.17.3: a diretiva só vale com `#` no começo do comentário ou depois de espaço.
# `# texto noqa` e `# `# noqa`` não calam nada e são prosa; `# texto # noqa` e `## noqa` calam.
DIRETIVA = re.compile(
    r"(?:^|[\s#])#\s*(?:noqa|flake8:\s*noqa|type:\s*ignore|pyright:|isort:\s*(?:skip|off)"
    r"|ruff:\s*(?:noqa|disable|ignore|file-ignore))",
    re.I,
)
SO_STRICT = re.compile(r"^#\s*pyright:\s*strict\s*$", re.I)
MOTIVO = re.compile(r"motivo:\s*\S", re.I)
ADR_ACEITO = re.compile(r"^\W*status\W+aceit", re.I | re.M)
PISO_DO_PYTHON = re.compile(r">=\s*(\d+\.\d+)")

CASTS = {"typing.cast", "typing_extensions.cast"}
SEM_TIPO = {"typing.no_type_check", "typing_extensions.no_type_check"}
PULOS = {
    "pytest.mark.skip",
    "pytest.mark.skipif",
    "pytest.skip",
    "unittest.skip",
    "unittest.skipIf",
    "unittest.skipUnless",
}


class IndeterminadoError(Exception):
    """O projeto não pôde ser lido; nada se aprova sem julgamento."""


@dataclass(frozen=True, slots=True)
class Achado:
    regra: str
    dono: str
    onde: str
    mensagem: str
    chave: str | None = None


@dataclass(frozen=True, slots=True)
class Projeto:
    raiz: Path
    pyproject: dict
    trilho: dict
    versionados: frozenset[str]
    fontes: tuple[str, ...]

    @property
    def tool(self) -> dict:
        return tabela(self.pyproject, "tool")


def tabela(origem: object, *chaves: str) -> dict:
    for chave in chaves:
        origem = origem.get(chave) if isinstance(origem, dict) else None
    return origem if isinstance(origem, dict) else {}


def textos(valor: object) -> list[str]:
    if isinstance(valor, str):
        return [valor]
    if isinstance(valor, list):
        return [item for item in valor if isinstance(item, str)]
    return []


def afrouxou(regra: str, chave: str, mensagem: str = "afrouxa o trilho") -> Achado:
    return Achado(regra, HUMANO, PYPROJECT, mensagem, chave)


def abrange(largo: str, estreito: str) -> bool:
    """Diz se o seletor do ruff `largo` inclui `estreito`: `B` não inclui `BLE001`, `PL` inclui `PLR`."""
    if largo in {"ALL", estreito}:
        return True
    if not estreito.startswith(largo):
        return False
    return largo == "PL" or estreito[len(largo)].isdigit()


def toca(codigo: str, prefixos: list[str]) -> bool:
    return any(abrange(p, codigo) or abrange(codigo, p) for p in prefixos)


def listas_do_ruff(projeto: Projeto, *nomes: str) -> list[str]:
    ruff = tabela(projeto.tool, "ruff")
    lint = tabela(ruff, "lint")
    return [item for nome in nomes for origem in (ruff, lint) for item in textos(origem.get(nome))]


def conferir_regras_do_ruff(projeto: Projeto) -> Iterator[Achado]:
    trilho = tabela(projeto.trilho, "ruff", "lint")
    prefixos = textos(trilho.get("select"))
    selecionados = listas_do_ruff(projeto, "select", "extend-select")
    for prefixo in prefixos:
        if not any(abrange(s, prefixo) for s in selecionados):
            yield afrouxou("GAT001", f"ruff.select:{prefixo}")
    aceitos = set(textos(trilho.get("ignore")))
    for codigo in listas_do_ruff(projeto, "ignore", "extend-ignore"):
        if codigo not in aceitos and toca(codigo, prefixos):
            yield afrouxou("GAT001", f"ruff.ignore:{codigo}")


def por_arquivo_do_trilho(projeto: Projeto) -> list[tuple[re.Pattern[str], set[str]]]:
    trilho = tabela(projeto.trilho, "ruff", "lint", "per-file-ignores")
    return [
        (re.compile(re.escape(caminho).replace("<pacote>", "[^/]+")), set(textos(codigos)))
        for caminho, codigos in trilho.items()
    ]


def conferir_por_arquivo(projeto: Projeto) -> Iterator[Achado]:
    prefixos = textos(tabela(projeto.trilho, "ruff", "lint").get("select"))
    permitidos = por_arquivo_do_trilho(projeto)
    lint = tabela(projeto.tool, "ruff", "lint")
    for nome in ("per-file-ignores", "extend-per-file-ignores"):
        for caminho, codigos in tabela(lint, nome).items():
            livres = {c for padrao, lista in permitidos if padrao.fullmatch(caminho) for c in lista}
            for codigo in textos(codigos):
                if codigo not in livres and toca(codigo, prefixos):
                    yield afrouxou("GAT001", f"ruff.per-file-ignores:{caminho}:{codigo}")


def limpo(padrao: str) -> str:
    return padrao.removeprefix("./").removeprefix("**/").removesuffix("/**").rstrip("/")


def conferir_exclusoes_do_ruff(projeto: Projeto) -> Iterator[Achado]:
    ruff = tabela(projeto.tool, "ruff")
    if "include" in ruff:
        yield afrouxou("GAT001", "ruff.include")
    excluidos = listas_do_ruff(projeto, "exclude", "extend-exclude")
    excluidos += textos(tabela(ruff, "format").get("exclude"))
    for padrao in excluidos:
        if limpo(padrao) not in EXCLUSOES_LIVRES:
            yield afrouxou("GAT001", f"ruff.exclude:{padrao}")


def conferir_chaves(projeto: Projeto) -> Iterator[Achado]:
    ruff = tabela(projeto.tool, "ruff")
    for chave in ruff.keys() - RUFF_NEUTRAS:
        yield afrouxou("GAT001", f"ruff.{chave}")
    for chave in tabela(ruff, "lint").keys() - LINT_NEUTRAS:
        yield afrouxou("GAT001", f"ruff.lint.{chave}")
    for chave in basedpyright(projeto).keys() - TIPOS_NEUTRAS:
        if not chave.startswith("report"):
            yield afrouxou("GAT002", f"basedpyright.{chave}")


def conferir_limites_do_ruff(projeto: Projeto) -> Iterator[Achado]:
    lint = tabela(projeto.tool, "ruff", "lint")
    trilho = tabela(projeto.trilho, "ruff", "lint")
    relativos = tabela(lint, "flake8-tidy-imports").get("ban-relative-imports")
    if relativos != tabela(trilho, "flake8-tidy-imports").get("ban-relative-imports"):
        yield afrouxou("GAT001", f"ruff.ban-relative-imports:{relativos}")
    limite = tabela(trilho, "mccabe").get("max-complexity")
    atual = tabela(lint, "mccabe").get("max-complexity")
    if not isinstance(atual, int) or not isinstance(limite, int) or atual > limite:
        yield afrouxou("GAT001", f"ruff.max-complexity:{atual}")
    banidas = tabela(lint, "flake8-tidy-imports", "banned-api")
    for nome in tabela(trilho, "flake8-tidy-imports", "banned-api"):
        if nome not in banidas:
            yield afrouxou("GAT001", f"ruff.banned-api:{nome}")


def basedpyright(projeto: Projeto) -> dict:
    return tabela(projeto.tool, "basedpyright") or tabela(projeto.tool, "pyright")


def conferir_tipos(projeto: Projeto) -> Iterator[Achado]:
    config = basedpyright(projeto)
    modo = config.get("typeCheckingMode")
    if modo is not None and modo not in MODOS_DE_TIPOS:
        yield afrouxou("GAT002", f"basedpyright.typeCheckingMode:{modo}")
    if config.get("failOnWarnings") is False:
        yield afrouxou("GAT002", "basedpyright.failOnWarnings")
    if config.get("enableTypeIgnoreComments") is not False:
        yield afrouxou("GAT002", "basedpyright.enableTypeIgnoreComments")
    for chave, valor in config.items():
        if chave.startswith("report") and (valor is False or valor in NIVEIS_FRACOS):
            yield afrouxou("GAT002", f"basedpyright.{chave}")


def conferir_alcance_dos_tipos(projeto: Projeto) -> Iterator[Achado]:
    config = basedpyright(projeto)
    for nome in ("exclude", "ignore"):
        for padrao in textos(config.get(nome)):
            if limpo(padrao) not in EXCLUSOES_LIVRES:
                yield afrouxou("GAT002", f"basedpyright.{nome}:{padrao}")
    incluidos = textos(config.get("include"))
    for pasta in ("src", "tests"):
        if incluidos and pasta not in incluidos and (projeto.raiz / pasta).is_dir():
            yield afrouxou("GAT002", f"basedpyright.include:{pasta}")


def conferir_linha_de_base(projeto: Projeto) -> Iterator[Achado]:
    padrao = projeto.raiz / ".basedpyright" / "baseline.json"
    if padrao.exists() or "baselineFile" in basedpyright(projeto):
        yield Achado(
            "CFG002",
            HUMANO,
            ".basedpyright/baseline.json",
            "a linha de base cala de uma vez todo erro listado nela",
            "basedpyright.linha-de-base",
        )


def argumentos_do_pytest(ini: dict) -> list[str]:
    return [argumento for item in textos(ini.get("addopts")) for argumento in shlex.split(item)]


def esconde_teste(argumento: str, anterior: str) -> bool:
    return (
        argumento in ESCONDE_TESTE_EXATO
        or argumento.startswith(ESCONDE_TESTE_PREFIXO)
        or (anterior == "-p" and argumento.startswith("no:"))
    )


def conferir_argumentos_do_pytest(projeto: Projeto, ini: dict) -> Iterator[Achado]:
    trilho = tabela(projeto.trilho, "pytest", "ini_options")
    argumentos = argumentos_do_pytest(ini)
    for exigido in argumentos_do_pytest(trilho):
        if exigido.startswith("--strict") and exigido not in argumentos:
            yield afrouxou("GAT003", f"pytest.addopts:{exigido}")
    for anterior, argumento in zip(["", *argumentos], argumentos, strict=False):
        if esconde_teste(argumento, anterior):
            yield afrouxou("GAT003", f"pytest.addopts:{argumento}")


def conferir_pytest(projeto: Projeto) -> Iterator[Achado]:
    ini = {**tabela(projeto.tool, "pytest"), **tabela(projeto.tool, "pytest", "ini_options")}
    yield from conferir_argumentos_do_pytest(projeto, ini)
    if str(ini.get("xfail_strict")).lower() != "true":
        yield afrouxou("GAT003", "pytest.xfail_strict")
    avisos = textos(ini.get("filterwarnings"))
    if "error" not in avisos:
        yield afrouxou("GAT003", "pytest.filterwarnings:error")
    for aviso in avisos:
        if any(acao.startswith(aviso.split(":")[0].strip()) for acao in AVISOS_CALADOS):
            yield afrouxou("GAT003", f"pytest.filterwarnings:{aviso}")
    for chave in ESCONDE_DA_COLETA:
        if chave in ini:
            yield afrouxou("GAT003", f"pytest.{chave}")
    pastas = textos(ini.get("testpaths"))
    if pastas and "tests" not in pastas and (projeto.raiz / "tests").is_dir():
        yield afrouxou("GAT003", "pytest.testpaths:tests")


def sem_comentario(texto: str) -> str:
    return "\n".join(re.sub(r"(^|\s)#.*$", "", linha) for linha in texto.splitlines())


def contratos(projeto: Projeto) -> list[dict]:
    lista = tabela(projeto.tool, "importlinter").get("contracts")
    return [c for c in lista if isinstance(c, dict)] if isinstance(lista, list) else []


def texto_se_existe(arquivo: Path) -> str:
    return sem_comentario(arquivo.read_text(encoding="utf-8")) if arquivo.is_file() else ""


def receita_de_check(makefile: str) -> str:
    achado = re.search(r"^check:(.*\n(?:\t.*\n?)*)", makefile, re.M)
    return achado.group(1) if achado else ""


def conferir_etapas(projeto: Projeto) -> Iterator[Achado]:
    portao = projeto.raiz / "scripts" / "portao.sh"
    makefile = texto_se_existe(projeto.raiz / "Makefile")
    # Só o que o `make check` executa conta: `make fmt` e `make test` não são o portão.
    linhas = (texto_se_existe(portao) if portao.is_file() else makefile).splitlines()
    if portao.is_file() and "portao.sh" not in receita_de_check(makefile):
        yield Achado("GAT004", HUMANO, "Makefile", "o check não roda o portão", "portao.make-check")
    etapas = (*ETAPAS, "lint-imports") if contratos(projeto) else ETAPAS
    for etapa in etapas:
        if not any(etapa in linha and not NEUTRALIZA.search(linha) for linha in linhas):
            mensagem = "etapa fora do portão ou neutralizada"
            yield Achado("GAT004", HUMANO, portao.name, mensagem, f"portao.etapa:{etapa}")


def existe_no_projeto(projeto: Projeto, modelo: str, modulo: str) -> bool:
    """O nome das camadas internas é layout do projeto: só se exige a que existe."""
    if not modelo.startswith("<pacote>."):
        return True
    caminho = Path(*modulo.split("."))
    bases = (projeto.raiz / "src" / caminho, projeto.raiz / caminho)
    return any(b.is_dir() or b.with_suffix(".py").is_file() for b in bases)


def conferir_fronteiras(projeto: Projeto) -> Iterator[Achado]:
    for contrato in contratos(projeto):
        for regra in textos(contrato.get("ignore_imports")):
            yield afrouxou("GAT005", f"importlinter.ignore_imports:{regra}")
    raiz = tabela(projeto.tool, "importlinter").get("root_package")
    do_dominio = [
        contrato
        for contrato in contratos(projeto)
        if contrato.get("type") == "forbidden"
        and f"{raiz}.dominio" in textos(contrato.get("source_modules"))
    ]
    if not do_dominio:
        yield afrouxou("GAT005", "padrao.dominio-puro", "sem contrato que guarde o domínio")
        return
    proibidos = {m for c in do_dominio for m in textos(c.get("forbidden_modules"))}
    for contrato in tabela(projeto.trilho, "importlinter").get("contracts", []):
        for modelo in textos(contrato.get("forbidden_modules")):
            modulo = modelo.replace("<pacote>", str(raiz))
            if modulo not in proibidos and existe_no_projeto(projeto, modelo, modulo):
                yield afrouxou("GAT005", f"importlinter.forbidden:{modulo}")


def versionado_e_presente(projeto: Projeto, caminho: str) -> bool:
    return caminho in projeto.versionados and (projeto.raiz / caminho).exists()


def conferir_ambiente(projeto: Projeto) -> Iterator[Achado]:
    if not versionado_e_presente(projeto, "uv.lock"):
        yield Achado("AMB001", AGENTE, "uv.lock", "versione o lock: `git add uv.lock`")
    if not versionado_e_presente(projeto, ".python-version"):
        yield Achado("AMB002", AGENTE, ".python-version", "crie e versione o arquivo")
    for caminho in sorted(projeto.versionados):
        if not re.fullmatch(r"requirements[^/]*\.txt", Path(caminho).name):
            continue
        arquivo = projeto.raiz / caminho
        if arquivo.is_file() and "autogenerated by uv" not in arquivo.read_text(encoding="utf-8"):
            yield Achado("AMB004", AGENTE, caminho, "dependência entra com `uv add`, não à mão")


def conferir_versao_do_python(projeto: Projeto) -> Iterator[Achado]:
    declarada = basedpyright(projeto).get("pythonVersion")
    arquivo = projeto.raiz / ".python-version"
    if declarada is None or not arquivo.is_file():
        return
    aceitas = {".".join(arquivo.read_text(encoding="utf-8").strip().split(".")[:2])}
    piso = PISO_DO_PYTHON.search(str(tabela(projeto.pyproject, "project").get("requires-python")))
    if piso:
        aceitas.add(piso.group(1))
    if declarada not in aceitas:
        mensagem = f"pythonVersion {declarada}: use uma destas: {', '.join(sorted(aceitas))}"
        yield Achado("AMB003", AGENTE, PYPROJECT, mensagem)


def projeto_aninhado(raiz: Path, pasta: Path, nome: str) -> bool:
    if nome != PYPROJECT or pasta == Path():
        return False
    texto = (raiz / pasta / nome).read_text(encoding="utf-8", errors="replace")
    return re.search(r"^\s*\[tool\.", texto, re.M) is not None


def config_paralela(raiz: Path, pasta: Path, nome: str) -> bool:
    caminho = raiz / pasta / nome
    if nome in CONFIG_EM_QUALQUER_PASTA:
        return True
    if pasta == Path() and nome in CONFIG_NA_RAIZ:
        return True
    if pasta == Path() and nome in SECOES_EM_INI:
        texto = caminho.read_text(encoding="utf-8", errors="replace")
        return any(secao in texto for secao in SECOES_EM_INI[nome])
    return False


def conferir_config_paralela(projeto: Projeto) -> Iterator[Achado]:
    # Olha o disco, não o git: a ferramenta lê o arquivo mesmo que o git não o veja.
    for pasta, subpastas, arquivos in os.walk(projeto.raiz):
        subpastas[:] = [s for s in subpastas if s not in PASTAS_FORA]
        relativa = Path(pasta).relative_to(projeto.raiz)
        for nome in arquivos:
            caminho = relativa / nome
            if config_paralela(projeto.raiz, relativa, nome):
                mensagem = "tire daqui: toda configuração fica no pyproject.toml da raiz"
                yield Achado("CFG001", AGENTE, str(caminho), mensagem, f"config:{caminho}")
            elif projeto_aninhado(projeto.raiz, relativa, nome):
                # Pode ser outro projeto, e pode ser um atalho: quem decide é o humano.
                mensagem = "pyproject aninhado com [tool.*] muda o que as ferramentas leem aqui"
                yield Achado("CFG003", HUMANO, str(caminho), mensagem, f"config:{caminho}")


def comentarios_por_linha(texto: str) -> dict[int, str]:
    comentarios: dict[int, str] = {}
    try:
        for token in tokenize.generate_tokens(io.StringIO(texto).readline):
            if token.type == tokenize.COMMENT:
                comentarios[token.start[0]] = token.string
    except (tokenize.TokenError, SyntaxError):
        return comentarios
    return comentarios


def tem_motivo_acima(linha: int, comentarios: dict[int, str], linhas: list[str]) -> bool:
    """Diretiva de arquivo não aceita texto depois dela: o motivo vem na linha acima do bloco."""
    anterior = linha - 1
    while anterior in comentarios and linhas[anterior - 1].lstrip().startswith("#"):
        if MOTIVO.search(comentarios[anterior]):
            return True
        if not DIRETIVA.search(comentarios[anterior]):
            return False
        anterior -= 1
    return False


def suprime_sem_motivo(linha: int, comentarios: dict[int, str], linhas: list[str]) -> bool:
    comentario = comentarios[linha]
    if not DIRETIVA.search(comentario) or SO_STRICT.search(comentario):
        return False
    if MOTIVO.search(comentario):
        return False
    sozinho = linhas[linha - 1].lstrip().startswith("#")
    return not (sozinho and tem_motivo_acima(linha, comentarios, linhas))


def apelidos(arvore: ast.AST) -> dict[str, str]:
    """Mapeia o nome local para o nome real: `from pytest import mark as m` dá m -> pytest.mark."""
    mapa: dict[str, str] = {}
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            mapa.update({nome.asname: nome.name for nome in no.names if nome.asname})
        elif isinstance(no, ast.ImportFrom) and no.module:
            for nome in no.names:
                mapa[nome.asname or nome.name] = f"{no.module}.{nome.name}"
    return mapa


def nome_de(no: ast.AST, mapa: dict[str, str]) -> str | None:
    partes: list[str] = []
    while isinstance(no, ast.Attribute):
        partes.append(no.attr)
        no = no.value
    if not isinstance(no, ast.Name):
        return None
    return ".".join([mapa.get(no.id, no.id), *reversed(partes)])


def regra_do_no(no: ast.AST, mapa: dict[str, str]) -> tuple[str, str] | None:
    if isinstance(no, ast.Call) and nome_de(no.func, mapa) in CASTS:
        return "SUP001", "cast"
    nome = nome_de(no, mapa)
    if nome in SEM_TIPO:
        return "SUP001", "no_type_check"
    if nome in PULOS:
        return "SUP002", "teste pulado"
    return None


def texto_preenchido(valor: ast.expr) -> bool:
    if isinstance(valor, ast.Constant):
        return isinstance(valor.value, str) and bool(valor.value.strip())
    return isinstance(valor, ast.JoinedStr)


def diz_o_motivo(chamada: ast.Call) -> bool:
    """O `skip` que já traz o motivo na chamada não precisa repetir em comentário."""
    motivo = next((k.value for k in chamada.keywords if k.arg == "reason"), None)
    if motivo is not None:
        return not isinstance(motivo, ast.Constant) or texto_preenchido(motivo)
    return any(texto_preenchido(valor) for valor in chamada.args)


def conferir_codigo(caminho: str, texto: str, comentarios: dict[int, str]) -> Iterator[Achado]:
    try:
        arvore = ast.parse(texto)
    except (SyntaxError, ValueError):
        return  # o ruff reprova o arquivo que não compila
    com_motivo = {
        id(no.func) for no in ast.walk(arvore) if isinstance(no, ast.Call) and diz_o_motivo(no)
    }
    mapa = apelidos(arvore)
    vistos: set[tuple[str, int]] = set()
    for no in ast.walk(arvore):
        achado = regra_do_no(no, mapa)
        if achado is None or (achado[0] == "SUP002" and id(no) in com_motivo):
            continue
        regra, oque = achado
        linha = getattr(no, "lineno", 0)
        if (regra, linha) not in vistos and not MOTIVO.search(comentarios.get(linha, "")):
            vistos.add((regra, linha))
            yield Achado(regra, AGENTE, f"{caminho}:{linha}", f"{oque} sem '# motivo: <por quê>'")


def conferir_supressoes(projeto: Projeto) -> Iterator[Achado]:
    for caminho in projeto.fontes:
        arquivo = projeto.raiz / caminho
        if not arquivo.is_file() or PASTAS_FORA.intersection(Path(caminho).parts):
            continue
        texto = arquivo.read_text(encoding="utf-8", errors="replace")
        comentarios = comentarios_por_linha(texto)
        linhas = texto.splitlines()
        for linha in sorted(comentarios):
            if suprime_sem_motivo(linha, comentarios, linhas):
                mensagem = "corrija o código ou escreva '# motivo: <por quê>' na mesma linha"
                yield Achado("SUP001", AGENTE, f"{caminho}:{linha}", mensagem)
        yield from conferir_codigo(caminho, texto, comentarios)


CONFERENCIAS = (
    conferir_config_paralela,
    conferir_linha_de_base,
    conferir_chaves,
    conferir_regras_do_ruff,
    conferir_por_arquivo,
    conferir_exclusoes_do_ruff,
    conferir_limites_do_ruff,
    conferir_tipos,
    conferir_alcance_dos_tipos,
    conferir_pytest,
    conferir_etapas,
    conferir_fronteiras,
    conferir_ambiente,
    conferir_versao_do_python,
    conferir_supressoes,
)


def adr_aceito(projeto: Projeto, adr: str) -> bool:
    raiz = projeto.raiz.resolve()
    arquivo = (raiz / adr).resolve()
    if not arquivo.is_relative_to(raiz) or not arquivo.is_file():
        return False
    return ADR_ACEITO.search(arquivo.read_text(encoding="utf-8", errors="replace")) is not None


def julgar(projeto: Projeto) -> tuple[list[Achado], int]:
    """Devolve os achados em aberto e quantos desvios do registro estão valendo."""
    achados = [achado for conferencia in CONFERENCIAS for achado in conferencia(projeto)]
    chaves = {achado.chave for achado in achados}
    desvios = tabela(projeto.tool, "trilhos").get("desvios")
    declarados: set[str] = set()
    problemas: list[Achado] = []
    for item in desvios if isinstance(desvios, list) else []:
        chave, adr = str(item.get("chave")), str(item.get("adr"))
        if not adr_aceito(projeto, adr):
            problemas.append(Achado("DES001", HUMANO, adr, "ADR ausente ou não aceito", chave))
        elif chave not in chaves:
            mensagem = f"{chave}: o registro não casa com nada; apague o item"
            problemas.append(Achado("DES002", AGENTE, PYPROJECT, mensagem))
        else:
            declarados.add(chave)
    return [a for a in achados if a.chave not in declarados] + problemas, len(declarados)


def carregar(raiz: Path) -> Projeto:
    try:
        pyproject = tomllib.loads((raiz / PYPROJECT).read_text(encoding="utf-8"))
        trilho = tomllib.loads(ASSET.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as erro:
        raise IndeterminadoError(str(erro)) from erro
    return Projeto(
        raiz,
        pyproject,
        tabela(trilho, "tool"),
        frozenset(git_lista(raiz)),
        tuple(git_lista(raiz, "--cached", "--others", "--exclude-standard", "*.py", "*.pyi")),
    )


def git_lista(raiz: Path, *args: str) -> list[str]:
    try:
        feito = subprocess.run(
            ["git", "ls-files", "-z", *args],
            cwd=raiz,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as erro:
        raise IndeterminadoError(f"git ls-files falhou: {erro}") from erro
    return [caminho for caminho in feito.stdout.split("\0") if caminho]


def relatar(achados: list[Achado], declarados: int) -> int:
    # O humano por último: o hook devolve o fim da saída, e o que para o agente não pode sair antes.
    for achado in sorted(achados, key=lambda a: (a.dono == HUMANO, a.onde, a.regra)):
        prefixo = f"{achado.chave}: " if achado.chave else ""
        print(f"{achado.onde} {achado.regra} [{achado.dono}] {prefixo}{achado.mensagem}")
    humanos = sum(achado.dono == HUMANO for achado in achados)
    agente = len(achados) - humanos
    if humanos:
        print("Pare: mudar o portão é decisão humana. Relate o que é [humano] e não tente calar.")
        print(f"trilhos: pare ({humanos} de decisão humana, {agente} a consertar)")
        return SAIDA_PARE
    if agente:
        print(f"trilhos: conserte ({agente} a consertar)")
        return SAIDA_CONSERTE
    plural = "desvio declarado" if declarados == 1 else "desvios declarados"
    print(f"trilhos: aprovado ({declarados} {plural})")
    return 0


def main() -> int:
    if len(sys.argv) > 1:
        print("trilhos: indeterminado (este script não aceita argumentos)")
        return SAIDA_INDETERMINADO
    try:
        achados, declarados = julgar(carregar(Path.cwd()))
    except Exception as erro:  # noqa: BLE001  # motivo: o que não se leu nunca vira "conserte"
        print(f"trilhos: indeterminado ({erro})")
        return SAIDA_INDETERMINADO
    return relatar(achados, declarados)


if __name__ == "__main__":
    sys.exit(main())
