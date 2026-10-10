#!/bin/sh
# Portão de um projeto Defold: domínio sem engine, LuaLS com as anotações oficiais,
# build headless pelo bob e o motor de verdade com --exigir por linha de log.
#
#   tools/portao.sh           tudo
#   tools/portao.sh --rapido  só testes de domínio e LuaLS (segundos), o que o hook Stop roda
#
# Copiado da skill ai-first-defold. Ajuste só o bloco AJUSTE abaixo.
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
. "$ROOT/tools/plataforma.sh"

# ---- AJUSTE ------------------------------------------------------------------
OUTDIR=${PORTAO_OUT:-${XDG_CACHE_HOME:-$HOME/.cache}/$(basename "$ROOT")-headless}
# Geradores com modo --check (fontes, tiles, ...): reprovam asset desatualizado.
geradores() {
  : # python3 tools/gen_fonts.py --check
}
# As passadas do motor. Cada uma exige o que a peça alterada PRECISA produzir:
# peça ausente não emite erro, então "não deu erro" não prova nada.
passadas() {
  APP=$1
  python3 tools/smoke.py "$APP" 6 --config=<projeto>.autoplay=1 \
    --exigir '^DEBUG:SCRIPT: <PROJETO> INICIO '
}
# ------------------------------------------------------------------------------

if [ -x ./run_tests.sh ]; then ./run_tests.sh; fi
tools/luals_check.sh
[ "$1" = "--rapido" ] && exit 0
geradores

BOB=${BOB_JAR:-}
if [ -z "$BOB" ] || [ ! -f "$BOB" ]; then
  echo "bob.jar nao encontrado. Exporte BOB_JAR=/caminho/para/bob.jar" >&2
  exit 1
fi
STATUS=0
# smoketest.ini: [display] vsync = 0. Sem vsync de hardware, o headless cai num
# vsync por software que às vezes espera para sempre (o motor sobe e não avança).
LOG=$(java -jar "$BOB" --root . --platform "$BOB_PLATAFORMA" --variant headless \
        --settings tools/smoketest.ini --archive --bundle-output "$OUTDIR" build bundle 2>&1) || STATUS=$?
# O bob sinaliza falha como ERROR e também como SEVERE, e então aborta deixando o
# bundle anterior no lugar — o smoke rodaria código velho e passaria.
if [ "$STATUS" -ne 0 ] || echo "$LOG" | grep -qE "ERROR|SEVERE|Could not parse"; then
  echo "--- BUILD FALHOU ---"
  echo "$LOG" | grep -E "ERROR|SEVERE|Could not parse|Exception" | grep -vE "^ *[0-9]+% " | head -20
  exit 1
fi
APP=$(acha_app "$OUTDIR" "$ROOT")
if [ -z "$APP" ]; then
  echo "--- BUILD FALHOU: o bundle nao foi produzido ($BOB_PLATAFORMA) ---"
  echo "$LOG" | grep -vE "^ *[0-9]+% " | tail -10
  echo "ClassNotFoundException? Refaça o link defold-editor.jar do bob (references/armadilhas.md)."
  exit 1
fi
echo "--- BUILD OK ($BOB_PLATAFORMA) ---"
passadas "$APP"
