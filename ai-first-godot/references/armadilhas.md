# Armadilhas do Godot 4.7 que o agente não vê

Medido no Godot 4.7.2 (Linux): no flipper-boom (2026-10-09) ou no relatório "Godot AI-first
comparado a Defold" (2026-10-09, marcado como [relatório]). O que foi conferido de novo leva
[versão]; o que vem só da documentação oficial, sem medição nossa, leva [doc]. Antes de confiar
num item em outra versão, reproduza o caso mínimo.

Esta lista cresce com o uso: armadilha de conceito do Godot em que um projeto caiu e que ele
resolveu entra aqui, com o número medido; a que vale para jogo em qualquer engine entra na seção
"Gerais de jogo", igual nas duas skills (ai-first-godot e ai-first-defold).

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

## Gerais de jogo (valem em qualquer engine)

A mesma seção está na ai-first-godot e na ai-first-defold; mude as duas juntas. Os números vêm do
flipper-boom (Godot 4.7.2), mas a lição não depende da engine.

### Testes que passam com qualquer código

- Não ponha a entrada do teste no ponto fixo da regra (distância zero, simetria, valor que a regra antiga e a nova tratam igual): ali qualquer implementação passa. Use valores perto do limite, dos dois lados. Quando a regra promete um caminho (aproximar sem cruzar, nunca recuar), confira a cada passo, não só no fim. Prove com um mutante da implementação errada mais provável: no flipper-boom, a 0,05 da linha e conferindo a cada 0,05 s, a puxada de força cheia cruzou de 0,002 para -0,001 (2026-10-15).
- Depois de trocar orientação, base ou layout, procure coordenadas e larguras fixas em specs e ferramentas: toque sintético fora da tela é aceito sem erro, e o spec segue verde. Aqui (360, 1100) ficava fora do canvas de 1280×720 e passava com a regra velha e com a nova (medido no flipper-boom, 2026-10-12). Marque os toques por fração do retângulo visível, meça no arranjo real e escolha um ponto em que só a regra nova passa.
- Spec não conta por contador compartilhado, como id global, número de nós ou tamanho de lista: ele anda por outros motivos, e o teste passa sem o comportamento. Aqui `_proximo_id` andava com inimigos, gemas, ataques e o chefe (medido no flipper-boom, 2026-10-12). Conte o evento ou o campo que só a ação testada altera e veja o spec falhar com a ação desligada.
- Para cada mudança, liste os caminhos de código que produzem o mesmo efeito (cada mesa, cada tipo de desenho, cada gatilho: evento de tamanho, timer, giro) e confira que algum spec passa por cada um. Spec que mede uma variante fica verde enquanto as outras quebram: aqui 3 das 4 mesas desenhavam o inimigo por um caminho sem spec (medido no flipper-boom, 2026-10-12). Faça grep pelo construtor ou pelo galho e procure-o nos specs.
- Argumento de semente que não é inteiro positivo (`abc`, `0`, `1.5`, `O1`) nunca cai calado no sorteio: a partida 'repetida' não se repetiria. O jogo registra `semente_invalida` no log com aviso e sorteia; a ferramenta de teste recusa o argumento e sai com erro (medido no flipper-boom, 2026-10-09). Uma mutação que aceita a semente inválida faz o spec falhar.
- Configuração que cai calada num padrão é o caso perigoso, não o erro alto: o erro para o jogo e alguém lê; o padrão joga outra partida no lugar da pedida, e todo teste segue verde. Vale para toda chave lida na fronteira (argumento de linha de comando, chave do projeto, arquivo de configuração), não só para a semente do item de cima. A fronteira ganha dois testes. No motor, uma passada de recusa: o portão dá o valor errado, exige o erro com o recebido, perdoa só ele e recusa o fato de início de partida (no Defold, `smoke.py --erro-esperado` e `--recusar`; no Godot, a linha de erro esperada no log que o portão lê); uma amostra de chaves basta. Na suíte, o módulo que lê a configuração, com uma API de configuração de mentira (um `sys` no Defold; no Godot, um leitor no lugar de `OS.get_cmdline_user_args()` e `ProjectSettings`): toda chave com um valor bom aceito e os ruins recusados com o recebido. A de mentira imita o comportamento medido do motor, e só o medido: no CampCrawler (Defold 1.14.0, 2026-10-17), `seed=abc` e `seed=1.5` viravam a semente 1 com o robô e uma sorteada pelo relógio sem ele, porque a leitura de inteiro do motor devolve 0 para o que não é inteiro. O defeito só apareceu rodando o motor de verdade; uma de mentira escrita pelo que o código supõe teria passado com ele. Recusar e sortear com aviso (o item de cima, do flipper-boom) valem os dois, desde que nunca calado: o valor recebido aparece no log e na tela. Para chave que o robô ou o portão passam, prefira a recusa: o aviso se perde no meio do log, e o erro para a passada. E toda leitura de configuração mora nesse módulo: um teste estático varre a pasta da cena e reprova a leitura em qualquer outro arquivo, com o arquivo e a linha. Sem ele, no CampCrawler, a leitura antiga devolvida ao script da cena passou na suíte e no portão (2026-10-17).
- Fato de log que prova o que a tela mostra sai lido do nó (o texto dele, a posição dele) e leva ao lado o valor que o domínio escolheu; o portão exige os dois iguais, com referência da regex (`canto=(-?1,-?1) ... esperado=\1`, no `re` do Python). Uma classe de valores plausíveis não prova o lugar certo: no CampCrawler, `canto=-?1,-?1` aceitou a contagem do alcance desenhada sempre no canto errado, e só com o `esperado` a passada reprovou (medido, 2026-10-16). Plante o defeito que a regex aceitaria e veja a passada cair.
- Teste de forma (os campos de um registro, de um evento, de um resultado) confere cada instância, não a união das chaves de várias: na união, um campo que falta numa instância só e um caminho de retorno que nenhum teste monta passam calados. Monte uma instância por caminho de retorno e exija em cada uma os campos obrigatórios; só 'declarado e nunca montado' se confere na união. No CampCrawler, três mutações passaram pela união e reprovaram por instância (2026-10-16).
- Validação repetida em duas camadas esconde a de cima: a camada de baixo recusa o mesmo valor com a mesma mensagem, e tirar a checagem de cima deixa a suíte verde. Teste a camada de cima pela diferença que só ela produz e prove tirando cada checagem, uma por vez: no CampCrawler, sem a checagem da bancada, o pedido ruim feito durante a apresentação saía como 'ocupado' em vez de estourar, e só um caso feito nesse estado o pegou (2026-10-17).

### Prova, oráculo e medição

- Um oráculo por semente idêntico só prova os caminhos que as partidas exercitam e o que o retrato serializa. Antes de confiar nele numa refatoração, instrumente uma cópia com um marcador antes de cada linha mudada e conte as que nenhuma execução alcança (no flipper-boom, 51 de 311). Cubra essas linhas com sondas de carga forçada e plante mutantes nas linhas raras: um deles mudou só 3 de 72 arquivos. Escreva o que fica fora. O contrato de serialização ganha spec próprio, porque o retrato que normaliza ausente para padrão não o vê. Nunca regrave a base para passar (2026-10-13).
- A prova de uma etapa roda no commit que a fecha, com a árvore limpa ou numa cópia de 'git archive', nunca na árvore de trabalho antes do commit. Toda ferramenta de prova grava na saída o commit e o número de arquivos rastreados modificados, e a comparação avisa quando esse número não é zero (no flipper-boom, as etapas 2 e 3 rodaram com 19 e 10 arquivos modificados e foram refeitas, 2026-10-13).
- Não compare desempenho com uma linha de base gravada em outra sessão: a mesma versão variou cerca de 10% com a carga da máquina (1,403 contra 1,266 ms), o bastante para esconder uma piora de ~20%. Meça a base (cópia congelada do commit de partida) e a nova intercaladas na mesma sessão, em pares, uma execução por vez e em ordem alternada. Antes, um A/A dá o ruído (~1%). Registre a carga e repita se ela subir: um pico levou a razão a 1,101 (medido no flipper-boom, 2026-10-13).
- Trocar um literal por uma conta 'equivalente' no papel pode mudar o double: 4,15 - 0,35 dá 3,8000000000000003, e não 3,8 (medido no Godot 4.7.2; o Lua usa o mesmo double). No flipper-boom essa diferença de 1 ULP mudou 62 de 168 arquivos do oráculo. Escreva a medida derivada como 'valor na configuração de referência + delta', com delta 0,0 nela, e cubra-a com == num teste e com o oráculo por semente (2026-10-13).
- Ao trocar chaves opcionais por campos tipados (Dictionary para classe no Godot, tabela para construtor no Defold), levante todos os padrões que cada chave recebia e fique com um só (no flipper-boom, 'padrao' tinha "" e "ataque"). Ausência com significado vira um booleano ou um sentinela documentado no comentário do campo. O log omite a chave enquanto o campo guarda o sentinela, para que quem lia '.get(chave, padrão)' continue recebendo o padrão. Um spec cobra as duas saídas de cada sentinela (medido em 2026-10-13).
- Na triagem por chave de regra (base mais uma regra ligada), declare o que cada chave requer e ligue os requisitos junto. Uma chave ligada sem eles mede efeito zero, calada: no flipper-boom, as 4 cartas de Flipper entravam no sorteio sem o Flipper para agir. Um spec liga cada chave sobre a base com e sem os requisitos e confere que a mecânica só acontece no primeiro caso (2026-10-13).
- Simulador, bot, captura, prancha e spec passam pelo caminho de produção: chamam a mesma função que a cena usa para aplicar uma regra ou opção, abrem estado pela regra e não pela entrada, e desenham com o mesmo material e a mesma fusão de malhas. Ferramenta que avança quadros à mão avança todo nó que muda com o tempo (a dica de 3,2 s ficou na tela até o minuto 1). Prove pela semente: com e sem a opção que o perfil desliga, a saída é idêntica (antes, 1426 contra 1581 abates) (medido no flipper-boom, 2026-10-15).
- O replay gravado em arquivo (uma linha por ação, uma seção por run) só serve se a conferência levar todo estado que as ações gravadas decidem, inclusive o que não muda número: no CampCrawler (2026-10-17), a conferência tinha vida, ataque, nível e regras, e trocar no arquivo um recruta lanceiro por um cavaleiro, de mesma vida e mesmo ataque, reproduzia 'tudo confere'. A classe entrou na conferência. Prove cada campo adulterando a ação no arquivo e cortando-o na conferência logo depois dela: mais adiante, outra diferença (uma luta) pode divergir e esconder a falta.
- O gravador fecha a seção antiga, com a ação do mesmo quadro e a conferência dela, antes de abrir a run nova: no CampCrawler, o reinício que chegava no mesmo quadro de uma ação a perdia do arquivo. E o portão confere quantas runs o arquivo tem, além de reproduzi-lo: a run nova que não chega ao arquivo não diverge de nada, e a reprodução sai com 0 (a passada da bancada exige cinco).

### Ferramentas de verificação

- Ferramenta que cria uma cópia ou uma pasta de saída aceita só pasta nova ou vazia, e recusa a que é o projeto, fica dentro dele ou acima dele. Nunca apague com rm -rf ou rmtree uma pasta que veio de argumento ou do ambiente, e não compare uma saída que já existia. Prove com uma pasta-sentinela: no flipper-boom, 'medir_avisos.py --copia ..' apagaria os worktrees, e a sentinela sumia antes da correção (2026-10-15).
- Todo medidor ou contador lê o código de saída do que rodou e reprova em timeout (124), em comando que não rodou (125 a 127) e em morte por sinal (128 ou mais, ou negativo): o zero de um processo que não terminou não quer dizer 'zero achados'. Toda varredura também afirma um mínimo lido (arquivos, linhas) e reprova abaixo dele. Prove com o motor fora do PATH: no flipper-boom isso dava total 0 antes da correção (2026-10-15).
- Script que lança várias execuções do motor com timeout em paralelo trata INT e TERM saindo de vez. Ele manda TERM ao timeout de cada job (pkill -TERM -P <job>) antes de mandar ao job: o timeout tem grupo de processos próprio, o Ctrl-C não chega a ele, e órfão ele deixa o motor escrevendo na saída. Depois disso, não lança mais nada. O passo que compara não roda quando a execução falhou ou foi interrompida (no flipper-boom, com TERM aos 25 s: saída 143 e nenhum Godot vivo, 2026-10-13).
- Exceção de fitness function ou de allowlist diz o arquivo, o trecho, o motivo e quantas linhas cobre (1 por padrão). Ela reprova se cobrir outro número de linhas ou se não achar mais a linha. Exceção por trecho ou por arquivo libera em silêncio a próxima ocorrência: no flipper-boom, uma 11ª linha passava numa exceção de 10 (2026-10-15).
- Fitness function por texto desce em subpastas, lê todo arquivo de texto (pula binário pelo byte zero, não por extensão) e cobre todo consumidor da regra: cena, bots, simulador e ferramentas. Ela traz linhas de sonda que tem de pegar e outras que tem de deixar passar, e diz por escrito o que não vê. Onde der, junte uma fitness dinâmica que roda a regra com o parâmetro variado: no flipper-boom, 7, 9, 11 e 13 colunas pegaram o '> 3.9' que a busca por texto deixou passar (2026-10-13).

### Entrada e troca de estado

- Quando um toque abre ou fecha uma camada, o segundo toque de um toque duplo acerta o que ficou sob o dedo. Aqui apagou as dicas vistas e forçou uma vitória que foi gravada no save (medido no flipper-boom, 2026-10-09). A camada exposta ignora o toque por 0,3 s, o intervalo do toque duplo do Android, e nenhum botão destrutivo nasce sob a pegada do botão que abriu a tela. O spec dá dois toques rápidos no mesmo ponto, sobre cada botão que a troca expõe, e confere que nada mais mudou.
- Toda troca de estado que passa a entrada para outro dono (cartas, pausa, queda, resultado) solta à mão os gestos em andamento, dedos e arrasto do mouse, no próprio quadro da troca. A soltura do dedo que já estava na tela chega depois, não passa mais pelo controle antigo, e ele fica preso: aqui o trilho ficou desenhado os 2 s da queda (medido no flipper-boom, 2026-10-09). O spec aperta antes da troca, troca o estado, solta depois e confere o controle limpo.

### Captura, cor e enquadramento

- Escolha, rotule e audite a cor pelo pixel da captura no lugar, não pelo hex do código. Isole cada peça por máscara (foto com a peça menos foto sem ela), tire 1–2 px de borda e use o mesmo quadro e a mesma semente para todas as candidatas. Luz, emissão e transparência mudam a cor: lima × lavanda deu 75,8 ΔE00 pelo hex e 16,0 pelo pixel. Para medir uma superfície, agrupe os tons a até 4 níveis do mais frequente: a cor exata partiu um chão em 8 entradas por ruído de ±1 (medido no flipper-boom, 2026-10-10).
- Uma otimização de render que promete a "mesma imagem" (fundir malhas, desenhar em lote, trocar material) prova isso pelo pixel, não pela contagem de chamadas. Capture antes e depois no mesmo quadro e com a mesma semente, e conte os pixels de cada cor de sinal: no D1 (609 → 198 chamadas), o halo de perigo foi de 667 px a 0, e as provas do commit já mostravam isso. "Refatoração sem mudança de comportamento" só se apoia no portão se o portão confere pixel (medido no flipper-boom, 2026-10-10).
- Faça o teste do cinza (valor antes do matiz) com L*, ou com o cinza de mesma luminância Y, nunca com a luma Rec.601: ela subestima verdes e cianos. A gema 6ff0a0 deu 192 pela luma e cerca de 220 pelo L* (86,1), e a maior diferença chegou a 28 níveis (medido no flipper-boom, 2026-10-10).
- Aceite um efeito visual pelo alcance medido na captura, não pelo parâmetro: meça a variação de cor ao longo de uma linha (R−G para uma tinta vermelha), antes e depois. A vinheta "de 10%" só se via até ~40 px (5,5%), porque a curva elevava a força ao quadrado; sem o quadrado, chegou a ~80 px (11%) (medido no flipper-boom, 2026-10-09).
- A captura só sai idêntica entre execuções se todo sorteio visual tiver semente: um RNG de apresentação criado sem semente muda as partículas a cada rodada (até 644 px numa caixa de 45×37, e o contraste foi de 3,00 a 2,98:1). Compare as candidatas no mesmo quadro da mesma execução, ou semeie o RNG da apresentação no modo de captura. Uma decisão perto de um limite pede duas rodadas (medido no flipper-boom, 2026-10-09).
- Meça o enquadramento ou o limite no pior quadro da animação (pulso, squash, recuo), não no repouso. O chefe medido parado ficava a 15 px do topo e, com o pulso de 6% por golpe, encostava nele. O spec confere em repouso e no pulso (medido no flipper-boom, 2026-10-12).
- Em 2.5D, a ameaça que acerta o personagem é desenhada sem teste de profundidade, por cima dele e dos projéteis amigos. Com profundidade, ela some atrás do corpo justo no contato: a chama sumia de 1,2 a 0,45 de distância, nos últimos ~0,2 s. Prove com capturas da aproximação em várias distâncias (medido no flipper-boom, 2026-10-09).
- Retorno visual de gesto (trilho, pad, botão sob o dedo) vai acima do ponto mais alto do gesto, nunca no ponto do toque. No aparelho ele some sob o polegar, e a captura do PC não mostra isso: no S20 FE (~10,6 px/mm), 104 px (9,8 mm) ficavam inteiros sob o dedo, e desenhar 128 px (~10,8 mm) acima resolveu (medido no flipper-boom, 2026-10-10). Prove com um polegar desenhado na captura e um spec de folga em mm.
- Em execuções paralelas sob Xvfb, dê a cada uma um número de tela próprio (`xvfb-run -a -n N`, com N distintos, por exemplo uma base mais o índice do job). Só com -a, duas execuções que sobem juntas pegaram a mesma :99, e a que terminou primeiro derrubou a outra ("X connection to :99 broken"). Vale também para o portão que roda specs com tela em paralelo (medido no flipper-boom, 2026-10-11).
- xvfb-run sem -s cria uma tela de 640×480. A janela maior abre e a captura sai inteira, mas as APIs de tela respondem 640×480: no Godot 4.7.2, a área útil do celular simulado caiu de 1440×688 para 346,67×304 lógicos. Toda prova com tela roda com `xvfb-run -a -s "-screen 0 2560x1440x24"`, ou com uma tela maior que a maior janela testada, e o log registra a tela junto com a janela (medido no flipper-boom, 2026-10-15).

### Log da partida

- Antes de um teste no aparelho, o log da partida traz uma linha por segundo de jogo com o tempo de jogo, o relógio do app e o FPS, mais os eventos de pausa e de ciclo de vida do app (perdeu o foco, pausou, retomou). Sem isso, a diferença entre relógio e jogo não separa pausa, saída do app e lentidão: aqui 392 s de relógio viraram 245 s de jogo, e ~2 min ficaram sem explicação (medido no flipper-boom, 2026-10-09).
- Atalho de teste que começa run nova (bancada, sala de testes, ir ao mapa N) deixa no log uma linha própria, e a ferramenta que agrupa runs a usa como fronteira, como faz com a abertura do jogo. Sem ela, o resumo do playtest juntou numa run só três runs da bancada na mesma semente, cada uma no mapa seguinte da outra, e as mostrou como uma run abandonada de vários mapas (CampCrawler, 2026-10-17). A ação recusada não é fronteira. Um teste da ferramenta com um log de exemplo, chamado pelo portão, prende isso.

### Instruções e skills do agente

Claude Code 2.1.300 e Codex 0.163.0, medidos nesta máquina em 2026-10-16 (CampCrawler e repositório das skills) ou lidos na documentação oficial e no código-fonte da versão ([doc]).

- O Codex lê no máximo 32.768 bytes de instrução do projeto (`project_doc_max_bytes`), somando os `AGENTS.md` da raiz do repositório até a pasta de trabalho, e corta o resto calado: um `tracing::warn` e nada para o agente nem para o autor; a regra do fim do arquivo deixa de existir para ele ([doc] `core/src/agents_md.rs`; o valor medido no binário). Ele nunca lê `CLAUDE.md` (só com `project_doc_fallback_filenames`), lê o `AGENTS.override.md` no lugar do `AGENTS.md` da mesma pasta [doc], e o `~/AGENTS.md` não entra num projeto: global é só o `$CODEX_HOME/AGENTS.md` (medido com `codex debug prompt-input`). O do CampCrawler estava com 30.551 bytes, ~2,2 KB de folga. Remédio: um teste que reprova acima do limite contando bytes, não caracteres (acento ocupa 2), e diz que seções o corte alcança, mais um que reprova `AGENTS.override.md` esquecido. No Defold, `tests/test_agents_md.lua` na suíte (o do CampCrawler é o modelo); no Godot, um spec headless `tests/agents_md_spec.gd` com `FileAccess.get_file_as_bytes("res://AGENTS.md").size()`, não o `length()` da String, que conta caracteres.
- Onde as skills são achadas. Claude Code: a pessoal (`~/.claude/skills/<nome>`) vence a do projeto (`.claude/skills/<nome>`) quando o nome colide, então uma cópia no repositório fica sombreada na máquina; a sessão na nuvem não vê `~/.claude/skills`, só o `.claude/skills` do repositório e as skills habilitadas no claude.ai [doc]. Codex: lê `.agents/skills` de cada pasta entre a de trabalho e a raiz do repositório, `~/.agents/skills` e o obsoleto `~/.codex/skills`, nunca `.claude/skills` [doc, medido]. Ele segue um symlink por skill (`~/.agents/skills/<nome>` → `~/.claude/skills/<nome>`); o symlink da pasta inteira arrastou o `synced/` do app e duplicou skills, 26 entradas, 20 delas do `synced/` (medido). Nome repetido em duas raízes aparece duas vezes, sem fusão: link de usuário e link no repositório juntos duplicam a skill [doc, medido]. O Codex corta a descrição em 1.024 caracteres, calado (medido); o Claude Code trunca `description` + `when_to_use` em 1.536 na lista [doc]. As duas ai-first estavam com 1.010 e 1.016. Remédio: uma fonte só, um symlink por skill e um verificador que reprova link ausente e descrição acima de 1.024 (no repositório das skills, `distribuir.py --check`).
- O checkout das skills é compartilhado: toda sessão local carrega o ramo que estiver em checkout em `~/.claude/skills`, e o Codex vê o mesmo pelos symlinks. Em 2026-10-16 a pasta estava no ramo de outra sessão, 5 commits atrás do `main` (medido: o `armadilhas.md` da ai-first-defold com 264 linhas contra 321); como toda sessão lê a skill do disco [doc], todas carregavam a versão velha sem aviso. Regra: a pasta fica no `main`; lição entra num ramo numa worktree fora do `/tmp` (aqui o `/tmp` é tmpfs: a worktree some no reboot e fica `prunable`), com `git -C ~/.claude/skills fetch` e `git -C ~/.claude/skills worktree add ~/.cache/claude-skills-wt/<ramo> -b <ramo> origin/main`, nunca trocando o ramo da pasta. Depois do merge, `git -C ~/.claude/skills pull --ff-only` atualiza o que as sessões leem e o `distribuir.py` do repositório regenera as cópias de `~/Documentos/Skills` que sobem para o claude.ai; o `distribuir.py --check` reprova a pasta fora do `main`.
