#!/usr/bin/env bash
# Hook Stop do usuário: roda o juiz, de fora do projeto, em todo repositório que o adotou. Fecha o
# que o portão não fecha sozinho: quem foi tirado do `portao.sh` não pode reclamar da própria saída.
# Mora na skill e não se copia. Registro, uma vez por máquina, em ~/.claude/settings.json:
#   {"hooks": {"Stop": [{"hooks": [{"type": "command",
#     "command": "$HOME/.claude/skills/python-on-rails/scripts/hook_juiz.sh", "timeout": 30}]}]}}
set -uo pipefail

juiz="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/conferir_trilho.py"
entrada="$(cat)"
# Na segunda parada seguida o agente já recebeu a falha uma vez: não prende a sessão em laço.
pasta="$(python3 -c '
import json, sys
dados = json.loads(sys.argv[1])
sys.exit(1) if dados.get("stop_hook_active") else print(dados["cwd"])
' "$entrada" 2> /dev/null)" || exit 0

cd "$pasta" 2> /dev/null || exit 0
raiz="$(git rev-parse --show-toplevel 2> /dev/null)" || exit 0
cd "$raiz" || exit 0

# A marca de adoção vem do histórico: apagar a chamada ou o portão não apaga a marca.
fontes=(scripts/portao.sh Makefile)
if ! grep -qs conferir_trilho "${fontes[@]}" \
  && [[ -z "$(git log -1 -Sconferir_trilho --format=%h -- "${fontes[@]}" 2> /dev/null)" ]]; then
  exit 0
fi

saida="$(python3 -I "$juiz" 2>&1)" && exit 0
{
  echo "O juiz do portão reprovou (conferir_trilho.py). Resolva antes de dizer que terminou:"
  printf '%s\n' "$saida" | tail -60
} >&2
exit 2
