#!/usr/bin/env sh
# Suíte de domínio sem engine. Teste novo entra sozinho: tests/test_*.lua.
#
# Roda em LuaJIT (o Lua do Defold) e, se houver, num Lua 5.x de referência: a regra
# precisa valer nos dois, para nenhuma dependência exclusiva do LuaJIT entrar no
# domínio sem ninguém ver. Sem interpretador nenhum, falha: não existe "passou"
# sem ter rodado. Copiado da skill ai-first-defold.
set -e
cd "$(dirname "$0")"
ran=0
for interpreter in luajit lua; do
  if command -v "$interpreter" >/dev/null 2>&1; then
    "$interpreter" tests/run.lua tests/test_*.lua
    ran=1
  fi
done
[ "$ran" -eq 1 ] || { echo "nenhum interpretador Lua encontrado (esperado luajit ou lua)" >&2; exit 2; }
