# Armadilhas do Defold que o agente não vê

Medido no Defold 1.13.2 (Linux x86_64, sem GPU): no Mineboom (2026-10-09/10), no BomberBoom
(`~/defold/bomberboom-df/docs/PEGADINHAS.md`, onde cada uma tem o sintoma inteiro) ou no
relatório "Godot AI-first comparado a Defold" (2026-10-09, marcado [relatório]). O que foi
conferido de novo na **1.14.0** (CampCrawler, 2026-10-13) leva [1.14.0]; o que vem só da
documentação oficial, sem medição nossa, leva [doc]. Antes de confiar num item em outra
versão, reproduza o caso mínimo.

Esta lista cresce com o uso: armadilha do Defold em que um projeto caiu e que ele resolveu entra
aqui, com o número medido; a que vale para jogo em qualquer engine entra em `gerais-de-jogo.md`,
na raiz do repositório das skills, e o `distribuir.py --copiar-gerais` a copia para
`references/gerais-de-jogo.md` de cada skill de motor.

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
| `sys.get_config_int` com valor que não é inteiro [1.14.0] | devolve **0** para `"abc"`, `"1.5"`, `"O1"`, `"7x"` e `"0x10"`, só com um `WARNING:DLIB: Unable to convert 'abc' to int` no console do motor; inteiro grande estoura os 32 bits calado (`99999999999` vira 1215752191) | ler com `sys.get_config_string` e validar em código puro, com o recebido no erro; provar com uma passada de recusa (`smoke.py --erro-esperado`, item abaixo) |
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
- Chave inteira que vira 0 [1.14.0]: no CampCrawler (2026-10-17, bundle headless) a semente
  era lida com `sys.get_config_int`, e `seed=abc` e `seed=1.5` viravam a semente 1 com o robô e
  uma sorteada pelo relógio sem ele (37965 e 37970); `seed=7` funcionava. A partida "repetida"
  não se repetia, e nada parava: o aviso do motor só sai no console (o arquivo da partida do
  `fact_log.lua` não o guarda), e o `smoke.py` só o pegaria pelo `Unable to` numa passada que
  desse o valor errado. Lida com `sys.get_config_string` e validada num módulo sem motor, a
  chave errada estoura no `init` com o recebido (`<projeto>.seed inválido: recebido "abc",
  esperado inteiro >= 0`). Com o erro no `init` de um `.gui_script`, o motor escreve o erro, o
  traceback e `ERROR:GAMESYS: Error when initializing gui component: RESULT_SCRIPT_ERROR.`, não
  inicia o componente, não chama o `update` dele e não gera erro em cascata. A passada de
  recusa declara as duas linhas em `--erro-esperado` (o `smoke.py` perdoa só elas e o
  traceback, e cobra que apareçam) e recusa o fato de início (`--recusar '<PROJETO> INICIO '`).
  No motor basta uma amostra, uma chave por forma de leitura; toda chave se cobra na suíte, com
  um `sys` de mentira que imita o medido aqui (`references/gerais-de-jogo.md`, configuração
  calada). Chave ainda lida com `get_config_int` (no CampCrawler, `autoplay` e as do robô)
  recebe 0 do valor errado, calada.

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
  preenchem o campo opcional, porque o `pairs` não vê campo nil, e uma instância por caminho de
  retorno do construtor. Em cada instância, todo campo sem `?` tem valor e toda chave está num
  `---@field`; só o `---@field` que nada monta se confere na união das instâncias. Exige o
  `---@return` em cada construtor. Conferir tudo pela união deixou passar três mutações no
  CampCrawler (campo ausente numa instância, chave nova num retorno que o teste não montava). Comece pelas
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

## Gerais de jogo: moram em `references/gerais-de-jogo.md`

Ali estão as lições de jogo que valem em qualquer engine: testes que passam com qualquer código,
prova e oráculo, ferramentas de verificação, entrada e troca de estado, captura e cor, log da
partida e instruções do agente. É cópia da fonte única `gerais-de-jogo.md`, na raiz do repositório
das skills. Não acrescente lição aqui: a fonte se edita num ramo em worktree, e o
`distribuir.py --check-gerais` reprova item de lista ou subtítulo nesta seção.
