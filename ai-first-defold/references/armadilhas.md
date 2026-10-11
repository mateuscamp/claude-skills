# Armadilhas do Defold que o agente não vê

Medido no Defold 1.13.2 (Linux x86_64, sem GPU): no Mineboom (2026-10-09/10), no BomberBoom
(`~/defold/bomberboom-df/docs/PEGADINHAS.md`, onde cada uma tem o sintoma inteiro) ou no
relatório "Godot AI-first comparado a Defold" (2026-10-09, marcado [relatório]). Antes de
confiar num item em outra versão, reproduza o caso mínimo.

## Build e ferramenta

| Situação | O que acontece | Remédio |
|---|---|---|
| bob com erro de settings | sinaliza `SEVERE`, não só `ERROR`, e **deixa o bundle anterior no lugar** | grep por `ERROR\|SEVERE\|Could not parse` **e** conferir se o executável existe |
| Editor atualizou | o link `defold-editor.jar` do wrapper aponta para um sha que não existe; a JVM falha **no idioma do sistema, sem ERROR** | `ln -sfn /opt/Defold/packages/defold-<engine_sha1>.jar ~/defold/bob/defold-editor.jar` (o sha está em `/opt/Defold/config`) |
| Executável rodado da raiz do projeto | carrega `build/default/` relativo ao cwd e roda **build velho** | cwd = pasta do executável |
| Headless sem vsync de hardware | vsync por software às vezes espera para sempre: o motor monta a cena e **não avança**, sem erro | `[display] vsync = 0` num `--settings` só do portão (o `.ini` do bob não aceita comentário) |
| Duas instâncias | disputam portas de log/profiler; `pkill` volta antes de matar e no Linux nem casa (nome truncado em 15) | uma por vez, mate por PID |
| bob pega 16 de 21 erros plantados [relatório] | passam: id duplicado de game object e de nó, chave errada no `game.project`, animação de sprite inexistente, `goto` | linter próprio, LuaLS, e passada que **executa** o caminho |
| `--config=secao.chave=valor` com uma chave que é prefixo de outra | a busca casa por **prefixo**: `--config=p.autoplay=1` antes de `--config=p.autoplay_reward=0` faz `sys.get_config_int("p.autoplay_reward")` devolver 1, sem erro; invertendo a ordem dos argumentos, volta a 0 (Mineboom, 2026-10-10) | nenhuma chave da seção pode ser prefixo de outra; um teste lê o `game.project` e as ferramentas e reprova |
| Saída do motor redirecionada para arquivo | fica em buffer até o processo sair: quem lê o log com o jogo rodando vê arquivo vazio | `stdbuf -oL -eL` ao lançar |

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
  (`false`, `{}`) em vez de criar exceção.
- Anotação que **falta** no 1.13.2: não há o módulo `camera` (`camera.screen_to_world`,
  `camera.world_to_screen`) nem as versões tipadas `sys.get_config_string`/`sys.get_config_int`
  — só `sys.get_config`. O motor tem as três. Remédio: um arquivo `---@meta` do projeto em
  `tools/luals/` (o `luals_check.sh` o põe em `workspace.library`), **só** com o que uma passada
  do portão exercita no motor, citando a linha de log que prova; linha sem esse respaldo é API
  inventada que o LuaLS passa a aceitar. Modelos: `~/defold/boomlitude/ferramentas/luals/` e
  `~/defold/mineboom/tools/luals/`.

## Entrada

- **Um toque chega como mouse e como multitoque** se os dois estiverem ligados à mesma ação. No
  desktop só existe o mouse, então todo teste de desktop passa e o aparelho gasta duas ações por
  toque. Ligue só `MOUSE_BUTTON_LEFT` (o primeiro dedo vira mouse no celular).
- `action.x/y` não chegam em coordenada de projeto quando a janela escala; `gui.pick_node`
  respeita o ajuste. Converter por aritmética erra por escala.
- `gui.get_screen_position` e `gui.pick_node` **discordam** quando a janela não tem a resolução do
  projeto: toque sintetizado a partir da posição de um nó acerta **outro nó**, sem erro. No
  headless a janela é a do projeto e os dois coincidem.

## Mensagens, objetos e GUI

- `msg.post` é entrega no próximo despacho; ler estado logo depois lê o velho, sem erro.
- `msg.post` para URL que não existe só gera log, e `pcall` volta true. [relatório]
- Mensagem de objeto sendo deletado **atravessa a troca de fase** (`go.delete` só vale no fim do
  quadro). Guarda por época, não por registro.
- Nome de mensagem que colide com tipo do motor (`set_speed`, `restart`) engole o payload.
- `euler` e `position` são do **game object**, não do componente: `go.animate("#sprite", "euler.z")`
  estoura no `init` e o erro aparece longe, no primeiro uso do id nil.
- `gui.cancel_animations` é plural; o singular compila e estoura quando o caminho roda.
- `gui.set_parent` sem o terceiro argumento preserva o transform local.
- Na GUI criada em código, a **ordem de criação é a ordem de desenho**: crie em sequência, não
  dentro de um construtor de tabela.
- Limite de mensagem: 2 KiB. Tetos de instâncias, sprites e nós no `game.project`/`.gui`.

## Animação

- O segundo `go.animate`/`gui.animate` na mesma propriedade cancela o primeiro **e descarta o
  callback dele** — o que esperava o fim da animação nunca roda. [relatório]
- Pixel art com filtro `nearest` só amplia em fator inteiro; posição fracionária faz o contorno
  cintilar. Arredonde a posição ao pixel da arte.
- Fonte distance-field com CJK inteiro é enorme: gere `extra_characters` a partir dos textos e
  reprove fonte desatualizada no portão (glifo ausente vira quadrado sem log).

## Sorteio

- `math.random` deu a **mesma** sequência em LuaJIT e HTML5 [relatório]. Os problemas reais:
  estado global (qualquer chamada fora da regra desloca a sequência), semente padrão fixa e 15
  bits. Gerador próprio com estado: LCG de 32 bits com multiplicador < 2^21 fica exato em double
  em Lua 5.1, LuaJIT e 5.4+.

## Automation Bridge 2.5.0

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

## API HTTP do editor (1.13.2)

- Sem projeto aberto (tela de boas-vindas) o editor não sobe servidor HTTP: nenhuma porta
  escuta. Medido em 2026-10-10.
- Partida rodada pelo editor (Ctrl+B) não grava o console do motor em arquivo: o
  `editor2.<data>.log` só tem o log do editor. As linhas do jogo saem por `GET /console`
  (`{"lines": [...]}`).
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
- O console é zerado a cada `run`: leia `/console` depois do `run`, não guarde índice de linha
  de antes.
