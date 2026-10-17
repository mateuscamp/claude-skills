#!/usr/bin/env python3
"""Roda o jogo no engine headless por alguns segundos e falha se houver erro.

Compilar so prova que os arquivos estao no formato certo. Isto aqui executa
init/update/on_message de verdade e pega erro de Lua, URL invalida, propriedade
inexistente, etc.

Uso:
    python3 tools/smoke.py <caminho/do/executavel> [segundos]
                           [--config=secao.chave=valor ...]
                           [--exigir REGEX ...] [--recusar REGEX ...]
                           [--erro-esperado REGEX ...]

`--config` vai direto para o engine, que aceita trocar qualquer chave do
game.project em tempo de execucao: a segunda passada do portao muda o ritmo sem
compilar um segundo bundle.

`--exigir` e o que separa "nao crashou" de "a regra rodou": o padrao TEM de
aparecer na saida, senao o smoke falha. Peca ausente nao emite erro nenhum.

`--recusar` e o espelho: o padrao NAO pode aparecer. Serve para provar que um
modo desligado continua desligado (a passada do modo antigo recusa qualquer linha
do fato que so o modo novo emite) e, na passada de recusa, que o jogo nao comecou.

`--erro-esperado` e o da passada de recusa: a chave com valor errado tem de parar
o jogo com o erro que diz o recebido. A linha de erro que casa o padrao (e o
traceback logo depois dela) nao conta como problema, e o padrao TEM de casar uma
linha de erro, como o `--exigir`; qualquer outro erro continua reprovando. Opcao
desconhecida e posicional a mais saem com 2, em vez de ignorados.

Veio do bomberboom-df (tools/smoke.py), onde cada protecao abaixo custou um
diagnostico; os comentarios dela foram mantidos.
"""
import collections
import os
import re
import signal
import subprocess
import sys
import tempfile
import time

BAD = re.compile(r"ERROR:|assertion|Lua error|attempt to |stack traceback|"
                 r"WARNING:SCRIPT|could not be found|Unable to")
# Ruido conhecido do engine headless que nao indica problema no jogo.
# Remotery e o profiler: se outra instancia ainda segura a porta, ele reclama e
# segue em frente. E problema de ambiente, nao defeito do jogo.
IGNORE = re.compile(r"Unable to create window|No such device|graphics_null|"
                    r"Unable to initialize graphics|sound device|Remotery")


Veredito = collections.namedtuple("Veredito", "problemas faltando vazaram erros_ausentes")
# Opcoes que pedem um padrao logo depois, e a chave delas no dicionario de argumentos.
COM_PADRAO = {"--exigir": "exigir", "--recusar": "recusar", "--erro-esperado": "erro_esperado"}


class Uso(Exception):
    """Argumento que a ferramenta nao entende; a mensagem diz o recebido."""


def ler_argumentos(argv):
    """Opcoes da linha de comando num dicionario; levanta Uso no que nao entende.

    Opcao desconhecida e posicional a mais sao recusados: antes, `--exijir PADRAO`
    virava posicional e era ignorado, e a passada aprovava sem cobrar nada -- a
    chave errada da propria ferramenta (tools/test_smoke.py).
    """
    args = {"config": [], "exigir": [], "recusar": [], "erro_esperado": []}
    posicionais = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg.startswith("--config="):
            args["config"].append(arg)
        elif arg in COM_PADRAO:
            i += 1
            if i >= len(argv):
                raise Uso("%s pede um padrao" % arg)
            args[COM_PADRAO[arg]].append(argv[i])
        elif arg.startswith("--"):
            raise Uso("opcao desconhecida: recebido %r, esperado --config=, %s" % (arg, ", ".join(COM_PADRAO)))
        else:
            posicionais.append(arg)
        i += 1
    if not posicionais:
        raise Uso(__doc__)
    if len(posicionais) > 2:
        raise Uso("posicional a mais: recebido %r, esperado <executavel> [segundos]" % posicionais[2:])
    args["exe"] = posicionais[0]
    try:
        args["segundos"] = float(posicionais[1]) if len(posicionais) > 1 else 4.0
    except ValueError:
        raise Uso("segundos: recebido %r, esperado numero" % posicionais[1])
    return args


def e_erro(linha):
    return bool(BAD.search(linha)) and not IGNORE.search(linha)


def linhas_do_erro_esperado(lines, erro_esperado):
    """Indices das linhas perdoadas: a de erro que casa um padrao esperado e o traceback logo depois dela."""
    perdoadas = set()
    for i, linha in enumerate(lines):
        if not (e_erro(linha) and any(re.search(p, linha) for p in erro_esperado)):
            continue
        perdoadas.add(i)
        # O motor escreve o traceback do erro nas linhas seguintes: o cabecalho e os
        # quadros recuados. E do mesmo erro; a primeira linha sem recuo encerra.
        j = i + 1
        while j < len(lines) and (lines[j] == "stack traceback:" or lines[j][:1] in (" ", "\t")):
            perdoadas.add(j)
            j += 1
    return perdoadas


def julgar(lines, exigir=(), recusar=(), erro_esperado=()):
    """Veredito sobre as linhas da saida, sem motor: o teste (tools/test_smoke.py) o chama.

    `erro_esperado` e o da passada de recusa: a linha de erro que casa um padrao (e o
    traceback dela) nao conta como problema, e todo padrao TEM de casar uma linha de
    erro -- casar um fato do log nao vale. Qualquer outro erro continua problema.
    """
    perdoadas = linhas_do_erro_esperado(lines, erro_esperado)
    problemas = [l for i, l in enumerate(lines) if i not in perdoadas and e_erro(l)]
    faltando = [p for p in exigir if not any(re.search(p, l) for l in lines)]
    vazaram = [(p, l) for p in recusar for l in lines if re.search(p, l)]
    ausentes = [p for p in erro_esperado if not any(e_erro(l) and re.search(p, l) for l in lines)]
    return Veredito(problemas, faltando, vazaram, ausentes)


def main():
    try:
        args = ler_argumentos(sys.argv[1:])
    except Uso as problema:
        print(problema)
        return 2
    exe, seconds, config = args["exe"], args["segundos"], args["config"]
    exigir, recusar = args["exigir"], args["recusar"]
    if not os.path.exists(exe):
        print("executavel nao encontrado:", exe)
        return 2

    # Cada prova encerra somente o processo que criou, no finally abaixo.
    # Matar pelo nome também fecharia uma sessão do editor ou do jogador.

    # A saida vai para ARQUIVO, nunca para pipe. Ler um fd nao-bloqueante pelo
    # BufferedReader do Python (set_blocking(False) + proc.stdout.read()) perde
    # dados em silencio: a captura saturava em ~5 KB por mais tempo que o jogo
    # rodasse, entao o portao enxergava so os ~50 primeiros segundos e qualquer
    # regressao depois disso passava batido. Medido em 2026-08-15: com arquivo a
    # saida cresce linear (~96 B/s) por pelo menos 120 s; com pipe, empaca.
    # Isto e o que separa "nao crashou" de "a regra rodou".
    #
    # cwd = pasta do executavel, nunca a raiz do projeto: o engine carrega
    # "build/default/" relativo ao cwd e acabaria rodando um build antigo.
    sink = tempfile.TemporaryFile()
    try:
        # Mudo: o portão roda enquanto o autor usa a máquina. O OpenAL do sistema
        # com o driver nulo engole o som sem mexer na configuração do jogo.
        proc = subprocess.Popen([exe] + config,
                                cwd=os.path.dirname(os.path.abspath(exe)),
                                stdout=sink, stderr=subprocess.STDOUT,
                                start_new_session=True, env=dict(os.environ, ALSOFT_DRIVERS="null"))
        deadline = time.time() + seconds
        try:
            while time.time() < deadline and proc.poll() is None:
                time.sleep(0.05)
        finally:
            if proc.poll() is None:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                proc.wait(timeout=5)
        sink.seek(0)
        buf = sink.read()
    finally:
        sink.close()

    lines = buf.decode("utf-8", "replace").splitlines()
    veredito = julgar(lines, exigir, recusar, args["erro_esperado"])

    # Agora que a captura vai ate o fim, uma corrida longa passa de 80 linhas --
    # e o interessante fica no FIM (fase avancada, cascata, fim de partida), nao
    # so no boot. Por isso mostra as duas pontas em vez das primeiras 80. A
    # varredura de erro abaixo continua rodando sobre o buffer inteiro.
    if config:
        print("--- config: %s ---" % " ".join(config))
    print("--- saida (%d linhas) ---" % len(lines))
    if len(lines) <= 80:
        for l in lines:
            print(l)
    else:
        for l in lines[:40]:
            print(l)
        print("... (%d linhas omitidas) ..." % (len(lines) - 80))
        for l in lines[-40:]:
            print(l)

    # Cada categoria que falhou e mostrada, nao so a primeira: na passada de recusa
    # o motivo de verdade (o erro esperado ausente, a linha INICIO que saiu) vinha
    # escondido atras do aviso do motor sobre o valor.
    falhou = False
    if veredito.problemas:
        falhou = True
        print("\n--- SMOKE FALHOU: %d problema(s) ---" % len(veredito.problemas))
        for p in veredito.problemas[:25]:
            print(p)
    if proc.returncode not in (None, 0, -9):
        falhou = True
        print("\n--- SMOKE FALHOU: engine saiu com codigo %s ---" % proc.returncode)

    # O ERRO ESPERADO e da passada de recusa: a chave errada tem de parar o jogo
    # com o erro que diz o valor recebido. Ausente, a chave errada rodou calada --
    # no CampCrawler, `seed=abc` virava a semente 1 com o robo (2026-10-17; o
    # sys.get_config_int devolve 0, references/armadilhas.md da ai-first-defold).
    if veredito.erros_ausentes:
        falhou = True
        print("\n--- SMOKE FALHOU: %d erro(s) esperado(s) nao apareceram ---" % len(veredito.erros_ausentes))
        for p in veredito.erros_ausentes:
            print("  esperava erro casando:", p)
        print("O valor errado foi aceito sem erro: o jogo seguiu com outro valor no lugar dele.")

    # A EXIGENCIA E O CONTRARIO DA VARREDURA DE ERRO, e por isso vem depois
    # dela: a varredura pergunta "apareceu algo ruim?", esta pergunta "apareceu o
    # que tinha de aparecer?". Peca ausente nao emite erro -- o portao aprovava
    # `robos=0/0 desarmadas=0` com os tres robos falhando no spawn --, entao sem
    # este bloco a passada nova so gastaria tempo.
    if veredito.faltando:
        falhou = True
        print("\n--- SMOKE FALHOU: %d exigencia(s) nao apareceram ---" % len(veredito.faltando))
        for p in veredito.faltando:
            print("  esperava casar:", p)
        if not veredito.problemas:
            print("O jogo rodou SEM erro nenhum, e e isso que torna esta falha util:")
            print("a peca que esta passada existe para exercitar nao apareceu.")

    # Linha que nao podia sair, saiu: a peca que esta passada desliga vazou.
    if veredito.vazaram:
        falhou = True
        print("\n--- SMOKE FALHOU: %d linha(s) recusada(s) apareceram ---" % len(veredito.vazaram))
        for p, l in veredito.vazaram[:10]:
            print("  recusava %s, saiu: %s" % (p, l))
    if falhou:
        return 1

    for rotulo, padroes in (("erros esperados atendidos", args["erro_esperado"]),
                            ("exigencias atendidas", exigir), ("recusas atendidas", recusar)):
        if padroes:
            print("--- %s: %s ---" % (rotulo, ", ".join(padroes)))
    print("\n--- SMOKE OK ---")
    return 0


if __name__ == "__main__":
    sys.exit(main())
