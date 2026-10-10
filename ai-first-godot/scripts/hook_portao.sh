#!/usr/bin/env bash
# Hook Stop do Claude Code: roda `tools/portao.sh --rapido` quando script, cena ou recurso mudou
# desde a última aprovação, e devolve a falha ao agente (exit 2) antes de ele dizer que terminou.
# Registro em .claude/settings.json do projeto:
#   {"hooks": {"Stop": [{"hooks": [{"type": "command",
#     "command": "\"$CLAUDE_PROJECT_DIR\"/tools/hook_portao.sh", "timeout": 300}]}]}}
# Copiado da skill ai-first-godot.
set -uo pipefail

raiz="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
entrada="$(cat)"
# Na segunda parada seguida o agente já recebeu a falha uma vez: não prende a sessão em laço.
if python3 -c 'import json,sys; sys.exit(0 if json.loads(sys.argv[1]).get("stop_hook_active") else 1)' \
    "$entrada" 2> /dev/null; then
  exit 0
fi

cd "$raiz" || exit 0
caminhos=('*.gd' '*.tscn' '*.tres' 'project.godot')
# Impressão digital: commit atual, diff não commitado e arquivos novos desses tipos.
digital="$({
  git rev-parse HEAD
  git diff HEAD -- "${caminhos[@]}"
  git ls-files --others --exclude-standard -- "${caminhos[@]}" | xargs -r sha1sum
} | sha1sum | cut -d' ' -f1)"
projeto="$(basename "$(git rev-parse --show-toplevel 2> /dev/null || echo "$raiz")")"
marca="$HOME/.cache/$projeto-portao/$(basename "$raiz").aprovado"
[[ -f "$marca" && "$(cat "$marca")" == "$digital" ]] && exit 0

if saida="$(tools/portao.sh --rapido 2>&1)"; then
  mkdir -p "$(dirname "$marca")"
  printf '%s\n' "$digital" > "$marca"
  exit 0
fi
{
  echo "Portão reprovou (tools/portao.sh --rapido): algum script não compila ou a importação deu erro."
  printf '%s\n' "$saida"
} >&2
exit 2
