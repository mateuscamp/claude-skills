#!/usr/bin/env python3
"""Testes das Gerais do distribuir.py (de jogo e de Lua): só a biblioteca padrão, sem rede.

Cada caso monta um repositório git temporário com as fontes `gerais-de-jogo.md` e `gerais-de-lua.md`,
as cópias (a de jogo nas três skills de motor, a de Lua só nas duas em Lua) e os ponteiros no
`armadilhas.md`, planta um defeito, faz commit e exige o problema, ou a recusa.

Uso, na raiz do repositório das skills: `python3 tests/test_distribuir.py`.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "distribuir.py")
# Sem __pycache__ na raiz do repositório das skills.
sys.dont_write_bytecode = True
sys.path.insert(0, ROOT)
import distribuir  # noqa: E402

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

SKILLS = distribuir.GENERAL_LESSONS_SKILLS
SOURCE = (
    "# Gerais de jogo\n"
    "\n"
    "Fonte única.\n"
    "\n"
    "### Testes que passam com qualquer código\n"
    "\n"
    "- Lição um: entrada perto do limite, dos dois lados, nunca no ponto fixo da regra.\n"
    "- Lição dois: spec não conta por contador compartilhado, que anda por outros motivos.\n"
    "- Lição três: semente que não é inteiro positivo nunca cai calada no sorteio.\n"
).encode()
MOTOR_HEAD = (
    "# Armadilhas do motor\n"
    "\n"
    "## Entrada\n"
    "\n"
    "- Armadilha do motor, que mora aqui.\n"
    "\n"
)
GAME_POINTER = (
    "## Gerais de jogo: moram em `references/gerais-de-jogo.md`\n"
    "\n"
    "Cópia da fonte única; não acrescente lição aqui.\n"
)
POINTER = (MOTOR_HEAD + GAME_POINTER).encode()
SKILL_MD = b"---\nname: ai-first-defold\ndescription: Skill de teste.\n---\n\n# Teste\n"

# As lições da linguagem Lua: o nome é fixo (o AGENTS.md do campcrawler-love o cita), e só as skills
# de motor em Lua recebem a cópia; a Godot não usa Lua. Escritos à mão, não lidos do distribuir.py.
LUA_SOURCE_NAME = "gerais-de-lua.md"
LUA_COPY = "references/gerais-de-lua.md"
LUA_SKILLS = ("ai-first-defold", "ai-first-love")
LUA_SOURCE = (
    "# Gerais de Lua\n"
    "\n"
    "Fonte única.\n"
    "\n"
    "### Valor que muda calado entre os dois\n"
    "\n"
    "- Lição um: `/` devolve float no Lua 5.3+, e só o texto mostra.\n"
    "- Lição dois: `a and f() or g()` corta os vários retornos num só.\n"
).encode()
LUA_POINTER = (
    "## Gerais de Lua: moram em `references/gerais-de-lua.md`\n"
    "\n"
    "Cópia da fonte única; não acrescente lição aqui.\n"
    "\n"
)
# A seção que o armadilhas.md das skills em Lua tinha antes da fonte única.
OLD_LUA_SECTION = "## Lua: LuaJIT do jogo e Lua 5.x da suíte\n\n"
LUA_POINTER_MD = (MOTOR_HEAD + LUA_POINTER + GAME_POINTER).encode()


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True)


class Fixture(unittest.TestCase):
    """Repositório com a base em dia, no ramo main."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="test-distribuir-")
        self.addCleanup(shutil.rmtree, self.tmp)
        self.repo = os.path.join(self.tmp, "repo")
        os.mkdir(self.repo)
        git(self.repo, "init", "-q", "-b", "main")
        self.write(distribuir.GENERAL_LESSONS_SOURCE, SOURCE)
        for skill in SKILLS:
            self.write(self.copy_path(skill), SOURCE)
        self.write(LUA_SOURCE_NAME, LUA_SOURCE)
        for skill in LUA_SKILLS:
            self.write(self.lua_copy_path(skill), LUA_SOURCE)
            self.write(self.armadilhas(skill), LUA_POINTER_MD)
        self.write(self.armadilhas("ai-first-godot"), POINTER)
        self.write("ai-first-defold/SKILL.md", SKILL_MD)
        self.commit("base")

    def path(self, relative):
        return os.path.join(self.repo, relative)

    def copy_path(self, skill):
        return f"{skill}/{distribuir.GENERAL_LESSONS_COPY}"

    def lua_copy_path(self, skill):
        return f"{skill}/{LUA_COPY}"

    def armadilhas(self, skill):
        return f"{skill}/references/armadilhas.md"

    def read(self, relative):
        with open(self.path(relative), "rb") as handle:
            return handle.read()

    def write(self, relative, content):
        os.makedirs(os.path.dirname(self.path(relative)) or self.repo, exist_ok=True)
        with open(self.path(relative), "wb") as handle:
            handle.write(content)

    def append(self, relative, content):
        with open(self.path(relative), "ab") as handle:
            handle.write(content)

    def commit(self, message):
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "--allow-empty", "-m", message)

    def problems(self, ref="main"):
        return distribuir.check_general_lessons(self.repo, ref)

    def assert_one_problem(self, *fragments):
        problems = self.problems()
        self.assertEqual(len(problems), 1, problems)
        for fragment in fragments:
            self.assertIn(fragment, problems[0])

    def run_script(self, *args):
        return subprocess.run([sys.executable, SCRIPT, "--repo", self.repo, *args],
                              capture_output=True, text=True)


class CheckGeneralLessons(Fixture):
    def test_base_in_sync(self):
        self.assertEqual(self.problems(), [])

    def test_copy_differs_at_line(self):
        self.write(self.copy_path("ai-first-godot"), SOURCE.replace("Lição dois".encode(), "Lição 2".encode()))
        self.commit("godot diverge")
        self.assert_one_problem("ai-first-godot/", "difere a partir da linha 8")

    def test_copy_missing(self):
        os.remove(self.path(self.copy_path("ai-first-love")))
        self.commit("lua sem cópia")
        self.assert_one_problem("ai-first-love/", "não existe")

    def test_source_edited_alone(self):
        self.append(distribuir.GENERAL_LESSONS_SOURCE, "- Lição quatro, só na fonte.\n".encode())
        self.commit("fonte sozinha")
        problems = self.problems()
        self.assertEqual(len(problems), len(SKILLS), problems)

    def test_source_missing(self):
        os.remove(self.path(distribuir.GENERAL_LESSONS_SOURCE))
        self.commit("sem fonte")
        self.assert_one_problem(f"{distribuir.GENERAL_LESSONS_SOURCE} não existe")

    def test_copy_without_final_newline(self):
        self.write(self.copy_path("ai-first-defold"), SOURCE.rstrip(b"\n"))
        self.commit("sem quebra final")
        self.assert_one_problem("ai-first-defold/", "difere")

    def test_copy_with_crlf(self):
        self.write(self.copy_path("ai-first-defold"), SOURCE.replace(b"\n", b"\r\n"))
        self.commit("crlf")
        self.assert_one_problem("ai-first-defold/", "difere a partir da linha 1")

    def test_copy_is_symlink(self):
        os.remove(self.path(self.copy_path("ai-first-godot")))
        os.symlink("../../gerais-de-jogo.md", self.path(self.copy_path("ai-first-godot")))
        self.commit("symlink")
        self.assert_one_problem("ai-first-godot/", "symlink")

    def test_lesson_written_in_old_section(self):
        self.append("ai-first-defold/references/armadilhas.md", "- Lição nova no lugar velho.\n".encode())
        self.commit("lição no lugar velho")
        self.assert_one_problem("ai-first-defold/references/armadilhas.md", "Gerais de jogo")

    def test_old_section_resurrected(self):
        # O merge que fica com o armadilhas.md de um ramo anterior à fonte única traz a seção inteira.
        old = POINTER.replace(b"moram em `references/gerais-de-jogo.md`", b"(valem em qualquer engine)")
        body = SOURCE.split(b"\n", 4)[4]
        self.write("ai-first-godot/references/armadilhas.md", old + b"\n" + body)
        self.commit("seção ressuscitada")
        self.assert_one_problem("ai-first-godot/references/armadilhas.md", "Gerais de jogo")

    def test_source_item_repeated_elsewhere(self):
        item = SOURCE.split(b"\n")[6]
        self.append("ai-first-defold/SKILL.md", b"\n" + item + b"\n")
        self.commit("item repetido")
        self.assert_one_problem("ai-first-defold/SKILL.md", "repete")

    def test_orphan_copy(self):
        self.write("ai-first-unity/SKILL.md", SKILL_MD)
        self.write("ai-first-unity/references/gerais-de-jogo.md", SOURCE.split(b"\n- ")[0])
        self.commit("órfã")
        self.assert_one_problem("ai-first-unity/references/gerais-de-jogo.md", "GENERAL_LESSONS_SKILLS")


class CheckLuaLessons(Fixture):
    def test_copy_missing(self):
        os.remove(self.path(self.lua_copy_path("ai-first-love")))
        self.commit("love sem a cópia de Lua")
        self.assert_one_problem("ai-first-love/references/gerais-de-lua.md", "não existe")

    def test_copy_differs_at_line(self):
        self.write(self.lua_copy_path("ai-first-defold"), LUA_SOURCE.replace("Lição dois".encode(), "Lição 2".encode()))
        self.commit("defold diverge")
        self.assert_one_problem("ai-first-defold/references/gerais-de-lua.md", "difere a partir da linha 8")

    def test_source_edited_alone(self):
        self.append(LUA_SOURCE_NAME, "- Lição três, só na fonte.\n".encode())
        self.commit("fonte de Lua sozinha")
        problems = self.problems()
        self.assertEqual(len(problems), len(LUA_SKILLS), problems)
        self.assertTrue(all(LUA_COPY in p for p in problems), problems)

    def test_source_missing(self):
        os.remove(self.path(LUA_SOURCE_NAME))
        self.commit("sem a fonte de Lua")
        self.assert_one_problem(f"{LUA_SOURCE_NAME} não existe")

    def test_copy_is_symlink(self):
        os.remove(self.path(self.lua_copy_path("ai-first-love")))
        os.symlink("../../gerais-de-lua.md", self.path(self.lua_copy_path("ai-first-love")))
        self.commit("symlink")
        self.assert_one_problem("ai-first-love/references/gerais-de-lua.md", "symlink")

    def test_copy_in_godot(self):
        # A Godot não usa Lua: a cópia ali o --check não compararia.
        self.write(self.lua_copy_path("ai-first-godot"), LUA_SOURCE)
        self.commit("cópia de Lua na godot")
        self.assert_one_problem("ai-first-godot/references/gerais-de-lua.md", "fora das skills")

    def test_lesson_written_in_pointer(self):
        md = self.read(self.armadilhas("ai-first-love"))
        lesson = "Cópia da fonte única; não acrescente lição aqui.\n\n- Lição nova no ponteiro de Lua.\n"
        md = md.replace("Cópia da fonte única; não acrescente lição aqui.\n\n".encode(), lesson.encode(), 1)
        self.write(self.armadilhas("ai-first-love"), md)
        self.commit("lição no ponteiro de Lua")
        self.assert_one_problem("ai-first-love/references/armadilhas.md", "Gerais de Lua")

    def test_old_section_resurrected(self):
        # O merge com o armadilhas.md de um ramo anterior à fonte única traz a seção "Lua:" inteira.
        body = LUA_SOURCE.split(b"\n", 6)[6]
        md = (MOTOR_HEAD + OLD_LUA_SECTION).encode() + body + b"\n" + GAME_POINTER.encode()
        self.write(self.armadilhas("ai-first-defold"), md)
        self.commit("seção de Lua ressuscitada")
        self.assert_one_problem("ai-first-defold/references/armadilhas.md", "Lua")

    def test_source_item_repeated_elsewhere(self):
        item = LUA_SOURCE.split(b"\n")[6]
        self.append("ai-first-defold/SKILL.md", b"\n" + item + b"\n")
        self.commit("item de Lua repetido")
        self.assert_one_problem("ai-first-defold/SKILL.md", "repete")

    def test_luals_section_is_not_the_lua_pointer(self):
        # "## LuaLS e anotações" é do motor: começa como "## Lua", mas não é a seção de Lua.
        self.append(self.armadilhas("ai-first-love"), "\n## LuaLS e anotações\n\n- Armadilha do LuaLS.\n".encode())
        self.commit("seção do LuaLS")
        self.assertEqual(self.problems(), [])


class CopyGeneral(Fixture):
    def plant_divergent_copy(self):
        self.write(self.copy_path("ai-first-godot"), b"velha\n")

    def copy_content(self, skill):
        with open(self.path(self.copy_path(skill)), "rb") as handle:
            return handle.read()

    def test_refuses_checkout_on_ref(self):
        self.plant_divergent_copy()
        result = self.run_script("--copiar-gerais")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("worktree em ramo próprio", result.stderr)
        self.assertEqual(self.copy_content("ai-first-godot"), b"velha\n")

    def test_refuses_detached_head(self):
        git(self.repo, "checkout", "-q", "--detach")
        self.plant_divergent_copy()
        result = self.run_script("--copiar-gerais")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("desanexado", result.stderr)
        self.assertEqual(self.copy_content("ai-first-godot"), b"velha\n")

    def test_rewrites_on_branch_and_undoes_symlink(self):
        git(self.repo, "checkout", "-q", "-b", "licao")
        self.plant_divergent_copy()
        os.remove(self.path(self.copy_path("ai-first-love")))
        os.symlink("../../gerais-de-jogo.md", self.path(self.copy_path("ai-first-love")))
        result = self.run_script("--copiar-gerais")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for skill in SKILLS:
            self.assertFalse(os.path.islink(self.path(self.copy_path(skill))), skill)
            self.assertEqual(self.copy_content(skill), SOURCE, skill)
        again = self.run_script("--copiar-gerais")
        self.assertNotIn("escrito", again.stdout)

    def test_rewrites_lua_copies_only_in_lua_skills(self):
        git(self.repo, "checkout", "-q", "-b", "licao")
        self.write(self.lua_copy_path("ai-first-defold"), b"velha\n")
        os.remove(self.path(self.lua_copy_path("ai-first-love")))
        os.symlink("../../gerais-de-lua.md", self.path(self.lua_copy_path("ai-first-love")))
        result = self.run_script("--copiar-gerais")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for skill in LUA_SKILLS:
            self.assertFalse(os.path.islink(self.path(self.lua_copy_path(skill))), skill)
            self.assertEqual(self.read(self.lua_copy_path(skill)), LUA_SOURCE, skill)
        self.assertFalse(os.path.lexists(self.path(self.lua_copy_path("ai-first-godot"))))
        again = self.run_script("--copiar-gerais")
        self.assertNotIn("escrito", again.stdout)

    def test_refuses_without_lua_source_before_writing(self):
        git(self.repo, "checkout", "-q", "-b", "licao")
        os.remove(self.path(LUA_SOURCE_NAME))
        self.plant_divergent_copy()
        result = self.run_script("--copiar-gerais")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(LUA_SOURCE_NAME, result.stderr)
        self.assertEqual(self.copy_content("ai-first-godot"), b"velha\n")


class CheckGeneralMode(Fixture):
    def test_reads_head_by_default(self):
        git(self.repo, "checkout", "-q", "-b", "licao")
        self.append("ai-first-defold/references/armadilhas.md", "- Lição nova no lugar velho.\n".encode())
        self.commit("lição no lugar velho")
        result = self.run_script("--check-gerais")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("PROBLEMA: ai-first-defold/references/armadilhas.md", result.stdout)

    def test_reads_lua_copy_in_head(self):
        git(self.repo, "checkout", "-q", "-b", "licao")
        self.write(self.lua_copy_path("ai-first-love"), b"velha\n")
        self.commit("love diverge na cópia de Lua")
        result = self.run_script("--check-gerais")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("PROBLEMA: ai-first-love/references/gerais-de-lua.md", result.stdout)

    def test_base_in_sync(self):
        result = self.run_script("--check-gerais")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("tudo em dia.", result.stdout)


class Generate(Fixture):
    def generate(self):
        destination = os.path.join(self.tmp, "destino")
        links = os.path.join(self.tmp, "links")
        return destination, self.run_script("--destino", destination, "--links", links)

    def test_generates_base(self):
        destination, result = self.generate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with zipfile.ZipFile(os.path.join(destination, "ai-first-defold.zip")) as archive:
            self.assertIn("ai-first-defold/references/gerais-de-jogo.md", archive.namelist())
            self.assertIn("ai-first-defold/references/gerais-de-lua.md", archive.namelist())

    def test_refuses_divergent_copy_before_writing(self):
        self.write(self.copy_path("ai-first-defold"), b"velha\n")
        self.commit("defold diverge")
        destination, result = self.generate()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("ai-first-defold/references/gerais-de-jogo.md", result.stdout)
        zips = [n for n in os.listdir(destination) if n.endswith(".zip")] if os.path.isdir(destination) else []
        self.assertEqual(zips, [])

    def test_refuses_divergent_lua_copy_before_writing(self):
        self.write(self.lua_copy_path("ai-first-love"), b"velha\n")
        self.commit("love diverge na cópia de Lua")
        destination, result = self.generate()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("ai-first-love/references/gerais-de-lua.md", result.stdout)
        zips = [n for n in os.listdir(destination) if n.endswith(".zip")] if os.path.isdir(destination) else []
        self.assertEqual(zips, [])

    def test_regenerating_overwrites_without_keeping_previous(self):
        self.generate()
        self.write("ai-first-defold/SKILL.md", SKILL_MD + b"\nlinha nova\n")
        self.commit("defold muda")
        destination, result = self.generate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(sorted(os.listdir(destination)), ["ai-first-defold.skill", "ai-first-defold.zip"])
        with zipfile.ZipFile(os.path.join(destination, "ai-first-defold.zip")) as archive:
            self.assertIn(b"linha nova", archive.read("ai-first-defold/SKILL.md"))
        folder_copy = os.path.join(destination, "ai-first-defold.skill", "ai-first-defold", "SKILL.md")
        with open(folder_copy, "rb") as handle:
            self.assertIn(b"linha nova", handle.read())

    def test_removes_previous_copy_left_by_old_versions(self):
        destination = os.path.join(self.tmp, "destino")
        os.makedirs(os.path.join(destination, "ai-first-defold.skill.antigo", "ai-first-defold"))
        for name in ("ai-first-defold.zip.antigo", "alheio.antigo"):
            with open(os.path.join(destination, name), "wb") as handle:
                handle.write(b"x")
        _, result = self.generate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(sorted(os.listdir(destination)),
                         ["ai-first-defold.skill", "ai-first-defold.zip", "alheio.antigo"])

    def test_code_audit_has_no_loose_markdown_and_leftover_goes(self):
        self.write("code-audit/SKILL.md", SKILL_MD.replace(b"ai-first-defold", b"code-audit"))
        self.commit("code-audit")
        destination = os.path.join(self.tmp, "destino")
        os.makedirs(destination)
        with open(os.path.join(destination, "code-audit-skill.md"), "wb") as handle:
            handle.write(b"sobra\n")
        _, result = self.generate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(sorted(os.listdir(destination)),
                         ["ai-first-defold.skill", "ai-first-defold.zip", "code-audit.skill", "code-audit.zip"])


if __name__ == "__main__":
    unittest.main()
