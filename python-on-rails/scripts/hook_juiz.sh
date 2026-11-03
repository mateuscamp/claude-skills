#!/usr/bin/env bash
# Hook Stop do usuário: roda o juiz, de fora do projeto, em todo repositório que o adotou. Fecha o
# que o portão não fecha sozinho: quem foi tirado do `portao.sh` não pode reclamar da própria saída.
# Mora na skill e não se copia. Registro, uma vez por máquina, em ~/.claude/settings.json:
#   {"hooks": {"Stop": [{"hooks": [{"type": "command",
#     "command": "$HOME/.claude/skills/python-on-rails/scripts/hook_juiz.sh", "timeout": 30}]}]}}
set -uo pipefail

juiz="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/conferir_trilho.py"
entrada="$(cat)"
# `-I`: a pasta do processo é o projeto, e um `json.py` ali calaria o hook. Na segunda parada
# seguida o agente já recebeu a falha uma vez: sai com 3 para não prender a sessão em laço.
leitura="$(python3 -I -c '
import json, sys
try:
    dados = json.loads(sys.argv[1])
except ValueError:
    dados = {}
if dados.get("stop_hook_active"):
    sys.exit(3)
print(dados.get("cwd", ""))
print(dados.get("session_id") or "sem-sessao")
' "$entrada" 2> /dev/null)"
[[ $? -eq 3 ]] && exit 0
pasta="${leitura%%$'\n'*}"
sessao="${leitura##*$'\n'}"

cd "${pasta:-$PWD}" 2> /dev/null || exit 0
raiz="$(git rev-parse --show-toplevel 2> /dev/null)" || exit 0
cd "$raiz" || exit 0

# A marca de adoção vem do histórico: apagar a chamada ou o portão não apaga a marca.
fontes=(scripts/portao.sh Makefile)
if ! grep -qs conferir_trilho "${fontes[@]}" \
  && [[ -z "$(git log -1 -Sconferir_trilho --format=%h -- "${fontes[@]}" 2> /dev/null)" ]]; then
  exit 0
fi

marcas="$HOME/.cache/python-on-rails-juiz"
marca="$marcas/${sessao//\//_}-$(printf '%s' "$raiz" | sha1sum | cut -c1-16)"
if saida="$(python3 -I "$juiz" 2>&1)"; then
  rm -f "$marca"
  exit 0
fi
# Cada sessão ouve a mesma pendência uma vez: quem espera decisão humana não ganha um turno extra
# a cada parada. Sessão nova ouve de novo, porque não tem memória da anterior.
digital="$(printf '%s' "$saida" | sha1sum | cut -d' ' -f1)"
[[ -f "$marca" && "$(cat "$marca")" == "$digital" ]] && exit 0
mkdir -p "$marcas"
find "$marcas" -type f -mtime +7 -delete 2> /dev/null
printf '%s\n' "$digital" > "$marca"
{
  echo "O juiz do portão reprovou (conferir_trilho.py). Resolva antes de dizer que terminou:"
  printf '%s\n' "$saida" | tail -60
} >&2
exit 2
