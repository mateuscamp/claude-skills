extends SceneTree

# Compila todos os scripts do projeto no contexto dele (autoloads e class_name visíveis).
# Os specs só carregam o que usam: um script que ninguém testa podia quebrar sem aviso.
# `--check-only` dá falso erro com autoload; carregar com load() não.
# Copiado da skill ai-first-godot: ajuste PASTAS para as pastas de código do projeto.

const PASTAS: Array[String] = ["res://game", "res://main", "res://tests", "res://tools"]


func _initialize() -> void:
	var quebrados: Array[String] = []
	var total: int = 0
	for pasta: String in PASTAS:
		total += _compilar(pasta, quebrados)
	if total == 0:
		push_error("nenhum script encontrado")
		quit(1)
		return
	for caminho: String in quebrados:
		push_error("não compila: " + caminho)
	print(JSON.stringify({
		"evento": "teste", "suite": "compilar_tudo", "arquivos": total,
		"quebrados": quebrados.size(), "resultado": "ok" if quebrados.is_empty() else "falha",
	}))
	quit(0 if quebrados.is_empty() else 1)


func _compilar(pasta: String, quebrados: Array[String]) -> int:
	var diretorio: DirAccess = DirAccess.open(pasta)
	if diretorio == null:
		return 0
	var total: int = 0
	for sub: String in diretorio.get_directories():
		total += _compilar(pasta.path_join(sub), quebrados)
	for nome: String in diretorio.get_files():
		if not nome.ends_with(".gd"):
			continue
		total += 1
		var caminho: String = pasta.path_join(nome)
		var script: GDScript = load(caminho) as GDScript
		if script == null or not script.can_instantiate():
			quebrados.append(caminho)
	return total
