#!/usr/bin/env python3
"""Testes do conferir_trilho.py da python-on-rails: só a biblioteca padrão, sem rede.

Cada caso monta um repositório git temporário com o asset colado, planta um defeito e exige a
regra e o código de saída. Adaptação legítima tem o caso contrário: nenhum achado.

Uso, na raiz do repositório das skills: `python3 tests/test_conferir_trilho.py`.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "python-on-rails")
SCRIPT = os.path.join(SKILL, "scripts", "conferir_trilho.py")
sys.dont_write_bytecode = True

# O git do teste não lê a configuração do usuário (hook, assinatura, autocrlf).
GIT_ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "teste",
    "GIT_AUTHOR_EMAIL": "teste@exemplo.invalid",
    "GIT_COMMITTER_NAME": "teste",
    "GIT_COMMITTER_EMAIL": "teste@exemplo.invalid",
}
os.environ.update(GIT_ENV)

ADR_ACEITO = "# 0001 — Desvio\n\n**Status:** Aceito (2026-11-03)\n"
ADR_PROPOSTO = "# 0002 — Desvio\n\n**Status:** Proposto\n"


class Base(unittest.TestCase):
    def setUp(self):
        self.raiz = tempfile.mkdtemp(prefix="trilho-")
        self.addCleanup(shutil.rmtree, self.raiz)
        with open(os.path.join(SKILL, "assets", "pyproject-trilho.toml"), encoding="utf-8") as f:
            trilho = f.read().replace("<pacote>", "demo")
        cabecalho = '[project]\nname = "demo"\nversion = "0.1.0"\nrequires-python = ">=3.13"\n\n'
        self.escrever("pyproject.toml", cabecalho + trilho)
        self.escrever("uv.lock", "version = 1\n")
        self.escrever(".python-version", "3.13\n")
        self.escrever("src/demo/__init__.py", '"""Demo."""\n')
        self.escrever("tests/test_x.py", '"""Testes."""\n')
        shutil.copy(os.path.join(SKILL, "assets", "Makefile"), self.raiz)
        os.mkdir(os.path.join(self.raiz, "scripts"))
        shutil.copy(os.path.join(SKILL, "scripts", "portao.sh"), os.path.join(self.raiz, "scripts"))
        self.git("init", "-q", ".")
        self.git("add", "-A")
        self.git("commit", "-qm", "base")

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.raiz, check=True, capture_output=True)

    def caminho(self, relativo):
        return os.path.join(self.raiz, relativo)

    def escrever(self, relativo, texto):
        os.makedirs(os.path.dirname(self.caminho(relativo)) or self.raiz, exist_ok=True)
        with open(self.caminho(relativo), "w", encoding="utf-8") as f:
            f.write(texto)

    def trocar(self, relativo, antes, depois):
        with open(self.caminho(relativo), encoding="utf-8") as f:
            texto = f.read()
        self.assertIn(antes, texto)
        self.escrever(relativo, texto.replace(antes, depois))

    def acrescentar(self, relativo, texto):
        with open(self.caminho(relativo), "a", encoding="utf-8") as f:
            f.write(texto)

    def declarar(self, chave, adr="docs/adr/0001-desvio.md"):
        self.acrescentar(
            "pyproject.toml", f'\n[[tool.trilhos.desvios]]\nchave = "{chave}"\nadr = "{adr}"\n'
        )

    def rodar(self):
        return subprocess.run(
            [sys.executable, "-I", SCRIPT],
            cwd=self.raiz,
            capture_output=True,
            text=True,
            check=False,
        )

    def exigir(self, saida, *regras):
        feito = self.rodar()
        self.assertEqual(feito.returncode, saida, feito.stdout + feito.stderr)
        for regra in regras:
            self.assertIn(f" {regra} ", feito.stdout)
        return feito.stdout

    def aprovar(self):
        return self.exigir(0)


class AssetColado(Base):
    def test_asset_colado_aprova(self):
        self.assertIn("aprovado", self.aprovar())


class Afrouxar(Base):
    """As onze formas medidas em 2026-11-03: todas passavam no portão."""

    def test_ignore(self):
        self.trocar("pyproject.toml", 'ignore = [\n', 'ignore = [\n  "T20",\n')
        self.assertIn("ruff.ignore:T20", self.exigir(3, "GAT001"))

    def test_ignore_de_regra_dentro_de_um_prefixo(self):
        self.trocar("pyproject.toml", 'ignore = [\n', 'ignore = [\n  "PLR2004",\n  "N818",\n')
        saida = self.exigir(3, "GAT001")
        self.assertIn("ruff.ignore:PLR2004", saida)
        self.assertIn("ruff.ignore:N818", saida)

    def test_per_file_ignores(self):
        self.trocar("pyproject.toml", '"tests/**" = [', '"src/**" = ["ALL"]\n"tests/**" = [')
        self.assertIn("ruff.per-file-ignores:src/**:ALL", self.exigir(3, "GAT001"))

    def test_extend_exclude(self):
        self.trocar("pyproject.toml", "line-length = 100", 'line-length = 100\nextend-exclude = ["src"]')
        self.assertIn("ruff.exclude:src", self.exigir(3, "GAT001"))

    def test_prefixo_tirado_do_select(self):
        self.trocar("pyproject.toml", '"T10", "T20",', '"T10",')
        self.assertIn("ruff.select:T20", self.exigir(3, "GAT001"))

    def test_regra_de_ambiente_apagada(self):
        self.trocar("pyproject.toml", '"os.getenv".msg', '"os.outro".msg')
        self.assertIn("ruff.banned-api:os.getenv", self.exigir(3, "GAT001"))

    def test_complexidade_maior(self):
        self.trocar("pyproject.toml", "max-complexity = 8", "max-complexity = 30")
        self.assertIn("ruff.max-complexity:30", self.exigir(3, "GAT001"))

    def test_ruff_toml_na_raiz(self):
        self.escrever("ruff.toml", '[lint]\nselect = ["F401"]\n')
        self.exigir(1, "CFG001")

    def test_ruff_toml_em_subpasta(self):
        self.escrever("src/demo/.ruff.toml", '[lint]\nselect = ["F401"]\n')
        self.assertIn("src/demo/.ruff.toml", self.exigir(1, "CFG001"))

    def test_pyrightconfig(self):
        self.escrever("pyrightconfig.json", '{"typeCheckingMode": "off"}')
        self.exigir(1, "CFG001")

    def test_pytest_ini(self):
        self.escrever("pytest.ini", "[pytest]\n")
        self.exigir(1, "CFG001")

    def test_arquivo_ignorado_pelo_git_tambem_conta(self):
        # A ferramenta lê o arquivo mesmo que o git não o veja.
        self.acrescentar(".git/info/exclude", "ruff.toml\n")
        self.escrever("ruff.toml", '[lint]\nselect = ["F401"]\n')
        self.exigir(1, "CFG001")

    def test_pyproject_aninhado_e_decisao_humana(self):
        # Pode ser um projeto de verdade: mandar apagar destruiria o trabalho.
        self.escrever("src/demo/pyproject.toml", '[tool.ruff]\nline-length = 200\n')
        saida = self.exigir(3, "CFG003")
        self.assertNotIn("apague", saida)

    def test_pyproject_aninhado_declarado_aprova(self):
        self.escrever("docs/adr/0001-desvio.md", ADR_ACEITO)
        self.escrever("livro/pyproject.toml", '[tool.ruff]\nline-length = 200\n')
        self.declarar("config:livro/pyproject.toml")
        self.aprovar()

    def test_pyproject_aninhado_sem_ferramenta_passa(self):
        self.escrever("livro/pyproject.toml", '[project]\nname = "livro"\n')
        self.aprovar()

    def test_modo_de_tipos(self):
        self.trocar("pyproject.toml", 'typeCheckingMode = "recommended"', 'typeCheckingMode = "off"')
        self.assertIn("basedpyright.typeCheckingMode:off", self.exigir(3, "GAT002"))

    def test_regra_de_tipos_desligada(self):
        self.trocar("pyproject.toml", "failOnWarnings = true", 'reportAny = "none"\nfailOnWarnings = true')
        self.assertIn("basedpyright.reportAny", self.exigir(3, "GAT002"))

    def test_fail_on_warnings(self):
        self.trocar("pyproject.toml", "failOnWarnings = true", "failOnWarnings = false")
        self.exigir(3, "GAT002")

    def test_type_ignore_religado(self):
        self.trocar(
            "pyproject.toml", "enableTypeIgnoreComments = false", "enableTypeIgnoreComments = true"
        )
        self.exigir(3, "GAT002")

    def test_exclude_de_tipos(self):
        self.trocar("pyproject.toml", "failOnWarnings = true", 'failOnWarnings = true\nexclude = ["src/demo/ruim.py"]')
        self.assertIn("basedpyright.exclude:src/demo/ruim.py", self.exigir(3, "GAT002"))

    def test_ignore_de_tipos(self):
        self.trocar("pyproject.toml", "failOnWarnings = true", 'failOnWarnings = true\nignore = ["src"]')
        self.assertIn("basedpyright.ignore:src", self.exigir(3, "GAT002"))

    def test_include_sem_src(self):
        self.trocar("pyproject.toml", 'include = ["src", "tests"]', 'include = ["tests"]')
        self.assertIn("basedpyright.include:src", self.exigir(3, "GAT002"))

    def test_linha_de_base(self):
        self.escrever(".basedpyright/baseline.json", "{}")
        self.exigir(3, "CFG002")

    def test_linha_de_base_em_outro_caminho(self):
        self.trocar("pyproject.toml", "failOnWarnings = true", 'failOnWarnings = true\nbaselineFile = "b.json"')
        self.exigir(3, "CFG002")

    def test_xfail_strict(self):
        self.trocar("pyproject.toml", "xfail_strict = true", "xfail_strict = false")
        self.exigir(3, "GAT003")

    def test_filterwarnings(self):
        self.trocar("pyproject.toml", 'filterwarnings = ["error"]', 'filterwarnings = ["error", "ignore::DeprecationWarning"]')
        self.exigir(3, "GAT003")

    def test_addopts_que_esconde_teste(self):
        self.trocar("pyproject.toml", 'addopts = ["--strict-markers"', 'addopts = ["--ignore=tests", "--strict-markers"')
        self.exigir(3, "GAT003")

    def test_tira_etapa_de_tipos(self):
        self.trocar("scripts/portao.sh", "uv run --locked basedpyright\n", "true\n")
        self.assertIn("portao.etapa:basedpyright", self.exigir(3, "GAT004"))

    def test_etapa_so_em_comentario_nao_conta(self):
        self.trocar("scripts/portao.sh", "uv run --locked basedpyright\n", "# uv run --locked basedpyright\n")
        self.exigir(3, "GAT004")

    def test_apaga_importlinter(self):
        with open(self.caminho("pyproject.toml"), encoding="utf-8") as f:
            texto = f.read()
        self.escrever("pyproject.toml", texto[: texto.index("# Domínio puro")])
        self.assertIn("padrao.dominio-puro", self.exigir(3, "GAT005"))


class Ambiente(Base):
    def test_lock_fora_do_git(self):
        self.git("rm", "-q", "--cached", "uv.lock")
        self.exigir(1, "AMB001")

    def test_python_version_ausente(self):
        os.remove(self.caminho(".python-version"))
        self.git("add", "-A")
        self.exigir(1, "AMB002")

    def test_python_version_divergente(self):
        self.trocar("pyproject.toml", 'pythonVersion = "3.13"', 'pythonVersion = "3.11"')
        self.exigir(1, "AMB003")

    def test_requirements_a_mao(self):
        self.escrever("requirements.txt", "requests\n")
        self.git("add", "-A")
        self.exigir(1, "AMB004")

    def test_requirements_gerado_pelo_uv_passa(self):
        self.escrever("requirements.txt", "# This file was autogenerated by uv via the following command:\n")
        self.git("add", "-A")
        self.aprovar()


class Supressao(Base):
    def test_noqa_sem_motivo(self):
        self.escrever("src/demo/a.py", '"""a."""\n\nprint(1)  # noqa: T201\n')
        self.git("add", "-A")
        self.assertIn("src/demo/a.py:3", self.exigir(1, "SUP001"))

    def test_arquivo_novo_fora_do_indice(self):
        self.escrever("src/demo/a.py", '"""a."""\n\nprint(1)  # noqa: T201\n')
        self.exigir(1, "SUP001")

    def test_motivo_vazio(self):
        self.escrever("src/demo/a.py", '"""a."""\n\nprint(1)  # noqa: T201  # motivo:\n')
        self.exigir(1, "SUP001")

    def test_arquivo_rastreado_apagado_nao_esconde_o_achado(self):
        self.escrever("src/demo/extra.py", '"""x."""\n')
        self.escrever("src/demo/a.py", '"""a."""\n\nprint(1)  # noqa: T201\n')
        self.git("add", "-A")
        os.remove(self.caminho("src/demo/extra.py"))
        self.exigir(1, "SUP001")

    def test_cast_sem_motivo(self):
        self.escrever("src/demo/a.py", 'from typing import cast\n\nx = cast("int", 1)\n')
        self.exigir(1, "SUP001")

    def test_no_type_check_sem_motivo(self):
        self.escrever("src/demo/a.py", 'from typing import no_type_check\n\n\n@no_type_check\ndef f(): ...\n')
        self.exigir(1, "SUP001")

    def test_skip_sem_motivo(self):
        self.escrever("tests/test_y.py", 'import pytest\n\n\n@pytest.mark.skip\ndef test_y():\n    assert False\n')
        self.exigir(1, "SUP002")

    def test_skip_chamado_sem_motivo(self):
        self.escrever("tests/test_y.py", 'import pytest\n\n\ndef test_y():\n    pytest.skip()\n')
        self.exigir(1, "SUP002")

    def test_skip_com_motivo_vazio(self):
        self.escrever("tests/test_y.py", 'import pytest\n\n\n@pytest.mark.skip(reason=" ")\ndef test_y(): ...\n')
        self.exigir(1, "SUP002")

    def test_skip_no_modulo_inteiro(self):
        self.escrever("tests/test_y.py", 'import pytest\n\npytestmark = pytest.mark.skip\n')
        self.exigir(1, "SUP002")

    def test_skip_que_ja_diz_o_motivo_passa(self):
        self.escrever(
            "tests/test_y.py",
            'import pytest\n\n\n@pytest.mark.skipif(\n    not TEM,\n    reason="sem áudio",\n)\n'
            'def test_y():\n    pytest.skip("sem dispositivo")\n',
        )
        self.aprovar()

    def test_skip_com_motivo_passa(self):
        self.escrever(
            "tests/test_y.py",
            'import pytest\n\n\n@pytest.mark.skip  # motivo: serviço fora do ar, ver issue 3\ndef test_y():\n    assert False\n',
        )
        self.aprovar()

    def test_com_motivo_passa(self):
        self.escrever("src/demo/a.py", '"""a."""\n\nprint(1)  # noqa: T201  # motivo: saída da CLI\n')
        self.aprovar()

    def test_pyright_strict_nao_e_supressao(self):
        self.escrever("src/demo/a.py", '# pyright: strict\n"""a."""\n')
        self.aprovar()

    def test_diretiva_de_arquivo_aceita_motivo_na_linha_de_cima(self):
        # Medido: `# pyright: basic  # motivo: x` deixa de valer, então o motivo vem acima.
        self.escrever(
            "src/demo/a.py",
            '# motivo: gerado por ferramenta\n# pyright: reportAny=false\n# pyright: basic\n"""a."""\n',
        )
        self.aprovar()

    def test_diretiva_de_arquivo_sem_motivo(self):
        self.escrever("src/demo/a.py", '# pyright: reportAny=false\n"""a."""\n')
        self.exigir(1, "SUP001")

    def test_formas_que_calam_de_fato(self):
        # Medido no ruff 0.17.3: todas calam o T201.
        for comentario in ("# texto # noqa: T201", "#noqa:T201", "# NOQA", "# flake8: noqa", "# ruff: ignore[T201]"):
            with self.subTest(comentario):
                self.escrever("src/demo/a.py", f'"""a."""\n\nprint(1)  {comentario}\n')
                self.exigir(1, "SUP001")

    def test_prosa_que_so_cita_a_diretiva_nao_conta(self):
        # Medido no ruff 0.17.3: nenhuma destas cala nada.
        for comentario in ("# texto noqa: T201", "# `# noqa: T201`", '# "noqa: T201"', '# honra "pyright: basic"'):
            with self.subTest(comentario):
                self.escrever("src/demo/a.py", f'"""a."""\n\n{comentario}\nX = 1\n')
                self.aprovar()

    def test_palavra_dentro_de_texto_nao_conta(self):
        self.escrever("src/demo/a.py", '"""Sobre o noqa e o cast(x)."""\n\nX = "# noqa"\n')
        self.aprovar()


class AdaptacaoLegitima(Base):
    """Cada caso existe em projeto real e reprovaria numa comparação ingênua."""

    def test_select_all(self):
        self.trocar("pyproject.toml", "select = [\n", 'select = ["ALL"]\nselect_antigo = [\n')
        self.trocar("pyproject.toml", 'ignore = [\n', 'ignore = [\n  "COM812",\n  "CPY001",\n  "D203",\n')
        self.aprovar()

    def test_modo_all(self):
        self.trocar("pyproject.toml", 'typeCheckingMode = "recommended"', 'typeCheckingMode = "all"')
        self.aprovar()

    def test_python_no_piso_de_biblioteca(self):
        self.trocar("pyproject.toml", '">=3.13"', '">=3.11"')
        self.trocar("pyproject.toml", 'pythonVersion = "3.13"', 'pythonVersion = "3.11"')
        self.aprovar()

    def test_sem_marcador_e2e(self):
        self.trocar("pyproject.toml", 'markers = ["e2e', 'markers_antigos = ["e2e')
        self.aprovar()

    def test_addopts_extras(self):
        self.trocar("pyproject.toml", 'addopts = ["--strict-markers"', 'addopts = ["-q", "-n", "auto", "--doctest-modules", "--strict-markers"')
        self.aprovar()

    def test_ignore_em_tests_de_regra_fora_do_trilho(self):
        self.trocar("pyproject.toml", '"tests/**" = ["S101", "PLR2004", "ANN401"]', '"tests/**" = ["S101", "PLR2004", "D", "INP001"]')
        self.aprovar()

    def test_contrato_com_mais_proibicoes(self):
        self.trocar("pyproject.toml", '"pydantic", "httpx"', '"pydantic", "httpx", "fastapi", "starlette"')
        self.aprovar()

    def test_exclui_claude(self):
        self.trocar("pyproject.toml", "line-length = 100", 'line-length = 100\nextend-exclude = [".claude"]')
        self.aprovar()

    def test_exclude_de_tipos_livre(self):
        self.trocar("pyproject.toml", "failOnWarnings = true", 'failOnWarnings = true\nexclude = [".claude", ".venv"]')
        self.aprovar()

    def test_nao_entra_em_claude_nem_venv(self):
        self.escrever(".claude/worktrees/x/ruff.toml", "")
        self.escrever(".venv/lib/pytest.ini", "")
        self.escrever(".claude/worktrees/x/a.py", "print(1)  # noqa: T201\n")
        self.acrescentar(".git/info/exclude", ".claude/\n.venv/\n")
        self.aprovar()

    def test_linha_mais_curta(self):
        self.trocar("pyproject.toml", "line-length = 100", "line-length = 88")
        self.aprovar()


class Desvios(Base):
    def test_desvio_declarado_aprova_e_aparece(self):
        self.escrever("docs/adr/0001-desvio.md", ADR_ACEITO)
        self.trocar("pyproject.toml", 'ignore = [\n', 'ignore = [\n  "N818",\n')
        self.declarar("ruff.ignore:N818")
        self.assertIn("1 desvio", self.aprovar())

    def test_linha_de_base_declarada_aprova(self):
        self.escrever("docs/adr/0001-desvio.md", ADR_ACEITO)
        self.escrever(".basedpyright/baseline.json", "{}")
        self.declarar("basedpyright.linha-de-base")
        self.aprovar()

    def test_adr_proposto_nao_vale(self):
        self.escrever("docs/adr/0002-desvio.md", ADR_PROPOSTO)
        self.trocar("pyproject.toml", 'ignore = [\n', 'ignore = [\n  "N818",\n')
        self.declarar("ruff.ignore:N818", "docs/adr/0002-desvio.md")
        self.exigir(3, "DES001")

    def test_adr_inexistente(self):
        self.trocar("pyproject.toml", 'ignore = [\n', 'ignore = [\n  "N818",\n')
        self.declarar("ruff.ignore:N818")
        self.exigir(3, "DES001")

    def test_adr_fora_do_projeto(self):
        self.trocar("pyproject.toml", 'ignore = [\n', 'ignore = [\n  "N818",\n')
        self.declarar("ruff.ignore:N818", "../fora.md")
        self.exigir(3, "DES001")

    def test_desvio_que_nao_casa_com_nada(self):
        self.escrever("docs/adr/0001-desvio.md", ADR_ACEITO)
        self.declarar("ruff.ignore:N818")
        self.exigir(1, "DES002")


class Veredito(Base):
    def test_sem_conserto_para_o_que_e_do_humano(self):
        self.trocar("pyproject.toml", "xfail_strict = true", "xfail_strict = false")
        saida = self.exigir(3, "GAT003")
        self.assertIn("[humano]", saida)
        self.assertNotIn("tool.trilhos", saida)
        self.assertNotIn("ADR", saida)

    def test_humano_vale_mais_que_agente_e_lista_os_dois(self):
        self.trocar("pyproject.toml", "xfail_strict = true", "xfail_strict = false")
        self.escrever("src/demo/a.py", '"""a."""\n\nprint(1)  # noqa: T201\n')
        self.exigir(3, "GAT003", "SUP001")

    def test_ultima_linha_diz_o_veredito(self):
        self.trocar("pyproject.toml", "xfail_strict = true", "xfail_strict = false")
        self.assertTrue(self.rodar().stdout.strip().splitlines()[-1].startswith("trilhos: pare"))

    def test_fora_do_git_nao_aprova(self):
        shutil.rmtree(self.caminho(".git"))
        self.exigir(2)

    def test_toml_invalido_nao_aprova(self):
        self.escrever("pyproject.toml", "[tool.ruff\n")
        self.exigir(2)

    def test_sem_pyproject_nao_aprova(self):
        os.remove(self.caminho("pyproject.toml"))
        self.exigir(2)

    def test_nao_existe_flag_que_cale(self):
        self.trocar("pyproject.toml", "xfail_strict = true", "xfail_strict = false")
        feito = subprocess.run(
            [sys.executable, "-I", SCRIPT, "--ignorar", "GAT003"],
            cwd=self.raiz,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(feito.returncode, 0)


class Portao(unittest.TestCase):
    """O juiz fica fora do projeto: o portão copiado só o chama, e sem ele reprova."""

    def test_portao_chama_o_script_da_pasta_da_skill(self):
        with open(os.path.join(SKILL, "scripts", "portao.sh"), encoding="utf-8") as f:
            texto = f.read()
        self.assertIn('.claude/skills/python-on-rails/scripts/conferir_trilho.py', texto)

    def test_portao_nao_guarda_mais_a_etapa_de_supressao(self):
        with open(os.path.join(SKILL, "scripts", "portao.sh"), encoding="utf-8") as f:
            self.assertNotIn("grep", f.read().replace("grep -q '^\\[tool.importlinter\\]'", ""))

    def test_sem_o_script_o_portao_reprova(self):
        with tempfile.TemporaryDirectory() as casa, tempfile.TemporaryDirectory() as raiz:
            os.mkdir(os.path.join(raiz, "scripts"))
            portao = os.path.join(raiz, "scripts", "portao.sh")
            shutil.copy(os.path.join(SKILL, "scripts", "portao.sh"), portao)
            falso = os.path.join(casa, "bin")
            os.mkdir(falso)
            uv = os.path.join(falso, "uv")
            with open(uv, "w", encoding="utf-8") as f:
                f.write("#!/bin/sh\nexit 0\n")
            os.chmod(uv, 0o755)
            ambiente = {**os.environ, "HOME": casa, "PATH": f"{falso}:{os.environ['PATH']}"}
            feito = subprocess.run(
                ["bash", portao, "--rapido"],
                env=ambiente,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(feito.returncode, 2, feito.stdout + feito.stderr)
        self.assertIn("conferir_trilho", feito.stdout + feito.stderr)
        self.assertNotIn("Portão aprovado", feito.stdout)


if __name__ == "__main__":
    unittest.main()
