#!/usr/bin/env python3
"""Prova de cena pela Automation Bridge oficial — EXEMPLO do projeto Mineboom.

Copiado da skill ai-first-defold. É um exemplo que funciona, não um genérico:
troque os ids (`hud_turn`, `cell_4_4`), as linhas de log exigidas (`TOQUE ...`) e
as chaves `--config` pelas do seu jogo. O que vale manter como está: o envelope
{ok, data}, o toque como sessão de ponteiro, o stdbuf e a espera do screenshot.

Abre o bundle debug com a Bridge (tools/bridge_build.sh), descobre a porta do
serviço do engine no log e, pela API HTTP da Bridge:

1. confere /health (build debug, plataforma, capacidades);
2. lê o texto do turno pelo id `hud_turn`;
3. toca DUAS vezes na célula `cell_4_4` pela entrada do engine — o caminho do
   mouse de verdade, on_input incluído, e não o atalho on_touch do robô;
4. exige no log a ordem aceita e no texto o turno 1;
5. grava um screenshot.

Uso (dentro de um display, ex. xvfb-run):
    python3 tools/prova_bridge.py <executavel> <pasta-de-saida>

Biblioteca padrão só. Sai com 1 se qualquer exigência faltar.
"""
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

CLIENT = "client_id=mineboom-prova&session_id=prova"


def fail(message, log_path=None):
    print("--- PROVA DA BRIDGE FALHOU: %s ---" % message)
    if log_path and os.path.exists(log_path):
        print("".join(open(log_path, encoding="utf-8", errors="replace").readlines()[-15:]))
    sys.exit(1)


def wait_for(predicate, seconds):
    deadline = time.time() + seconds
    while time.time() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.1)
    return None


def request(base, method, path, body=None):
    """Resposta da Bridge já desembrulhada: o `data` do envelope em sucesso,
    {"error": ...} em falha lógica, {} quando a conexão não respondeu."""
    url = base + path
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"} if data else {})
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            envelope = json.loads(response.read().decode() or "{}")
    except urllib.error.HTTPError as error:
        # Falha lógica chega como HTTP 500 com o envelope de erro no corpo.
        try:
            envelope = json.loads(error.read().decode() or "{}")
        except ValueError:
            return {"error": {"status": error.code}}
    except (urllib.error.URLError, ConnectionError, TimeoutError):
        return {}
    if envelope.get("ok") is True:
        data = envelope.get("data")
        return data if isinstance(data, dict) else {"value": data}
    return {"error": envelope.get("error") or envelope}


def log_text(path):
    return open(path, encoding="utf-8", errors="replace").read() if os.path.exists(path) else ""


def element(base, name):
    """O id de nó que o jogo dá com gui.set_id aparece como `name`; o `id` da
    Bridge é de snapshot e muda com a cena."""
    reply = request(base, "GET", "/elements?name_exact=%s&include=bounds,properties" % name)
    items = reply.get("elements") or []
    return items[0] if items else None


def element_text(item):
    if not item:
        return ""
    for key in ("text", "label"):
        if isinstance(item.get(key), str):
            return item[key]
    props = item.get("properties") or {}
    return str(props.get("text", ""))


def tap(base, item):
    """Toque como sessão de ponteiro: abre, segura e solta.

    /input/click com duração zero é despachado (o /input/status diz `released`) e
    mesmo assim o jogo não registra — medido no bomberboom-df,
    docs/AVALIACAO_AUTOMATION_BRIDGE.md. O recibo do POST é do aceite, não da
    entrega; por isso a prova confere o efeito no jogo, e não o recibo.
    """
    center = (item.get("bounds") or {}).get("center") or {}
    if "x" not in center:
        fail("elemento sem bounds para tocar: %s" % json.dumps(item)[:300])
    opened = request(base, "POST", "/input/pointer/open?x=%s&y=%s&pointer_lease=5&%s" % (
        center["x"], center["y"], CLIENT))
    if opened.get("error") or "input_id" not in opened:
        fail("ponteiro recusado: %s" % json.dumps(opened)[:300])
    input_id = opened["input_id"]
    request(base, "POST", "/input/pointer/hold?input_id=%s&duration=0.12&pointer_lease=5&%s" % (input_id, CLIENT))
    up = request(base, "POST", "/input/pointer/up?input_id=%s&%s" % (input_id, CLIENT))
    if up.get("error"):
        fail("soltar o ponteiro falhou: %s" % json.dumps(up)[:300])
    return input_id


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    exe = os.path.abspath(sys.argv[1])
    out = os.path.abspath(sys.argv[2])
    os.makedirs(out, exist_ok=True)
    log_path = os.path.join(out, "jogo.log")
    sink = open(log_path, "w")
    # cwd na pasta do executável: o engine carrega build/ relativo ao diretório atual.
    # stdbuf: com a saída indo para arquivo o engine segura o log num buffer até
    # sair, e a prova leria o arquivo vazio enquanto o jogo ainda roda.
    line_buffered = ["stdbuf", "-oL", "-eL"] if shutil.which("stdbuf") else []
    proc = subprocess.Popen(line_buffered + [exe, "--config=mineboom.lang=en", "--config=mineboom.seed=3"],
                            cwd=os.path.dirname(exe), stdout=sink, stderr=subprocess.STDOUT,
                            start_new_session=True)
    try:
        port = wait_for(lambda: (re.search(r"Engine service started on port (\d+)", log_text(log_path)) or [None, None])[1],
                        20)
        if not port:
            fail("o engine não anunciou a porta do serviço", log_path)
        base = "http://127.0.0.1:%s/automation-bridge/v2" % port

        health = wait_for(lambda: request(base, "GET", "/health"), 15) or {}
        if not health or health.get("error"):
            fail("Bridge não respondeu em %s: %s" % (base, health), log_path)
        print("health: debug=%s plataforma=%s capacidades=%s" % (
            health.get("debug"), health.get("platform"), ",".join(sorted(health.get("capabilities") or []))[:300]))
        if health.get("debug") is not True:
            fail("a Bridge precisa de build debug: %s" % health.get("debug"))

        turn = wait_for(lambda: element(base, "hud_turn"), 10)
        if not turn:
            fail("elemento hud_turn não encontrado na cena", log_path)
        before = element_text(turn)
        print("turno antes: %r" % before)

        cell = element(base, "cell_4_4")
        if not cell:
            fail("elemento cell_4_4 não encontrado na cena", log_path)
        print("cell_4_4: %s" % json.dumps({k: cell.get(k) for k in ("id", "bounds", "visible", "enabled")})[:300])

        request(base, "PUT", "/input/configure?%s&lease=10&device=mouse&visualize=0" % CLIENT)
        tap(base, cell)
        if not wait_for(lambda: "TOQUE avanco=nao celula=4,4 efeito=selected" in log_text(log_path), 5):
            fail("o primeiro clique não selecionou a célula 4,4", log_path)
        tap(base, cell)
        if not wait_for(lambda: "TOQUE avanco=nao celula=4,4 efeito=order_accepted" in log_text(log_path), 5):
            fail("o segundo clique não emitiu a ordem", log_path)
        after = wait_for(lambda: (lambda t: t if "1" in t and t != before else None)(element_text(element(base, "hud_turn"))),
                         10)
        if not after:
            fail("o texto do turno não mudou para o turno 1: %r" % element_text(element(base, "hud_turn")), log_path)
        print("turno depois: %r" % after)
        # Um toque, uma ação: se mouse e toque chegassem juntos, o segundo clique
        # contaria duas vezes e o log teria mais de uma ordem para dois cliques.
        orders = log_text(log_path).count("efeito=order_accepted")
        if orders != 1:
            fail("dois cliques produziram %d ordens, esperado 1" % orders, log_path)

        # O screenshot é assíncrono: o GET devolve `pending`, e o arquivo só vale
        # quando /screenshot/status disser que terminou.
        shot = request(base, "GET", "/screenshot")
        if shot.get("pending"):
            shot = wait_for(lambda: (lambda st: st if not st.get("pending") else None)(
                request(base, "GET", "/screenshot/status?capture_id=%s" % shot.get("capture_id"))), 10) or shot
        path = shot.get("path")
        if path and os.path.exists(path):
            shutil.copy(path, os.path.join(out, "bridge.png"))
            print("screenshot: %s" % os.path.join(out, "bridge.png"))
        else:
            print("screenshot indisponível: %s" % json.dumps(shot)[:300])
        print("--- PROVA DA BRIDGE OK ---")
        return 0
    finally:
        if proc.poll() is None:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            proc.wait(timeout=5)
        sink.close()


if __name__ == "__main__":
    sys.exit(main())
