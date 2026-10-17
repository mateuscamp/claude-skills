# Armadilhas do Godot 4.7 que o agente não vê

Medido no Godot 4.7.2 (Linux): no flipper-boom (2026-10-09) ou no relatório "Godot AI-first
comparado a Defold" (2026-10-09, marcado como [relatório]). O que foi conferido de novo leva
[versão]; o que vem só da documentação oficial, sem medição nossa, leva [doc]. Antes de confiar
num item em outra versão, reproduza o caso mínimo.

Esta lista cresce com o uso: armadilha de conceito do Godot em que um projeto caiu e que ele
resolveu entra aqui, com o número medido; a que vale para jogo em qualquer engine entra em
`gerais-de-jogo.md`, na raiz do repositório das skills, e o `distribuir.py --copiar-gerais` a
copia para `references/gerais-de-jogo.md` de cada skill de motor.

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

- No GDScript, um erro de execução aborta só a função em que acontece: o chamador recebe o valor padrão (0, null), segue em frente, e o script ainda imprime o 'ok' final e sai com 0 (Godot 4.7.2). Num script de verificação com etapas, cada etapa incrementa um contador na última linha e o script reprova se faltar alguma. No flipper-boom a sub-auditoria do Ímã abortava e o resultado dizia 'ok'; com o contador, o mutante deu 'abortadas: 3 de 6' (medido em 2026-10-13). Script fora do portão ainda tem o log lido.
- Vazamento na saída não é ERROR: no Godot 4.7.2 um nó solto ou um ciclo de RefCounted sai como 'WARNING: N ObjectDB instance(s) was/were leaked at exit', com exit 0 (reproduzido), ao lado do mesmo 'ERROR: N resources still in use at exit' do áudio preso. Ponha 'ObjectDB instances? (was|were) leaked' no padrão de erro do portão. Para tolerar um vazamento conhecido, rode com --verbose e tolere por classe nas linhas 'Leaked instance: <Classe>' e 'Resource still in use:', nunca pela mensagem: tolerando a mensagem, um mutante com ciclo passou com 0 erros e 135 a 437 objetos vazados fora do áudio (medido no flipper-boom, 2026-10-13).

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

- Ao contar warnings como erro (unsafe_* em 2), um script que usa outro com aviso para em 'Compile Error: Failed to compile depended scripts' sem ser analisado: no Godot 4.7.2 o --check-only dele sai com 0 e o compilar_tudo o carrega como instanciável. Não leia o código de saída nem essa linha como zero avisos. Conte só os erros cujo 'at: GDScript::reload (res://…)' é o próprio arquivo, liste os dependentes à parte e meça-os de novo numa cópia com @warning_ignore_start nas dependências já contadas, até compilarem; sobrar algum reprova (no flipper-boom eram 14 arquivos lidos como 0, medido em 2026-10-13).
- Classe tipada não pega o caminho dinâmico: no Godot 4.7.2, obj.call("_f", {…}) para um parâmetro tipado e Array[T].append({…}) compilam. O call falha rodando com SCRIPT ERROR; o append imprime 'ERROR: Attempted to push_back…', descarta o item e a função segue. Ao trocar Dictionary por classe, faça grep antes e depois por '.call(' com '{', por 'append({' e por '{}' atribuído aos campos trocados em todas as pastas, inclusive nos scripts que o portão só compila. Prefira a chamada direta a .call()/callv() (no flipper-boom um escapou na etapa 3, e o grep da etapa 4 achou 30 montagens, 2026-10-13).
- Ao trocar registros Dictionary por classe, == e has passam a comparar identidade, e não conteúdo, e duplicate(true) deixa de copiar o registro: no Godot 4.7.2 ele não copia objetos (o retrato guardado continuou == ao estado depois da mudança). Antes da troca, liste todo duplicate(), todo literal que copia campos e todo ==, != ou has entre registros. Retrato de estado para teste é dado: serialize-o (para_log) antes de guardar e comparar. Onde o duplicate() protegia de molde reaproveitado, recuse o objeto já registrado (id ≠ 0) e faça o oráculo reprovar o mesmo objeto duas vezes numa lista (no flipper-boom, 6 retratos e um mutante que passou por todos os specs, 2026-10-13).

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

- `Engine.time_scale` escala só o delta. Passo fixo por quadro não acompanha: em 2× um passo de 0,19 por quadro andou 5,7 u por segundo de jogo, abaixo dos 6,2 u/s da personagem. A escala é global ao processo, sobrevive à troca de cena, e os testes a sobem para acelerar (aqui 12). Guarde a velocidade escolhida numa fonte própria, reaplique-a no `_ready` e não derive passo nem log do `Engine.time_scale` (medido no flipper-boom, 2026-10-13). O spec muda o `time_scale` e confere que nada além do ritmo mudou.
- Depois de uma ação que pode trocar ou recarregar a cena, o spec confere `is_instance_valid(cena) and current_scene == cena` antes de usá-la. Sem isso, o código errado vira SCRIPT ERROR de instância liberada, o `_initialize` aborta e o spec TRAVA no timeout, em vez de FALHAR com a mensagem (medido no flipper-boom, 2026-10-09). No fim, solte o `current_scene`, que é a cena recarregada, e não a instância que o spec criou: senão sobram '2 resources still in use at exit'.
- Áudio preso na saída: a espera antes do quit() depende da carga da máquina. Com quatro specs em paralelo, 0,3 s não bastou em 2 de 4 rodadas (musica_parque.wav ainda em uso, visto com --verbose). Em spec que toca música, pare o player, solte a cena atual (se o spec recarregou a cena, solte a recarregada: sair com ela viva deu o erro em 5 de 5) e espere 1 s (Godot 4.7.2, medido no flipper-boom, 2026-10-12).
- Um spec com galho `DisplayServer.get_name() == "headless"` que pula o caso, ou troca o toque de verdade por chamada direta, vai para COM_TELA no portão; se rodar headless, o caso nunca roda e o spec fica verde. Faça o spec imprimir quantos casos rodou, para a diferença aparecer (36 sem tela contra 37 com tela). Para auditar, procure DisplayServer.get_name() nos specs com grep (medido no flipper-boom, 2026-10-15).

## Log em arquivo (4.7.2)

- `debug/file_logging/enable_file_logging` é `false`, mas `enable_file_logging.pc` é `true`: no
  desktop todo processo grava `user://logs/godot.log`, inclusive `--headless --script`. Medido
  em 2026-10-11.
- Rotação: o mais novo é sempre `godot.log`; os anteriores viram `godot<AAAA-MM-DD>T<hh.mm.ss>.log`,
  até `max_log_files` (5). Cinco execuções de teste no mesmo `user://` apagam o playtest de ontem.
- `--log-file <arquivo>` grava ali **em vez de** `user://logs`: nada é criado na pasta do
  projeto do usuário. Caminho absoluto ou relativo à pasta do projeto.
- `push_error` chega ao arquivo com `at:` e o `GDScript backtrace`.

- INF e NaN não existem em JSON: no Godot 4.7.2, JSON.stringify escreve INF como 1e99999 sem aviso (a volta pelo parse dá 'Exponent too high'; o Python lê inf e regrava Infinity, que é JSON inválido) e NaN como null, com aviso só na primeira vez. Registro com sentinela INF ou NaN omite a chave no retrato de log. Um spec reprova número não finito no log e confere que cada retrato volta do JSON.parse_string (medido no flipper-boom, 2026-10-13).

## Texto que quebra (4.7.2)

Medido em 2026-10-16 num projeto mínimo, `Label` com a fonte padrão do tema e largura 120:

- Sem `autowrap_mode` o texto não quebra: o `Label` ignora o `size` e cresce na largura (586 px,
  uma linha), passando da borda.
- Com `AUTOWRAP_WORD_SMART`: 7 linhas e 179 px de altura. O vizinho posto à mão logo abaixo da
  altura de uma linha (`y = 123`) fica por baixo; num `VBoxContainer` ele desce sozinho (`y = 183`).
- A altura que vale é a do `Label` depois de um quadro (`size.y`). `Font.get_multiline_string_size`
  dá 161: não conta o `line_spacing` do tema (3 px entre linhas).
- Depois de trocar texto, `font_size`, fonte, autowrap ou largura de um Label, chame `update_minimum_size()` antes de `get_combined_minimum_size()`. Sem isso o Label devolve a medida anterior até o próximo desenho: deu caixa de 108 para texto de 149 e de 75 para 111, e depois da correção 117 para 105 e 123 para 111 (4.7.2, medido no flipper-boom, 2026-10-12). O Button nunca fica menor que o texto mais as margens do stylebox: ele cresce e sai do lugar sem erro. Para caber num retângulo fixo, escolha a maior letra que cabe na largura útil (`size` menos as margens do stylebox, por `Font.get_string_size`) ou ligue o autowrap, e atribua o `size` por último. O spec troca textos em sequência e refaz a medida, senão lê o mesmo número velho que o código.

## Screenshot e display

- Com `--headless`, `get_image()` devolve null, `--write-movie` trava e a janela tem 64×64.
  Use `xvfb-run -a` (ou Weston/cage com `--rendering-driver opengl3`). [relatório]
- Capturas sob xvfb saem idênticas byte a byte; `Image.compute_image_metrics` serve de diff.
  [relatório]
- Para achar um ponto 3D na captura da raiz, converta: `root.get_final_transform() * camera.unproject_position(p)`. unproject_position dá a coordenada no canvas, e a imagem de root.get_texture() vem em pixels da janela; com stretch canvas_items e escala (1,5 no flipper-boom), os dois divergem e o recorte mira o lugar errado (4.7.2, medido no flipper-boom, 2026-10-12).
- Com --headless, a raiz tem 100×100 dentro de _initialize e 64×64 a partir da primeira chamada adiada; window_get_size() e screen_get_size() dão 0×0. O root.size pedido em _initialize é desfeito antes do primeiro quadro: o spec de geometria fixa root.size no começo de uma função adiada (call_deferred). Um valor que vem do viewport e foi gravado headless não é o do jogo: no flipper-boom, a base do oráculo guardou a câmera 23,95 em vez de 13,47 (4.7.2, medido no flipper-boom, 2026-10-15).
- Jogo em paisagem com stretch canvas_items usa window/stretch/aspect="keep_height" (no retrato, "keep_width"), não "expand". Com expand, uma janela mais alta que a base estica o canvas (1268×1356 → 1280×1368,67; 2048×1536 → 1280×960) e o HUD posto a partir do topo sai do lugar. No headless (64×64) o canvas fica quadrado (1280×1280), e toda conta feita pela proporção erra sem aviso. O spec troca a janela para uma em pé e uma 4:3 e reprova canvas mais alto que a base (4.7.2, medido no flipper-boom, 2026-10-15).
- Não use DisplayServer.get_display_safe_area() como margem fora do celular: no Linux ela devolve a tela do monitor, não a janela (xvfb 640×480 com uma janela de 2400×1080), e no --headless vem vazia, sem recortes. Leia a área segura num lugar só e converta-a ali para o canvas com (área − window_get_position()) e root.get_final_transform().affine_inverse(). Dê aos specs uma área e recortes simulados. Releia de tempos em tempos, não só no size_changed: pelo código do 4.7.2, no Android o giro de 180° em paisagem troca o furo de lado sem sinal nenhum (ainda não medido no aparelho) (medido no flipper-boom, 2026-10-12).

## Shaders e cor (Compatibility, 4.7.2)

- Em shader canvas_item, o COLOR de entrada já traz o modulate (e o self_modulate) do nó: nunca o sobrescreva sem lê-lo, multiplique (`COLOR = vec4(cor.rgb, cor.a * forca * COLOR.a)`). Com o modulate 1 / 0,5 / 0, o vermelho saiu 0,788 / 0,788 / 0 sobrescrevendo e 0,788 / 0,392 / 0 multiplicando. O spec usa um valor intermediário (0,5): com 0 o item nem é desenhado e o defeito passa (4.7.2 Compatibility, medido no flipper-boom, 2026-10-15).
- No Compatibility, ALBEDO, uniform source_color e COLOR de vértice vão à tela como estão, sem conversão linear→sRGB (ALBEDO 0,5 sai 0x80; source_color 0,31 sai 0,31). Converta só o que vem linear (COLOR_0 de glTF), dentro de `if (OUTPUT_IS_SRGB)`, e nunca reconverta a source_color: a tinta 0,31 virou 0,59. Uma constante escrita "em linear" sai escura (0,004 deu 000000, não 0d0809). A mistura alfa também é feita em sRGB: preveja a cor translúcida com alfa·cor + (1−alfa)·fundo nos valores sRGB (4.7.2, medido no flipper-boom, 2026-10-15).
- No Compatibility, a cor que carrega significado (perigo, item, sinal) só sai no hex em 2D, em material sem luz ou num shader com luz que só emite (ALBEDO e SPECULAR zerados, cor em EMISSION). Nunca ponha a mesma cor em ALBEDO e em EMISSION: as duas somam, passam de 1,0, são cortadas e o matiz muda (ffb347 → ffff74, fc6581 → ff9fc6). O especular padrão (0,5) também soma, mesmo com roughness 0,95. Só emitindo, as 15 cores de sinal saíram a ΔE00 0–0,1 (4.7.2, medido no flipper-boom, 2026-10-10).

## Entrada (4.7.2)

- Com `emulate_mouse_from_touch=false` (o ajuste que esta skill manda ligar), o Button responde ao toque, mas o HSlider não: toque e arrasto injetados deixaram o slider em 0,5, e o clique na mesma posição o levou a 0,24 (4.7.2, medido no flipper-boom, 2026-10-02 e reproduzido em 2026-10-16). Todo Control nativo que só lê mouse ganha um `gui_input` que converte InputEventScreenTouch/ScreenDrag em valor e chama `accept_event()`. O spec exercita cada tipo de Control interativo por toque injetado (`push_input`), não por clique.
- A roda do mouse chega como InputEventMouseButton com `pressed=true` (WHEEL_UP é o índice 4), como os botões direito e do meio. Todo clique que aciona algo confere `event.button_index == MOUSE_BUTTON_LEFT`, não só `pressed`: aqui o erro apareceu duas vezes, primeiro pulando a queda e depois disparando a ultimate (4.7.2, medido no flipper-boom, 2026-10-09 e 2026-10-12). O spec de cada zona clicável empurra WHEEL_UP/DOWN, RIGHT e MIDDLE por `root.push_input` e confere que nada muda.

## Cena e árvore (4.7.2)

- `reload_current_scene` e `change_scene_*` só valem no fim do quadro. Toques ou Voltar seguidos antes disso ainda chegam à cena velha, e a segunda recarga roda num nó fora da árvore (aqui pagou duas vezes e chamou `reload_current_scene` sobre um valor nulo; medido no flipper-boom, 2026-10-09). Toda ação que recarrega ou troca a cena leva uma guarda que a deixa valer uma vez. O spec dispara as ações no mesmo quadro e confere o efeito único.

## Exportação e Android (4.7.2)

- `input_devices/sensors/enable_accelerometer` vem `false`, assim como `enable_gravity` e `enable_gyroscope`. No Android, `Input.get_accelerometer()` não entrega leitura e só avisa no log (4.7.2, medido no flipper-boom no Galaxy S20 FE, 2026-10-03; padrão conferido por --doctool). Jogo que lê sensor liga a chave de cada sensor no project.godot. Desktop e headless nunca leem o sensor, então nenhum teste vê a falha: um spec confere a chave, e o efeito se confere no aparelho, pelo log.
- `application/config/quit_on_go_back` vem `true`, e o Voltar do Android fecha o app de uma vez. Para ele fechar a tela de cima, ponha `false` e trate NOTIFICATION_WM_GO_BACK_REQUEST com `call_deferred`: a notificação chega no meio da propagação pela árvore, onde recarregar a cena ou tirar nós é recusado. Na chamada adiada, confira `is_inside_tree()`, porque dois Voltar no mesmo quadro viram duas chamadas (4.7.2, medido no flipper-boom, 2026-10-09). Prove com `root.propagate_notification(NOTIFICATION_WM_GO_BACK_REQUEST)` a partir da raiz, e não chamando a função, com dois Voltar no mesmo quadro e sem erro no log.
- `OS.is_debug_build()` é verdadeiro no editor, em todo teste e no APK de depuração, e os modelos de exportação, de release e de depuração, ignoram `--script` (`disable_path_overrides=True` por padrão no SConstruct do 4.7.2). Ferramenta de depuração gateada por ele só se prova numa exportação de verdade: exporte uma cópia com uma sonda como cena principal e compare `--export-release` com `--export-debug` (aqui 14 → 14 itens contra 14 → 22; medido no flipper-boom, 2026-10-09). No teste, a release se simula só desligando, nunca ligando.

## Gerais de jogo: moram em `references/gerais-de-jogo.md`

Ali estão as lições de jogo que valem em qualquer engine: testes que passam com qualquer código,
prova e oráculo, ferramentas de verificação, entrada e troca de estado, captura e cor, log da
partida e instruções do agente. É cópia da fonte única `gerais-de-jogo.md`, na raiz do repositório
das skills. Não acrescente lição aqui: a fonte se edita num ramo em worktree, e o
`distribuir.py --check-gerais` reprova item de lista ou subtítulo nesta seção.
