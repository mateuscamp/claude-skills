#!/usr/bin/env python3
"""Teste do tools/smoke.py: o juízo das linhas da saída do motor e os argumentos.

Roda no tools/portao.sh (bloco `geradores`), só com a biblioteca padrão. Sai com 1 se
algum caso falhar. Copie junto com o smoke.py; não precisa de adaptação.

O `--erro-esperado` existe para as passadas de recusa: a chave errada tem de parar o
jogo com o erro que diz o valor recebido. A linha casada não conta como problema e
TEM de aparecer, como o `--exigir`; qualquer outro erro continua reprovando.

Modelo da skill ai-first-defold (veio do CampCrawler, 2026-10-17).
"""
import os
import stat
import subprocess
import sys
import tempfile
import unittest

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import smoke  # noqa: E402

# Saída do motor 1.14.0 com erro no init do gui_script, medida no CampCrawler com
# `--config=campcrawler.trees=2`, com o nome do projeto trocado por `jogo`/`JOGO` (o
# juízo não depende dele): a mensagem, o traceback dela e a linha do GAMESYS que diz
# que o componente não iniciou.
ERRO_NO_INIT = [
    'ERROR:SCRIPT: main/scene_config.lua:77: jogo.trees inválido: recebido "2", esperado 0 ou 1',
    "stack traceback:",
    "  [C]:-1: in function error",
    "  main/scene_config.lua:77: in function trees",
    "  main/game.gui_script:324: in function <main/game.gui_script:311>",
    "",
    "ERROR:GAMESYS: Error when initializing gui component: RESULT_SCRIPT_ERROR.",
    "INFO:ENGINE: Defold Engine 1.14.0 (a81dbb0)",
]
MENSAGEM = r'jogo\.trees inválido: recebido "2", esperado 0 ou 1$'
COMPONENTE = r"^ERROR:GAMESYS: Error when initializing gui component"

PARTIDA_LIMPA = [
    "INFO:ENGINE: Defold Engine 1.14.0 (a81dbb0)",
    "DEBUG:SCRIPT: JOGO INICIO autoplay=true semente=3",
    "DEBUG:SCRIPT: JOGO TURNO fim=1 turno=1",
]


def limpo(veredito):
    return not (veredito.problemas or veredito.faltando or veredito.vazaram or veredito.erros_ausentes)


class ErroEsperado(unittest.TestCase):
    def test_erro_esperado_presente_aprova(self):
        v = smoke.julgar(ERRO_NO_INIT, erro_esperado=[MENSAGEM, COMPONENTE])
        self.assertTrue(limpo(v), "o erro esperado, o traceback dele e o GAMESYS declarado: %r" % (v,))

    def test_erro_esperado_ausente_reprova(self):
        v = smoke.julgar(PARTIDA_LIMPA, erro_esperado=[MENSAGEM])
        self.assertEqual(v.erros_ausentes, [MENSAGEM], "a chave errada rodou calada: tem de reprovar")

    def test_erro_inesperado_junto_reprova(self):
        linhas = ERRO_NO_INIT + ["ERROR:SCRIPT: main/game.gui_script:390: attempt to index a nil value"]
        v = smoke.julgar(linhas, erro_esperado=[MENSAGEM, COMPONENTE])
        self.assertEqual(v.problemas, [linhas[-1]], "só o erro esperado é perdoado")

    def test_erro_nao_declarado_continua_problema(self):
        v = smoke.julgar(ERRO_NO_INIT, erro_esperado=[MENSAGEM])
        self.assertEqual(v.problemas, [ERRO_NO_INIT[6]], "o GAMESYS não declarado reprova")

    def test_traceback_de_erro_inesperado_reprova(self):
        v = smoke.julgar(ERRO_NO_INIT, erro_esperado=[COMPONENTE])
        self.assertEqual(v.problemas, ERRO_NO_INIT[:2], "o traceback só é do erro esperado quando vem logo depois dele")

    def test_linha_que_nao_e_erro_nao_conta_como_erro_esperado(self):
        linhas = PARTIDA_LIMPA + ["DEBUG:SCRIPT: JOGO NOTA jogo.trees inválido: recebido \"2\", esperado 0 ou 1"]
        v = smoke.julgar(linhas, erro_esperado=[MENSAGEM])
        self.assertEqual(v.erros_ausentes, [MENSAGEM], "erro esperado casa só linha de erro")


class ExigirERecusar(unittest.TestCase):
    def test_partida_limpa_aprova(self):
        v = smoke.julgar(PARTIDA_LIMPA, exigir=["JOGO TURNO fim=1 "], recusar=["JOGO CHAVE "])
        self.assertTrue(limpo(v), repr(v))

    def test_exigencia_ausente_reprova(self):
        v = smoke.julgar(PARTIDA_LIMPA, exigir=["JOGO RUN "])
        self.assertEqual(v.faltando, ["JOGO RUN "])

    def test_recusa_presente_reprova(self):
        v = smoke.julgar(PARTIDA_LIMPA, recusar=["JOGO TURNO "])
        self.assertEqual(v.vazaram, [("JOGO TURNO ", PARTIDA_LIMPA[2])])

    def test_erro_sem_erro_esperado_reprova(self):
        v = smoke.julgar(ERRO_NO_INIT)
        self.assertEqual(v.problemas, [ERRO_NO_INIT[0], ERRO_NO_INIT[1], ERRO_NO_INIT[6]])

    def test_ruido_do_motor_headless_nao_reprova(self):
        v = smoke.julgar(PARTIDA_LIMPA + ["WARNING:DLIB: Unable to create window"])
        self.assertTrue(limpo(v), repr(v))


class Argumentos(unittest.TestCase):
    def test_erro_esperado_se_repete(self):
        a = smoke.ler_argumentos(["app", "4", "--config=jogo.trees=2", "--erro-esperado", "A",
                                  "--erro-esperado", "B", "--exigir", "C", "--recusar", "D"])
        self.assertEqual((a["exe"], a["segundos"], a["config"], a["erro_esperado"], a["exigir"], a["recusar"]),
                         ("app", 4.0, ["--config=jogo.trees=2"], ["A", "B"], ["C"], ["D"]))

    def test_opcao_desconhecida_e_recusada(self):
        # Antes, `--exijir PADRAO` virava posicional e era ignorado: a passada aprovava
        # sem cobrar nada. Opção errada é a chave errada da própria ferramenta.
        with self.assertRaises(smoke.Uso) as ctx:
            smoke.ler_argumentos(["app", "4", "--exijir", "JOGO RUN "])
        self.assertIn("opcao desconhecida: recebido '--exijir'", str(ctx.exception))

    def test_posicional_a_mais_e_recusado(self):
        with self.assertRaises(smoke.Uso) as ctx:
            smoke.ler_argumentos(["app", "4", "JOGO RUN "])
        self.assertIn("JOGO RUN ", str(ctx.exception))

    def test_segundos_que_nao_sao_numero_sao_recusados(self):
        with self.assertRaises(smoke.Uso) as ctx:
            smoke.ler_argumentos(["app", "quatro"])
        self.assertIn("'quatro'", str(ctx.exception))

    def test_opcao_sem_padrao_e_recusada(self):
        with self.assertRaises(smoke.Uso):
            smoke.ler_argumentos(["app", "4", "--erro-esperado"])


class DePontaAPonta(unittest.TestCase):
    """O smoke.py inteiro contra um motor de mentira que imprime a saída medida."""

    def rodar(self, linhas, *opcoes):
        with tempfile.TemporaryDirectory() as pasta:
            saida = os.path.join(pasta, "saida.txt")
            with open(saida, "w", encoding="utf-8") as f:
                f.write("\n".join(linhas) + "\n")
            motor = os.path.join(pasta, "motor")
            with open(motor, "w", encoding="utf-8") as f:
                f.write("#!/bin/sh\ncat '%s'\n" % saida)
            os.chmod(motor, os.stat(motor).st_mode | stat.S_IXUSR)
            feito = subprocess.run([sys.executable, os.path.join(AQUI, "smoke.py"), motor, "5"] + list(opcoes),
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
            return feito.returncode, feito.stdout.decode("utf-8", "replace")

    def test_passada_de_recusa_aprova_com_o_erro(self):
        codigo, texto = self.rodar(ERRO_NO_INIT, "--erro-esperado", MENSAGEM, "--erro-esperado", COMPONENTE,
                                   "--recusar", "JOGO INICIO ")
        self.assertEqual(codigo, 0, texto)

    def test_passada_de_recusa_reprova_sem_o_erro(self):
        codigo, texto = self.rodar(PARTIDA_LIMPA, "--erro-esperado", MENSAGEM)
        self.assertEqual(codigo, 1, texto)
        self.assertIn("erro(s) esperado(s) nao apareceram", texto)

    def test_mostra_toda_categoria_que_falhou(self):
        # Medido no motor com `seed=abc` antes da correção: o aviso do motor sobre o
        # valor escondia o motivo de verdade, o erro esperado ausente e o INICIO que saiu.
        linhas = PARTIDA_LIMPA + ["WARNING:DLIB: Unable to convert 'abc' to int"]
        codigo, texto = self.rodar(linhas, "--erro-esperado", MENSAGEM, "--recusar", "JOGO INICIO ")
        self.assertEqual(codigo, 1, texto)
        for trecho in ("1 problema(s)", "1 erro(s) esperado(s) nao apareceram", "1 linha(s) recusada(s)"):
            self.assertIn(trecho, texto)


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=1).result
    sys.exit(0 if result.wasSuccessful() else 1)
