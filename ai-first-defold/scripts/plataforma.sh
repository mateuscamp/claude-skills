# Onde o bob compila e onde o bundle sai. Para ser lido com `.` pelos scripts.
# Copiado da skill ai-first-defold.
#
# Define BOB_PLATAFORMA (o --platform) e acha_app (o executável DESCOBERTO no
# bundle). Achar em vez de montar o caminho também é a prova de build: quando o
# link do bob quebra, a JVM falha no idioma do sistema e sem ERROR, e só "o
# executável está lá?" não depende de idioma.
if [ -z "$BOB_PLATAFORMA" ]; then
  case "$(uname -s)-$(uname -m)" in
    Darwin-arm64) BOB_PLATAFORMA=arm64-macos ;;
    Darwin-*) BOB_PLATAFORMA=x86_64-macos ;;
    Linux-aarch64|Linux-arm64) BOB_PLATAFORMA=arm64-linux ;;
    Linux-*) BOB_PLATAFORMA=x86_64-linux ;;
    *) echo "plataforma nao reconhecida: $(uname -s). Exporte BOB_PLATAFORMA." >&2; exit 1 ;;
  esac
fi

# O nome do executável é o title do game.project (no Linux com .x86_64 no fim).
titulo_do_projeto() {
  sed -n 's/^title *= *//p' "${1:-.}/game.project" | head -1
}

acha_app() {
  find "$1" -maxdepth 4 -type f -name "$(titulo_do_projeto "${2:-.}")*" -perm -u+x 2>/dev/null | head -1
}
