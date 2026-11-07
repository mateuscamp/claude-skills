#!/usr/bin/env bash
# Hook Stop do Claude Code: roda `tools/portao.sh --rapido` (testes de domínio + LuaLS)
# quando Lua, script ou recurso Defold mudou desde a última aprovação, e devolve a
# falha ao agente (exit 2) antes de ele dizer que terminou.
# Registro em .claude/settings.json do projeto:
#   {"hooks": {"Stop": [{"hooks": [{"type": "command",
#     "command": "\"$CLAUDE_PROJECT_DIR\"/tools/hook_portao.sh", "timeout": 300}]}]}}
# Copiado da skill ai-first-defold.
set -uo pipefail

raiz="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
entrada="$(cat)"
# Na segunda parada seguida o agente já recebeu a falha uma vez: não prende a sessão em laço.
if python3 -c 'import json,sys; sys.exit(0 if json.loads(sys.argv[1]).get("stop_hook_active") else 1)' \
    "$entrada" 2> /dev/null; then
  exit 0
fi

cd "$raiz" || exit 0
caminhos=('*.lua' '*.script' '*.gui_script' '*.render_script' '*.gui' '*.collection' '*.go' 'game.project')
impressao() {
  local base
  # Antes do primeiro commit não há HEAD: a base é a árvore vazia, e o diff contra ela vê o stage e
  # a worktree. A árvore vazia vem do git porque o hash muda com o formato do repositório.
  base="$(git rev-parse -q --verify HEAD 2> /dev/null)" \
    || base="$(git hash-object -t tree /dev/null 2> /dev/null)" || return 1
  printf '%s\n' "$base"
  git diff "$base" --binary -- "${caminhos[@]}" 2> /dev/null || return 1
  # O arquivo que o sha1sum não lê (symlink quebrado, sem permissão) entra pela mensagem de erro, que
  # traz o nome: a digital continua estável, e só a falha do git a zera.
  git ls-files -z --others --exclude-standard -- "${caminhos[@]}" 2> /dev/null \
    | { LC_ALL=C xargs -0 -r sha1sum 2>&1; true; } || return 1
}
# Digital que não se calcula fica vazia e nunca pula o portão: o git que falha não aprova calado.
digital="$(impressao | sha1sum | cut -d' ' -f1)" || digital=""
projeto="$(basename "$(git rev-parse --show-toplevel 2> /dev/null || echo "$raiz")")"
marca="$HOME/.cache/$projeto-portao/$(basename "$raiz").aprovado"
[[ -n "$digital" && -f "$marca" && "$(cat "$marca")" == "$digital" ]] && exit 0

if saida="$(tools/portao.sh --rapido 2>&1)"; then
  if [[ -n "$digital" ]]; then
    mkdir -p "$(dirname "$marca")"
    printf '%s\n' "$digital" > "$marca"
  fi
  exit 0
fi
{
  echo "Portão reprovou (tools/portao.sh --rapido): teste de domínio ou LuaLS."
  printf '%s\n' "$saida"
} >&2
exit 2
