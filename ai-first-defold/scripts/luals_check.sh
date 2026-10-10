#!/bin/sh
# Checagem estática dos scripts Lua com o LuaLS e as anotações OFICIAIS do Defold.
#
#   tools/luals_check.sh
#
# Por que existe: o bob aceita API inventada e tipo errado — `gui.cancel_animation`
# compila e só estoura quando aquele caminho roda (pegadinha 11 do bomberboom-df).
# O LuaLS com as anotações da versão instalada pega isso em segundos.
#
# Nada é baixado: o editor 1.13.2 traz o LuaLS e as anotações do Defold dentro do
# próprio jar. Este script os extrai para um cache da MÁQUINA, separado por sha do
# engine — atualizar o editor gera um cache novo, e anotação de outra versão nunca
# julga este código.
#
# Copiado da skill ai-first-defold. AJUSTE: LUALS_IGNORAR lista pastas que não são
# código do jogo (separadas por espaço), além de build/, dist/ e .internal/.
#
# Sem `files.associations` o LuaLS só lê `.lua` e pula EM SILÊNCIO `.script`,
# `.gui_script` e `.render_script`: o código de cena passava verde sem ser lido.
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
DEFOLD=${DEFOLD:-/opt/Defold}
SHA=$(grep -E '^engine_sha1' "$DEFOLD/config" | cut -d' ' -f3)
JAR="$DEFOLD/packages/defold-$SHA.jar"
if [ -z "$SHA" ] || [ ! -f "$JAR" ]; then
  echo "jar do editor nao encontrado em $DEFOLD (engine_sha1=$SHA). Exporte DEFOLD=<pasta do editor>." >&2
  exit 2
fi

case "$(uname -s)-$(uname -m)" in
  Linux-x86_64) PLAT=x86_64-linux ;;
  Linux-aarch64) PLAT=arm64-linux ;;
  Darwin-arm64) PLAT=arm64-macos ;;
  Darwin-x86_64) PLAT=x86_64-macos ;;
  *) echo "plataforma sem LuaLS conhecida: $(uname -s)-$(uname -m)" >&2; exit 2 ;;
esac

CACHE=${XDG_CACHE_HOME:-$HOME/.cache}/defold-luals/$SHA
LUALS="$CACHE/_unpack/$PLAT/bin/lsp/lua/bin/lua-language-server"
if [ ! -x "$LUALS" ]; then
  mkdir -p "$CACHE"
  (cd "$CACHE" && unzip -q -o "$JAR" "_unpack/$PLAT/bin/lsp/lua/*")
  chmod +x "$LUALS"
fi
LIBRARY="$CACHE/_unpack/$PLAT/bin/lsp/lua/meta/3rd/Defold/library"

# A configuração leva caminho absoluto da máquina, então nasce no cache e não no
# repositório. As regras de verdade ficam aqui, versionadas.
IGNORAR='"build", "dist", ".internal"'
for pasta in ${LUALS_IGNORAR:-}; do IGNORAR="$IGNORAR, \"$pasta\""; done
# Anotações do projeto para o que a oficial deixa de fora (um arquivo `---@meta`,
# só com API que uma passada do portão exercita no motor). LUALS_ANOTACOES muda a pasta.
ANOTACOES="$ROOT/${LUALS_ANOTACOES:-tools/luals}"
BIBLIOTECA="\"$LIBRARY\""
[ -d "$ANOTACOES" ] && BIBLIOTECA="$BIBLIOTECA, \"$ANOTACOES\""
CONFIG="$CACHE/luarc.json"
cat > "$CONFIG" <<JSON
{
  "runtime.version": "LuaJIT",
  "files.associations": { "*.script": "lua", "*.gui_script": "lua", "*.render_script": "lua", "*.editor_script": "lua" },
  "workspace.library": [$BIBLIOTECA],
  "workspace.checkThirdParty": false,
  "workspace.ignoreDir": [$IGNORAR],
  "diagnostics.globals": ["init", "final", "update", "fixed_update", "on_message", "on_input", "on_reload"],
  "diagnostics.severity": { "lowercase-global": "Error", "undefined-global": "Error", "undefined-field": "Error" }
}
JSON

LOG="$CACHE/check.json"
rm -f "$LOG"
"$LUALS" --check "$ROOT" --configpath "$CONFIG" --checklevel Warning --check_out_path "$LOG" >/dev/null 2>&1 || true

# Sem relatório não há prova de que a checagem rodou: falha, em vez de aprovar.
if [ ! -f "$LOG" ]; then
  echo "LuaLS nao produziu relatorio; a checagem nao rodou" >&2
  exit 2
fi
python3 - "$LOG" "$ROOT" <<'PY'
import json, sys, urllib.parse
report = json.load(open(sys.argv[1]))
# Sem problemas, o LuaLS grava uma lista vazia em vez de um objeto.
if isinstance(report, list):
    report = {}
root = sys.argv[2]
problems = []
for uri, diags in report.items():
    path = urllib.parse.unquote(uri.replace("file://", ""))
    rel = path[len(root) + 1:] if path.startswith(root) else path
    for d in diags:
        line = d["range"]["start"]["line"] + 1
        problems.append("%s:%d [%s] %s" % (rel, line, d.get("code"), d["message"].splitlines()[0]))
for p in sorted(problems):
    print(p)
if problems:
    print("--- LuaLS: %d problema(s) ---" % len(problems))
    sys.exit(1)
print("LuaLS: nenhum problema, com as anotacoes do Defold instalado")
PY
