#!/bin/sh
# Bundle debug COM a Automation Bridge (skill ai-first-defold), separado do portão.
#
#   tools/bridge_build.sh [saida]      (padrão: dist/bridge)
#
# A dependência mora em tools/bridge.ini, nunca no game.project: a Bridge é
# extensão nativa, e extensão nativa compila no servidor de build da Defold. Se ela
# estivesse no game.project, todo tools/check.sh passaria a depender de rede e de
# serviço externo. Release nunca a recebe.
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT=${1:-$ROOT/dist/bridge}
BUILD_SERVER=${BUILD_SERVER:-https://build.defold.com}
. "$ROOT/tools/plataforma.sh"
cd "$ROOT"
BOB=${BOB_JAR:-}
if [ -z "$BOB" ] || [ ! -f "$BOB" ]; then
  echo "bob.jar nao encontrado. Exporte BOB_JAR=/caminho/para/bob.jar" >&2
  exit 1
fi
STATUS=0
LOG=$(java -jar "$BOB" --root . --settings tools/bridge.ini --platform "$BOB_PLATAFORMA" --variant debug \
        --build-server "$BUILD_SERVER" --archive --bundle-output "$OUT" resolve build bundle 2>&1) || STATUS=$?
if [ "$STATUS" -ne 0 ] || echo "$LOG" | grep -qE "ERROR|SEVERE|Could not parse"; then
  echo "--- BUILD DA BRIDGE FALHOU ---"
  echo "$LOG" | grep -E "ERROR|SEVERE|Could not parse|Exception|error" | grep -vE "^ *[0-9]+% " | head -30
  exit 1
fi
APP=$(acha_app "$OUT" "$ROOT")
if [ -z "$APP" ]; then
  echo "--- BUILD DA BRIDGE FALHOU: bundle nao produzido ---"
  echo "$LOG" | grep -vE "^ *[0-9]+% " | tail -15
  exit 1
fi
echo "$APP"
