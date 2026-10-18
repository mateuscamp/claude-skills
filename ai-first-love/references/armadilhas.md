# Armadilhas do LÖVE que o agente não vê

**Quase nada aqui foi medido no LÖVE.** Foi escrito lendo o fonte; o AppImage do b7daef0 entrou
na máquina em 2026-10-17, e só o marcado `[medido@b7daef0]` rodou nele (a R0.1 da reescrita do
CampCrawler, o boot, no mesmo dia). A wiki (love2d.org) responde 403 a
acesso automatizado. As armadilhas vêm da leitura do fonte, na tag `11.5` e no `main`, feita na
auditoria da troca Defold → LÖVE e conferida de novo no `main` (reescrita do CampCrawler,
2026-10-17). Cada item diz o sintoma, a causa e o remédio, e leva a citação, no formato que a
afirmação sobre o LÖVE pede em qualquer armadilha, `AGENTS.md`, skill ou anotação (é o mesmo que
o projeto cobra dele):

- `love:<caminho>:<linhas>@<sha7>`: lido no fonte do love2d/love naquele commit, com o caminho a
  partir da raiz do repositório. `@b7daef0` é o `main` de 2026-09-20 (12.0, codinome "Bestest
  Friend", não lançado); `@6eb8d54` é a tag `11.5` (2023-12-03), que é **pista** para o `main`;
  `[pista 11.5@6eb8d54]` é a leitura da 11.5 sem a linha anotada;
- `love-android:<caminho>:<linhas>@4c65fff` e `megasource:<caminho>:<linhas>@5118c13`: o mesmo no
  `main` do love-android (2026-07-25) e no megasource que ele fixa;
- `[medido@<sha7>]`: medido no LÖVE daquele commit, por um comando de `tools/` do projeto que
  grava o `exe=` do binário (no CampCrawler, o `tools/smoke.py`, desde a R0.1);
- `[lido: strings da liblove-12.0.so do lock]`: o Lua embutido no binário que roda (`boot.lua`,
  `callbacks.lua`, `arg.lua`, o `love.run` padrão), lido por `strings`, sem baixar o fonte;
- `[medido]`: medido nesta máquina **fora do LÖVE** (LuaJIT 2.1.1791988261, Lua 5.5.1, pacotes),
  com a versão e a data;
- `[lido: <fonte>]`: outra fonte nomeada (API do GitHub, AUR, AOSP, LuaCATS);
- `[inferido]`: dedução a partir do lido, sem leitura direta nem medida.

11.5, wiki e memória são pista: antes de afirmar algo do `main`, confira o `changes.txt`, o
`testing/tests/`, o wrap e o boot do pin, ou rode um caso mínimo. Uma citação vira
`[medido@<sha>]` quando um projeto reproduz o caso e grava o número. Este arquivo é a única casa
da citação e do número: o `SKILL.md` diz a regra e aponta o item, e a medida nova se escreve só
aqui. Medida que contradiz o lido reescreve a entrada, e o `SKILL.md` e o modelo que dependem
dela mudam na mesma frente. Antes de confiar num item em outro sha, reproduza. Esta lista cresce
com o uso: armadilha do LÖVE em que um projeto caiu e que ele resolveu entra aqui, com o número
medido; a que vale para jogo em qualquer engine entra em `gerais-de-jogo.md`, na raiz do
repositório das skills (seção Gerais, no fim).

## Versão e binário

- **O fato de início não consegue dizer qual LÖVE rodou.** `love.getVersion()` devolve
  `12, 0, 0, "Bestest Friend"`: nenhum sha entra no binário, e a linha do 12 diz `12.0` desde
  dez/2019 (157d763); a história do `main` traz ainda commits do ramo 11.x, com `11.5` no
  `version.h` (78e7c444, 2023), fundidos depois. Remédio: o pino mora num `runtime.lock` do
  repositório (sha, origem e sha256 de todo arquivo do runtime), e o fato de início leva o
  `love_sha=` do lock e o `exe=`, o sha256 do executável lido de dentro do processo, conferido
  contra o lock. `[love:src/common/version.h:28-34@b7daef0; love:src/modules/love/love.cpp:288-305@b7daef0; histórico: medido, gh api]`
- **Fixar só o LÖVE não fixa o jogo.** O AUR `love-git` compila a ponta do `main` sem sha, com
  `-DLOVE_USE_SDL3=YES`, e gera o executável `love-git`; ele usa o luajit, o sdl3 e o freetype2
  do sistema, que são rolling (aqui luajit 2.1.1791988261 e sdl3 3.4.18). O `love` 11.5-3 do
  pacman depende de `sdl2`, que nesta máquina é o sdl2-compat 2.32.74 sobre o SDL3. Um `-Syu`
  troca o intérprete ou a rasterização do texto sem ninguém pedir. O AppImage do CI embute as
  bibliotecas dele. Remédio: `source=...#commit=<sha>` no PKGBUILD; no lock, o sha256 do binário
  e da liblove (e, no AppImage, de toda a árvore extraída); no fato de início, `libs_fora=`, as
  bibliotecas do runtime (libluajit, libSDL3, libfreetype, libharfbuzz, libopenal) que o
  `/proc/self/maps` achou fora dele. Qual via, decide o autor; instalar pede o sim dele.
  `[lido: AUR love-git; medido: pacman -Q, luajit -v; /proc/self/maps: inferido]`
- **O `love` do PATH não é o do lock.** `love <pasta>` roda o binário que o PATH achar, com o
  `LD_LIBRARY_PATH` e o `LUA_PATH`/`LUA_CPATH` do shell, que o carregador e o `package` do
  LuaJIT leem calados. Remédio: o jogo só abre por um lançador do projeto (`tools/love`), que
  confere o lock, limpa `LD_*` e `LUA_*`, roda o binário do runtime direto e põe a pasta antes
  dos argumentos; a passada exige o `exe=` do lock. `[inferido]`
- **A API muda entre commits.** Entre o pino do love-android (love@792690b, 2026-07-24) e o
  b7daef0 há 34 commits em dois meses, de gráficos, Vulkan, webp, áudio e `File:read`. Remédio:
  trocar de sha é rodar o portão inteiro e ler o diff de `boot.lua`, `callbacks.lua`, `arg.lua`
  e `event/` antes; a lista da API sai do binário do lock (um dump de `love.*` rodado por ele), e
  o diff de pinos é o diff das listas. `[lido: gh api compare 792690b...b7daef0]`
- **O LuaJIT do AppImage não é o da máquina, e o `LD_LIBRARY_PATH` troca as cinco.** A árvore
  extraída (`--appimage-extract`) roda sem FUSE e com `env -i`: `bin/love` e a liblove têm
  RUNPATH `$ORIGIN/../lib`. O LuaJIT dela é o 2.1.1788856981, e o do sistema, 2.1.1791988261: a
  suíte não roda o Lua do jogo. Um `LD_LIBRARY_PATH=/usr/lib` vence o RUNPATH, e as cinco do
  runtime vêm do sistema (`libs_fora=5`, `jit=` do sistema). Remédio: o lançador limpa `LD_*` e o
  `INICIO` leva `libs_fora=` e `jit=`, cobrados. `[medido@b7daef0; RUNPATH: readelf -d; bibliotecas: /proc/self/maps]`
- **O binário do CI some.** O artefato `love-linux-X64.AppImage` da run do b7daef0 expira em
  2026-12-19, e baixá-lo pede o gh autenticado. Remédio: se essa for a fonte, guarde a cópia
  fora do repositório, com o sha256 no lock (baixar pede aprovação). `[lido: gh api actions/runs]`

## Lançamento e argumentos

- **Um `--x` antes da pasta vira o caminho do jogo.** O primeiro argumento que não é opção
  conhecida, inclusive um `--config=...`, é tomado como o jogo; o LÖVE para na tela "Cannot load
  game at path" esperando um quit, e a passada só cai pelo prazo. Remédio: o lançador põe a
  pasta (ou o `.love`) logo depois das opções do LÖVE, ou `--` antes dela, e tem teste da ordem.
  `[love:src/modules/love/arg.lua:128-158@b7daef0; pista 11.5@6eb8d54]`
- **Opção do LÖVE depois da pasta também é comida.** O laço do `parseOptions` segue depois do
  jogo: `--console`, `--fused`, `--game`, `--renderers X` e `--excluderenderers X` em qualquer
  ponto antes de um `--` são do LÖVE, e o jogo nunca os recebe no `love.load`. Remédio: chave do
  jogo só na forma `--config=<projeto>.<chave>=<valor>`, que não casa nenhuma opção.
  `[love:src/modules/love/arg.lua:104-158@b7daef0; efeito no jogo: inferido]`
- **Os índices do `args` não começam onde parece.** O `love.load` recebe os argumentos do jogo
  sem as opções que o LÖVE consumiu, com o executável e o que vem antes nos índices ≤ 0 e os do
  jogo a partir de 1. Remédio: o parser percorre de 1 a `#args`, recusa argumento solto e tem
  teste com o argv como tabela. `[inferido: love:src/modules/love/arg.lua:160-174@b7daef0]`
- **Pasta ou `.love` sem `main.lua` na raiz cai no handler de erro.** O boot estoura
  `No code to run` ("Your game might be packaged incorrectly"), e o caminho que não existe,
  `Cannot load game at path`; os dois vão ao handler, e o padrão abre a tela de erro. Remédio: o
  executor das passadas recusa as duas linhas. Medido: a linha é
  `Error: [love "boot.lua"]:452: No code to run at <caminho do jogo>`, e sob Xvfb o padrão espera na tela de erro
  até o prazo; sem o `setvbuf` do `conf.lua` (que ali não existe), o SIGKILL leva tudo: 0 linhas.
  `[love:src/modules/love/boot.lua:448-455,507-516@b7daef0; medido@b7daef0]`
- **`t.version` de outra versão prende a passada numa caixa modal.** Depois do `conf.lua` e antes
  do `main.lua`, o boot compara `t.version` com a lista de compatíveis, que no `main` é só
  `"12.0"`; fora dela, imprime "This game indicates it was made for version ..." e, com o módulo
  window, abre `showMessageBox("Compatibility Warning")`, que sob Xvfb espera até o SIGKILL.
  Código vindo da 11.5 traz `t.version = "11.5"`. Remédio: `t.version` igual ao pin, e o executor
  recusa `^This game indicates`. `[love:src/modules/love/boot.lua:379-391@b7daef0; love:src/common/version.h:33@b7daef0; trava sob Xvfb: medido@b7daef0, a linha saiu e a passada ficou presa até o prazo]`
- **A prova toca som.** O áudio do LÖVE é o OpenAL Soft, que lê `ALSOFT_DRIVERS`; com
  `ALSOFT_DRIVERS=null` no ambiente, a passada e a captura rodam mudas. Remédio: o executor monta
  o ambiente por lista branca, com a variável nela. `[inferido: variável do OpenAL Soft, não lida pelo LÖVE]`
- **`require` ausente acha o arquivo no diretório atual.** O loader do LÖVE fica no searcher 2,
  e o `package.path` do Lua, com `./?.lua`, vem depois: a passada rodada da raiz do projeto
  aprova um módulo que o `.love` não leva, e o aparelho quebra ao abrir. Remédio: o `main.lua` e
  cada thread zeram `package.path` (salvo uma via declarada e medida), `package.cpath` e
  `love.filesystem.setCRequirePath`, e uma passada roda o `.love` gerado com o diretório atual
  numa pasta vazia fora da worktree; dado de jogo lido por `love.filesystem`.
  `[love:src/modules/filesystem/wrap_Filesystem.cpp:897-929@b7daef0; pista 11.5@6eb8d54]`
- **`require("a/b")` desenha um aviso na tela.** No `main`, require com `/` está deprecado
  (aviso descrito em "Saída, erro e log"). Remédio: `require("a.b")`.
  `[love:src/modules/filesystem/wrap_Filesystem.cpp:1122-1124@b7daef0; love:changes.txt:114@b7daef0]`
- **A identidade vem do alvo do symlink.** O caminho do jogo passa por
  `std::filesystem::weakly_canonical`, e a identidade padrão sai da folha do alvo: a pasta do
  jogo que é symlink grava o save em outro nome. Se o LÖVE segue um symlink de dentro do jogo
  para fora dele (um `modules/` emprestado de outro repositório), ainda não foi medido.
  Remédio: `t.identity` sempre no `conf.lua`; medir o symlink no esqueleto, e a alternativa lida
  é `love.filesystem.mountFullPath(caminho_absoluto, ponto, [permissão])`.
  `[love:src/modules/filesystem/physfs/Filesystem.cpp:153-164,259-350,421-454@b7daef0; seguir para fora: inferido]`

## Saída, erro e log

- **O SIGKILL leva a cauda do log e o próprio erro.** Com a saída num arquivo ou num pipe, o
  `print` fica em buffer de bloco; a passada que estoura o prazo mata o processo e perde tudo,
  inclusive o texto do erro. No LuaJIT da máquina: 0 bytes sem buffer de linha, 39 com.
  Remédio: `io.stdout:setvbuf("line")` na primeira linha do `conf.lua` (ele roda antes do
  `main.lua`), cobrado por passada. `[medido: LuaJIT 2.1.1791988261, fora do LÖVE; ordem conf → main: love:src/modules/love/boot.lua:250,444@b7daef0]`
- **O SIGTERM do prazo sai com 0.** O SDL3 troca SIGTERM e SIGINT por `SDL_EVENT_QUIT`, o LÖVE o
  entrega como `quit` sem argumento, e o `love.run` padrão devolve `a or 0`: a passada morta
  pelo prazo termina com o código de quem acabou o plano. Remédio: só o fato de fim do plano
  (`FIM`), num lugar só, chama `love.event.quit(0)`; o `love.run` do projeto devolve um código
  próprio para quit sem `FIM`; o executor reprova prazo e morte por sinal, qualquer que seja o
  código. `[love:src/modules/event/sdl/Event.cpp:566-568@b7daef0; love:src/modules/love/callbacks.lua:180-183@b7daef0; SIGTERM vira quit: medido@b7daef0, o love.run do projeto devolveu o código do quit sem FIM ao SIGTERM aos 2 s]`
- **O handler de erro padrão trava sob Xvfb.** O `love.errorhandler` (o `love.errhand` é
  apelido) imprime `Error: <msg>` e o traceback, e então:
  - sem o módulo window, retorna, e o processo sai com 1;
  - com window, mas sem graphics ou event, ou se o `setMode(800, 600)` falha, abre
    `love.window.showMessageBox("Initialization error", ...)`, **modal**, que sob Xvfb espera
    até o SIGKILL (na 11.5 retornava);
  - com a janela fechada e graphics carregado, abre a janela e a tela azul de erro, que espera
    Escape (sai com 1) ou quit (`a or 1`).

  Remédio: um `love.errorhandler` nosso, atribuído antes de qualquer `require`, que imprime o
  traceback e grava no arquivo da partida. Devolver `nil` termina o laço do boot e sai com 1;
  devolver `function() return 3 end` sai com 3, e o portão distingue erro de Lua de quit (o erro
  plantado no `conf.lua` tem de sair com 3, não com 1). Passada sem janela desliga também
  `t.modules.window`. `[love:src/modules/love/callbacks.lua:217-352@b7daef0; love:src/modules/love/boot.lua:462-521@b7daef0; código de saída do handler nosso: medido@b7daef0, 3 com o erro plantado antes do love.conf]`
- **O erro do `conf.lua` depois do `function love.conf` some.** O `love.init` faz
  `pcall(require, "conf")` e, se `love.conf` existe, `pcall(love.conf, c)`, que sobrescreve o
  `confok, conferr` do primeiro: o erro de qualquer linha depois da definição se perde, e o jogo
  abre como se nada fosse. Antes dela, o erro chega ao handler com o prefixo
  `[love "boot.lua"]:395: ` na mensagem. Remédio: o `love.conf` é o último comando do `conf.lua`,
  cobrado por teste, e o `--erro-esperado` do erro de conf aceita o prefixo.
  `[lido: love.init nas strings da liblove-12.0.so do lock; medido@b7daef0: error() plantado depois do love.conf, passada aprovada; antes dele, saída 3]`
- **O handler definido no `main.lua` chega tarde.** O `main.lua` é carregado dentro do
  `love.init`, depois dos módulos, da janela e da caixa de versão; erro num `require` do topo
  dele, antes da linha que atribui o handler, cai no padrão. O erro do `conf.lua` é relançado
  depois de carregar os módulos, então um handler definido no próprio `conf.lua` já o pega; o
  padrão já existe ali (o boot carrega o `callbacks.lua` antes), e o nosso pode delegar a ele.
  Falha no `love.boot` imprime e sai com 1, sem handler nenhum. Remédio: handler e buffer de
  linha nas primeiras linhas do `conf.lua`. `[love:src/modules/love/boot.lua:30,250,395,444,462-521@b7daef0; handler do conf.lua pegar: inferido]`
- **O aviso de deprecação entra na captura, e ligado tarde não imprime.** Cada API deprecada
  imprime `LOVE - Warning: ...` na primeira chamada e desenha, dentro do `present()`, uma caixa
  no canto de baixo com até quatro avisos por 20 s de relógio; ela sai no `captureScreenshot` e
  estraga a amostra de pixel. O boot faz `love.setDeprecationOutput(not fused)`: no modo fundido
  nada imprime nem desenha. Ligar depois só imprime a deprecada usada uma vez até ali: a usada
  duas vezes antes nunca imprime, e a caixa mostra todas. Disparam: `require` com `/`,
  `love.graphics.newText`, `Texture:newImageData`, `t.renderers` no topo do `conf` e o
  `love.data.hash(função, dado)` de dois argumentos (vale `love.data.hash("string", função,
  dado)`; o aviso diz "replaced by variant with container return type parameter" [medido@b7daef0]:
  a sonda manual fundida, sem a deprecação religada, não o via; a passada o recusou). Remédio:
  a passada roda no modo (fundido ou não) do autor, com `love.setDeprecationOutput(true)` no topo
  do `conf.lua` quando a variável da passada está posta, e o executor recusa
  `^LOVE - Warning: `. `[love:src/modules/love/boot.lua:96,283-289@b7daef0; love:src/common/deprecation.cpp:69-92,146-190@b7daef0; love:src/modules/graphics/Deprecations.cpp:45-90@b7daef0]`
- **A captura que falha não dá erro.** Se a codificação ou a gravação do `captureScreenshot`
  falha, sai só um `printf` sem `\n` ("Screenshot encoding or saving failed"), e o Lua não
  recebe nada. Remédio: a prova confere que o arquivo existe, ou usa a variante com função, que
  recebe o `ImageData`. Não há captura sem janela. `[love:src/modules/graphics/wrap_Graphics.cpp:484@b7daef0; sem janela: love:src/modules/graphics/opengl/Graphics.cpp:1217-1218,1255@b7daef0 e love:src/modules/graphics/Graphics.cpp:814-820@b7daef0; buffer: inferido]`
- **No Android, só o `print` chega ao logcat.** O `print` é trocado por um que chama
  `SDL_Log("[LOVE] %s")`; `io.write` e `io.stdout` não vão para o logcat, e a linha longa demais
  se corta (o logger do Android carrega ~4 KB por entrada). Remédio: fato e erro por `print`, o
  emissor de fatos estoura acima de 4.000 B, o leitor do aparelho tira o `[LOVE] ` antes de
  cobrar (`adb logcat -v raw -s SDL/APP:I`), e o arquivo da partida vem por `adb pull`.
  `[love:src/modules/love/love.cpp:255-283,559-560@b7daef0; io.write, corte e etiqueta SDL/APP: inferido]`

## Laço, tempo e janela

- **O primeiro quadro da volta traz todo o tempo em segundo plano.** O `love.run` padrão passa
  `love.timer.step()` sem teto. No Android o jogo para em segundo plano (o gráfico fica
  inativo e o `love.draw` não roda); no desktop ele segue rodando minimizado. O Defold cortava
  em 1/30 s. Remédio: `love.run` nosso, com teto de dt e descarte do quadro de volta, e o tempo
  de run contado pelo dt já cortado. O sinal da volta se mede no aparelho: o
  `DID_ENTER_BACKGROUND` e o `WILL_ENTER_FOREGROUND` só mexem no `love.graphics.isActive()`
  (nenhum callback), e os callbacks `visible` e `focus` vêm de eventos de janela. Se o laço
  ficar parado em segundo plano, a transição do `isActive` de falso para verdadeiro pode nem ser
  vista. `[love:src/modules/love/callbacks.lua:94-101,168-206@b7daef0; love:src/modules/timer/Timer.cpp:58-83@b7daef0; love:src/modules/event/sdl/Event.cpp:89-97,777-803@b7daef0; laço parado e sinal: inferido]`
- **Um quadro roda dentro do outro no redimensionar.** O boot registra a função devolvida pelo
  `love.run` (o laço inteiro: eventos, update e desenho) como callback de desenho modal, e o
  SDL a chama de dentro do `love.event.pump` durante o live-resize: update, robô e contador de
  quadro rodam reentrantes. E o callback que devolve um valor vira quit. Remédio:
  `love.event.setModalDrawCallback(f)`, que tem prioridade sobre o padrão, com um `f` que só
  redesenha a lista apresentada e não devolve nada. `[love:src/modules/love/boot.lua:507-518@b7daef0; love:src/modules/event/sdl/Event.cpp:100-104@b7daef0; love:src/modules/event/Event.cpp:108-130@b7daef0; love:src/modules/event/wrap_Event.cpp:160-219@b7daef0]`
- **Recarregar reabre o Lua inteiro.** `love.event.restart(v)` (novo no 12) empurra
  `quit("restart", v)`; o `love.run` devolve `"restart"`, e o executável fecha o estado Lua e
  abre outro, com `v` em `love.restart` (valor simples: objeto do LÖVE não passa). Nada sobrevive
  senão `v`, e o código de saída do `love.run` nosso deixa o `"restart"` passar. Remédio: o estado
  volta pelo replay; troca de módulo a quente (lurker) é dependência nova. Qual dos dois, decide
  o autor. `[love:src/modules/event/wrap_Event.cpp:138-152,254@b7daef0; love:src/love.cpp:247-290@b7daef0]`
- **A janela não redimensiona, e o `updateMode` não prova o redimensionar.** `resizable` vem
  `false`. Na 11.5 o `updateMode` fecha e recria a janela, esvazia os eventos de janela e não
  dispara `love.resize`; Canvas e cache de glifos somem. No `main`, com a janela aberta,
  `setMode` e `updateMode` não recriam: chamam `SDL_SetWindowSize`, `SDL_SetWindowResizable` e
  `SDL_SyncWindow` sem esvaziar eventos, e o `love.resize` pode passar a sair (o TODO do código
  fala nele). Remédio: `resizable = true`, em `t.window` ou, com `t.window = false` (o boot só
  abre a janela com `t.window` e o módulo window), nos flags do `setMode` com que a plataforma a
  abre no `love.load`, depois do parser; e o redimensionar provado pelo gerenciador de janelas
  (xdotool sob Xvfb), não pelo `updateMode`; medir no esqueleto se o `updateMode` dispara.
  `[love:src/modules/window/sdl/Window.cpp:565-588,696,724-726@b7daef0; love:src/modules/love/boot.lua:194,398-426@b7daef0; pista 11.5@6eb8d54; disparar: inferido]`
- **`love.resize` chega em unidades de DPI**, a partir do `SDL_EVENT_WINDOW_PIXEL_SIZE_CHANGED`,
  e é seguido de um `collectgarbage`; misturar `getPixelDimensions` (ou o tamanho da janela do
  sistema) com as coordenadas de entrada erra pela escala. Remédio: uma unidade em toda a
  cadeia (layout, lista, hit-test, robô, amostra, adb). Ou a de `love.graphics.getDimensions`,
  com o pixel só na amostra e no adb, convertido por `getDPIScale` com teste; ou o pixel em tudo,
  com `usedpiscale = false` (em `t.window` ou nos flags do `setMode`), que muda o tamanho do que
  se vê em tela de alta densidade e por isso é proposta que o autor julga pela captura, no
  backend dele.
  `[love:src/modules/event/sdl/Event.cpp:811-837@b7daef0; love:src/modules/love/boot.lua:196,422@b7daef0; mistura: pista 11.5 + inferido]`
- **O toque do adb cai em outra célula.** Com `usedpiscale` (o padrão, ainda `true` no `main`),
  dimensões, mouse e toque chegam em unidades de DPI: um 1080×2400 com escala 2,75 vira ~393×873.
  O `adb shell input tap` é em pixel físico: calculado a partir dos fatos do jogo, toca a 2,75×
  do ponto. Remédio: o fato `JANELA` leva `love.window.getDPIScale()` e as duas unidades, e a
  conversão do adb tem teste (ou a unidade única do item de cima).
  `[love:src/modules/love/boot.lua:196@b7daef0; pista 11.5@6eb8d54; números do aparelho: inferido]`
- **O portão e o autor rodam renderers diferentes.** No Linux a ordem padrão é Vulkan, depois
  OpenGL; o Vulkan de CPU (lavapipe) tem nota 0 sem a variável
  `LOVE_GRAPHICS_VULKAN_ALLOW_SOFTWARE`. Assim, Xvfb com llvmpipe cai no OpenGL, e a GPU do
  autor sobe em Vulkan. Mínimo: GL 3.3 ou GLES 3.0. Remédio: o fato de início leva
  `love.graphics.getRendererInfo()`, e a saída é do autor (escolher renderer por hipótese não
  vale): uma passada ou captura no renderer dele, ou o OpenGL fixo nos dois
  (`t.graphics.renderers = { "opengl" }`, nunca o `t.renderers` do topo, deprecado; ou
  `--renderers opengl` antes da pasta). `[love:src/modules/graphics/Graphics.cpp:118-135@b7daef0; love:src/modules/graphics/vulkan/Graphics.cpp:1806-1809@b7daef0; love:src/modules/window/sdl/Window.cpp:252-283@b7daef0; love:src/modules/love/boot.lua:283-289@b7daef0; Xvfb no OpenGL e GPU do autor no Vulkan: inferido]`
- **Não há LÖVE sem janela para desenhar.** `RENDERER_NONE` é só sentinela, e a criação
  estoura "Cannot create graphics: no supported renderer". Dezesseis construtores de
  `love.graphics` estouram "love.graphics cannot function without a window.": `newCanvas`,
  `newTexture` (e o apelido `newImage`), `newCubeTexture`, `newArrayTexture`, `newVolumeTexture`,
  `newQuad`, `newFont`, `newImageFont`, `newSpriteBatch`, `newParticleSystem`, `newShader`,
  `newBuffer`, `newMesh`, `newTextBatch` (e `newText`), `newVideo` e `getFont`. Remédio: a vista
  não cria objeto de `love.graphics` (a lista é dado); a passada sem vídeo confere PNG e fonte por
  `love.image` e `love.font`, com tamanho, DPI e área segura injetados; a de tela roda sob Xvfb, e
  o driver `offscreen` do SDL3 (`SDL_VIDEO_DRIVER=offscreen`, EGL/GLES e Vulkan) é candidato a
  passada sem X, por medir. O CI do próprio LÖVE roda a suíte dele sob Xvfb com openbox.
  `[love:src/modules/graphics/wrap_Graphics.cpp:56-60@b7daef0; love:src/modules/graphics/Graphics.h:69-75@b7daef0; love:src/modules/graphics/Graphics.cpp:165-207@b7daef0; love:.github/workflows/main.yml:64-124@b7daef0; offscreen funcionar: inferido]`
- **Wayland do autor, X11 da prova.** Com SDL3, o LÖVE tende a abrir em Wayland nativo, e toda
  prova roda em X11. Remédio: uma passada no backend do autor, ou forçar o mesmo nos dois; a
  passada declara o vídeo dela (`SDL_VIDEO_DRIVER` explícito, nunca herdado). `[inferido]`

## Entrada

- **O dedo chega duas vezes.** Com o SDL3, `SDL_HINT_TOUCH_MOUSE_EVENTS` vale 1 (o LÖVE só mexe
  em `TRACKPAD_IS_TOUCH_ONLY` e `JOYSTICK_ALLOW_BACKGROUND_EVENTS`): o dedo gera primeiro o
  mouse sintético (`mousemoved`, depois `mousepressed` com `istouch = true`) e só então
  `touchpressed`; só o primeiro dedo vira mouse. Um filtro por sequência conta duas vezes, e o
  movimento sintético dobraria uma métrica de deslocamento. Remédio: só `mousepressed` do botão
  1, `touch*` ignorado, com um teste da suíte sobre a ordem gravada no aparelho e no desktop
  (até a gravação, a ordem lida aqui, com a citação no nome do teste). `[love:src/modules/event/sdl/Event.cpp:354-442@b7daef0; megasource:libs/SDL3/src/events/SDL_touch.c:342-405@5118c13; megasource:libs/SDL3/src/events/SDL_mouse.c:127-169@5118c13; o padrão do SDL2 na 11.5 não foi conferido]`
- **O mouse de verdade no Android vira toque.** `SDL_HINT_MOUSE_TOUCH_EVENTS` vale 1 no Android
  e no iOS (0 no desktop): mouse físico, DeX, Chromebook ou mouse do adb gera também
  `touchpressed` com o 8º argumento `mouse = true`. Remédio: o mesmo contrato (`touch*`
  ignorado); código que um dia tratar toque filtra `mouse = true`. `[love:src/modules/love/callbacks.lua:55-56@b7daef0; megasource:libs/SDL3/src/events/SDL_mouse.c:159-169@5118c13]`
- **`love.event.push` para no primeiro `nil`.** Os argumentos são guardados até o primeiro
  `nil`: `push("mousepressed", x, y, 1, nil, 1)` perde o `presses`. Valor que não é booleano,
  número, string ou userdata estoura. Remédio: o robô passa a tupla inteira, com `false`, nunca
  `nil`. `[love:src/modules/event/wrap_Event.cpp:90-115@b7daef0]`
- **O evento empurrado não passa pela conversão nem mexe no estado do mouse.** O `push` põe na
  mesma fila (deque com mutex) que o `pump` enche pelo SDL, e o `love.run` despacha tudo pelos
  mesmos `love.handlers`; o empurrado no `update` do quadro N sai no N+1, e o empurrado antes do
  `pump` sai no mesmo quadro. Ficam de fora a conversão (`clampToWindow`, `windowToDPICoords`) e
  o estado: `love.mouse.getPosition`, `isDown` e `love.touch.getTouches` não mudam, e o ponto
  fora da janela entra como veio. Remédio: o robô empurra na unidade da lista, com o ponto preso
  na janela, lê o efeito pelo fato, e nada do jogo lê `love.mouse` nem `love.touch`.
  `[love:src/modules/event/Event.cpp:57-90@b7daef0; love:src/modules/event/sdl/Event.cpp:50-70,127-209,342@b7daef0; ordem no quadro: inferido; estado: pista 11.5 + inferido]`
- **`love.handlers` estoura com evento desconhecido** (`Unknown event: <nome>`): robô que empurra
  nome errado cai alto, o que é bom. Callback novo do 12 (`exposed`, `occluded`,
  `localechanged`, `dropbegan`, `sensorupdated`, `audiodisconnected`, `themechanged`) chega sem
  ninguém pedir. Remédio: não troque a metatable por uma que engole; trate só o que o jogo usa.
  `[love:src/modules/love/callbacks.lua:27-162@b7daef0]`
- **O `adb shell input tap` é um dedo só, instantâneo.** Fonte touchscreen, DOWN e UP com o
  mesmo timestamp, `pointerCount = 1` fixo; `input swipe x y x y 300` é o toque longo; multitoque
  fica com a mão do autor. `[lido: AOSP InputShellCommand.java]`

## Arquivos e save

- **Cada worktree grava num save diferente.** Sem `t.identity`, a identidade é a folha do
  diretório real do `main.lua`; a pasta só nasce na primeira escrita. Remédio: `t.identity`
  fixo no `conf.lua` e a pasta criada no início. `[love:src/modules/love/boot.lua:136-150,440-442@b7daef0; love:src/modules/filesystem/physfs/Filesystem.cpp:357-376@b7daef0]`
- **A save sombreia o código.** Com `t.appendidentity = false`, o padrão, a pasta de save entra
  no caminho de busca **antes** do jogo: um arquivo na save com o nome de um módulo ou de um
  asset (`modules/x.lua`, `assets/a.png`) é o que o `require` e o `love.filesystem` carregam,
  calado. Só o `conf.lua` escapa (o boot o lê com a save depois). Remédio:
  `t.appendidentity = true`, e ferramenta nunca escreve na save real: a passada aponta o
  `XDG_DATA_HOME` para um `mktemp -d` e exige o `save=` e o `log=` dentro dele.
  `[love:src/modules/love/boot.lua:150,231,442-444@b7daef0; love:src/modules/filesystem/physfs/Filesystem.cpp:181,227-233@b7daef0; append falso põe antes: inferido do PHYSFS_mount]`
- **O save muda de lugar com o modo fundido.** No Linux, fora do modo fundido:
  `$XDG_DATA_HOME/love/<id>` (ou `~/.local/share/love/<id>`); fundido (`love --fused <pasta>` ou
  executável com zip anexado): `~/.local/share/<id>`. No Android (`main`): armazenamento interno
  (externo com `t.externalstorage`) + `/save/` + `<id>` no APK embutido ou `love/<id>` fora
  dele, criado na primeira escrita (na 11.5, `save/<id>` criado já no `setIdentity`). Remédio: o
  código nunca decide por `isFused()`, e a passada roda no modo do autor.
  `[love:src/modules/filesystem/physfs/Filesystem.cpp:181-252,582-745@b7daef0; love:src/modules/filesystem/Filesystem.h:38-52@b7daef0; pista 11.5@6eb8d54]`

## Texto e fonte

- **Sem janela não há quebra de linha do LÖVE.** O `love.font` não pede janela, mas o
  `Rasterizer` só tem `getHeight`, `getAdvance`, `getAscent`, `getDescent`, `getLineHeight`,
  `getGlyphData`, `getGlyphCount` e `hasGlyphs`: nem `getWrap` nem kerning. `Font:getWrap` só
  existe por `love.graphics`. Remédio: medidor injetado na vista; o da suíte é nosso, sobre os
  avanços, e devolve um intervalo `[inf, sup]` com a folga medida (a moldagem do HarfBuzz afasta
  a largura real da soma): afirma "cabe" só com `sup` ≤ limite e "não cabe" só com `inf` >
  limite; a medida de verdade é da passada com janela. `[love:src/modules/font/wrap_Rasterizer.cpp:129-136@b7daef0; love:src/modules/font/wrap_Font.cpp:241-245@b7daef0; diferença da soma: inferido]`
- **A largura do texto muda de versão.** O TrueType passa a ser moldado pelo HarfBuzz
  (kerning e combinação melhores), e a fonte padrão passa de Vera 12 a Noto Sans 13. Nenhuma
  expectativa de largura vinda do Defold ou da 11.5 transfere. Remédio: nunca a fonte padrão; a
  largura cobrada vem da passada com janela no sha fixado. `[love:src/modules/graphics/wrap_Font.cpp:273-286@b7daef0; love:src/modules/font/freetype/TrueTypeRasterizer.cpp:228-231@b7daef0; love:changes.txt:88-89@b7daef0]`
- **Japonês e chinês quebram em qualquer caractere.** A quebra volta ao caractere logo depois
  do último `' '` ou `'\t'`; sem espaço, quebra no caractere que estoura, e se ele é o primeiro
  da linha fica sozinho nela (na 11.5 era descartado). Sem kinsoku nem UAX#14, e U+3000 não
  conta como espaço: a pontuação pode abrir linha. Quem julga é o autor, pela captura.
  `[love:src/modules/font/GenericShaper.cpp:149-209@b7daef0; love:src/modules/font/freetype/HarfbuzzShaper.cpp:375-450@b7daef0; love:src/modules/graphics/Font.cpp:815-870@6eb8d54]`
- **Glifo ausente não avisa.** TTF e OTF desenham a caixa `.notdef`, sem log, e com
  `Font:setFallbacks` o glifo que falta na primeira cai calado noutra fonte, com outra métrica.
  Remédio: uma fonte por escrita (o idioma escolhe), sem fallback, e o portão confere a
  cobertura de todo texto da tabela de idiomas contra o `cmap` dela e com `hasGlyphs`, também
  pelo `Rasterizer`, sem janela. `[pista 11.5@6eb8d54; hasGlyphs no main: love:src/modules/font/wrap_Rasterizer.cpp:129-136@b7daef0; fallback calado: inferido]`
- **SDF sem shader, e a opção errada é ignorada.** `love.graphics.newFont(arq, tam, { sdf = true })`
  (ou `love.font.newRasterizer`) liga o `FT_RENDER_MODE_SDF` e volta ao normal calado se falhar;
  as opções se leem pelo nome exato (`hinting`, `dpiscale`, `sdf`), e `{ SDF = true }` vira fonte
  comum sem aviso. Não achei shader de SDF embutido, então o desenho e o contorno pedem shader
  nosso; não há opção de contorno. Remédio: o modo de fonte se prova pelo glifo (a margem do
  `GlyphData` do SDF), não pela opção. `[love:src/modules/font/wrap_Font.cpp:67-104@b7daef0; love:src/modules/font/freetype/TrueTypeRasterizer.cpp:115-140@b7daef0; precisar de shader e a margem: inferido]`
- **`newText` dispara o aviso de tela.** O tipo agora é `TextBatch` (`newTextBatch`); `newText`
  é apelido deprecado. `[love:src/modules/graphics/wrap_Graphics.cpp:2343-2347,4069,4200@b7daef0]`

## Gráficos e pixel

- **Cor de 0 a 255 não estoura.** Desde a 11.0 toda cor é de 0 a 1; o `setColor(255, 0, 0)`
  vindo de código antigo ou de memória satura em branco ou vermelho puro, sem erro. Remédio: o
  construtor da lista estoura cor fora de [0, 1] com o recebido. `[love:changes.txt:448@b7daef0; saturar: inferido]`
- **`Canvas:newImageData` dispara o aviso.** O Canvas virou `Texture` (`isCanvas`), e a leitura
  é `love.graphics.readbackTexture(tex, ...)`, que devolve `ImageData` (e `readbackTextureAsync`);
  `Texture:newImageData` está deprecado. `ImageData:getPixel` continua sendo a amostra.
  `[love:src/modules/graphics/wrap_Graphics.cpp:2411-2449,4074-4075@b7daef0]`
- **A captura é em pixel, com alfa 255 e o aviso por cima.** O `captureScreenshot` enfileira e
  captura dentro do `present()`, depois do `love.draw` e do aviso de deprecação: `glReadPixels`
  do backbuffer, RGBA8, alfa forçado a 255, origem no alto à esquerda, em pixels
  (`getPixelWidth`). Remédio: a amostra converte o retângulo do item para pixel, compara pela
  medida do `kind` (SKILL, seção 3, Amostra de pixel) e só vale sem aviso na saída.
  `[love:src/modules/graphics/wrap_Graphics.cpp:508-558@b7daef0; love:src/modules/graphics/opengl/Graphics.cpp:1215-1320@b7daef0]`
- **Fonte guardada fora de um dono vaza.** Cada `newFont` é um objeto de GPU, e um cache por
  vista cresce a cada troca de idioma ou de tamanho. Remédio: um módulo de plataforma só cria,
  guarda (por escrita, papel e px) e libera fontes, com teto; o render recebe a fonte pelo
  argumento (`print(texto, font, x, y)`), nunca por `setFont`; e o `getStats().fonts` é igual ao
  tamanho do cache. `[love:src/modules/graphics/wrap_Graphics.cpp:3206-3231@b7daef0; crescer: inferido]`
- **Shader e mipmap que só quebram no aparelho.** Na 11.5, o desktop compila GLSL `#version 120`
  e o Android GLSL ES 100 com `mediump`; em GLES2 sem NPOT, o mipmap de PNG NPOT é descartado sem
  aviso. O `main` pede GL 3.3 ou GLES 3.0 (o manifesto do love-android exige GLES 3.0), e o que
  vale para shader nele ainda não foi lido. Remédio: todo shader novo (contorno, SDF) e todo
  mipmap entram com prova no aparelho. `[pista 11.5@6eb8d54; love:src/modules/window/sdl/Window.cpp:252-283@b7daef0; love-android:app/src/main/AndroidManifest.xml:11@4c65fff]`

## Rede, licença e terceiros

- **O jogo abre rede sem dependência nova.** O runtime pré-carrega `socket` (luasocket), `enet`
  e `https`, e `love.system.openURL` abre o navegador: "nenhuma biblioteca nova" não quer dizer
  "sem rede". Remédio: um teste reprova `socket`, `https`, `enet`, `package.loadlib` e `openURL`
  em todo `.lua` do `.love`; rede e telemetria são decisão do autor.
  `[love:src/modules/love/love.cpp:654-665@b7daef0; love:src/modules/system/wrap_System.cpp:90-93,134@b7daef0]`
- **O portão que depende da rede não avisa.** Uma ferramenta que baixa (o runtime, a anotação,
  uma fonte) passa enquanto houver rede e falha no dia em que o artefato expira. Remédio: o
  portão e o `--rapido` se relançam em `unshare --user --map-current-user --net`, leem
  `/proc/self/net/dev` e reprovam interface além de `lo` ou passo pulado; baixar é só uma
  ferramenta de preparo, fora do portão e com o sim do autor. Nesta máquina o namespace sobe sem
  root e só com `lo`. `[medido: util-linux 2.42.4, 2026-10-17; o LÖVE e o Xvfb dentro dele: inferido]`
- **Licenças que o artefato carrega.** O LÖVE é zlib; o pacote leva OpenAL Soft (LGPL), LuaJIT,
  FreeType, HarfBuzz e outros; o `main` tirou o mpg123 (dr_mp3). Remédio: um registro único de
  terceiros (`CREDITS.md`: SPDX, onde está, obrigação), que todo terceiro do artefato e do fonte
  fixado casa; SPDX fora da lista que o autor aprovou só com decisão dele, e cabeçalho de
  terceiro fora de `vendor/` reprova. Quando a LGPL entra e como, decide o autor.
  `[pista 11.5@6eb8d54; love:CMakeLists.txt:106-107,186-192@b7daef0]`

## Android

- **O README do love-android está velho.** Ele pede JDK 17, SDK 34 e NDK 26.1; vale o
  `build.gradle`: AGP 9.3.1, Gradle wrapper 9.5.0, Java 17 no CI, `compileSdk` e `targetSdk` 35,
  `minSdk` 23, NDK 27.3.13750724, CMake 3.21+, ABIs armeabi-v7a, arm64-v8a e x86_64. O APK com o
  jogo sai de `./gradlew assembleEmbedNoRecordRelease` e o AAB de `bundleEmbedNoRecordRelease`
  (`assembleNormalRecord` é o carregador genérico, sem jogo); o jogo vai em
  `app/src/embed/assets/` (pasta com `main.lua`, ou `game.love`). No `gradle.properties`:
  `app.application_id`, `app.orientation`, `app.version_code`, `app.version_name`, e `app.name`
  **ou** `app.name_byte_array`, nunca os dois. `[love-android:app/build.gradle:9-33,148-155@4c65fff; love-android:build.gradle:8@4c65fff; love-android:gradle/wrapper/gradle-wrapper.properties:3@4c65fff; love-android:gradle.properties:1-12@4c65fff; love-android:.github/workflows/main.yml:26-32@4c65fff]`
- **O love-android não compila o mesmo LÖVE do desktop.** O submódulo está em love@792690b, 34
  commits atrás do b7daef0, e o megasource em 5118c13 (SDL3 3.4.10, LuaJIT 2.1.1784580905
  pré-compilado com NDK r27d). O desktop pelo AUR roda o luajit do sistema (2.1.1791988261).
  "Mesma semente, mesmo mapa" e o replay de uma run do celular ficam sem prova enquanto a suíte
  não roda nesse LuaJIT. Remédio: `jit.version` e `jit.status()` no `jit=` do fato de início;
  um digest de determinismo das mesmas sementes em LuaJIT, Lua 5.x e dentro do runtime, com o
  JIT dele e com `jit.off()`; o mesmo sha nos dois exige escolher o pino ou trocar o submódulo
  (decisão do autor). `[lido: árvore dos submódulos do love-android@4c65fff; megasource:libs/LuaJIT/android/arm64-v8a/luajit.h:33@5118c13; medido: luajit -v]`
- **O JIT voltou a ligar no ARM.** A 11.5 fazia `jit.off()` em todo arm e arm64, Android
  incluso; o commit fc42127 (2025-11-06) tirou o bloco, e o `jitsetup.lua` do `main` só ajusta
  `jit.opt`. A premissa "o celular roda o interpretador" e o passe `-joff` como espelho dele
  caem, a menos que o jogo force `jit.off()` (decisão do autor). No Apple, o CMake põe
  `LOVE_JIT=FALSE` por padrão. `[pista 11.5@6eb8d54; love:src/modules/love/jitsetup.lua:25-36@b7daef0; love:CMakeLists.txt:85-91@b7daef0]`
- **O megasource traz instruções de agente.** O `libs/SDL3` do megasource fixado tem `AGENTS.md`
  e `CLAUDE.md`: o agente que trabalha dentro do checkout do love-android carrega as regras do
  SDL, e o `CLAUDE.md` faz o Claude Code ignorar o `AGENTS.md` do lugar. Remédio: o love-android
  mora fora do repositório do jogo, num checkout limpo no sha do lock, remendado só por
  `.patch`, e o agente não trabalha de dentro dele. `[lido: gh api megasource@5118c13, libs/SDL3]`
- **A biblioteca pré-compilada fura o alinhamento de 16 KB.** O `build.gradle` liga as páginas de
  16 KB do que ele compila, mas o libluajit do megasource já vem pronto. Remédio: medir o APK
  (`readelf -lW` em cada `.so` do arm64, `LOAD` com alinhamento ≥ 0x4000) antes de publicar.
  `[inferido; medir]`
- **Voltar, área segura, orientação e sensores.** Na 11.5, o botão voltar vira `escape` (e fecha
  o app se o jogo não tratar), `getSafeArea` só vale em tela cheia e o acelerômetro abre como
  joystick. O love-android `main` abre com `LAYOUT_IN_DISPLAY_CUTOUT_MODE_NEVER` e só passa a
  `SHORT_EDGES` no modo imersivo; o manifesto não tem `android:appCategory` nem `isGame` (sem
  eles o Android 16 ignora a trava de orientação em tela grande; o `appCategory` vai dentro de
  `<application>`), e `app.orientation` vira `android:screenOrientation`. O `main` traz o
  módulo `sensor` e `love.system.getPreferredLocales` (idioma do sistema). Remédio: decidir
  voltar, tela cheia, orientação e idioma com o autor e provar no aparelho; a verificação do
  APK lê o manifesto mesclado (alvo, `appCategory`, permissões, exportados, backup,
  `debuggable`). `[pista 11.5@6eb8d54; love-android:app/src/main/java/org/love2d/android/GameActivity.java:119,245-257,280-287@4c65fff; love-android:app/src/main/AndroidManifest.xml:36-38@4c65fff; Android 16: lido na auditoria; love:src/modules/system/wrap_System.cpp:110-137@b7daef0]`
- **A máquina não compila o love-android `main`.** Tem java 21 do sistema, o JDK 25 do Defold,
  `~/Android/Sdk` só com o NDK 28.2.13676358 e o platform android-34, e `ANDROID_HOME` vazio;
  faltam o NDK 27.3 e o platform 35. Instalar pede o sim do autor. `[medido, 2026-10-17]`

## LuaLS e anotações

- **Não há anotação do LÖVE 12 pronta, e a da 11.5 erra calada.** O LuaLS 3.18.0 do mason (fora
  do PATH) traz `meta/3rd/love2d` com 20 arquivos e `-- version: 11.5`. A LuaCATS/love2d e o
  love-api master também dizem 11.5 (a issue #111, "Start Documenting 12.0 Functions", segue
  aberta). O que existe de 12 é o fork MikuAuahDark/love2d-api, ramo `love-12` @0f0d668
  (2025-01-23), parado antes de `renderers`, `sdf` e `mountFullPath`, e sem licença. Contra o
  `main`, a da 11.5 não conhece dezenas de funções (69 ou mais, na conta da reescrita do
  CampCrawler) e dá deprecadas como normais (11): falso `undefined-field` na API nova e
  silêncio na que saiu. Remédio: uma anotação do projeto (overlay), **sozinha** no `.luarc`, só
  com o que o jogo chama, cada entrada com a citação do fonte do pin, e um teste que confere todo
  nome dela contra o dump da API do binário do lock e fora da lista de deprecadas; a base
  gerada do fork entra só com o sim do autor, declarada no cabeçalho. `[medido: find no mason; lido: LuaCATS/love2d, love2d-community/love-api, MikuAuahDark/love2d-api; as contagens: lido na reescrita do CampCrawler, 2026-10-17]`
- **A anotação upstream trocou a forma dos callbacks.** A cópia empacotada no LuaLS tem 36
  `---@alias love.*` (`love.update`, `love.mousepressed`); a LuaCATS atual declara funções com
  `---@param`, e o veredito pode mudar com `--checklevel`. Remédio: o `luals_check.sh` aponta
  para uma cópia fixada (caminho e versão no script) e a troca dela passa pelo portão.
  `[medido: cópias locais; lido: LuaCATS/love2d]`

## Lua: LuaJIT do jogo e Lua 5.x da suíte

- **`-joff` quebra teste que relança o intérprete.** No CampCrawler, a suíte em `luajit -joff`
  passou inteira antes do replay (367 testes, 13,4 s contra 6,8 s com o JIT); depois dele, levou
  ~15 s contra ~9 s e 6 casos de `test_reproduz_run` reprovaram, porque relançam o intérprete
  por `arg[-1]`, que vira `-joff`. Remédio: o teste acha o intérprete pelo menor índice negativo
  de `arg`, ou por variável de ambiente. `[medido: LuaJIT 2.1.1791988261, auditorias de 2026-10-17]`
- **Lua 5.5 recusa atribuir à variável do `for`.** `for i = 1, 2 do i = i + 1 end` compila no
  LuaJIT e no Lua 5.4 e no 5.5.1 estoura "attempt to assign to const variable 'i'": o jogo roda,
  a suíte em Lua 5.5 não carrega. Remédio: variável local nova dentro do laço.
  `[medido: LuaJIT 2.1.1791988261, Lua 5.4, Lua 5.5.1, 2026-10-17]`
- **`/` devolve float no Lua 5.3+**: `4/2` é `2.0` no Lua 5.5 e `2` no LuaJIT, e
  `string.format("%d", 3/2)` estoura no Lua 5.5 e sai `1`, calado, no LuaJIT. Remédio:
  `math.floor` em toda divisão inteira (a lição do CampCrawler está na ai-first-defold, seção
  Lua). `[medido: LuaJIT 2.1.1791988261 e Lua 5.5.1, 2026-10-17; LuaJIT 2.1, Lua 5.4 e 5.5 na ai-first-defold, 2026-10-16]`

## Gerais de jogo: moram em `references/gerais-de-jogo.md`

Ali estão as lições de jogo que valem em qualquer engine: testes que passam com qualquer código,
prova e oráculo, ferramentas de verificação, entrada e troca de estado, captura e cor, log da
partida e instruções do agente. É cópia da fonte única `gerais-de-jogo.md`, na raiz do repositório
das skills. Não acrescente lição aqui: a fonte se edita num ramo em worktree, e o
`distribuir.py --check-gerais` reprova item de lista ou subtítulo nesta seção.
