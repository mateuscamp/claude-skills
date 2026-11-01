"""Fitness functions atômicas do projeto.

Cada teste aqui verifica uma DECISÃO registrada em docs/adr/, não o domínio.
Falha aqui significa que a arquitetura foi atravessada — não que a feature quebrou.

Só depende de stdlib + pytest. Rodar em CI a cada push:  pytest tests/arquitetura

Ao ajustar um limite, ajustar também o ADR correspondente: número que muda sem
registro é número que não governa nada.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

# --------------------------------------------------------------------------
# Configuração — ajustar por projeto
# --------------------------------------------------------------------------

RAIZ = Path(__file__).resolve().parents[2]
PACOTE = "meuprojeto"
SRC = RAIZ / "src" / PACOTE

# ADR-0001: camadas. Cada chave só pode importar os pacotes do seu conjunto.
# Com CONTEXTOS, a regra vale dentro de cada contexto.
DEPENDENCIAS_PERMITIDAS: dict[str, set[str]] = {
    "dominio": set(),
    "aplicacao": {"dominio"},
    "infra": {"dominio", "aplicacao"},
    "interface": {"dominio", "aplicacao"},
}

# ADR-0004: contextos delimitados, um pacote de primeiro nível cada. Vazio =
# projeto sem contextos, com as camadas na raiz do pacote.
CONTEXTOS: set[str] = set()  # ex.: {"vendas", "cadastro", "pagamento"}
API_PUBLICADA = "api"  # outro contexto só importa <contexto>.api

# ADR-0005: camada anticorrupção. Pacote externo → único lugar de SRC que o
# importa (pasta ou módulo, sem o .py).
ACL: dict[str, str] = {}  # ex.: {"stripe": "pagamento/acl"}

# ADR-0006: linguagem ubíqua. Por contexto ("" = pacote inteiro), a palavra
# proibida e o termo do glossário, em minúsculas, uma palavra por entrada.
SINONIMOS_PROIBIDOS: dict[str, dict[str, str]] = {}
# ex.: {"vendas": {"order": "pedido", "compra": "pedido"}}

LIMITE_LINHAS_ARQUIVO = 500  # ADR-0002: cabe em uma leitura do agente
LIMITE_LINHAS_FUNCAO = 40  # teto duro; o alvo escrito no AGENTS.md é 20

NOMES_PROIBIDOS = {
    "data", "info", "handler", "manager", "helper", "utils",
    "process", "service", "base", "common", "item", "obj",
}

# Funções de rede que exigem timeout explícito (ADR-0003: disponibilidade).
CHAMADAS_DE_REDE = {"get", "post", "put", "patch", "delete", "request", "head"}
MODULOS_DE_REDE = {"requests", "httpx", "urllib3", "session", "client"}

# Exceções conscientes. Toda entrada precisa de motivo e ADR — allowlist sem
# justificativa é a porta pela qual a arquitetura vaza.
ISENCOES: dict[str, str] = {
    # "src/meuprojeto/infra/migracoes_legado.py": "ADR-0009: migração congelada",
}


# --------------------------------------------------------------------------
# Coleta
# --------------------------------------------------------------------------


def arquivos_python() -> list[Path]:
    if not SRC.exists():  # pragma: no cover
        pytest.skip(f"pacote não encontrado em {SRC}")
    return [
        caminho
        for caminho in sorted(SRC.rglob("*.py"))
        if relativo(caminho) not in ISENCOES
    ]


def relativo(caminho: Path) -> str:
    return caminho.relative_to(RAIZ).as_posix()


def modulo_de(caminho: Path) -> list[str]:
    """Partes do módulo dentro do pacote: src/<pacote>/vendas/api.py → [vendas, api]."""
    partes = list(caminho.relative_to(SRC).with_suffix("").parts)
    return partes[:-1] if partes[-1] == "__init__" else partes


def contexto_e_camada(partes: list[str]) -> tuple[str, str | None]:
    """(contexto, camada) de um módulo interno; contexto "" fora de contexto."""
    if partes and partes[0] in CONTEXTOS:
        return partes[0], partes[1] if len(partes) > 1 else None
    return "", partes[0] if partes else None


def imports_internos(caminho: Path, arvore: ast.AST) -> list[tuple[list[str], int]]:
    """Devolve (partes do alvo dentro do pacote, linha) de cada import interno.

    `from <pacote>.vendas import api` vira [vendas, api]. O import relativo é
    resolvido a partir do arquivo: sem isso, `from ..infra import x` atravessa a
    fronteira sem que nenhuma checagem veja.
    """
    origem = modulo_de(caminho)
    pacote_atual = origem if caminho.name == "__init__.py" else origem[:-1]
    encontrados: list[tuple[list[str], int]] = []
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            for alias in no.names:
                partes = alias.name.split(".")
                if partes[0] == PACOTE and len(partes) > 1:
                    encontrados.append((partes[1:], no.lineno))
        elif isinstance(no, ast.ImportFrom):
            if no.level:
                subir = no.level - 1
                if subir > len(pacote_atual):
                    continue  # sai do pacote
                base = pacote_atual[: len(pacote_atual) - subir]
                modulo = base + (no.module.split(".") if no.module else [])
            elif no.module and no.module.split(".")[0] == PACOTE:
                modulo = no.module.split(".")[1:]
            else:
                continue
            encontrados.extend((modulo + [alias.name], no.lineno) for alias in no.names)
    return encontrados


def arvores() -> list[tuple[Path, ast.Module]]:
    return [
        (caminho, ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho)))
        for caminho in arquivos_python()
    ]


# --------------------------------------------------------------------------
# Fronteiras e acoplamento
# --------------------------------------------------------------------------


def test_camadas_respeitam_a_direcao_de_dependencia() -> None:
    """ADR-0001: a dependência só aponta para dentro, em cada contexto."""
    violacoes = []
    for caminho, arvore in arvores():
        contexto, origem = contexto_e_camada(modulo_de(caminho))
        if origem not in DEPENDENCIAS_PERMITIDAS:
            continue
        permitidos = DEPENDENCIAS_PERMITIDAS[origem] | {origem}
        for alvo, linha in imports_internos(caminho, arvore):
            contexto_alvo, destino = contexto_e_camada(alvo)
            if contexto_alvo != contexto:
                continue  # entre contextos, quem julga é o teste da API publicada
            if destino in DEPENDENCIAS_PERMITIDAS and destino not in permitidos:
                violacoes.append(
                    f"{relativo(caminho)}:{linha} — '{origem}' importa '{destino}' "
                    f"(permitido: {sorted(permitidos)}) — proibido por ADR-0001"
                )
    assert not violacoes, "\n" + "\n".join(violacoes)


def test_contexto_so_entra_pela_api_publicada() -> None:
    """ADR-0004: outro contexto só entra por <contexto>.api, a linguagem publicada."""
    if not CONTEXTOS:
        pytest.skip("CONTEXTOS vazio: projeto sem contextos declarados")
    violacoes = []
    for caminho, arvore in arvores():
        contexto, _ = contexto_e_camada(modulo_de(caminho))
        if not contexto:
            continue  # a raiz que monta a aplicação liga os contextos e fica livre
        for alvo, linha in imports_internos(caminho, arvore):
            contexto_alvo, porta = contexto_e_camada(alvo)
            if contexto_alvo and contexto_alvo != contexto and porta != API_PUBLICADA:
                violacoes.append(
                    f"{relativo(caminho)}:{linha} — '{contexto}' importa "
                    f"'{'.'.join(alvo)}'; outro contexto só entra por "
                    f"'{contexto_alvo}.{API_PUBLICADA}' — proibido por ADR-0004"
                )
    assert not violacoes, "\n" + "\n".join(violacoes)


def test_fornecedor_so_entra_pela_acl() -> None:
    """ADR-0005: o modelo do fornecedor não vaza; só a ACL importa o pacote dele."""
    if not ACL:
        pytest.skip("ACL vazio: nenhum fornecedor isolado")
    violacoes = []
    for caminho, arvore in arvores():
        local = caminho.relative_to(SRC).with_suffix("").as_posix()
        for no in ast.walk(arvore):
            if isinstance(no, ast.Import):
                nomes = [alias.name for alias in no.names]
            elif isinstance(no, ast.ImportFrom) and not no.level and no.module:
                nomes = [no.module]
            else:
                continue
            for nome in nomes:
                lugar = ACL.get(nome.split(".")[0])
                if lugar and local != lugar and not local.startswith(f"{lugar}/"):
                    violacoes.append(
                        f"{relativo(caminho)}:{no.lineno} — importa '{nome}' fora de "
                        f"'{lugar}', a camada anticorrupção — proibido por ADR-0005"
                    )
    assert not violacoes, "\n" + "\n".join(violacoes)


def test_sem_ciclo_entre_modulos() -> None:
    """Ciclo é acoplamento que nenhum refactor local resolve."""
    grafo: dict[str, set[str]] = {}
    for caminho, arvore in arvores():
        modulo = caminho.relative_to(SRC).with_suffix("").as_posix()
        alvos = set()
        for no in ast.walk(arvore):
            nome = None
            if isinstance(no, ast.Import):
                nome = next(
                    (a.name for a in no.names if a.name.startswith(f"{PACOTE}.")), None
                )
            elif isinstance(no, ast.ImportFrom) and no.module:
                nome = no.module if no.module.startswith(f"{PACOTE}.") else None
            if nome:
                alvos.add(nome[len(PACOTE) + 1 :].replace(".", "/"))
        grafo[modulo] = alvos

    ciclos: list[str] = []
    visitando: list[str] = []

    def visitar(no: str, visto: set[str]) -> None:
        if no in visitando:
            inicio = visitando.index(no)
            ciclos.append(" → ".join(visitando[inicio:] + [no]))
            return
        if no in visto or no not in grafo:
            return
        visitando.append(no)
        for vizinho in grafo[no]:
            visitar(vizinho, visto)
        visitando.pop()
        visto.add(no)

    vistos: set[str] = set()
    for modulo in grafo:
        visitar(modulo, vistos)

    assert not ciclos, "ciclos de import encontrados:\n" + "\n".join(sorted(set(ciclos)))


# --------------------------------------------------------------------------
# Legibilidade por agente
# --------------------------------------------------------------------------


def test_arquivos_cabem_em_uma_leitura() -> None:
    """ADR-0002: arquivo grande obriga o agente a paginar e fragmenta o raciocínio."""
    grandes = [
        f"{relativo(c)} — {n} linhas (limite {LIMITE_LINHAS_ARQUIVO})"
        for c in arquivos_python()
        if (n := len(c.read_text(encoding="utf-8").splitlines())) > LIMITE_LINHAS_ARQUIVO
    ]
    assert not grandes, "\n" + "\n".join(grandes)


def test_funcoes_dentro_do_teto() -> None:
    longas = []
    for caminho, arvore in arvores():
        for no in ast.walk(arvore):
            if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)):
                tamanho = (no.end_lineno or no.lineno) - no.lineno + 1
                if tamanho > LIMITE_LINHAS_FUNCAO:
                    longas.append(
                        f"{relativo(caminho)}:{no.lineno} — {no.name}() tem "
                        f"{tamanho} linhas (teto {LIMITE_LINHAS_FUNCAO})"
                    )
    assert not longas, "\n" + "\n".join(longas)


def tokens_do_nome(nome: str) -> list[str]:
    """Quebra CamelCase e snake_case em palavras minúsculas."""
    palavras: list[str] = []
    for pedaco in nome.split("_"):
        atual = ""
        for letra in pedaco:
            if letra.isupper() and atual:
                palavras.append(atual.lower())
                atual = letra
            else:
                atual += letra
        if atual:
            palavras.append(atual.lower())
    return palavras


def test_nomes_publicos_sao_grepaveis() -> None:
    """Nome genérico devolve dezenas de matches e obriga o agente a ler todos."""
    ruins = []
    for caminho, arvore in arvores():
        for no in ast.walk(arvore):
            if not isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if no.name.startswith("_"):
                continue
            palavras = tokens_do_nome(no.name)
            if palavras and all(p in NOMES_PROIBIDOS for p in palavras):
                ruins.append(
                    f"{relativo(caminho)}:{no.lineno} — nome genérico '{no.name}': "
                    f"todo termo está na lista de nomes de baixo valor de busca"
                )
    assert not ruins, "\n" + "\n".join(ruins)


def test_nomes_usam_o_termo_do_glossario() -> None:
    """ADR-0006: sinônimo faz o grep achar metade dos usos e cria um segundo modelo."""
    if not SINONIMOS_PROIBIDOS:
        pytest.skip("SINONIMOS_PROIBIDOS vazio: glossário sem termo proibido")
    violacoes = []
    for caminho, arvore in arvores():
        contexto, _ = contexto_e_camada(modulo_de(caminho))
        proibidos = SINONIMOS_PROIBIDOS.get("", {}) | SINONIMOS_PROIBIDOS.get(contexto, {})
        for no in ast.walk(arvore):
            if not isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            for palavra in tokens_do_nome(no.name):
                if palavra in proibidos:
                    violacoes.append(
                        f"{relativo(caminho)}:{no.lineno} — '{no.name}' usa '{palavra}'; "
                        f"em '{contexto or PACOTE}' o termo é '{proibidos[palavra]}' "
                        f"(glossário do AGENTS.md) — proibido por ADR-0006"
                    )
    assert not violacoes, "\n" + "\n".join(violacoes)


# --------------------------------------------------------------------------
# Disponibilidade
# --------------------------------------------------------------------------


def test_toda_chamada_de_rede_tem_timeout() -> None:
    """ADR-0003: a rede não é confiável; chamada sem timeout pendura o processo."""
    sem_timeout = []
    for caminho, arvore in arvores():
        for no in ast.walk(arvore):
            if not isinstance(no, ast.Call) or not isinstance(no.func, ast.Attribute):
                continue
            if no.func.attr not in CHAMADAS_DE_REDE:
                continue
            base = no.func.value
            nome_base = getattr(base, "id", getattr(base, "attr", "")).lower()
            if not any(m in nome_base for m in MODULOS_DE_REDE):
                continue
            if not any(k.arg == "timeout" for k in no.keywords):
                sem_timeout.append(
                    f"{relativo(caminho)}:{no.lineno} — "
                    f"{nome_base}.{no.func.attr}() sem timeout explícito"
                )
    assert not sem_timeout, "\n" + "\n".join(sem_timeout)
