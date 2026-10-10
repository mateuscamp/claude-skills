extends SceneTree

# Fitness function da fronteira do domínio: as regras do jogo não importam conceito da engine.
# Domínio que lê Input, Time ou cria Node não roda headless, não repete por semente e não testa
# sem cena. Copiado da skill ai-first-godot: ajuste PASTAS e PROIBIDOS ao projeto.
#   godot --headless --audio-driver Dummy --path . --script res://tests/fronteira_spec.gd

const PASTAS: Array[String] = ["res://game/domain", "res://game/content"]
const PROIBIDOS: Array[String] = [
	"Node", "Node2D", "Node3D", "Control", "Input", "InputEvent", "Timer", "Tween", "SceneTree",
	"CanvasItem", "RigidBody2D", "Area2D", "Time", "OS", "randi", "randf", "randomize",
]


func _initialize() -> void:
	var total: int = 0
	for pasta: String in PASTAS:
		var diretorio: DirAccess = DirAccess.open(pasta)
		if diretorio == null:
			_falhar("pasta ausente: " + pasta)
			return
		for nome: String in diretorio.get_files():
			if not nome.ends_with(".gd"):
				continue
			total += 1
			var caminho: String = pasta.path_join(nome)
			var texto: String = _sem_comentarios(FileAccess.get_file_as_string(caminho))
			for proibido: String in PROIBIDOS:
				if RegEx.create_from_string("\\b%s\\b" % proibido).search(texto) != null:
					_falhar("%s importa conceito da engine: %s" % [caminho, proibido])
					return
	if total == 0:
		_falhar("fronteira vazia: nenhum script em " + ", ".join(PASTAS))
		return
	print(JSON.stringify({"evento": "teste", "suite": "fronteira", "arquivos": total, "resultado": "ok"}))
	quit()


# Comentário pode citar a engine ("não use Input aqui"); código não.
func _sem_comentarios(texto: String) -> String:
	return RegEx.create_from_string("(?m)#.*$").sub(texto, "", true)


func _falhar(mensagem: String) -> void:
	push_error(mensagem)
	quit(1)
