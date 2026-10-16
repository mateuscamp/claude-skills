# Armadilhas do Defold que o agente não vê

Medido no Defold 1.13.2 (Linux x86_64, sem GPU): no Mineboom (2026-10-09/10), no BomberBoom
(`~/defold/bomberboom-df/docs/PEGADINHAS.md`, onde cada uma tem o sintoma inteiro) ou no
relatório "Godot AI-first comparado a Defold" (2026-10-09, marcado [relatório]). O que foi
conferido de novo na **1.14.0** (CampCrawler, 2026-10-13) leva [1.14.0]; o que vem só da
documentação oficial, sem medição nossa, leva [doc]. Antes de confiar num item em outra
versão, reproduza o caso mínimo.

Esta lista cresce com o uso: armadilha do Defold em que um projeto caiu e que ele resolveu entra
aqui, com o número medido; a que vale para jogo em qualquer engine entra na seção "Gerais de
jogo", igual nas duas skills (ai-first-defold e ai-first-godot).

## Build e ferramenta

| Situação | O que acontece | Remédio |
|---|---|---|
| bob com erro de settings | sinaliza `SEVERE`, não só `ERROR`, e **deixa o bundle anterior no lugar** | grep por `ERROR\|SEVERE\|Could not parse` **e** conferir se o executável existe |
| Editor atualizou | o link `defold-editor.jar` do wrapper aponta para um sha que não existe; a JVM falha **no idioma do sistema, sem ERROR** | `ln -sfn /opt/Defold/packages/defold-<engine_sha1>.jar ~/defold/bob/defold-editor.jar` (o sha está em `/opt/Defold/config`) |
| Editor atualizou (JDK) [1.14.0] | o editor **se atualiza sozinho** (1.13.2 → 1.14.0 em 2026-10-12, sem ninguém pedir) e a pasta `/opt/Defold/packages/jdk-*` muda de nome; o `java` do sistema no PATH dá `UnsupportedClassVersionError` | `export PATH=$(command ls -d /opt/Defold/packages/jdk-* \| head -1)/bin:$PATH` no comando do AGENTS.md, nunca o caminho fixo; refaça também o link da linha acima e decida com o autor se a versão fixada acompanha |
| Executável rodado da raiz do projeto | carrega `build/default/` relativo ao cwd e roda **build velho** | cwd = pasta do executável |
| Headless sem vsync de hardware | vsync por software às vezes espera para sempre: o motor monta a cena e **não avança**, sem erro | `[display] vsync = 0` num `--settings` só do portão (o `.ini` do bob não aceita comentário) |
| Duas instâncias | disputam portas de log/profiler; `pkill` volta antes de matar e no Linux nem casa (nome truncado em 15) | uma por vez, mate por PID |
| bob pega 16 de 21 erros plantados [relatório] | passam: id duplicado de game object e de nó, chave errada no `game.project`, animação de sprite inexistente, `goto` | linter próprio, LuaLS, e passada que **executa** o caminho |
| `--config=secao.chave=valor` com uma chave que é prefixo de outra | a busca casa por **prefixo**: `--config=p.autoplay=1` antes de `--config=p.autoplay_reward=0` faz `sys.get_config_int("p.autoplay_reward")` devolver 1, sem erro; invertendo a ordem dos argumentos, volta a 0 (Mineboom, 2026-10-10) | nenhuma chave da seção pode ser prefixo de outra; um teste lê o `game.project` e as ferramentas e reprova |
| Saída do motor redirecionada para arquivo | fica em buffer até o processo sair: quem lê o log com o jogo rodando vê arquivo vazio | `stdbuf -oL -eL` ao lançar |
| Cache HTTP do motor com índice velho [1.14.0] | o motor abre o cache da máquina ao subir, mesmo sem `http.request`; com o `index` velho, um `WARNING:DLIB: Unable to remove` por entrada reprova o smoke (item abaixo) | `[network] http_cache_enabled = 0` no `smoketest.ini` do portão |

- Cache HTTP [1.14.0]: `network.http_cache_enabled` vem 1 no `meta.properties`, então o motor
  abre o cache da máquina mesmo em jogo sem rede. No CampCrawler (2026-10-15, portão da D52) o
  `index` de 10/out apontava para arquivos que já não existiam, e o smoke, que reprova
  `Unable to`, falhou com 57 "problemas" sem defeito no jogo. A causa foi inferida na sessão:
  mover o `index` para fora, sem apagar, limpou o portão. O `=0` foi medido em 2026-10-16 por
  `--config`, com HOME vazio: o motor nem cria a pasta (`~/.local/share/Defold/http-cache`);
  que ele cale também o índice velho segue disso, sem medição com o índice. No
  `scripts/smoketest.ini` a mesma chave entra no bundle pelo bob e vale para todas as passadas
  de uma vez, em vez de um `--config` repetido em cada uma; é melhor que pôr o aviso no
  `IGNORE` do smoke.

## Verificação estática

- O editor 1.13.2 traz o LuaLS **e** as anotações oficiais do Defold dentro do jar
  (`_unpack/<plat>/bin/lsp/lua/` e `.../meta/3rd/Defold/library`). Nada precisa ser baixado.
  `scripts/luals_check.sh` extrai para `~/.cache/defold-luals/<sha>` e roda `--check` em ~1 s.
- O LuaLS pega API inventada (`gui.set_textt`) e tipo errado que o bob aceita. Sem problemas, ele
  grava o relatório como **lista vazia**, não objeto vazio; com problemas, objeto por arquivo.
- **O LuaLS só lê `.lua` sem `files.associations`.** `.script`, `.gui_script` e
  `.render_script` são pulados em silêncio e o relatório sai limpo: `gui.set_textt(...)`
  plantado num `.gui_script` passou verde no Boomlitude, e o Mineboom, com quase toda a cena em
  `main/game.gui_script`, nunca tinha sido checado (2026-10-10). A luarc precisa de
  `"files.associations": { "*.script": "lua", "*.gui_script": "lua", "*.render_script": "lua", "*.editor_script": "lua" }`
  — o `scripts/luals_check.sh` já traz. Prove plantando o erro **num script de cena**, não num
  módulo `.lua`.
- Anotação mais estrita que o motor: `gui.is_enabled(node)` acusa parâmetro faltando (o
  `recursive` é opcional no motor); o mesmo com `sys.get_sys_info()` e o `options` de
  `go.set`/`go.get` (o texto diz "(optional)", a assinatura não). Passe o argumento explícito
  (`true` antes de `pick_node`, ver Entrada; `{}`) em vez de criar exceção.
- Anotação que **falta** no 1.13.2: não há o módulo `camera` (`camera.screen_to_world`,
  `camera.world_to_screen`) nem as versões tipadas `sys.get_config_string`/`sys.get_config_int`
  — só `sys.get_config`. O motor tem as três. Remédio: um arquivo `---@meta` do projeto em
  `tools/luals/` (o `luals_check.sh` o põe em `workspace.library`), **só** com o que uma passada
  do portão exercita no motor, citando a linha de log que prova; linha sem esse respaldo é API
  inventada que o LuaLS passa a aceitar. Modelos: `~/defold/boomlitude/ferramentas/luals/` e
  `~/defold/campcrawler/tools/luals/`.
- [1.14.0] **O LuaLS só cobra campo de tabela que tem classe.** Sem anotação, `a.kidn` no lugar
  de `a.kind` passa limpo, venha a tabela de um construtor de outro módulo ou de um literal no
  mesmo arquivo; com `---@class` e sem `---@return` no construtor, passa também. Com os dois, o
  mesmo acesso reprova como `undefined-field` (erro no `scripts/luals_check.sh`). No CampCrawler
  (2026-10-16), quatro acessos errados plantados passaram com exit 0 sem a anotação e
  reprovaram os quatro com ela, inclusive `outcome.events[1].kidn`, que chega pelo
  `---@field events Event[]`. Num caso mínimo, a classe incompleta e a velha não falham igual:
  - campo que o construtor monta e a classe não declara: `inject-field` onde a variante o
    acrescenta (`e.enemy = enemy`) e `undefined-field` em quem o lê; no literal do `return`,
    sem leitor, passa;
  - campo que a classe declara e nada monta: passa, e quem o lê recebe sempre nil. O
    `missing-fields` só olha literal com `---@type`, não o `return` sob `---@return`.

  Por isso a anotação anda com um teste da suíte que a prende ao construtor (CampCrawler,
  `tests/test_type_annotations.lua`). Ele monta instâncias reais, inclusive pelas variantes que
  preenchem o campo opcional, porque o `pairs` não vê campo nil. Compara as chaves com os
  `---@field` do bloco nos dois sentidos e exige o `---@return` em cada construtor. Comece pelas
  tabelas que cruzam módulos (evento, configuração, resultado de ação) e anote as outras quando
  passarem a cruzar ou forem mexidas; tabela de outra forma, mesmo devolvida pelo mesmo módulo, é
  outra classe.

## Entrada

- **Um toque chega como mouse e como multitoque** se os dois estiverem ligados à mesma ação. No
  desktop só existe o mouse, então todo teste de desktop passa e o aparelho gasta duas ações por
  toque. Ligue só `MOUSE_BUTTON_LEFT` (o primeiro dedo vira mouse no celular).
- `action.x/y` não chegam em coordenada de projeto quando a janela escala; `gui.pick_node`
  respeita o ajuste. Converter por aritmética erra por escala.
- `gui.get_screen_position` e `gui.pick_node` **discordam** quando a janela não tem a resolução do
  projeto: toque sintetizado a partir da posição de um nó acerta **outro nó**, sem erro. No
  headless a janela é a do projeto e os dois coincidem.
- [1.14.0] `gui.pick_node` **não olha se o nó está ligado**: o nó desligado com
  `gui.set_enabled(no, false)` continua acertável, e o filho de pai desligado também. O toque
  atravessa o cartão ou a aba que sumiu e acerta o que não se vê, sem erro. Pergunte antes:
  `gui.is_enabled(no, true) and gui.pick_node(no, x, y)`. Com `false` o `is_enabled` só olha o
  próprio nó, e o filho de pai desligado responde `true` (medido em 2026-10-16). O CampCrawler
  desliga cada nó e usa `false` (`main/hud_view.lua`, `main/squad_view.lua`). Quem desliga o
  grupo pelo pai precisa do `true`.

## Mensagens, objetos e GUI

- `msg.post` é entrega no próximo despacho; ler estado logo depois lê o velho, sem erro.
- `msg.post` para URL que não existe só gera log, e `pcall` volta true. [relatório]
- Mensagem de objeto sendo deletado **atravessa a troca de fase** (`go.delete` só vale no fim do
  quadro). Guarda por época, não por registro.
- Nome de mensagem que colide com tipo do motor (`set_speed`, `restart`) engole o payload.
- `euler` e `position` são do **game object**, não do componente: `go.animate("#sprite", "euler.z")`
  estoura no `init` e o erro aparece longe, no primeiro uso do id nil.
- `gui.cancel_animations` é plural; o singular compila e estoura quando o caminho roda.
- `gui.set_parent(no, pai)` sem o terceiro argumento (ou com `false`) preserva o transform
  **local**. Com `true` (`keep_scene_transform`) preserva a posição **na tela** e compensa o
  transform que o pai tem **naquele momento**. [1.14.0] Pai em (100, 0) com escala 0,5: o filho
  em (400, 400) adotado com `true` fica com local (600, 800) e não encolhe com o pai. Com
  `false`, fica com local (400, 400) e tela (300, 200).
- [1.14.0] Para caber mais na mesma caixa (tabuleiro 9x11 onde cabia o 9x9, CampCrawler D54),
  escale um raiz próprio do grupo em vez de recalcular posições. Adote os filhos com esse raiz
  na identidade (todos no `init`, antes do primeiro `gui.set_scale` dele): assim a coordenada de
  projeto continua sendo a posição local deles. Daí em diante `gui.get_position` é local, e o
  ponto em coordenada de projeto (espaço do pai do raiz) é `origem + escala * local` (é por ele
  que o robô toca, `board_view.touch_point`). O `gui.pick_node` já conta a escala do pai, então
  a entrada não muda.
- Na GUI criada em código, a **ordem de criação é a ordem de desenho**: crie em sequência, não
  dentro de um construtor de tabela.
- [1.14.0] Texto que quebra muda de altura, e o vizinho em posição fixa fica por baixo: a linha
  de regras do painel quebrou em duas num idioma e cobriu o estado (CampCrawler D56). Meça e
  desça o vizinho pela altura medida (`main/hud_view.lua`, `place_hint`):
  `resource.get_text_metrics(gui.get_font_resource(gui.get_font(no)), gui.get_text(no),
  { width = gui.get_size(no).x, line_break = true }).height * gui.get_scale(no).y`. A métrica
  é da fonte, sem a escala do nó. Sem `line_break = true` o `width` é ignorado e volta a altura
  de uma linha (medido com a `default.font` dos builtins: 16,3 sem quebra, 65,2 com
  `width = 120` e quebra). Título que não cabe nem assim se resolve no texto: o da tela do
  camponês passou por baixo do botão de idioma e foi encurtado nos dez idiomas.
- `gui.get_text_metrics_from_node` não existe mais: o LuaLS acusou no 1.13.2, e no 1.14.0 ela é
  `nil`. Ela vem da memória de versão antiga; quem a substitui é a chamada de cima.
- Limite de mensagem: 2 KiB. Tetos de instâncias, sprites e nós no `game.project`/`.gui`.
- [1.14.0] Passar do `max_nodes` do `.gui` imprime `ERROR:GUI: Could not create the node since
  the buffer is full (N).`, e o `gui.new_*_node` **levanta** `Out of nodes (max N)`: o resto da
  função não roda. O `gui.delete_node` só devolve a vaga no fim do quadro, então apagar e criar
  no mesmo quadro também estoura (medido em 2026-10-16 com `max_nodes: 16`).
- [1.14.0] Para ver a folga sem contar à mão, conte com uma sonda por pai e emita o total num
  fato: `gui.new_box_node`, `gui.set_parent(sonda, pai, false)`, `gui.get_index(sonda)`
  (quantos irmãos vieram antes) e `gui.delete_node`. A sonda só vê filhos diretos: todo pai novo
  entra na lista, senão o total cai calado (CampCrawler D54: de 997 para 91 quando as células
  passaram para o `board_root`). Ela ocupa vaga até o fim do quadro. Com o fato `NOS` à vista,
  o 9x11 (99 células com 10 camadas mais o HUD, ≈1180) subiu o `max_nodes` de 1024 para 2048
  antes de estourar.

## Animação

- O segundo `go.animate`/`gui.animate` na mesma propriedade cancela o primeiro **e descarta o
  callback dele** — o que esperava o fim da animação nunca roda. [relatório]
- Pixel art com filtro `nearest` só amplia em fator inteiro; posição fracionária faz o contorno
  cintilar. Arredonde a posição ao pixel da arte.
- Fonte distance-field com CJK inteiro é enorme: gere `extra_characters` a partir dos textos e
  reprove fonte desatualizada no portão (glifo ausente vira quadrado sem log).

## Lua: LuaJIT do motor e Lua 5.x da suíte

- `/` devolve float no Lua 5.3+: `3*2/2` é `3` no LuaJIT e `3.0` no Lua 5.4 e 5.5. O `==`
  continua verdadeiro, então só muda o que vira texto (`tostring`, `..`, `%s`), e `%d` com valor
  fracionário estoura no 5.3+. O motor (LuaJIT) nunca mostraria: só a suíte no Lua 5.x pega. No
  CampCrawler (D52, `squad.level_threshold`), a soma `base * passos + passos * (passos - 1) / 2`
  saiu `"2.0,5.0,9.0,14.0,20.0"`, e o teste que compara texto reprovou só no Lua 5.5. Remédio:
  `math.floor` em toda divisão cujo resultado é inteiro (medido em 2026-10-16: LuaJIT 2.1, Lua
  5.4 e 5.5).

## Sorteio

- `math.random` deu a **mesma** sequência em LuaJIT e HTML5 [relatório]. Os problemas reais:
  estado global (qualquer chamada fora da regra desloca a sequência), semente padrão fixa e 15
  bits. Gerador próprio com estado: LCG de 32 bits com multiplicador < 2^21 fica exato em double
  em Lua 5.1, LuaJIT e 5.4+.

## Automation Bridge 2.5.0 (API v2)

- [1.14.0] A 2.5.0 ainda era a última tag em 2026-10-13 (`gh api repos/defold/extension-automation-bridge/tags`).
  No CampCrawler as três provas passaram com ela no 1.14.0: dois toques reais em `cell_4_4`
  (turno 0 → 1), layout em 10 tamanhos de janela, e rajada de toques mais recompensa tocada.
- Base: `http://127.0.0.1:<porta do engine service>/automation-bridge/v2`. A porta sai na linha
  `INFO:ENGINE: Engine service started on port <port>` do motor (e no `target.url` do
  `run` do editor). O manual de referência fica em `automation_bridge/README.md` do repositório.
- [doc] Comece pelo `GET /health`: `capabilities`, `capability_versions`, `native_version`,
  `api_version_min/max`. Rota sem suporte responde `501 unsupported_capability`; negocie a
  versão (ex.: `input.key>=2` para `hold`) em vez de supor.
- [doc] A entrada tem dono: `PUT /input/configure?client_id=&session_id=&lease=&device=`
  (`auto`, `mouse` ou `touch`; `touch` só em iOS, Android e Switch, e um gesto nunca injeta os
  dois). Fila FIFO com recibo: `/input/status`, `/input/pending`, `/input/cancel`, `/input/flush`;
  lease vencido solta o ponteiro sozinho. Há `drag`, `drag_path`, `key` (texto ou `{KEY_...}`,
  `hold`, `modifiers`) e `wheel`.
- [doc] **Canal da aplicação**, opcional e só debug: `[automation_bridge] application_api = 1`
  (no `--settings` da Bridge, nunca no `game.project`). O jogo publica estado com
  `automation_bridge.publish(nome, tabela)` (`GET /state`, `GET /state/wait?after_revision=N`),
  emite eventos com `emit` (`GET /events?cursor=N` com long-poll; cursor velho volta
  `overflow: true`, nunca avança calado), registra comandos nomeados com `command` (`POST
  /commands`; não há eval), confirma o que fez com um toque com `acknowledge_input(input_id,
  {accepted, reason})`, liga nó a chave de localização com `annotate` e documenta tudo com
  `describe` (`GET /application/catalog`). Nomes com prefixo do projeto (`jogo.estado`).
  - O módulo `automation_bridge` **não existe** em release nem no headless do portão: a cena
    só chama atrás de `if automation_bridge then`, e o domínio nunca chama.
  - Serve para a prova esperar estado e saber se o jogo aceitou o toque, em vez de ler log. O
    portão headless continua lendo log: a Bridge não roda nele.
- [doc] Gravação de vídeo nativa só em macOS e Windows; captura de GPU (Metal) só em macOS.
- Extensão **nativa**: o build compila no servidor da Defold (`build.defold.com`) ou num Extender
  local. No `game.project`, todo portão passaria a depender de rede — ponha a dependência num
  `--settings` separado (`scripts/bridge.ini`).
- Só em build **debug**; não existe em `--variant headless` (o fonte fica atrás de `DM_DEBUG`).
- O repositório e o pacote não declaram licença: registre e mantenha fora de release.
- Resposta em envelope `{ok, data}` ou `{ok:false, error}`; erro lógico chega como HTTP 500.
- `/input/click` com duração zero é **despachado** (o `/input/status` diz `released`) e o jogo
  **não registra**. Toque é sessão de ponteiro: `pointer/open` → `pointer/hold` (0,12 s) →
  `pointer/up`. O recibo do POST é do aceite, não da entrega: confira o efeito no jogo.
- O soltar é reportado no centro da tela, não no ponto do toque. Jogo que age no soltar precisa
  medir isso antes.
- O id de nó dado por `gui.set_id` aparece como `name`; o `id` da Bridge é de snapshot e muda com
  a cena. Busque por `name_exact` e clique pelo `id` recém-lido.
- `/screenshot` é assíncrono (`pending`); espere `/screenshot/status?capture_id=N`.

## Log em arquivo (1.13.2)

- `project.write_log` está marcado obsoleto no `meta.properties` do bob; o atual é
  `project.write_log_file` (0 Never, 1 Debug, 2 Always). `minimum_log_level` padrão é 1 (USER
  DEBUG), que já inclui `print`.
- No Linux o motor anuncia `Writing log to: ./log.txt` e grava **no cwd**, não na pasta de save
  (que ele cria vazia, com o `title` do projeto). Cada abertura regrava o arquivo. Medido em
  2026-10-11 com bundle debug.
- `sys.get_save_file("app", "x")` no Linux dá `~/.local/share/app/x` e cria a pasta.
- `sys.set_error_handler` recebe `(source, message, traceback)` e **não** suprime o
  `ERROR:SCRIPT` do motor no console: o handler só precisa copiar, não imprimir de novo.
- `io.open` e `os.date` funcionam no script de cena; ficam fora do domínio, que não tem relógio.

## API HTTP do editor (1.13.2)

- Sem projeto aberto (tela de boas-vindas) o editor não sobe servidor HTTP: nenhuma porta
  escuta. Medido em 2026-10-10.
- Partida rodada pelo editor (Ctrl+B) não grava o console do motor em arquivo **a menos que**
  `project.write_log_file` esteja ligado: o `editor2.<data>.log` só tem o log do editor. As
  linhas do jogo saem por `GET /console` (`{"lines": [...]}`) e somem quando o editor fecha.
- `GET /console/stream` com o console parado não manda nem o cabeçalho HTTP até a primeira linha
  nova (conferido com `curl -i`). Um `urlopen` antes da janela de leitura bloqueia até o timeout
  de socket e sai com `TimeoutError`. Medido em 2026-10-11, editor aberto sem jogo rodando.
- Um segundo `/opt/Defold/Defold` com o editor já aberto repassa o projeto à instância existente e
  sai; as linhas de `Shutdown` no terminal não querem dizer que o editor fechou.
- Desde a 1.13.2 cada comando tem caminho próprio e o build devolve o resultado na resposta;
  `/command/build` é alias obsoleto de `run`. Confira no `/openapi.json` antes de usar.
- `.internal/editor.port` e `.internal/editor.token` nascem quando o projeto abre e somem quando
  ele fecha. Medido em 2026-10-10.
- `POST /command/run` devolve o build na própria resposta: `{"success", "issues", "target":
  {"url"}}`. `issues` traz o lint do editor (pegou um `Need check nil` que o `luals_check`
  do projeto não pegou) e `target.url` é o engine service do jogo lançado.
- O `run` só aceita `focus`. Com `focus=false` o editor acrescenta
  `--config=display.focus_on_show=0`: o jogo abre sem foco, e jogo que pausa ao perder o foco
  deixa o robô parado depois do primeiro toque. Para o robô jogar, `focus=true` (rouba o foco
  do autor).
- `--config` chega ao jogo pela preferência `run/engine-arguments`, **uma por linha**
  (`"--config=a=1\n--config=b=2"`). Com o jogo já aberto, um novo `run` reinicia o mesmo
  processo pelo engine service e os argumentos novos **não** se aplicam: feche o jogo antes.
- `POST /command/debugger-stop` responde `403` quando o debugger não está ligado; não serve
  para fechar o jogo.
- [doc] Comandos que **bloqueiam** e devolvem o resultado (1.13.2+): `compile`, `run`,
  `clean-build`, `build-html5`, `debugger-start` e `hot-reload`. Códigos: `200` feito, `202`
  aceito e seguindo (não prova nada: espere o efeito, com prazo), `403` fora do estado, `404`
  indisponível, `422` build ou validação falhou, `500` erro do editor. Cada item de `issues` pode
  ter `message`, `severity`, `resource` e `range`, e há item só com `message`.
- [doc] `POST /command/compile` compila **sem rodar** o jogo: com o editor aberto, é a conferência
  mais barata e traz o lint do editor. `clean-build` só quando build comum se comporta
  diferente a cada vez. `build-html5` serve o jogo em `http://127.0.0.1:<porta-do-editor>/html5/`;
  build pronto não é jogo carregado no navegador.
- [doc] `GET /preview/{path}` (sem barra inicial; `width` e `height` de 1 a 4096; desde a 1.13.1)
  devolve PNG da cena **como o editor a vê**: não mostra objeto criado em runtime, pós-processamento
  nem diferença de plataforma. Para isso, screenshot do jogo (captura sob Xvfb ou Bridge).
- [doc] `/prefs/{path}` (GET lê, POST grava JSON) é preferência do usuário, não `game.project`:
  guarde o valor e restaure, como no `run/engine-arguments`.
- [doc] `/eval`: `Authorization: Bearer <conteúdo de .internal/editor.token>`, corpo `text/plain`;
  `401` token, `422` Lua inválido, `503` ambiente não pronto (repita poucas vezes). Só API do
  editor (`editor.get`, `editor.transact`, `editor.can_*`), nunca `go.*`.
- [doc] Rotas de editor script (`get_http_server_routes`) **não** passam pelo token: cuide da
  segurança delas. Ganchos de ciclo de vida moram num único `hooks.editor_script` na raiz
  (`on_build_started` que dá erro **para** o build do editor), mas são só do editor: regra que
  importa vai num script que o portão e o CI também rodam.
- [doc] `/ref?q=` busca na documentação da versão instalada: espaço é E, `|` é OU, filtros
  `environment` (`editor`, `runtime`) e `language`. Ao abrir o editor, espere o
  `.internal/editor.port` e repita `/openapi.json` até vir documento válido.
- O console é zerado a cada `run`: leia `/console` depois do `run`, não guarde índice de linha
  de antes.

## Gerais de jogo (valem em qualquer engine)

A mesma seção está na ai-first-godot e na ai-first-defold; mude as duas juntas. Os números vêm do
flipper-boom (Godot 4.7.2), mas a lição não depende da engine.

### Testes que passam com qualquer código

- Não ponha a entrada do teste no ponto fixo da regra (distância zero, simetria, valor que a regra antiga e a nova tratam igual): ali qualquer implementação passa. Use valores perto do limite, dos dois lados. Quando a regra promete um caminho (aproximar sem cruzar, nunca recuar), confira a cada passo, não só no fim. Prove com um mutante da implementação errada mais provável: no flipper-boom, a 0,05 da linha e conferindo a cada 0,05 s, a puxada de força cheia cruzou de 0,002 para -0,001 (2026-10-15).
- Depois de trocar orientação, base ou layout, procure coordenadas e larguras fixas em specs e ferramentas: toque sintético fora da tela é aceito sem erro, e o spec segue verde. Aqui (360, 1100) ficava fora do canvas de 1280×720 e passava com a regra velha e com a nova (medido no flipper-boom, 2026-10-12). Marque os toques por fração do retângulo visível, meça no arranjo real e escolha um ponto em que só a regra nova passa.
- Spec não conta por contador compartilhado, como id global, número de nós ou tamanho de lista: ele anda por outros motivos, e o teste passa sem o comportamento. Aqui `_proximo_id` andava com inimigos, gemas, ataques e o chefe (medido no flipper-boom, 2026-10-12). Conte o evento ou o campo que só a ação testada altera e veja o spec falhar com a ação desligada.
- Para cada mudança, liste os caminhos de código que produzem o mesmo efeito (cada mesa, cada tipo de desenho, cada gatilho: evento de tamanho, timer, giro) e confira que algum spec passa por cada um. Spec que mede uma variante fica verde enquanto as outras quebram: aqui 3 das 4 mesas desenhavam o inimigo por um caminho sem spec (medido no flipper-boom, 2026-10-12). Faça grep pelo construtor ou pelo galho e procure-o nos specs.
- Argumento de semente que não é inteiro positivo (`abc`, `0`, `1.5`, `O1`) nunca cai calado no sorteio: a partida 'repetida' não se repetiria. O jogo registra `semente_invalida` no log com aviso e sorteia; a ferramenta de teste recusa o argumento e sai com erro (medido no flipper-boom, 2026-10-09). Uma mutação que aceita a semente inválida faz o spec falhar.

### Prova, oráculo e medição

- Um oráculo por semente idêntico só prova os caminhos que as partidas exercitam e o que o retrato serializa. Antes de confiar nele numa refatoração, instrumente uma cópia com um marcador antes de cada linha mudada e conte as que nenhuma execução alcança (no flipper-boom, 51 de 311). Cubra essas linhas com sondas de carga forçada e plante mutantes nas linhas raras: um deles mudou só 3 de 72 arquivos. Escreva o que fica fora. O contrato de serialização ganha spec próprio, porque o retrato que normaliza ausente para padrão não o vê. Nunca regrave a base para passar (2026-10-13).
- A prova de uma etapa roda no commit que a fecha, com a árvore limpa ou numa cópia de 'git archive', nunca na árvore de trabalho antes do commit. Toda ferramenta de prova grava na saída o commit e o número de arquivos rastreados modificados, e a comparação avisa quando esse número não é zero (no flipper-boom, as etapas 2 e 3 rodaram com 19 e 10 arquivos modificados e foram refeitas, 2026-10-13).
- Não compare desempenho com uma linha de base gravada em outra sessão: a mesma versão variou cerca de 10% com a carga da máquina (1,403 contra 1,266 ms), o bastante para esconder uma piora de ~20%. Meça a base (cópia congelada do commit de partida) e a nova intercaladas na mesma sessão, em pares, uma execução por vez e em ordem alternada. Antes, um A/A dá o ruído (~1%). Registre a carga e repita se ela subir: um pico levou a razão a 1,101 (medido no flipper-boom, 2026-10-13).
- Trocar um literal por uma conta 'equivalente' no papel pode mudar o double: 4,15 - 0,35 dá 3,8000000000000003, e não 3,8 (medido no Godot 4.7.2; o Lua usa o mesmo double). No flipper-boom essa diferença de 1 ULP mudou 62 de 168 arquivos do oráculo. Escreva a medida derivada como 'valor na configuração de referência + delta', com delta 0,0 nela, e cubra-a com == num teste e com o oráculo por semente (2026-10-13).
- Ao trocar chaves opcionais por campos tipados (Dictionary para classe no Godot, tabela para construtor no Defold), levante todos os padrões que cada chave recebia e fique com um só (no flipper-boom, 'padrao' tinha "" e "ataque"). Ausência com significado vira um booleano ou um sentinela documentado no comentário do campo. O log omite a chave enquanto o campo guarda o sentinela, para que quem lia '.get(chave, padrão)' continue recebendo o padrão. Um spec cobra as duas saídas de cada sentinela (medido em 2026-10-13).
- Na triagem por chave de regra (base mais uma regra ligada), declare o que cada chave requer e ligue os requisitos junto. Uma chave ligada sem eles mede efeito zero, calada: no flipper-boom, as 4 cartas de Flipper entravam no sorteio sem o Flipper para agir. Um spec liga cada chave sobre a base com e sem os requisitos e confere que a mecânica só acontece no primeiro caso (2026-10-13).
- Simulador, bot, captura, prancha e spec passam pelo caminho de produção: chamam a mesma função que a cena usa para aplicar uma regra ou opção, abrem estado pela regra e não pela entrada, e desenham com o mesmo material e a mesma fusão de malhas. Ferramenta que avança quadros à mão avança todo nó que muda com o tempo (a dica de 3,2 s ficou na tela até o minuto 1). Prove pela semente: com e sem a opção que o perfil desliga, a saída é idêntica (antes, 1426 contra 1581 abates) (medido no flipper-boom, 2026-10-15).

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

### Instruções e skills do agente

Claude Code 2.1.300 e Codex 0.163.0, medidos nesta máquina em 2026-10-16 (CampCrawler e repositório das skills) ou lidos na documentação oficial e no código-fonte da versão ([doc]).

- O Codex lê no máximo 32.768 bytes de instrução do projeto (`project_doc_max_bytes`), somando os `AGENTS.md` da raiz do repositório até a pasta de trabalho, e corta o resto calado: um `tracing::warn` e nada para o agente nem para o autor; a regra do fim do arquivo deixa de existir para ele ([doc] `core/src/agents_md.rs`; o valor medido no binário). Ele nunca lê `CLAUDE.md` (só com `project_doc_fallback_filenames`), lê o `AGENTS.override.md` no lugar do `AGENTS.md` da mesma pasta [doc], e o `~/AGENTS.md` não entra num projeto: global é só o `$CODEX_HOME/AGENTS.md` (medido com `codex debug prompt-input`). O do CampCrawler estava com 30.551 bytes, ~2,2 KB de folga. Remédio: um teste que reprova acima do limite contando bytes, não caracteres (acento ocupa 2), e diz que seções o corte alcança, mais um que reprova `AGENTS.override.md` esquecido. No Defold, `tests/test_agents_md.lua` na suíte (o do CampCrawler é o modelo); no Godot, um spec headless `tests/agents_md_spec.gd` com `FileAccess.get_file_as_bytes("res://AGENTS.md").size()`, não o `length()` da String, que conta caracteres.
- Onde as skills são achadas. Claude Code: a pessoal (`~/.claude/skills/<nome>`) vence a do projeto (`.claude/skills/<nome>`) quando o nome colide, então uma cópia no repositório fica sombreada na máquina; a sessão na nuvem não vê `~/.claude/skills`, só o `.claude/skills` do repositório e as skills habilitadas no claude.ai [doc]. Codex: lê `.agents/skills` de cada pasta entre a de trabalho e a raiz do repositório, `~/.agents/skills` e o obsoleto `~/.codex/skills`, nunca `.claude/skills` [doc, medido]. Ele segue um symlink por skill (`~/.agents/skills/<nome>` → `~/.claude/skills/<nome>`); o symlink da pasta inteira arrastou o `synced/` do app e duplicou skills, 26 entradas, 20 delas do `synced/` (medido). Nome repetido em duas raízes aparece duas vezes, sem fusão: link de usuário e link no repositório juntos duplicam a skill [doc, medido]. O Codex corta a descrição em 1.024 caracteres, calado (medido); o Claude Code trunca `description` + `when_to_use` em 1.536 na lista [doc]. As duas ai-first estavam com 1.010 e 1.016. Remédio: uma fonte só, um symlink por skill e um verificador que reprova link ausente e descrição acima de 1.024 (no repositório das skills, `distribuir.py --check`).
- O checkout das skills é compartilhado: toda sessão local carrega o ramo que estiver em checkout em `~/.claude/skills`, e o Codex vê o mesmo pelos symlinks. Em 2026-10-16 a pasta estava no ramo de outra sessão, 5 commits atrás do `main` (medido: o `armadilhas.md` da ai-first-defold com 264 linhas contra 321); como toda sessão lê a skill do disco [doc], todas carregavam a versão velha sem aviso. Regra: a pasta fica no `main`; lição entra num ramo numa worktree fora do `/tmp` (aqui o `/tmp` é tmpfs: a worktree some no reboot e fica `prunable`), com `git -C ~/.claude/skills fetch` e `git -C ~/.claude/skills worktree add ~/.cache/claude-skills-wt/<ramo> -b <ramo> origin/main`, nunca trocando o ramo da pasta. Depois do merge, `git -C ~/.claude/skills pull --ff-only` atualiza o que as sessões leem e o `distribuir.py` do repositório regenera as cópias de `~/Documentos/Skills` que sobem para o claude.ai; o `distribuir.py --check` reprova a pasta fora do `main`.
