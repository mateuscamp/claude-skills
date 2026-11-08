#!/usr/bin/env python3
"""Testes do hook_portao.sh da ai-first-godot e da ai-first-defold: só a biblioteca padrão, sem rede.

Cada caso monta um projeto git temporário com o hook da skill em `tools/`, como o SKILL.md manda
copiar, e um `tools/portao.sh` falso que só conta as chamadas. O hook tem de pular o portão só
quando nada do que a digital dele lê mudou (os tipos da lista `caminhos`), e aprovar em silêncio.
O hook da python-on-rails tem os casos dele em `test_conferir_trilho.py`.

Uso, na raiz do repositório das skills: `python3 tests/test_hook_portao.py`.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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


class Hook(unittest.TestCase):
    """Os casos de toda skill de motor. A subclasse diz a skill e um arquivo que a digital lê."""

    skill = ""
    # Um arquivo de um tipo da lista `caminhos` do hook, numa subpasta: o filtro vale em qualquer nível.
    lido = ""
    # O projeto chega à parada com commit. As subclasses `SemCommit` cobrem o projeto novo antes dele.
    commit = True
    formato = "sha1"

    def setUp(self):
        self.casa = tempfile.mkdtemp(prefix="casa-")
        self.raiz = tempfile.mkdtemp(prefix="hook-")
        self.addCleanup(shutil.rmtree, self.casa)
        self.addCleanup(shutil.rmtree, self.raiz)
        ferramentas = os.path.join(self.raiz, "tools")
        os.mkdir(ferramentas)
        shutil.copy(os.path.join(ROOT, self.skill, "scripts", "hook_portao.sh"), ferramentas)
        self.chamadas = os.path.join(self.casa, "chamadas")
        with open(os.path.join(ferramentas, "portao.sh"), "w", encoding="utf-8") as f:
            f.write(f"#!/bin/sh\necho x >> '{self.chamadas}'\n")
        os.chmod(os.path.join(ferramentas, "portao.sh"), 0o755)
        self.git("init", "-q", f"--object-format={self.formato}", ".")
        self.git("add", "-A")
        if self.commit:
            self.git("commit", "-qm", "base")

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.raiz, check=True, capture_output=True)

    def caminho(self, relativo):
        return os.path.join(self.raiz, relativo)

    def escrever(self, relativo, texto, modo="w"):
        os.makedirs(os.path.dirname(self.caminho(relativo)), exist_ok=True)
        with open(self.caminho(relativo), modo, encoding="utf-8") as f:
            f.write(texto)

    def outro_do_tipo(self, nome):
        """Um arquivo de mesmo tipo que `lido`, com outro nome, na mesma pasta."""
        pasta, base = os.path.split(self.lido)
        return os.path.join(pasta, nome + os.path.splitext(base)[1])

    def parar(self, path=None, entrada="{}"):
        # O teto impede o git de achar um repositório acima da pasta temporária.
        teto = os.path.dirname(self.raiz)
        env = {**os.environ, "HOME": self.casa, "GIT_CEILING_DIRECTORIES": teto}
        if path:
            env["PATH"] = path + os.pathsep + env["PATH"]
        feito = subprocess.run(
            ["bash", "tools/hook_portao.sh"],
            cwd=self.raiz,
            input=entrada,
            text=True,
            env=env,
            capture_output=True,
            check=False,
        )
        # O portão falso aprova: o hook sai com 0 e não diz nada, nem o erro de um git que falhou.
        self.assertEqual((feito.returncode, feito.stderr), (0, ""))
        return feito

    def chamadas_do_portao(self):
        if not os.path.exists(self.chamadas):
            return 0
        with open(self.chamadas, encoding="utf-8") as f:
            return len(f.readlines())

    def test_segunda_parada_seguida_nao_roda_o_portao(self):
        # Com `stop_hook_active`, o agente já recebeu a falha uma vez: rodar de novo prende a sessão.
        self.parar(entrada='{"stop_hook_active": true}')
        self.assertEqual(self.chamadas_do_portao(), 0)

    def test_arquivo_plantado_no_projeto_nao_pula_o_portao(self):
        # Sem `-I`, o `python3 -c` do hook importa o `json.py` da pasta onde roda: o que sai com 0
        # passa por segunda parada seguida e o portão nunca roda (o caso igual da python-on-rails).
        self.escrever("json.py", "import sys\n\nsys.exit(0)\n")
        self.parar()
        self.assertEqual(self.chamadas_do_portao(), 1)

    def test_sem_mudanca_nao_repete(self):
        self.parar()
        self.parar()
        self.assertEqual(self.chamadas_do_portao(), 1)

    def test_arquivo_novo_refaz_o_portao(self):
        self.parar()
        self.escrever(self.lido, "-- novo\n")
        self.parar()
        self.assertEqual(self.chamadas_do_portao(), 2)

    def test_arquivo_em_stage_editado_refaz_o_portao(self):
        self.escrever(self.lido, "-- um\n")
        self.git("add", self.lido)
        self.parar()
        self.escrever(self.lido, "-- dois\n", modo="a")
        self.parar()
        self.assertEqual(self.chamadas_do_portao(), 2)

    def test_edicao_posta_em_stage_refaz_o_portao(self):
        # O agente que edita e roda `git add` deixa a worktree igual ao stage: só o diff contra a
        # base (o HEAD ou a árvore vazia) vê a edição.
        self.escrever(self.lido, "-- um\n")
        self.git("add", self.lido)
        self.parar()
        self.escrever(self.lido, "-- dois\n", modo="a")
        self.git("add", self.lido)
        self.parar()
        self.assertEqual(self.chamadas_do_portao(), 2)

    def test_git_que_falha_no_diff_roda_o_portao_em_toda_parada(self):
        # Um passo do git que falha zera a digital inteira, mesmo com os outros passos de pé.
        falso = os.path.join(self.casa, "bin")
        os.mkdir(falso)
        with open(os.path.join(falso, "git"), "w", encoding="utf-8") as f:
            f.write(f'#!/bin/sh\n[ "$1" = diff ] && exit 128\nexec \'{shutil.which("git")}\' "$@"\n')
        os.chmod(os.path.join(falso, "git"), 0o755)
        self.parar(path=falso)
        self.parar(path=falso)
        self.assertEqual(self.chamadas_do_portao(), 2)

    def test_arquivo_em_stage_e_novo_ao_lado_refaz_o_portao(self):
        # O arquivo em stage e o não rastreado entram juntos: nenhum dos dois apaga o outro.
        self.escrever(self.lido, "-- um\n")
        self.git("add", self.lido)
        self.parar()
        self.escrever(self.outro_do_tipo("vizinho"), "-- novo\n")
        self.parar()
        self.assertEqual(self.chamadas_do_portao(), 2)

    def test_arquivo_fora_dos_caminhos_nao_refaz_o_portao(self):
        self.parar()
        self.escrever("notas.md", "um\n")
        self.git("add", "notas.md")
        self.parar()
        self.escrever("notas.md", "dois\n", modo="a")
        self.parar()
        self.assertEqual(self.chamadas_do_portao(), 1)

    def test_nome_com_espaco_e_acento_editado_refaz_o_portao(self):
        # Sem `-z`, o xargs parte o nome no espaço e o git cita o acento: o sha1sum não acha o
        # arquivo, o conteúdo fica fora da digital e a edição não refaz o portão.
        nome = self.outro_do_tipo("fase ação")
        self.escrever(nome, "-- um\n")
        self.parar()
        self.escrever(nome, "-- dois\n", modo="a")
        self.parar()
        self.assertEqual(self.chamadas_do_portao(), 2)

    def test_sem_git_roda_o_portao_em_toda_parada(self):
        # Sem repositório a digital não se calcula, e a digital que não se calcula não pula nada.
        shutil.rmtree(self.caminho(".git"))
        self.parar()
        self.parar()
        self.assertEqual(self.chamadas_do_portao(), 2)

    def test_symlink_quebrado_nao_desliga_o_cache(self):
        # O arquivo que o sha1sum não lê entra na digital pelo nome, sem zerar a digital inteira.
        quebrado = self.outro_do_tipo("dados")
        os.makedirs(os.path.dirname(self.caminho(quebrado)), exist_ok=True)
        os.symlink("/nao/existe", self.caminho(quebrado))
        self.parar()
        self.parar()
        self.assertEqual(self.chamadas_do_portao(), 1)
        os.remove(self.caminho(quebrado))
        os.symlink(self.caminho("tools/portao.sh"), self.caminho(quebrado))
        self.parar()
        self.assertEqual(self.chamadas_do_portao(), 2)


class Godot(Hook):
    skill = "ai-first-godot"
    lido = "cenas/jogo.gd"


class GodotSemCommit(Godot):
    """Projeto novo: `git init`, tudo em stage e o primeiro commit só no fim do ciclo.

    Sem HEAD, `git diff HEAD` falhava e a digital só via os arquivos não rastreados: o arquivo em
    stage editado depois não refazia o portão (o mesmo defeito do hook da python-on-rails, PR #62).
    """

    commit = False


class GodotSemCommitSha256(GodotSemCommit):
    """A árvore vazia do repositório sha256 tem outro hash: o hook pede ao git, não usa constante."""

    formato = "sha256"


class Defold(Hook):
    skill = "ai-first-defold"
    lido = "main/jogo.lua"


class DefoldSemCommit(Defold):
    """Projeto novo, como em `GodotSemCommit`."""

    commit = False


class DefoldSemCommitSha256(DefoldSemCommit):
    """Repositório sha256, como em `GodotSemCommitSha256`."""

    formato = "sha256"


# A base não é caso: sem skill, ela não tem hook para copiar. Fora do módulo, o unittest não a
# coleta, e as subclasses seguem com ela.
del Hook


if __name__ == "__main__":
    unittest.main()
