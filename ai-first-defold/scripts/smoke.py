#!/usr/bin/env python3
"""Roda o jogo no engine headless por alguns segundos e falha se houver erro.

Compilar so prova que os arquivos estao no formato certo. Isto aqui executa
init/update/on_message de verdade e pega erro de Lua, URL invalida, propriedade
inexistente, etc.

Uso:
    python3 tools/smoke.py <caminho/do/executavel> [segundos]
                           [--config=secao.chave=valor ...]
                           [--exigir REGEX ...]

`--config` vai direto para o engine, que aceita trocar qualquer chave do
game.project em tempo de execucao: a segunda passada do portao muda o ritmo sem
compilar um segundo bundle.

`--exigir` e o que separa "nao crashou" de "a regra rodou": o padrao TEM de
aparecer na saida, senao o smoke falha. Peca ausente nao emite erro nenhum.

Veio do bomberboom-df (tools/smoke.py), onde cada protecao abaixo custou um
diagnostico; os comentarios dela foram mantidos.
"""
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


def main():
    posicionais, config, exigir = [], [], []
    resto = sys.argv[1:]
    i = 0
    while i < len(resto):
        arg = resto[i]
        if arg.startswith("--config="):
            config.append(arg)
        elif arg == "--exigir":
            i += 1
            if i >= len(resto):
                print("--exigir pede um padrao")
                return 2
            exigir.append(resto[i])
        else:
            posicionais.append(arg)
        i += 1

    if not posicionais:
        print(__doc__)
        return 2
    exe = posicionais[0]
    seconds = float(posicionais[1]) if len(posicionais) > 1 else 4.0
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
    problems = [l for l in lines if BAD.search(l) and not IGNORE.search(l)]

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

    if problems:
        print("\n--- SMOKE FALHOU: %d problema(s) ---" % len(problems))
        for p in problems[:25]:
            print(p)
        return 1
    if proc.returncode not in (None, 0, -9):
        print("\n--- SMOKE FALHOU: engine saiu com codigo %s ---" % proc.returncode)
        return 1

    # A EXIGENCIA E O CONTRARIO DA VARREDURA DE ERRO, e por isso vem depois
    # dela: a varredura pergunta "apareceu algo ruim?", esta pergunta "apareceu o
    # que tinha de aparecer?". Peca ausente nao emite erro -- o portao aprovava
    # `robos=0/0 desarmadas=0` com os tres robos falhando no spawn --, entao sem
    # este bloco a passada nova so gastaria tempo.
    faltando = [p for p in exigir if not any(re.search(p, l) for l in lines)]
    if faltando:
        print("\n--- SMOKE FALHOU: %d exigencia(s) nao apareceram ---"
              % len(faltando))
        for p in faltando:
            print("  esperava casar:", p)
        print("O jogo rodou SEM erro nenhum, e e isso que torna esta falha util:")
        print("a peca que esta passada existe para exercitar nao apareceu.")
        return 1

    if exigir:
        print("\n--- exigencias atendidas: %s ---" % ", ".join(exigir))
    print("\n--- SMOKE OK ---")
    return 0


if __name__ == "__main__":
    sys.exit(main())
