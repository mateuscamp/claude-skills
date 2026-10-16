# Armadilhas do Godot 4.7 que o agente não vê

Medido no Godot 4.7.2 (Linux): no flipper-boom (2026-10-09) ou no relatório "Godot AI-first
comparado a Defold" (2026-10-09, marcado como [relatório]). O que foi conferido de novo leva
[versão]; o que vem só da documentação oficial, sem medição nossa, leva [doc]. Antes de confiar
num item em outra versão, reproduza o caso mínimo.

## Códigos de saída mentem

| Situação | O que acontece | Medido |
|---|---|---|
| Cena com erros de script (`--quit-after N`) | sai com **0** | 147 `SCRIPT ERROR` e exit 0 |
| `--import`, `--editor --quit` com recurso quebrado | sai com **0** | [relatório] |
| Erro de execução dentro de `_initialize` de um `extends SceneTree` | a função aborta, o `quit()` nunca roda, o processo **fica parado** | travou até `timeout` (exit 124) |
| Erro de parse no script passado a `--script` | sai com 1 | é o único caso honesto |
| `-d` com erro de script | cai no prompt `debug>` e trava | [relatório] |
| GUT com arquivo de teste que não compila | ignora o arquivo e sai com 0 | [relatório] |

Regra: **todo comando Godot leva `timeout` e tem o log lido** procurando
`SCRIPT ERROR|Parse Error|^ERROR:`. O `scripts/portao.sh` já faz isso.

## Compilação

- `--check-only --script x.gd` dá **falso erro** com autoload e não enxerga `class_name` sem
  `--import` antes. [relatório]
- Um spec só compila o que carrega. Script que nenhum teste usa quebra calado. Por isso
  `scripts/compilar_tudo.gd` carrega todos os `.gd` com `load()`.
- Não use `ResourceLoader.CACHE_MODE_IGNORE` para recarregar todos os scripts: ao recarregar o
  próprio script em execução, o Godot **cai com sinal 11**.
- O LSP headless (`--headless --editor --lsp-port`) mostra warnings que a CLI não imprime.
  [relatório]

## Warnings estritos

- `debug/gdscript/warnings/<nome>=2` no `project.godot` transforma o warning em erro de parse.
  Os úteis: `untyped_declaration`, `unsafe_property_access`, `unsafe_method_access`,
  `unsafe_cast`, `unsafe_call_argument`.
- `debug/gdscript/warnings/directory_rules` (Dictionary, padrão `{"res://addons": 0}`) liga e
  desliga os warnings **por pasta**. `0` exclui a pasta. **Caminho de arquivo não funciona.**
- Ler valor de `Dictionary` ou `Array` sem tipo, com os `unsafe_*` ligados:

  | Forma | Passa? | Pega chave errada? |
  |---|---|---|
  | `int(d["x"])` | não | não |
  | `d["x"] as int` | não (cast inseguro) | não |
  | `var v: int = d["x"]` | sim | **não**: só move a checagem para a execução |
  | `Dictionary[String, int]` | sim | não: só serve a valores de um tipo |
  | classe `RefCounted` com campos tipados | sim | **sim, na compilação** |

  Ou seja: registros de jogo em `Array[Dictionary]` não se consertam com locais tipadas.
  O conserto é estrutural (classes), e a refatoração deve provar que não mudou o jogo
  comparando os logs de evento por semente, byte a byte, antes e depois.

## Cena e recursos escritos à mão [relatório]

- Propriedade desconhecida ou do Godot 3 (`rect_min_size`, `align`) é descartada sem aviso.
- Valor de tipo errado é convertido em silêncio (`cost = "three"` vira 0).
- `[connection]` para método inexistente nunca dispara e nunca dá erro.
- UID copiado de outro arquivo sobrepõe o `path` sem aviso: em `.tscn` escrito à mão, use
  `path` e omita `uid`.
- Depois de criar ou mover arquivo, rode `--import`; sem ele, a cena instancia **sem o script**
  e o processo sai com 0.
- `PackedScene.pack()` descarta os nós sem `owner`.
- Num checkout novo, a **primeira** importação acusa os recursos que ela mesma gera (traduções
  de CSV, por exemplo). Importe uma vez sem ler o log; a segunda importação é a que vale.

## Execução

- **Áudio preso na saída:** liberar a cena e chamar `quit()` no mesmo quadro deixa o stream no
  AudioServer, e a saída acusa `ERROR: 1 resources still in use at exit`. É intermitente: depende
  do tempo. Remédio: `cena.queue_free()` e depois `await create_timer(0.3).timeout` antes do
  `quit()`. Um `await process_frame` só não basta.
- Spec que depende do estado de `user://` reprova na segunda execução na mesma pasta. Cada spec
  apaga os arquivos que usa no início, atrás de uma trava que recusa `user://` fora de `/tmp`
  ou `~/.cache`. Conferir só que `XDG_DATA_HOME` existe não basta: uma sessão pode exportá-lo
  como `~/.local/share`.
- `--audio-driver Dummy` em todo Godot automatizado; Blender com `-noaudio`.
- `--fixed-fps 60` torna repetível uma execução roteirizada com tween; sem a flag, os valores
  mudam entre execuções. [relatório]
- Silenciosos de runtime [relatório]: dois tweens na mesma propriedade, tween em nó liberado,
  lambda conectada duas vezes, `Control` de tela cheia com `mouse_filter` STOP/PASS engolindo
  cliques, toque que chega duas vezes (como toque e como mouse emulado:
  `input_devices/pointing/emulate_mouse_from_touch=false`).

## Log em arquivo (4.7.2)

- `debug/file_logging/enable_file_logging` é `false`, mas `enable_file_logging.pc` é `true`: no
  desktop todo processo grava `user://logs/godot.log`, inclusive `--headless --script`. Medido
  em 2026-10-11.
- Rotação: o mais novo é sempre `godot.log`; os anteriores viram `godot<AAAA-MM-DD>T<hh.mm.ss>.log`,
  até `max_log_files` (5). Cinco execuções de teste no mesmo `user://` apagam o playtest de ontem.
- `--log-file <arquivo>` grava ali **em vez de** `user://logs`: nada é criado na pasta do
  projeto do usuário. Caminho absoluto ou relativo à pasta do projeto.
- `push_error` chega ao arquivo com `at:` e o `GDScript backtrace`.

## Texto que quebra (4.7.2)

Medido em 2026-10-16 num projeto mínimo, `Label` com a fonte padrão do tema e largura 120:

- Sem `autowrap_mode` o texto não quebra: o `Label` ignora o `size` e cresce na largura (586 px,
  uma linha), passando da borda.
- Com `AUTOWRAP_WORD_SMART`: 7 linhas e 179 px de altura. O vizinho posto à mão logo abaixo da
  altura de uma linha (`y = 123`) fica por baixo; num `VBoxContainer` ele desce sozinho (`y = 183`).
- A altura que vale é a do `Label` depois de um quadro (`size.y`). `Font.get_multiline_string_size`
  dá 161: não conta o `line_spacing` do tema (3 px entre linhas).

## Screenshot e display

- Com `--headless`, `get_image()` devolve null, `--write-movie` trava e a janela tem 64×64.
  Use `xvfb-run -a` (ou Weston/cage com `--rendering-driver opengl3`). [relatório]
- Capturas sob xvfb saem idênticas byte a byte; `Image.compute_image_metrics` serve de diff.
  [relatório]
