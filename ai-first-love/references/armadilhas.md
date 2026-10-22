# Armadilhas do LÖVE que o agente não vê

**Quase nada aqui foi medido no LÖVE.** Foi escrito lendo o fonte; o AppImage do b7daef0 entrou
na máquina em 2026-10-17, e só o marcado `[medido@b7daef0]` rodou nele (as etapas R0.1 a R0.6 da
reescrita do CampCrawler, de 17 e 18/10). A wiki (love2d.org) responde 403 a
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
repositório das skills (seção Gerais de jogo, no fim), e a da linguagem, entre o LuaJIT do jogo e
o Lua 5.x da suíte, em `gerais-de-lua.md`, também na raiz (seção Gerais de Lua).

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

- **O AppImage se lê sem executar.** O `7z` abre o squashfs de dentro do ELF: a árvore extraída
  do AppImage do b7daef0 saiu igual ao lock (41 arquivos e os links), sem rodar o runtime do
  AppImage. Trocar de sha, ensaiado de b7daef0 para 792690b e de volta numa cópia: mudam o lock,
  o teste que prende o sha e o cabeçalho da anotação gerada; o portão inteiro passa nos dois
  sentidos, a API por nome é igual, e o `boot.lua`, o `callbacks.lua` e o `arg.lua` embutidos no
  `liblove` são idênticos, lidos do binário (o `event/`, em C++, pede o fonte). `[medido: 7z e tools/love --conferir; o ensaio: tools/check.sh numa cópia, CampCrawler R0.6.9]`

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
  `ALSOFT_DRIVERS=null` no ambiente, a passada e a captura rodam mudas: o
  `love.audio.getPlaybackDevice()` diz `No Output`, e o `newSource`, o `clone` e o `play` seguem
  valendo (o `play` devolve verdadeiro e o `isPlaying` também), então a passada cobra o som tocado
  num fato sem fazer barulho. Remédio: o executor monta o ambiente por lista branca, com a variável
  nela, e a passada exige o dispositivo nulo num fato do boot (o nome tem espaço: troque-o antes de
  pôr no fato). `[medido@b7daef0: sonda pelo tools/love e o fato AUDIO de toda passada do tools/smoke.py, CampCrawler, 21/10]`
- **Sem dispositivo de som, o nome vem vazio, ou estoura.** Quando o OpenAL não abre (sem servidor
  de som, driver desconhecido, sem sessão), o LÖVE imprime "Could not open device." e cai no áudio
  nulo, cujo `getPlaybackDevice` devolve `""`; o do OpenAL estoura quando o nome falta. O jogo segue
  mudo, mas quem põe o nome num fato que recusa valor vazio derruba o boot, num caso que a passada,
  com `ALSOFT_DRIVERS=null`, nunca vê (CampCrawler: achado da auditoria). Remédio: `pcall` e um
  valor declarado (`nenhum`), com o teste do nome vazio e do que estoura. `[lido: love:src/modules/audio/wrap_Audio.cpp:682-708@b7daef0; love:src/modules/audio/null/Audio.cpp:225-228@b7daef0; love:src/modules/audio/openal/Audio.cpp:399-406@b7daef0; medido@b7daef0: sonda pelo tools/love com ALSOFT_DRIVERS=nenhum e sem XDG_RUNTIME_DIR, nome vazio, CampCrawler, 21/10]`
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

- **Um `.lua` solto roda como jogo, com a janela padrão.** No 12, `love arquivo.lua` roda o
  arquivo; sem `conf.lua`, o boot abre a janela padrão antes dele, e com o `DISPLAY` da sessão
  ela aparece na tela de quem está usando a máquina. Remédio: sonda é pasta com `conf.lua`
  (`t.window = false` quando não desenha) e roda sob um Xvfb próprio. `[medido@b7daef0: love.window.isOpen() verdadeiro no .lua solto, CampCrawler R0.6.11]`
- **Sem janela ainda pede vídeo.** Com `t.window = false` e o módulo `window` carregado, o boot
  inicia o vídeo do SDL: sem `DISPLAY` (e com o `SDL_VIDEO_DRIVER=x11` do lançador), cai em
  "Could not initialize SDL video subsystem (x11 not available)". Remédio: Xvfb mesmo sem
  janela, ou `t.modules.window` e `t.modules.graphics` desligados, e aí o jogo roda sem Xvfb
  nenhum (a passada sem vídeo). `[medido@b7daef0: o dump da API sem DISPLAY, CampCrawler R0.6.5 e .11; a sem vídeo sem Xvfb: tools/smoke.py --video=nenhum, CampCrawler R0.6.4]`

## Saída, erro e log

- **O SIGKILL leva a cauda do log e o próprio erro.** Com a saída num arquivo ou num pipe, o
  `print` fica em buffer de bloco; a passada que estoura o prazo mata o processo e perde tudo,
  inclusive o texto do erro. No LuaJIT da máquina: 0 bytes sem buffer de linha, 39 com.
  Remédio: `io.stdout:setvbuf("line")` na primeira linha do `conf.lua` (ele roda antes do
  `main.lua`), cobrado por passada. No LÖVE, o aviso de deprecação (um `printf` no mesmo
  `stdout` do C) e a linha seguinte sobrevivem ao SIGKILL com o buffer de linha; sem ele, 0
  linhas. `[medido: LuaJIT 2.1.1791988261, fora do LÖVE; medido@b7daef0: sonda morta por SIGKILL, CampCrawler R0.6.10; o printf: love:src/common/deprecation.cpp:69-73@b7daef0; ordem conf → main: love:src/modules/love/boot.lua:250,444@b7daef0]`
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

- **O OpenAL suja o stdout sem dispositivo.** Sem sessão de áudio (sem `XDG_RUNTIME_DIR`) e sem
  `ALSOFT_DRIVERS=null`, "Could not open device." sai no stdout do jogo, no meio da saída que uma
  ferramenta lê linha a linha. Remédio: `ALSOFT_DRIVERS=null` no ambiente de toda passada e
  sonda, e leitura estrita da saída (a linha estranha reprova, não se pula). `[medido@b7daef0: o dump da API, CampCrawler R0.6.5 e .11]`

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
  (xdotool sob Xvfb), não pelo `updateMode`. Medido no `main`: o `love.resize` dispara uma vez na
  abertura, com o tamanho de já (sob Xvfb; a causa, o `setMode` do `love.load`, é inferida), e a
  cada `windowsize` de fora; quem relata a janela (o fato `JANELA`) reemite no `love.resize`, e o
  robô espera o tamanho pedido antes da próxima ação, ou o alvo calculado no layout velho cai na
  janela nova. O pedido no tamanho que a janela já tem não dispara nada: recuse-o no boot.
  `[love:src/modules/window/sdl/Window.cpp:565-588,696,724-726@b7daef0; love:src/modules/love/boot.lua:194,398-426@b7daef0; pista 11.5@6eb8d54; disparar: medido@b7daef0, tools/smoke.py --redimensiona do CampCrawler, 655c623; o updateMode sozinho: inferido]`
- **O `xdotool search` com padrão não filtra pelo pid.** As condições se juntam por "ou" (o
  `--any` é o padrão): `search --pid N ""` devolveu três janelas, a primeira de fora do jogo, e o
  `windowmove --sync` nela esperou para sempre; encadeado a outro comando sem padrão, o `search`
  toma o comando seguinte como o padrão de nome e não acha nada. Remédio: `xdotool search --sync
  --pid N` sozinho, com o `--pid` no fim, exatamente uma janela exigida, e o comando seguinte na
  janela achada. `[medido: xdotool 4.20260303.1 sob Xvfb, com a janela do LÖVE b7daef0, 18/10]`
- **`love.resize` chega em unidades de DPI**, a partir do `SDL_EVENT_WINDOW_PIXEL_SIZE_CHANGED`,
  e é seguido de um `collectgarbage`; misturar `getPixelDimensions` (ou o tamanho da janela do
  sistema) com as coordenadas de entrada erra pela escala. Remédio: uma unidade em toda a
  cadeia (layout, lista, hit-test, robô, amostra, adb). Ou a de `love.graphics.getDimensions`,
  com o pixel só na amostra e no adb, convertido por `getDPIScale` com teste; ou o pixel em tudo,
  com `usedpiscale = false` (em `t.window` ou nos flags do `setMode`), que muda o tamanho do que
  se vê em tela de alta densidade e por isso é proposta que o autor julga pela captura, no
  backend dele.
  `[love:src/modules/event/sdl/Event.cpp:811-837@b7daef0; love:src/modules/love/boot.lua:196,422@b7daef0; mistura: pista 11.5 + inferido]`
- **A escala de DPI se força sob Xvfb pelo SDL.** Sem nada, a escala é 1; com
  `SDL_VIDEO_X11_SCALING_FACTOR=2` no ambiente do jogo, a janela pedida de 1920x1080 abriu com
  1920x1080 pixels e 960x540 unidades (`getDimensions`), `getDPIScale` 2, e a posição
  (`getPosition`) seguiu em pixel, a mesma das duas escalas. Com `usedpiscale = false` nos flags
  do `setMode` e as fontes em `dpiscale = 1`, a mesma janela ficou em 1920x1080 unidades e
  `getDPIScale` 1, e a imagem saiu igual, pixel a pixel, à da escala 1; sem a flag, ela diferia só
  no texto (a fonte na metade do tamanho, rasterizada a 2×, posta em unidade inteira, em passos de
  2 px). Remédio: a passada na escala forçada é a que prova a unidade; com a da DPI, a conversão
  entre pixel e unidade (Entrada), com o `JANELA` na escala pedida e os pixels iguais às unidades
  vezes o dpi; com o pixel, que a escala do sistema não vaza (`JANELA` com dpi 1 e os pixels
  iguais às unidades). `[medido@b7daef0: tools/smoke.py --escala 2 do CampCrawler, 527058d e c2c6e94, e as capturas de 8ee2319; o porquê do tamanho: inferido]`
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
- **O evento empurrado não prova a conversão entre pixel e unidade.** O robô que empurra no centro
  do item, na unidade da lista, e confere o id que respondeu pega o hit-test deslocado; não pega o
  que mora entre o pixel da tela e a unidade, porque o `push` pula a conversão. No CampCrawler, a
  posição da janela relatada em unidade, a conversão do condutor sem o dpi e a lista em pixel com
  o desenho certo aprovaram pelo push e pelo xdotool em escala 1 (lá a conversão é a identidade), e
  só o xdotool na escala 2 reprovou. Remédio: uma passada com o clique de fora numa escala
  forçada, com o desvio julgado em pixel da tela (em unidade, a escala 2 aceita 1 px inteiro), até
  meio pixel, o medido. `[medido@b7daef0: tools/smoke.py --clique --escala 2 do CampCrawler, 527058d e os mutantes da R0.4.4 sobre 655c623]`
- **O foco no lugar onde o ponteiro já está não chega.** O X11 não gera movimento sem mudança de
  posição: o `xdotool mousemove` ao pixel onde o ponteiro parou no clique anterior não dá
  `mousemoved`, e o foco pedido ali (o alcance que acende sob o mouse) nunca responde. Remédio: o
  ponteiro entra de fora da janela a cada ação e volta a um ponto de espera fora dela (com a tela
  do Xvfb maior que a janela); o foco não depende de onde a ação anterior o deixou.
  `[inferido: o X11 só gera MotionNotify com o ponteiro movido; o desenho, medido@b7daef0 no CampCrawler, 38ae218]`
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

- **As pastas das passadas reprovadas enchem o `/tmp`.** O executor guarda a pasta da passada que
  reprova, para leitura, e com a captura externa ela leva as cópias do framebuffer do Xvfb (XWD,
  ~59 MB por quadro numa tela de 3840²; até 340 MB por passada). Um catálogo de mutantes, que
  reprova de propósito, deixou 168 delas e encheu a 80% o `/tmp` (tmpfs de 8 GB), e o resto da
  tabela reprovou por ambiente, sem linha `REPROVA`. Remédio: a ferramenta dos mutantes roda o
  portão com o `TMPDIR` dentro da cópia descartável, e as pastas somem com ela; o verificador que
  reprova sem `REPROVA` mostra o fim da saída. `[medido: o tools/mutantes.py do CampCrawler, 18/10]`
- **A ferramenta que lê e grava PNG fora da pasta do jogo.** O `love.filesystem` só alcança a
  fonte e a save, e o `newImageData(caminho)` não abre `assets/` nem `build/` de outro programa.
  Remédio: um programa à parte no mesmo repositório (sem janela nem gráficos no `conf.lua`), com
  os bytes pelo `io`: `newFileData(bytes, nome)` vira os bytes do arquivo, `newImageData(filedata)`
  decodifica, o `getString()` do ImageData dá os bytes crus em `rgba8`, e
  `newImageData(w, h, "rgba8", bytes)`, com o tamanho exato, mais o `encode("png")` gravam. Os
  módulos do repositório se acham pela raiz, que o boot do programa acrescenta ao `package.path`
  (o pai do `getSource()`). Sem o módulo window, o erro sai pelo `error_printer` e o handler padrão
  volta sem abrir caixa: o processo termina, não prende sob Xvfb. No CampCrawler, as 47 imagens do
  atlas foram e voltaram por ele sem pixel diferente.
  `[love:src/modules/filesystem/wrap_Filesystem.cpp:107-111,450-451@b7daef0; love:src/modules/image/wrap_Image.cpp:58-77,87-99@b7daef0; love:src/modules/data/wrap_Data.cpp:40-50@b7daef0; love:src/modules/image/wrap_ImageData.cpp:237-260@b7daef0; love:src/modules/love/callbacks.lua:221-228@b7daef0; visto: o pixel-art/ do campcrawler-love f7a310e, 22/10]`

## Texto e fonte

- **Sem janela não há quebra de linha do LÖVE.** O `love.font` não pede janela, mas o
  `Rasterizer` só tem `getHeight`, `getAdvance`, `getAscent`, `getDescent`, `getLineHeight`,
  `getGlyphData`, `getGlyphCount` e `hasGlyphs`: nem `getWrap` nem kerning. `Font:getWrap` só
  existe por `love.graphics`. Remédio: medidor injetado na vista; o da suíte é nosso, sobre os
  avanços, e devolve um intervalo `[inf, sup]` com a folga medida (a moldagem do HarfBuzz afasta
  a largura real da soma): afirma "cabe" só com `sup` ≤ limite e "não cabe" só com `inf` >
  limite; a medida de verdade é da passada com janela, que confere também a largura real dentro
  do intervalo (o "MEDIDOR fora"), de que a suíte e a passada sem vídeo dependem. O `love.font`
  não tem moldador (só `newBMFontRasterizer`, `newGlyphData`, `newImageRasterizer`,
  `newRasterizer` e `newTrueTypeRasterizer`), e a soma dos avanços do `GlyphData` erra até 9 px
  contra a `Font:getWidth` (en, de e ja, a 26, 32 e 60 px): medidor sem janela pelos avanços
  muda a quebra perto do limite. `[love:src/modules/font/wrap_Rasterizer.cpp:129-136@b7daef0; love:src/modules/font/wrap_Font.cpp:241-245@b7daef0; medido@b7daef0: sondas, CampCrawler R0.6.4 e .11]`
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
  pelo `Rasterizer`, sem janela. A passada com janela aprovou um Hangul em alemão (desenhou a
  caixa): só o `hasGlyphs` da fonte real no fato do texto e o `cmap` lido no portão (por
  `struct`, sem fontTools) o pegam. O `hasGlyphs("")` devolve falso. `[pista 11.5@6eb8d54; hasGlyphs no main: love:src/modules/font/wrap_Rasterizer.cpp:129-136@b7daef0; texto vazio: love:src/modules/font/Rasterizer.cpp:79-82@b7daef0; a caixa aprovada: medido@b7daef0, o mutante glifo, CampCrawler R0.6.6; fallback calado: inferido]`
- **SDF sem shader, e a opção errada é ignorada.** `love.font.newTrueTypeRasterizer(arq, px,
  { sdf = true })` e o `newFont` dele ligam o `FT_RENDER_MODE_SDF` e voltam ao normal calado se
  falhar; as opções se leem pelo nome exato, e a chave desconhecida (`{ qualquer = 1 }`) passa
  calada. O 12 desenha o campo de distância cru, um halo: o desenho pede shader nosso
  (`fwidth` e `smoothstep` no alfa, só em GL), e o contorno sai no mesmo shader. Remédio: o modo
  de fonte se prova pelo glifo, a margem do `GlyphData` (8 px: o `A` a 40 px sai 41×45 contra
  25×29), não pela opção. **E gerar o SDF na hora é caro:** a troca para japonês com as fontes
  novas levou 3,5 s só nos textos de uma tela e 19 s na tabela inteira (o exact, 11 ms e 61 ms);
  SDF viável pede glifo pré-gerado ou cache. `[love:src/modules/font/wrap_Font.cpp:67-104@b7daef0; love:src/modules/font/freetype/TrueTypeRasterizer.cpp:115-140@b7daef0; medido@b7daef0: sondas da folha de texto, CampCrawler R0.6.7 e .11]`
- **A fonte CJK inteira pesa megabytes; o recorte carrega igual.** As Noto Sans KR, SC e TC
  somam 18,7 MB (15,8 comprimidas), e o jogo usa poucas centenas de letras de cada. O `pyftsubset`
  (fontTools) com as letras da tabela de idiomas, o ASCII de 32 a 126 (o número e o sinal que a
  tela formata fora da tabela) e `--layout-features='*'` (a moldagem do HarfBuzz) deu 95, 133 e
  141 KB, que o LÖVE 12 carrega pelo `love.font` e pelo `newFont` e desenha com `hasGlyphs`
  verdadeiro; a mesma fonte e as mesmas letras dão o mesmo arquivo, byte a byte. Remédio: o
  recorte no repositório, com o comando escrito ao lado e refeito sempre da fonte inteira, nunca do
  recorte; o portão confere o `cmap` de cada recorte contra a tabela pela biblioteca padrão (o
  fontTools fica só para refazer), e a letra nova reprova dizendo o comando. `[medido@b7daef0: o FONTE da passada sem vídeo e as capturas em ko, zh_CN e zh_TW pelo tools/smoke.py, CampCrawler, 21/10; medido: python-fonttools 4.67.0, duas corridas]`
- **`newText` dispara o aviso de tela.** O tipo agora é `TextBatch` (`newTextBatch`); `newText`
  é apelido deprecado. `[love:src/modules/graphics/wrap_Graphics.cpp:2343-2347,4069,4200@b7daef0]`

- **O medidor aproximado não decide o estouro da quebra.** Com o intervalo largo que a moldagem
  pede (no CampCrawler, 0,25 a 1,05 em por caractere), o mínimo de uma linha japonesa sem quebra
  não passa da coluna de 730 px, e a suíte só afirma "não cabe" quando ele passa. Remédio: o item
  de texto declara o contêiner (`wrap_w`), e a passada com janela mede cada texto pela fonte real
  contra ele. A quebra medindo a 0,6 do tamanho desenhado deu, na luta em japonês, a linha de
  1022 px contra o limite de 730. `[medido@b7daef0: tools/smoke.py do CampCrawler, 95529ed]`

- **O teto do medidor aproximado não serve à invariante de sobreposição.** Ele é largo de propósito
  (o intervalo que garante a quebra), e dois textos que não se tocam na tela se sobrepõem pelo teto:
  a invariante reprova o código certo. Remédio: com fonte monoespaçada, a largura exata é o número de
  glifos vezes o avanço da tabela `hmtx` (constante), lido do arquivo da fonte pela biblioteca padrão;
  a passada com janela a confirma pelo `TEXTO`, com a fonte real. `[medido@b7daef0: no CampCrawler,
  a Vera Sans Mono Bold avança 1233 de 2048, e o "-1" a 48 px mediu 58,00 px pela Font, contra 57,8
  da conta; 62a9a57]`

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
- **A borda de meio pixel o GL pinta, e o ponto do centro mente.** Um rect cuja borda cai em
  x,5 deixa a linha daquele pixel com o centro na própria borda; no b7daef0 (OpenGL, sob Xvfb) o
  GL a pintou: a moldura do alcance do CampCrawler, 9 de espessura centrada na divisa, foi de
  35,5 a 44,5, e a linha 44 saiu vermelha. A amostra que dava o ponto por limpo olhando só o
  centro do pixel reprovou o código certo com 91 de diferença. Remédio: ponto limpo é o pixel que
  nenhum item de depois toca (o quadrado [px, px + 1) cruzando a caixa), não o de centro
  descoberto. `[medido@b7daef0: tools/smoke.py, passadas da luta e da poção do campcrawler-love, ce64214]`
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
- **Arte pré-ampliada reduzida a uma fração exata nunca mistura pixels no filtro linear.** No
  CampCrawler, a arte de 37 px ampliada 4× (148) desenhada em 111 px (escala 0,75, o 1080p
  deitado), em posição inteira: o centro de cada pixel cai em u = (px + 0,5) × 4/3 − 0,5, cujo
  resto por 4 só dá 0,17, 1,5 e 2,83, nunca entre dois pixels da arte. O alfa vai de 0 a 1 sem
  meio-termo, e o blend errado (o padrão no lugar do premultiplicado) não muda pixel nenhum: a
  amostra deitada o aprova, e com razão. Remédio: o defeito de blend se prova numa escala que
  mistura, com a borda de alfa amostrada (SKILL, seção 3, Amostra de pixel): em pé (1080x1920) ou
  depois de um resize deitado. A 1280x720, 2560x1440 e 3840x2160 (a arte a 0,5, 1 e 1,5) a porta
  tem ponto de borda e, no 4K, o soldado também, e o blend trocado reprova pela amostra nos três.
  `[medido@b7daef0: tools/smoke.py do CampCrawler, 7f540d4 e 0061111; o resize e o blend nele, c2c6e94, na auditoria da R0.4]`
- **O transparente preto já está premultiplicado.** Arte cujo transparente é (0,0,0,0) e o resto
  opaco vale como premultiplicada: basta desenhá-la com `setBlendMode("alpha", "premultiplied")` e
  a cor do item premultiplicada. Com o blend padrão (`alphamultiply`) e filtro linear, o filtro
  mistura o preto na borda e o blend o multiplica de novo pelo alfa: a borda escurece. Remédio:
  premultiplique no carregamento (identidade nessa arte; o atlas conta os pixels que mudaram) e
  desenhe com o blend premultiplicado. `[medido: histograma das PNGs de assets/hd do CampCrawler,
  18/10; escurecer: inferido, e o mutante do blend reprova em pé]`
- **O extrude do atlas só se lê na ampliação, e a tela não o prova.** O filtro linear lê o texel
  além do quad só quando a arte sai maior que o atlas: o primeiro pixel dentro do item cai em
  u = (0,5 + f) × q/W − 0,5, com f de 0 a 1, que só fica abaixo de 0 se q/W < 1. Reduzida (no
  CampCrawler, a arte hd a 0,75 deitado e 0,72 em pé), a GPU nunca o lê: o atlas sem extrude
  nenhum passou nas passadas e na amostra de pixel, que ainda prendia o índice ao quad, o que o
  extrude promete. Remédio: confira o extrude no atlas montado, lendo de volta cada texel da borda
  repetida contra a borda da imagem, e exija zero diferenças num fato do boot. A passada na
  ampliação não basta: a 3840x2160 (a arte a 1,5) o filtro lê o extrude só no 1º pixel de cada
  borda (u < 0 só ali), e a amostra que olha a 2 px para dentro passou sem tocá-lo; a prova pela
  tela pede um ponto nesse anel. `[medido@b7daef0: tools/smoke.py do CampCrawler, d24ba8c, e a amostra aprovando o 4K, 655c623; o anel: inferido, pela conta acima]`
- **O layout não refeito depois de ampliar a janela passa na amostra e no clique.** A lista, o
  desenho e o toque saem do mesmo layout velho, coerentes entre si, e o tabuleiro fica no canto da
  janela nova: a amostra (103 pontos iguais) e o clique aprovaram. Na redução o item sai da
  janela, e o `ImageData:getPixel` da amostra estoura (`Attempt to get out-of-range pixel!`) sem
  dizer o item. Remédio: um fato de geometria do item contra uma fórmula independente da janela
  (no CampCrawler, `LAYOUT` com a célula contra o encaixe, 111 · min(w/1920, h/1080)); e a amostra
  confere a caixa do item dentro da captura antes de ler, com o item fora como falha nomeada.
  `[medido@b7daef0: tools/smoke.py --redimensiona do CampCrawler, 655c623]`
- **Espelhar por escala negativa tira a imagem do retângulo do item.** `draw(img, quad, x, y, 0,
  -sx, sy)` leva o quad de x − w a x: a matriz faz x + sx · u, e sem origem nada o devolve
  `[love:src/common/Matrix.cpp:265-282@b7daef0]`. A lista diz [x, x + w], o desenho sai à esquerda,
  e a amostra lê o fundo. Remédio: o espelho é dado do item (`mirror`, só na imagem), o render
  desenha em x + w com a escala negativa, e a amostra emula a coluna espelhada (u = w − u) com
  chave própria para o espelhado: sem ela, só o virado para a direita vai à amostra, e o render que
  não vira passa. `[medido@b7daef0: tools/smoke.py do CampCrawler, 3ee27a4: o soldado espelhado
  passa nos 5 pontos, e o render sem o espelho reprova 4 deles, até 216 de diferença]`
- **Girar 90° pelo ângulo tira a imagem do retângulo do item.** Com `r = −π/2` e sem origem, a matriz
  faz X = x + sy · v e Y = y − sx · u: o quad vai de y − w a y, acima do ponto
  `[love:src/common/Matrix.cpp:265-282@b7daef0]`. Remédio: o item leva o retângulo já deitado e o giro
  como dado (`rotation`, de 90, sem o espelho junto), o render desenha em (x, y + h) com `sx = h/qw` e
  `sy = w/qh`, e a amostra emula o texel (u = h − y, v = x, no item). `[medido@b7daef0: tools/smoke.py
  do CampCrawler, c4c313a: o caído deitado passa nos 5 pontos, com diferença máxima de 1, e o render
  que o desenha de pé reprova]`
- **O SDL centraliza a janela menor que a tela.** Sob um Xvfb de 1920x1920, sem gerenciador de
  janela, a janela de 1080x1920 abriu em x=420. Remédio: quem lê a tela por fora (a captura
  externa, o xdotool) soma a posição que o jogo relata (`love.window.getPosition()`), nunca supõe
  0,0. `[medido@b7daef0: tools/smoke.py do CampCrawler, 0061111]`

- **Sob o Xvfb, a GPU é a da máquina.** Com o driver da NVIDIA, o `getRendererInfo` sob o Xvfb
  dá a placa (uma RTX 4070), não o Mesa: a passada e a captura desenham na GPU de quem roda, e o
  que depende de driver diverge do CI (o Mesa). O lövetest do b7daef0, como o CI o roda (o
  `testing/main.lua --all --isRunner --renderers opengl`, sob Xvfb), deu aqui 341 passam e 1 falha,
  o array de `bool` em uniform do `Shader`, que o CI passa (342 e 0). Remédio: a tolerância e a
  base de imagem são da máquina; lövetest no portão só com a falha local que o CI não teve
  declarada. `[medido@b7daef0: getRendererInfo, CampCrawler R0.6.7 e .11; o lövetest: o AppRun do lock conferido, CampCrawler R0.6.10; o caso: love:testing/tests/graphics.lua:892-895@b7daef0; o CI: lido no check-run test-report-linux-X64-opengl do b7daef0]`

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
  terceiro fora de `vendor/` reprova. Quando a LGPL entra e como, decide o autor. O
  `license.txt` do AppImage do CI traz o UTF8-CPP do `liblove` sob o texto da BSL-1.0, rotulado
  "Unknown, MIT/Expat-like", e não cita HarfBuzz, Ogg, Vorbis, Theora, modplug nem zlib, que vêm
  no `lib/` dele: o aviso da BSD-3-Clause da Xiph, que a distribuição tem de levar, falta. O APK
  do love-android traz ainda o Oboe e a `libc++_shared`.
  `[pista 11.5@6eb8d54; love:CMakeLists.txt:106-107,186-192@b7daef0; lido: license.txt e lib/ do AppImage do b7daef0, lib/ do APK do 792690b, CampCrawler R0.6.8]`

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
  (decisão do autor). No CampCrawler, os 25 mapas das sementes 1 a 25, com a 1ª ordem, dão a
  mesma digital em LuaJIT 2.1.1791988261, em Lua 5.5.1 e no runtime (LuaJIT 2.1.1788856981), com
  o JIT ligado e depois de `jit.off()` e `jit.flush()` (o `flush` joga fora o código já
  compilado); percorrer o estado por `pairs` muda a digital. `[lido: árvore dos submódulos do love-android@4c65fff; megasource:libs/LuaJIT/android/arm64-v8a/luajit.h:33@5118c13; medido: luajit -v; medido@b7daef0: o fato DETERMINISMO, CampCrawler R0.6.3]`
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

- **As bibliotecas arm64 do APK já vêm em páginas de 16 KB.** No APK do CI do love-android que
  compila o 792690b, toda `.so` de arm64-v8a (`libluajit`, `liblove`, `libSDL3`, `libopenal`,
  `liboboe`, `libc++_shared`) tem `LOAD` alinhado em 0x4000; as de armeabi-v7a, em 0x1000.
  `[medido: readelf -lW no APK da run 30122584815, CampCrawler R0.6.11]`

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

- **A anotação pode sair do próprio binário.** Uma pasta de dump (`main.lua` e `conf.lua` com
  `t.window = false`), rodada pelo lançador sob Xvfb, percorre `love.*` (os módulos são os de
  `package.loaded["love.<nome>"]`), as metatabelas do registro por nome com `typeOf` (cada uma
  já com os métodos herdados) e as chaves de `love.handlers`, e gera a anotação inteira, só
  nomes e todo retorno `any`: no b7daef0, 20 módulos, 423 funções, 54 tipos, 1.205 métodos e 40
  eventos. O `undefined-field` como erro pega o nome que o 12 não tem, no módulo e no método
  (`fun(self: love.Image, ...: any): ...any` o LuaLS aceita), num caminho que nenhuma passada
  roda; o portão refaz o dump e reprova a anotação velha. `[medido@b7daef0: tools/overlay.py e o mutante api, CampCrawler R0.6.5]`
- **A vírgula do `fun` dentro de uma tabela anotada vira retorno.** Em
  `---@param a { novo: fun(f: string, k: string): table, nome: fun(): string }`, o LuaLS lê
  `table, nome` como a lista de retornos do `novo`, e o campo `nome` some: `undefined-field` no
  `a.nome()`. Remédio: `table` com a forma no texto, ou uma `---@class` com um `---@field` por
  linha. `[medido: LuaLS 3.18.0 do mason, CampCrawler, 21/10]`
- **O `--check` sem arquivo diz que está tudo bem.** O LuaLS 3.18.0 com a pasta vazia, ou com o
  `ignoreDir` errado, responde "no problems found". Remédio: o executor confere o total da barra
  de progresso (`N/N`) contra os `.lua` que ele mesmo conta, os do jogo e os da biblioteca.
  `[medido: LuaLS 3.18.0 do mason, CampCrawler R0.6.5]`
- **O `--check` sai com 1 quando acha erro, e escreve na própria instalação.** O executor que para
  no código não lê o `check.json` e reprova sem dizer o arquivo e a linha: o 1 é "achou", leia o
  relatório; outro código é o LuaLS que não rodou. Cada chamada grava o `log/` dentro da instalação:
  o `--logpath` desvia o `service.log`, mas o `middleScript.lua` vai a `ROOT/log` fixo; e o
  `--metapath` numa pasta própria faz o `meta/` gerado virar biblioteca dele e entrar na conta dos
  arquivos lidos (no CampCrawler, 116 contra 98). Remédio: só o `--logpath`, numa pasta que o
  `ignoreDir` ignora (o `build/`), e o resto declarado. E o lock fixa a árvore que decide, não o
  binário: a lógica está no `script/`, a versão no `changelog.md` e a biblioteca padrão no
  `meta/template/`; com só o binário no sha256, um diagnóstico desligado no `script/` passava.
  `[medido: LuaLS 3.18.0 do mason, a auditoria da R0.6 do CampCrawler; lido: script/library.lua:187 e script/version.lua:4-9 do 3.18.0]`

## Gerais de Lua: moram em `references/gerais-de-lua.md`

Ali estão as diferenças da linguagem entre o LuaJIT do jogo e o Lua 5.x da suíte, comuns à
ai-first-defold: valor que muda calado entre os dois (os retornos que o `a and f() or g()` corta,
o `/` que devolve float), código que só um dos dois carrega (a variável do `for`) e a suíte que
roda nos dois (o `-joff` de quem relança o intérprete, a ordem natural do `pairs`). É cópia da
fonte única `gerais-de-lua.md`, na raiz do repositório das skills. Não acrescente lição aqui: a
fonte se edita num ramo em worktree, e o `distribuir.py --check-gerais` reprova item de lista ou
subtítulo nesta seção.

## Gerais de jogo: moram em `references/gerais-de-jogo.md`

Ali estão as lições de jogo que valem em qualquer engine: testes que passam com qualquer código,
prova e oráculo, ferramentas de verificação, entrada e troca de estado, captura e cor, log da
partida e instruções do agente. É cópia da fonte única `gerais-de-jogo.md`, na raiz do repositório
das skills. Não acrescente lição aqui: a fonte se edita num ramo em worktree, e o
`distribuir.py --check-gerais` reprova item de lista ou subtítulo nesta seção.
