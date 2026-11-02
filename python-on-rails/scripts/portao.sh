#!/usr/bin/env bash
# Portão único do projeto Python: o mesmo comando para o agente, o hook Stop e o CI.
# Aprova só se tudo passar; a primeira etapa que reprova encerra com a saída dela.
#   scripts/portao.sh            completo (make check e CI)
#   scripts/portao.sh --rapido   sem a auditoria de dependências, que precisa de rede (hook Stop)
# Copiado da skill python-on-rails.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
rapido=false
[[ "${1:-}" == "--rapido" ]] && rapido=true

etapa() { printf '\n== %s\n' "$1"; }

etapa "lock em dia com o pyproject"
uv lock --check

etapa "formatação"
uv run --locked ruff format --check .

etapa "lint"
uv run --locked ruff check .

etapa "supressão sem motivo"
# Toda supressão diz por quê na mesma linha: `# noqa: S603  # motivo: ...`. Contam, em qualquer
# caixa (o ruff aceita `# NOQA`), as diretivas `noqa`, `type: ignore`, `ruff: disable`,
# `isort: skip`, `skip_file` e `off`, e todo `pyright:` que não seja `# pyright: strict` sozinho na
# linha (`basic`, `ignore[...]`, `reportX=false`, em lista, com tab); e, na caixa exata, o código
# que cala o verificador: `cast(` e `no_type_check`. Vale para `.py` e `.pyi`, e para arquivo novo
# ainda sem `git add`: é com ele que o hook Stop dispara. A lista vai com -z, porque espaço no nome
# partia o arquivo em dois. A etapa decide pelas linhas achadas, não pelo código de saída: com
# pipefail, um lote do xargs sem achado, ou um arquivo rastreado já apagado (daí o -s), fazia a
# etapa aprovar calada.
git rev-parse --is-inside-work-tree > /dev/null  # fora do git a lista viria vazia: reprova
diretiva='noqa|type:[[:space:]]*ignore|ruff:[[:space:]]*disable|pyright:'
diretiva+='|isort:[[:space:]]*(skip|off)'
codigo='\bcast\(|@[^#]*no_type_check|\bno_type_check\('
so_strict=':[0-9]+:[[:space:]]*#[[:space:]]*pyright:[[:space:]]*strict[[:space:]]*$'
fontes() { git ls-files -z --cached --others --exclude-standard '*.py' '*.pyi'; }
sem_motivo="$({
  fontes | xargs -0 -r grep -sHniE "$diretiva"
  fontes | xargs -0 -r grep -sHnE "$codigo"
} | grep -iv 'motivo:' | grep -ivE "$so_strict" | sort -t: -k1,1 -k2,2n -u || true)"
if [[ -n "$sem_motivo" ]]; then
  printf '%s\n' "$sem_motivo"
  echo "Supressão sem '# motivo:' na mesma linha. Corrija o código ou escreva o motivo."
  exit 1
fi
# A linha de base (`basedpyright --writebaseline`) cala de uma vez todo erro listado nela.
if [[ -e .basedpyright/baseline.json ]]; then
  echo ".basedpyright/baseline.json existe: o basedpyright cala os erros dela. Corrija e apague."
  exit 1
fi

etapa "tipos"
uv run --locked basedpyright

if grep -q '^\[tool.importlinter\]' pyproject.toml; then
  etapa "fronteiras"
  uv run --locked lint-imports
fi

etapa "testes"
# Os funcionais (`e2e`) ficam no `make e2e`: navegador deixaria o hook Stop lento demais.
uv run --locked pytest -m "not e2e"

if ! $rapido; then
  etapa "dependências com vulnerabilidade conhecida"
  uv audit --locked --preview-features audit
fi

printf '\nPortão aprovado.\n'
