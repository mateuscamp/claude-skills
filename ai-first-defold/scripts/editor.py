#!/usr/bin/env python3
"""Prova pelo editor aberto, pela API HTTP oficial do Defold.

Modelo da skill ai-first-defold (veio do CampCrawler, D34). Adapte TAG ao prefixo
dos fatos do projeto e o fato de foco em `paused`.

Cobra no console do editor as mesmas linhas `<PROJETO>` que o portao cobra no
motor headless. Nao substitui o `tools/check.sh`: a API e experimental e depende
do editor aberto; isto e para o momento em que o autor testa pelo editor.

Uso:
    python3 tools/editor.py lancar [segundos] [--config=secao.chave=valor ...]
                                   [--exigir REGEX ...] [--recusar REGEX ...]
                                   [--sem-foco] [--projeto PASTA]
    python3 tools/editor.py observar [segundos] [--exigir ...] [--recusar ...]
                                     [--projeto PASTA]

`lancar` compila e roda pelo editor, com o `--config` passado (o robo joga).
`observar` nao roda nada: le o console enquanto o autor joga.

Sem `--recusar`, `lancar` termina assim que todas as exigencias aparecem.
Saida: 0 aprovado, 1 reprovado, 2 uso ou ambiente.
"""
import json
import os
import re
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from smoke import BAD, IGNORE  # a mesma varredura de erro do portao

ARGS_PREF = "run/engine-arguments"
# Operacoes de que a ferramenta depende. O /openapi.json e a fonte da verdade
# (manual da Editor HTTP API); se uma versao do editor mudar uma delas, a
# ferramenta para antes de agir em vez de falhar no meio.
TAG = "<PROJETO>"  # prefixo das linhas de fato do jogo

NEEDED_OPS = [("/command/run", "post"), ("/console/stream", "get"),
              ("/prefs/{path}", "get"), ("/prefs/{path}", "post")]


class Usage(Exception):
    """Erro de uso ou de ambiente: sai com 2, sem ter mudado nada."""


def parse_args(argv):
    """argv -> dict com modo, segundos, config, exigir, recusar, foco, projeto."""
    if not argv or argv[0] not in ("lancar", "observar"):
        raise Usage(__doc__)
    opts = {"mode": argv[0], "seconds": 60.0, "config": [], "require": [],
            "refuse": [], "focus": True, "project": None}
    rest = argv[1:]
    i = 0
    while i < len(rest):
        arg = rest[i]
        if arg.startswith("--config="):
            opts["config"].append(arg)
        elif arg == "--sem-foco":
            opts["focus"] = False
        elif arg in ("--exigir", "--recusar", "--projeto"):
            if i + 1 >= len(rest):
                raise Usage("%s pede um valor" % arg)
            i += 1
            key = {"--exigir": "require", "--recusar": "refuse"}.get(arg)
            if key:
                opts[key].append(rest[i])
            else:
                opts["project"] = rest[i]
        else:
            opts["seconds"] = parse_seconds(arg)
        i += 1
    if opts["mode"] == "observar" and (opts["config"] or not opts["focus"]):
        raise Usage("observar nao lanca o jogo: --config e --sem-foco nao se aplicam")
    return opts


def parse_seconds(text):
    try:
        value = float(text)
    except ValueError:
        raise Usage("argumento desconhecido: %r (esperava segundos ou opcao)" % text)
    if value <= 0:
        raise Usage("segundos deve ser positivo, recebi %s" % text)
    return value


def git_root(path):
    out = subprocess.run(["git", "-C", path, "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else os.path.abspath(path)


def find_project(explicit):
    """Pasta do projeto que o editor abriu, e a porta dele.

    Sem --projeto, so aceita o checkout atual. Numa worktree o editor costuma
    estar no checkout principal, e provar aquele codigo achando que e este seria
    um erro mudo."""
    here = git_root(os.getcwd())
    project = os.path.abspath(explicit) if explicit else here
    port_file = os.path.join(project, ".internal", "editor.port")
    if os.path.exists(port_file):
        with open(port_file) as f:
            return project, int(f.read().strip())
    common = subprocess.run(["git", "-C", here, "rev-parse", "--git-common-dir"],
                            capture_output=True, text=True).stdout.strip()
    main = os.path.dirname(os.path.abspath(os.path.join(here, common)))
    hint = ""
    if not explicit and os.path.exists(os.path.join(main, ".internal", "editor.port")):
        hint = ("\nO editor esta aberto em %s, outro checkout: ele compila AQUELE "
                "codigo. Se e isso que voce quer provar, passe --projeto %s" % (main, main))
    raise Usage("editor sem este projeto aberto (falta %s)%s" % (port_file, hint))


def request(base, path, method="GET", body=None, timeout=10):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(base + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        return err.code, err.read().decode("utf-8", "replace")
    except (urllib.error.URLError, OSError) as err:
        raise Usage("editor nao respondeu em %s%s: %s" % (base, path, err))


def check_openapi(base):
    status, text = request(base, "/openapi.json")
    if status != 200:
        raise Usage("/openapi.json respondeu %s: %s" % (status, text[:200]))
    paths = json.loads(text).get("paths", {})
    missing = ["%s %s" % (m.upper(), p) for p, m in NEEDED_OPS if m not in paths.get(p, {})]
    if missing:
        raise Usage("o editor nao oferece %s; confira a versao do editor" % ", ".join(missing))


def engine_pids():
    """Pids dos motores que o editor lanca (o `dmengine` do unpack dele).

    So Linux, como o resto das ferramentas. O bundle do portao se chama
    Mineboom.x86_64 e nao entra aqui."""
    pids = set()
    for name in os.listdir("/proc"):
        if not name.isdigit():
            continue
        try:
            exe = os.readlink("/proc/%s/exe" % name)
        except OSError:
            continue
        if os.path.basename(exe) == "dmengine":
            pids.add(int(name))
    return pids


def wait_new_engine(before, timeout=15.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        new = engine_pids() - before
        if new:
            return max(new)
        time.sleep(0.2)
    return None


def engine_args(pid):
    with open("/proc/%d/cmdline" % pid, "rb") as f:
        return [a.decode("utf-8", "replace") for a in f.read().split(b"\0") if a]


def stop_engine(pid):
    """Encerra so o processo que esta ferramenta lancou, nunca pelo nome."""
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    for _ in range(25):
        if pid not in engine_pids():
            return
        time.sleep(0.2)
    os.kill(pid, signal.SIGKILL)


def read_pref(base):
    status, text = request(base, "/prefs/" + ARGS_PREF)
    if status != 200:
        raise Usage("nao li a preferencia %s: %s %s" % (ARGS_PREF, status, text[:200]))
    return json.loads(text)


def write_pref(base, value):
    status, text = request(base, "/prefs/" + ARGS_PREF, "POST", value)
    if status != 200:
        raise RuntimeError("preferencia %s recusou %r: %s %s" % (ARGS_PREF, value, status, text[:200]))


def run_build(base, focus):
    """POST /command/run. Devolve True se o build passou; mostra o lint do editor."""
    query = "?focus=%s" % ("true" if focus else "false")
    status, text = request(base, "/command/run" + query, "POST", timeout=300)
    try:
        result = json.loads(text)
    except ValueError:
        print("--- run respondeu %s sem JSON: %s ---" % (status, text[:300]))
        return False
    issues = result.get("issues", [])
    errors = [i for i in issues if i.get("severity") == "error"]
    print("--- run: http=%s success=%s avisos=%d erros=%d ---"
          % (status, result.get("success"), len(issues) - len(errors), len(errors)))
    for issue in errors:
        print("  %s:%s %s" % (issue.get("resource"),
                              issue.get("range", {}).get("start", {}).get("line"),
                              issue.get("message")))
    return status == 200 and result.get("success") is True and not errors


def collect_console(base, seconds, done):
    """Le /console/stream por ate `seconds`; para antes se done(linhas) for verdade.

    A leitura bloqueante fica numa thread: timeout de socket no meio de um
    readline pode perder a linha parcial, e a linha perdida seria uma exigencia
    falsa. O stream comeca pelas linhas que o console ja tem.

    A conexao tambem abre dentro da thread: com o console parado, o editor
    1.13.2 nao manda nem o cabecalho HTTP ate a primeira linha nova, e um
    urlopen aqui travava a janela inteira e estourava TimeoutError depois de
    `seconds + 30` (medido em 2026-10-11, editor aberto sem jogo rodando)."""
    import threading
    lines = []
    opened = []

    def pump():
        try:
            resp = urllib.request.urlopen(base + "/console/stream", timeout=seconds + 30)
            opened.append(resp)
            for raw in resp:
                lines.append(raw.decode("utf-8", "replace").rstrip("\r\n"))
        except (OSError, ValueError, AttributeError):
            # Conexao fechada abaixo, ao fim da janela, ou console mudo ate o
            # timeout. O http.client do Python 3.14 levanta AttributeError ao
            # ler um chunk depois do close.
            pass

    threading.Thread(target=pump, daemon=True).start()
    deadline = time.time() + seconds
    while time.time() < deadline and not done(list(lines)):
        time.sleep(0.25)
    for resp in opened:
        resp.close()
    return list(lines)


def all_required(require):
    def done(lines):
        return bool(require) and all(any(re.search(p, l) for l in lines) for p in require)
    return done


def paused(lines):
    """A ultima linha de janela diz que o jogo ficou sem foco?"""
    window = [l for l in lines if TAG + " JANELA" in l]
    return bool(window) and "foco=perdido" in window[-1]


def judge(lines, require, refuse):
    """Mesmo juizo do smoke.py: erro, exigencia ausente, recusa presente."""
    facts = [l for l in lines if TAG in l]
    print("--- console: %d linhas, %d %s (ultimas abaixo) ---" % (len(lines), len(facts), TAG))
    for l in facts[-20:]:
        print(l)
    problems = [l for l in lines if BAD.search(l) and not IGNORE.search(l)]
    missing = [p for p in require if not any(re.search(p, l) for l in lines)]
    leaked = [(p, l) for p in refuse for l in lines if re.search(p, l)]
    for l in problems[:25]:
        print("  erro: " + l)
    for p in missing:
        print("  esperava casar: " + p)
    for p, l in leaked[:10]:
        print("  recusava %s, saiu: %s" % (p, l))
    if problems or missing or leaked:
        print("\n--- EDITOR FALHOU: %d erro(s), %d exigencia(s) ausente(s), %d recusa(s) ---"
              % (len(problems), len(missing), len(leaked)))
        return 1
    print("\n--- EDITOR OK ---")
    return 0


def launch(base, opts):
    """Modo lancar: preferencia trocada, run, prova, e tudo devolvido no finally."""
    if engine_pids():
        raise Usage("ja ha um jogo do editor aberto (pid %s). Feche-o: ele pode ser do "
                    "autor, e com ele aberto o run reinicia o mesmo motor sem o "
                    "--config." % ", ".join(map(str, sorted(engine_pids()))))
    original = read_pref(base)
    pid = None
    try:
        if opts["config"]:
            write_pref(base, "\n".join(opts["config"]))
        if not run_build(base, opts["focus"]):
            return 1
        pid = wait_new_engine(set())
        if pid is None:
            print("--- EDITOR FALHOU: o run nao lancou um motor novo ---")
            return 1
        lost = [c for c in opts["config"] if c not in engine_args(pid)]
        if lost:
            print("--- EDITOR FALHOU: o motor %d nao recebeu %s ---" % (pid, " ".join(lost)))
            return 1
        done = all_required(opts["require"]) if not opts["refuse"] else (lambda _l: False)
        lines = collect_console(base, opts["seconds"], done)
        verdict = judge(lines, opts["require"], opts["refuse"])
        if verdict and paused(lines):
            print("O jogo terminou sem foco, e sem foco ele pausa: o robo parou ali. "
                  "Clique na janela do jogo enquanto a prova roda.")
        return verdict
    finally:
        if pid is not None:
            stop_engine(pid)
        if opts["config"]:
            write_pref(base, original)


def main(argv):
    try:
        opts = parse_args(argv)
        project, port = find_project(opts["project"])
        base = "http://127.0.0.1:%d" % port
        check_openapi(base)
    except Usage as err:
        print(err)
        return 2
    print("--- editor %s, projeto %s ---" % (base, project))
    if opts["mode"] == "observar":
        lines = collect_console(base, opts["seconds"], lambda _l: False)
        return judge(lines, opts["require"], opts["refuse"])
    try:
        return launch(base, opts)
    except Usage as err:
        print(err)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
