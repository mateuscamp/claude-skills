#!/usr/bin/env bash
# Portão de verificação de um projeto Godot: importa, compila todos os scripts e roda todos os
# tests/*_spec.gd. Reprova por código de saída, por timeout E por erro no log: o Godot sai com 0
# mesmo com SCRIPT ERROR, e um erro dentro de _initialize trava o processo antes do quit().
#
#   tools/portao.sh           tudo (import, compilação, specs em paralelo)
#   tools/portao.sh --rapido  só import e compilação (segundos), o que o hook Stop roda
#
# Copiado da skill ai-first-godot. Ajuste só o bloco AJUSTE abaixo.
set -uo pipefail

raiz="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ---- AJUSTE ------------------------------------------------------------------------------
projeto="$(basename "$(git -C "$raiz" rev-parse --show-toplevel 2> /dev/null || echo "$raiz")")"
# Logs fora do /tmp (tmpfs com cota) e um diretório por worktree.
logs="${PB_PORTAO_LOGS:-$HOME/.cache/$projeto-portao/$(basename "$raiz")}"
specs_glob="tests/*_spec.gd"
script_compilar="res://tests/compilar_tudo.gd"
# Specs que precisam de servidor gráfico (rodam sob xvfb-run); o resto roda headless.
declare -A COM_TELA=()
# Erros que um spec provoca de propósito: padrão estreito, ou o portão passa a esconder erro.
declare -A ERROS_ESPERADOS=()
# ------------------------------------------------------------------------------------------

temp="/tmp/portao-$projeto-$$"
paralelo="${PB_PORTAO_PARALELO:-4}"
limite="${PB_PORTAO_LIMITE:-600}"  # segundos por spec
erros_no_log='SCRIPT ERROR|Parse Error|^ERROR:'
rm -rf "$logs" && mkdir -p "$logs"
trap 'rm -rf "$temp"' EXIT

_erros() {
  local esperado="${ERROS_ESPERADOS[$1]:-}"
  if [[ -n "$esperado" ]]; then
    grep -E "$erros_no_log" "$2" | grep -vE "$esperado"
  else
    grep -E "$erros_no_log" "$2"
  fi
}

# Cada execução com user:// próprio: specs não herdam saves uns dos outros nem do jogador.
rodar() {
  local nome="$1" limite_spec="$2"
  shift 2
  local log="$logs/$nome.log" codigo erros
  mkdir -p "$temp/$nome/data" "$temp/$nome/config"
  XDG_DATA_HOME="$temp/$nome/data" XDG_CONFIG_HOME="$temp/$nome/config" \
    timeout "$limite_spec" "$@" > "$log" 2>&1
  codigo=$?
  erros=$(_erros "$nome" "$log" | wc -l)
  if [[ $codigo -eq 0 && $erros -eq 0 ]]; then
    printf 'ok     %s\n' "$nome"
    return 0
  fi
  if [[ $codigo -eq 124 ]]; then
    printf 'TRAVOU %s (timeout %ss; erro antes do quit?)  %s\n' "$nome" "$limite_spec" "$log"
  else
    printf 'FALHOU %s (exit=%s, erros no log=%s)  %s\n' "$nome" "$codigo" "$erros" "$log"
  fi
  _erros "$nome" "$log" | head -3 | sed 's/^/         /'
  return 1
}

# Sem som: o áudio real toca no alto-falante de quem está na máquina.
godot_headless=(godot --headless --audio-driver Dummy --path "$raiz")

cd "$raiz" || exit 2
# Num checkout novo a primeira importação acusa recursos que ela mesma ainda vai gerar.
[[ -d .godot ]] || "${godot_headless[@]}" --editor --import --quit > /dev/null 2>&1
falhas=0
rodar import 600 "${godot_headless[@]}" --editor --import --quit || falhas=$((falhas + 1))
rodar compilar_tudo 120 "${godot_headless[@]}" --script "$script_compilar" || falhas=$((falhas + 1))

if [[ "${1:-}" != "--rapido" && $falhas -eq 0 ]]; then
  for spec in $specs_glob; do
    [[ -f "$spec" ]] || continue
    nome="$(basename "$spec" .gd)"
    while (( $(jobs -rp | wc -l) >= paralelo )); do wait -n; done
    if [[ -n "${COM_TELA[$nome]:-}" ]]; then
      rodar "$nome" "$limite" xvfb-run -a godot --audio-driver Dummy --path "$raiz" \
        --script "res://$spec" > "$logs/$nome.resultado" &
    else
      rodar "$nome" "$limite" "${godot_headless[@]}" --script "res://$spec" \
        > "$logs/$nome.resultado" &
    fi
  done
  wait
  if compgen -G "$logs/*.resultado" > /dev/null; then
    cat "$logs"/*.resultado > "$logs/specs.txt"
    cat "$logs/specs.txt"
    falhas=$((falhas + $(grep -cvE '^(ok |  )' "$logs/specs.txt")))
  fi
fi

if [[ $falhas -eq 0 ]]; then
  echo "portão: ok (logs em $logs)"
  exit 0
fi
echo "portão: $falhas falha(s) (logs em $logs)"
exit 1
