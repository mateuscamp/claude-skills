---
name: ai-first-love
description: Boas práticas AI-first para jogo em Lua com LÖVE (love2d) escrito por agente - a cena como lista de desenho (estado, lista, pixels: invariantes visuais na suíte, toque e robô pela mesma lista, replay e diff por quadro, amostra de pixel, medidor de texto injetado), como escrever (domínio em Lua puro com semente, um adaptador de entrada, love.run e conf.lua próprios, parser de chaves, fatos em log) e o ciclo de verificação que o agente fecha sozinho (teste visto falhar antes, suíte em LuaJIT e Lua 5.x, LuaLS, runtime fixado num lock, portão sem compilador e sem rede, passadas sob Xvfb, .love fora da worktree, hook Stop). Use sempre que o projeto for LÖVE - jogo novo, porte de outro motor para LÖVE, auditoria - e quando o assunto for conf.lua, love.run, love.errorhandler, erro visual, "funciona mas não como devia", teste de tela, captura, xdotool, Xvfb, toque contando duas vezes, love-android, adb, logcat, .love, LuaLS do love2d ou LÖVE 12. Complementa a skill jogos-ai-first (método e governança).
---

# AI-first em LÖVE

**Tudo o que esta skill diz do LÖVE é lido no fonte ou `[inferido]` até um projeto medir.** Ela
foi escrita lendo o fonte do `main` no commit b7daef0 (12.0, não lançado), da tag 11.5 (6eb8d54)
e do love-android 4c65fff; o AppImage do b7daef0 entrou na máquina em 2026-10-17, e nele só o
boot rodou (a R0.1 da reescrita do CampCrawler: o `[medido@b7daef0]` das armadilhas). A citação de cada afirmação (`love:<caminho>:<linha>@<sha7>`, ou
`[medido@<sha7>]` quando um projeto medir) mora **só** em `references/armadilhas.md`; aqui fica
a regra, com o item entre parênteses (ex.: "armadilhas, Entrada"). O `[medido]` daqui é de Lua
fora do LÖVE (LuaJIT 2.1.1791988261, Lua 5.4.9 e 5.5.1) ou da máquina.

O agente escreve Lua bem. No LÖVE, laço, tela e entrada são código do projeto, e o erro mudo
muda de forma (o `print` em buffer que some no SIGKILL, o argumento antes da pasta que vira o
caminho do jogo, o dedo que chega como mouse e como toque, o prazo que sai com 0:
`references/armadilhas.md`). E sobra o erro que mais custa ao agente: o jogo que **funciona mas
não como a intenção** (o número coberto pelo soldado, o texto que estoura, a contagem no canto
errado), sem erro nenhum. Esta skill dá **a cena como lista de desenho**, para que esse erro vire
dado que o agente lê e testa; **como escrever**, para que os mudos não nasçam; e **como
verificar**, para que os que nascerem reprovem antes do "terminei".

O método geral (contrato, posse, determinismo, ADR, fitness function, risco) está na
**jogos-ai-first**. A referência viva é a reescrita do CampCrawler em LÖVE (repositório próprio,
que por ora consome o domínio do jogo em Defold); as lições do Defold estão na `ai-first-defold`.

Arquivos desta skill:
- `assets/AGENTS-love.md`: a seção LÖVE do `AGENTS.md` do projeto, pronta para adaptar. É **a
  lista das boas práticas de código e de teste**; leia-a inteira antes de escrever código LÖVE.
- `assets/draw_list.lua`: esboço do item da lista (`---@class DrawItem`), do construtor que
  valida, da lista apresentada, do hit-test e da ação de toque, provado em LuaJIT, Lua 5.4 e 5.5
  e no LuaLS.
- `assets/loop.lua` e `assets/conf.lua`: esboços do `love.run` e do `conf.lua`, cada linha com
  a armadilha que a pede. Carregam em LuaJIT, Lua 5.4 e 5.5 [medido: `loadfile`]; uma
  adaptação deles fez o boot verde do CampCrawler no b7daef0 (R0.1).
- `references/armadilhas.md`: o que o fonte do LÖVE faz e engana em silêncio, com sintoma,
  causa, remédio e citação. Leia antes de afirmar qualquer coisa sobre o LÖVE.
- `references/gerais-de-jogo.md`: as lições de jogo de qualquer engine (cópia: seção 6).
- `scripts/`: o executor da suíte, `run.lua` e `run_tests.sh` (os da ai-first-defold), e
  `test_fronteira.lua` (domínio e vistas sem `love`, e só o renderizador desenha). Portão,
  lançador, executor das passadas e hook ainda não têm versão de LÖVE provada: nascem no
  esqueleto, adaptados dos da ai-first-defold.

## Por onde começar

**Projeto novo**
1. Fixe o LÖVE: a release 11.5 ou um sha do `main` (12.0, sem release), e a via do binário
   (AppImage do CI, `love-git` do AUR com `#commit=`, ou compilar). As duas escolhas são do
   autor; esta skill marca o que muda entre as versões (seção 3, Versão). Escreva o `AGENTS.md`
   a partir de `assets/AGENTS-love.md`, com as pastas reais: `modules/` (domínio), `scene/`
   (orquestração, vistas e o adaptador de entrada, Lua puro), `platform/` (o único que conhece
   `love`; repassa o callback cru ao adaptador), `conf.lua` e `main.lua` só montam.
2. Monte o esqueleto de prova antes da primeira mecânica: `runtime.lock` e o lançador, o
   `conf.lua` e o `love.run` dos esboços, parser de chaves, log da partida, robô por quadro com
   dt fixo que termina pelo plano, uma vista como lista de desenho, e o portão com uma passada
   (seções 2 e 3). Instale a suíte e a fronteira (`scripts/`) no mesmo passo.
3. Teste primeiro, visto falhar pelo motivo certo: regra nova em `modules/` começa por um teste
   da suíte; vista nova, pelas invariantes dela na suíte e pelo `--exigir` do fato que ela
   emite numa passada. A regra inteira está em "Testes e prova" no `assets/AGENTS-love.md`.

**Porte de outro motor (Defold, Godot)**
1. **A sonda A primeiro.** Uma vista (no CampCrawler, o tabuleiro) como lista de desenho no LÖVE,
   sob Xvfb. Plante defeitos visuais do histórico do jogo (contagem no canto errado, texto que
   estoura em alemão ou japonês, arranjo em pé) e anote qual verificador pega cada um, com as
   tolerâncias fixadas antes de plantar (seção 3); meça o tempo de uma passada com llvmpipe e
   com GPU sem janela; capture texto pequeno e número com contorno para o autor julgar. Ela pede
   o LÖVE instalado: aprovação do autor antes.
2. **Base do motor de origem**, se o autor a fizer alvo: retângulos e capturas por vista, na
   mesma semente, nos tamanhos da prova de layout e num em pé, nunca regravados. O automático
   compara só retângulos; o pixel vai em folha para o olho, sem as regiões de texto.
3. **O domínio tem uma fonte só**, e mudança de regra vai lá, pelo processo de lá. Ele se lê de
   um **commit nomeado** (pino num lock, ou a ponta do ramo resolvida no lançamento, como o
   autor decidir), nunca do checkout vivo: uma ferramenta confere o servido contra o
   `git ls-tree` dele, com contagem > 0, e sai com erro, nunca pula, se faltar caminho, sha ou
   lista; o `CODIGO` leva `dominio=` e `dominio_hash=` (seção 3). Como o LÖVE alcança a pasta
   se **mede no esqueleto** (armadilhas, Lançamento e argumentos).
4. **Suposição de motor no domínio vai a um inventário**, sem mudar o domínio até o autor
   responder (no CampCrawler, uma pose que sobe em +y: o y do LÖVE desce); todo tipo de evento
   do domínio está no despacho da apresentação ou numa lista de ignorados, com teste.
5. **Porte por vista**, cada uma com a sua passada e a comparação com a base. O motor de origem
   continua sendo o jogo até a última vista passar.
6. **Regra que existia por causa do motor antigo pode mudar, com o motivo registrado** (a chave
   que não pode ser prefixo de outra existia pelo `--config` do Defold).
7. **Caminho da pasta não entra em nada**: relativo à raiz, o outro repositório por variável
   (transitório), saída em `build/` ou `mktemp`. A memória do agente não segue a pasta sozinha.
   Nenhum `AGENTS.md` ou `CLAUDE.md` de outro projeto entre a home e o projeto: um `CLAUDE.md`
   acima faz o Claude Code ignorar o `AGENTS.md` do projeto.

**Projeto existente**: audite medindo e mostre a tabela ao usuário.

| Prática | Como conferir |
|---|---|
| LÖVE fixado | `runtime.lock`, lançador e `exe=` no `INICIO`? |
| Fronteiras | `scripts/test_fronteira.lua` com `GRUPOS` e `DESENHO_SO_EM` ajustados |
| Desenho só pela lista | `grep -rn --include="*.lua" "love\.graphics" . --exclude-dir=platform --exclude-dir=.claude --exclude-dir=build` |
| Um callback de entrada | `grep -rn --include="*.lua" -e touchpressed -e love.mousepressed . --exclude-dir=.claude --exclude-dir=build` |
| `love.run` | robô antes do `pump`, teto de dt, callback modal, quit sem `FIM`? |
| `conf.lua` | buffer e handler no topo, `version`, `identity`, `appendidentity`, `t.window = false`? |
| Código só da árvore | `package.path` e `cpath` zerados no `main.lua`? |
| RNG com semente | `grep -rn "math\.random" modules/ scene/` (pega também `love.math.random`) |
| Fatos no log | as passadas exigem linhas? todo `--recusar` tem `--exigir`? |
| Sem rede | o portão se relança em `unshare --net`? |
| `.love` testado | alguma passada roda o `.love` com o diretório atual fora da worktree? |
| LuaLS | rode e conte os problemas; anotação de qual versão? |
| Suíte em dois Luas | `luajit` e `lua` rodam? arquivo que não carrega reprova? |
| Hook | `.claude/settings.json` roda o `--rapido` no `Stop`? |
| Teste no commit | `git log --stat` de correções e mecânicas |

## 1. A cena como lista de desenho

### Por que

A maior dificuldade do agente é o erro visual e de jogo: a partida roda, nada estoura, e a tela
não mostra o que a regra decidiu. Com a cena como **estado → lista de desenho → pixels**, cada
quadro vira uma tabela de Lua que o agente lê, compara e cobra na suíte, sem GPU.

Honestamente: um modelo de vista em Lua puro testado na suíte é possível em qualquer motor.
Exclusivo do LÖVE: o desenho roda em toda passada do portão, sem transformação do motor entre o
modelo e o pixel. Exclusivo do Defold: o oráculo independente (a Automation Bridge lê nó,
retângulo e texto por fora). Por isso a lista é **autorrelato** (item 7) e se fecha por fora; a
vantagem do LÖVE aqui é condicional e inferida (a sonda A mede).

### O fluxo por quadro

```text
entrada do LÖVE → adaptador de entrada (Lua puro) → ação explícita → domínio (modules/)
  → eventos → orquestração (fila de apresentação; o estado MOSTRADO só avança pelo evento entregue)
  → vista: build(mostrado, layout, relógio da apresentação, medidor de texto)
  → LISTA DE DESENHO → renderizador (platform/) → pixels
```

O estado mostrado é o que a tela já exibiu, não o estado vivo do domínio: o domínio decide no
aceite da ordem, e a vista que lê o vivo anuncia o resultado antes da animação (CampCrawler,
D56; `ai-first-defold`, seção 3). A entrada da vista é estrita: só os quatro campos, e o
mostrado sem função, userdata nem metatable; a suíte a constrói com `love` ausente.

### O contrato

1. **A lista é dado em Lua puro**, com a forma no construtor e `---@class DrawItem`
   (`assets/draw_list.lua`):
   - `id` estável e único, vindo da identidade no domínio (`cell_4_4`, `soldier_2`,
     `hud_turn`), nunca do índice na lista nem de contador do quadro;
   - `kind` (`rect`, `image`, `text`) validado; `layer`, inteiro de constante nomeada, e `seq`
     (camada, depois inserção: o `table.sort` não é estável `[lido: manual do Lua 5.1]`);
   - retângulo em coordenadas de **tela** já transformadas, na unidade da entrada, e `color` de
     0 a 1; `image` do manifesto do atlas; `text`, `font_role` (o papel, não o arquivo),
     `size_px`, `align` e `wrap_w`;
   - `role` e `state` quando uma invariante precisa (soldado parado ou andando); `hit` e
     `target` no que aceita toque (a intenção como dado, `{ action, <campos do projeto> }`: x e
     y de tela não circulam); `probe = true` no que a amostra confere.

   O construtor estoura, com o recebido, em campo fora da forma (nome ou tipo), `kind` fora da
   enumeração, `id` repetido, imagem fora do manifesto, cor fora de [0, 1] (o 0..255 de código
   antigo satura calado: armadilhas, Gráficos e pixel) e `target` sem `action`. O que o jogo do
   autor faz com esse erro em execução é decisão dele.
2. **O `love.draw` só percorre a lista.** Só o renderizador de `platform/` desenha, e vista
   nenhuma conhece `love`; a expansão do item em argumentos de desenho é função pura, testada, e
   o render só faz `origin()` e desenha, sem transformação nem `r`, `ox`, `oy` (o retângulo da
   lista é o da tela). É teste, não conselho, na suíte e no hook (o porte que espalha
   `love.graphics.print` pelas vistas perde até o que o motor antigo dava):
   `scripts/test_fronteira.lua` reprova a palavra `love` inteira em `modules/` e `scene/` (pega
   `local L = love`), `require` fora da lista de permissão do grupo (nome calculado também) e
   `graphics` fora de `DESENHO_SO_EM` (renderizador, laço e `conf.lua`; fontes
   (`platform/fonts.lua`) e captura, por nome), `main.lua` inclusive; o que ele não vê está no
   topo dele, e a camada seguinte confere os globais do bytecode (`luajit -bl`) contra uma lista
   branca.
3. **A coordenada morre no hit-test.** Só o hit-test da **lista apresentada** (a do último
   `present`) responde: o item de cima com `hit`, alfa > 0 e centro na janela que contém o ponto;
   dali em diante só circula a ação (`kind`, `id`, `target`), nunca x e y. Alvo coberto ou em
   parte fora da janela: decisão do autor, declarada na tela (um modal é um item de tela inteira
   com `hit` e sem `target`). O **robô** acha o alvo pelo `id` na lista apresentada (até K
   quadros; o plano é Lua puro, com teste) e só entra por `love.event.push`, com a tupla inteira
   (`"mousepressed", x, y, 1, false, 1`) e o ponto preso na janela, pela fila e pelos
   `love.handlers` da entrada real; nunca chama o adaptador, e nada do jogo lê `love.mouse` nem
   `love.touch` (armadilhas, Entrada). Cada toque deixa `ROBO`, `ENTRADA alvo=` e `ALVO`;
   `TOQUE_ERRADO` e `TOQUE_PERDIDO` se recusam.
4. **Intenção visual vira teste na suíte**, sem GPU, nos tamanhos e nos dois arranjos (deitado e
   em pé) de uma constante única, lida pela suíte e pela captura. Exemplos do CampCrawler: texto
   não abaixo do mínimo; alvo de toque com o tamanho mínimo; soldado parado sem cobrir o número;
   inimigo em luta com presença; nada fora da janela nem da área segura.
   **Quais invariantes valem em cada vista decide o autor**, porque é visual: a vista nasce com
   as que ele aprovou e a captura mostrada a ele, cada uma cita a decisão ou a data, e o piso que
   ele não decidiu fica declarado provisório. No teste, o **esperado de geometria** é número
   escrito, fórmula independente ou a base (se alvo), nunca a conta que o teste prova; **toda
   invariante tem mutante** (trecho único, troca, teste que cai; queda por erro de carga não
   conta); e um meta-teste exige invariantes em toda vista com `build`.
5. **O laço é nosso** (seção 2): dt fixo no robô; o replay usa o dt gravado (no jogo, o real com
   teto de 1/30 s); descarte do quadro de volta; contador de quadro; entrada e dt gravados por
   quadro; o replay refaz a lista. O "defeito de um quadro" vira **o primeiro quadro N cuja
   lista difere** entre duas execuções que deviam dar a mesma (gravação e replay; robô e
   xdotool; antes e depois da mudança, na mesma semente e com o mesmo medidor). A lista se
   serializa em ordem (`layer`, `seq`), com números por `string.format`, nunca `tostring`, e o
   robô grava a do repouso, igual em LuaJIT, Lua 5.x e em toda velocidade, sem a pose da
   animação: a velocidade instantânea conclui a fila sem dar tarefa a ninguém, e quem anda fica
   onde estava (medido no CampCrawler, R0.2); o resultado é igual, a pose não. O dt se grava com ida
   e volta exata (`%.17g`, ou microssegundos inteiros), com teste: no LuaJIT, `tostring(1/3)` dá
   `0.33333333333333`, que não volta ao mesmo número
   `[medido: LuaJIT 2.1.1791988261; no Lua 5.5.1 volta]`.
6. **Fato de tela sai da lista, não do domínio.** `LAYOUT` e `TEXTO` saem dos itens desenhados,
   com o valor que o domínio escolheu ao lado (`esperado=`), e o portão exige os dois iguais
   (`references/gerais-de-jogo.md`, fato que prova o que a tela mostra). Emitir o valor do
   domínio no lugar do mostrado aprova sem provar o desenho (CampCrawler, D36).
7. **A lista é autorrelato.** Desenho e toque vêm do mesmo código: uma conta de layout errada
   aprova os dois juntos. Fecha-se por fora (seção 3): a **amostra de pixel** prova que o render
   desenhou o que a lista diz; o **xdotool**, que o toque do sistema chega ao item (a conversão
   que o `push` pula); a **captura** leva ao olho do autor a conta errada. **Triagem**: lista
   errada → o mostrado, o layout ou a vista (o primeiro quadro que difere); lista certa e pixel
   errado → render, atlas, fonte ou ambiente; as duas certas e o autor discorda → intenção não
   declarada, que vai a ele com a captura. "Está feio" continua sendo do olho.
8. **Texto precisa de largura e quebra, e o medidor é injetado**: no jogo, a fonte real
   (`Font:getWrap`, que exige janela); na suíte, um medidor determinístico **declarado
   aproximado**, que dá um intervalo e só afirma o que o intervalo garante (armadilhas, Texto e
   fonte). A quebra é da vista (linhas, larguras, altura e ascendente do medidor); o render
   nunca mede. A medida de verdade é a bancada da passada com janela (seção 3).

## 2. Como escrever

As regras de código estão em `assets/AGENTS-love.md` (Organização, Código, Recursos e arquivos);
aqui fica o que pede código ou motivo.

- **Domínio puro com RNG semeado.** Regra em `modules/`, sem nada do que a tabela `PURO` de
  `tests/test_fronteira.lua` proíbe (ela é a lista; `love.math.random` também é `love`) e sem
  `require` fora de `modules`; ações, tempo e semente entram como parâmetro. Gerador próprio: um
  LCG de 32 bits com multiplicador < 2^21 fica exato em double em Lua 5.1, LuaJIT e 5.4+.
- **Um adaptador de entrada, um uso por callback.** O adaptador mora em `scene/`, Lua puro, e a
  plataforma só lhe repassa os argumentos crus do callback. Só `love.mousepressed` do botão 1
  vira ação; `touch*` é ignorado; outro callback que o jogo precise (movimento, tecla do console)
  tem um uso declarado. O dedo chega como mouse sintético (com `istouch`) e depois como toque, só o
  primeiro vira mouse, e no Android o mouse físico gera também toque (armadilhas, Entrada):
  tratar os dois, ou filtrar por sequência, conta cada toque duas vezes. Um teste da suíte dá ao
  adaptador as sequências (dedo, mouse no Android, mouse no desktop), gravadas dos callbacks crus
  no aparelho e no desktop (até lá, a ordem lida, citada no nome do teste, e a gravação
  pendente, declarada), e confere uma ação em cada.
- **`love.run` próprio** (`assets/loop.lua`). A ordem do quadro é a regra: **robô (lê a lista
  apresentada) → `pump` → handlers → update → draw → present**, e só então a lista nova vale
  para o toque; o desenho modal (live-resize) só redesenha a apresentada. **O fim é pelo
  plano**: só o fato `FIM`, num lugar, chama `love.event.quit(0)`, e o quit sem `FIM` (o SIGTERM
  do prazo vira quit: armadilhas, Saída, erro e log) devolve um código próprio. O relógio que
  corta o dt e descarta o quadro de volta é Lua puro com teste; o sinal da volta se mede no
  aparelho.
- **`conf.lua` primeiro** (`assets/conf.lua`): `io.stdout:setvbuf("line")` e o
  `love.errorhandler` nosso antes de qualquer `require`: o do `main.lua` chega tarde para o
  `require` que falhou, depois da caixa de versão (armadilhas, Saída, erro e log). Nas passadas
  o handler imprime o traceback, grava no arquivo da partida e sai com um código próprio (o erro
  plantado no `conf.lua` sai com ele, não com 1, se vier antes do `love.conf`: depois dele o boot
  o engole, e o `love.conf` fecha o arquivo), e `love.setDeprecationOutput(true)` liga ali.
  Na partida do autor, tela de erro ou seguir com a linha no log é **decisão aberta do autor**.
  No `love.conf`: `t.identity`, `t.appendidentity = true` (a save não sombreia o código),
  `t.version` igual ao pin (outra abre caixa modal) e `t.window = false`: a janela abre no
  `love.load`, depois do parser, `resizable` e com `vsync = 0` na passada. Fora do parser, só se
  leem, por nome, as variáveis da passada (`<PROJETO>_PASSADA` e `<PROJETO>_VIDEO`, cujo
  `nenhum` tira `window` e `graphics`).
- **Código só pela árvore do jogo** (`assets/AGENTS-love.md`, Código): sem `package.path`
  zerado, o `require` ausente acha o `./?.lua` do diretório atual (armadilhas, Lançamento e
  argumentos).
- **Renderer e unidade: decisões abertas do autor.** `t.graphics.renderers` fica fora do
  `conf.lua` até ele decidir (sob Xvfb o LÖVE cai no OpenGL e na GPU dele sobe Vulkan,
  `[inferido]`). A unidade é uma só em toda a cadeia (lista, hit-test, robô, amostra, adb): a do
  DPI com conversão testada, ou o pixel com `usedpiscale = false` no `setMode`, que ele julga
  pela captura no backend dele (armadilhas, Laço, tempo e janela). O `INICIO` leva o renderer; o
  fato `JANELA`, a escala e as duas unidades.
- **Parser de chaves**, módulo puro em `love.load(args)`, testado com o argv como tabela, sobre
  `1..#args`: só `--config=<projeto>.<chave>=<valor>` (não casa opção do LÖVE); chave
  desconhecida, repetida ou argumento solto estouram com o recebido, e cada chave lida sai num
  fato `CONFIG chave= valor= origem=` (armadilhas, Lançamento e argumentos).
- **Mais dois abertos do autor.** Hot reload: o lurker (dependência nova) ou
  `love.event.restart`, que reabre o Lua inteiro, com o replay refazendo o estado. Fontes CJK
  inteiras ou em subconjunto, nitidez (SDF do 12) e contorno (cópias ou shader), por captura e
  no aparelho (armadilhas, Texto e fonte).

## 3. Como verificar

**Citação.** Afirmação sobre o LÖVE (armadilha, `AGENTS.md`, skill, anotação, a linha de código
que existe por comportamento dele) cita no formato do topo de `references/armadilhas.md`, que
diz também o que é só pista (11.5, wiki, memória). Citação de sha velho reprova.

**Versão e lançador.** O `love.getVersion()` não diz o commit (armadilhas, Versão e binário).
- O runtime mora fora do repositório e do sistema (`$LOVE_RUNTIME`); o `runtime.lock`, dentro,
  guarda sha, origem e sha256 de todo arquivo dele (no `love-git`, do binário e da liblove).
  LuaLS, `luajit`, `lua` e `python` do portão também têm versão e sha256 registrados.
- **Tudo abre pelo lançador** (`tools/love`), nunca pelo `love` do PATH: confere o lock, limpa
  `LD_*` e `LUA_*`, roda o binário direto e põe a pasta antes dos argumentos; tem teste.
- O `INICIO` leva `love=`, `love_sha=` (do lock), `exe=` (sha256 lido de dentro, conferido com o
  lock), `libs_fora=` (bibliotecas do runtime achadas fora dele no `/proc/self/maps`), `jit=`
  (`jit.version` e `jit.status()`), `render=`, `video=` e `fundido=`; antes dele, o `CODIGO`
  leva a digital da árvore (`codigo=`, sha1 de `caminho\tblob`) e, no porte, `dominio=` e
  `dominio_hash=` (os blobs que o `require` leu). A passada exige esse hash e o `exe=` do lock,
  e a do `.love`, o `codigo=` da pasta. Prova é processo novo, e cai se o `codigo=` mudou
  durante a corrida.
- Trocar de sha é frente própria, com registro de decisão; medida do LÖVE é comando de `tools/`
  que grava o `exe=`; API existe se o dump rodado pelo binário do lock a lista. Compilar ou
  baixar o binário pede o sim do autor.

**Suíte em dois Luas.** `cp scripts/run.lua scripts/test_fronteira.lua tests/` e
`cp scripts/run_tests.sh .`: a suíte roda em LuaJIT (o Lua do LÖVE) e num Lua 5.x de
referência, e arquivo que não carrega reprova. O `run_tests.sh` roda o Lua 5.x só se houver: o
portão exige os dois antes de chamá-lo
(`for i in luajit lua; do command -v "$i" >/dev/null || { echo "falta $i" >&2; exit 2; }; done`).
Ajuste `GRUPOS`, `DESENHO_SO_EM` e `PERMITIDOS` do `test_fronteira.lua` (exceção exata:
arquivo, trecho, regra, motivo e número de linhas; a órfã reprova). O LuaJIT da máquina não é o
do runtime: um digest de determinismo das mesmas sementes sai em LuaJIT, Lua 5.x e dentro do
LÖVE, com o JIT dele e com `jit.off()`. O passe em `luajit -joff` (cerca do dobro do tempo
`[medido]`) não espelha mais o celular: o `main` deixou de desligar o JIT no ARM (armadilhas,
Android), e forçar `jit.off()` é **decisão aberta do autor**.

**LuaLS.** O 3.18.0 do mason está na máquina, fora do PATH, com as anotações love2d da 11.5, que
erram o 12 caladas (armadilhas, LuaLS e anotações). Um `tools/luals_check.sh` roda `--check` com
`runtime.version = "LuaJIT"` e `undefined-field` como erro. A anotação do LÖVE é do projeto,
**sozinha** no `.luarc`: só o que o jogo chama, com a citação, e um teste confere cada nome
contra o dump e as deprecadas; a de tabela que cruza módulos tem teste que a prende ao
construtor (`ai-first-defold`, Verificação estática).

**Portão sem compilador.** O LÖVE não tem build que reprove: o portão faz o papel do bob.
- `loadfile` em todo `.lua`, em LuaJIT e em Lua 5.x (no CampCrawler, 120 arquivos em 29 ms no
  LuaJIT `[medido]`), e busca textual do que o LuaJIT aceita e a regra proíbe (`goto`, que o
  LuaJIT 2.1 compila `[medido]`);
- todo `require` literal resolvido para um arquivo da árvore do jogo, sem `/` no nome;
- todo asset do manifesto carregado de uma vez numa passada, e o gerador com `--check`;
- o pacote derivado de raízes declaradas e exclusões com motivo, com `--check` (lista velha ou
  entrada de topo sem dono reprova) e zip determinístico (ordem e datas fixas);
- cobertura de glifos de todo texto da tabela de idiomas, contra o `cmap` de cada fonte;
- o LuaLS e a suíte; o `--rapido` e o hook nunca abrem o LÖVE.

**Sem rede, terceiros registrados.** O portão e o `--rapido` se relançam em
`unshare --user --map-current-user --net` e reprovam interface além de `lo` em
`/proc/self/net/dev`, ou passo pulado; baixar é só do preparo, fora do portão (armadilhas, Rede,
licença e terceiros). Um teste reprova `socket`, `https`, `enet`,
`package.loadlib` e `openURL` no `.love`. Todo terceiro do artefato e do fonte fixado casa uma
linha do registro único (`CREDITS.md`: SPDX, onde, obrigação), e cabeçalho de terceiro fora de
`vendor/` reprova.

**Passadas.** O executor das passadas (o par do `smoke.py` da ai-first-defold) abre o jogo pelo
lançador, com prazo, em série (paralelo só se a série medida passar do orçamento, com uma tela
por passada), e o fato `TEMPO` de cada uma. Regras:
- toda passada declara o vídeo (`--video=nenhum|gl|x11`; o `x11` é o de xdotool e
  redimensionar), e o ambiente se monta por **lista branca**, nunca por cópia do de fora: idioma
  fixo, `ALSOFT_DRIVERS=null`, `XDG_*` num `mktemp -d` (a passada exige `save=` e `log=` dentro
  dele: ferramenta nunca escreve na save real), `SDL_VIDEO_DRIVER` e `--renderers` explícitos,
  só o `DISPLAY` do Xvfb criado, e as variáveis da passada. Sem vídeo, nenhuma janela (a variante
  é a que reprova um `getDimensions` plantado), PNG e fonte por `love.image` e `love.font`, e
  tamanho, DPI e área segura injetados;
- a passada roda no modo do autor (fundido ou não), com a deprecação ligada no `conf.lua`;
- **o fim é pelo plano**: o robô termina no `FIM`, com dt fixo; prazo estourado, morte por
  sinal ou quit sem `FIM` reprovam, qualquer que seja o código;
- o executor lê a saída linha a linha e cobra `--exigir`, `--recusar` e `--erro-esperado`
  ancorados em `^<PROJETO> `. **Todo `--recusar` vem com um `--exigir` de presença e contagem
  mínima declarada, nunca zero**: a recusa de uma linha que nunca nasce aprova qualquer coisa;
- as linhas que ele reprova sozinho são só as **medidas no LÖVE do lock**, cada uma com o caso
  que a provoca; as candidatas lidas: `Error: ` no começo da linha, `LOVE - Warning: `,
  `This game indicates`, `Cannot load game`, `No code to run` e `Screenshot encoding or saving
  failed` (armadilhas, Lançamento e argumentos; Saída, erro e log);
- **não confie no código de saída**: a prova é a linha exigida; a passada de recusa dá a chave
  com valor errado, exige o erro com o recebido e recusa o `INICIO`;
- uma passada roda **o `.love` gerado, com o diretório atual numa pasta vazia fora da
  worktree**, e exige o `codigo=` da pasta.

**Amostra de pixel.** Numa passada com janela, `captureScreenshot` com a variante de função (que
recebe o `ImageData` e não engole a falha), nos quadros `PRONTO` e no último. No centro e nas
bordas de cada item marcado com `probe`, a medida segue o `kind`: `rect`, a cor; `image`, o
texel do atlas vezes a cor do item; `text`, a fração de tinta contra o fundo (nunca o centro).
O resumo se cobra com referência na regex
(`AMOSTRA_RESUMO marcados=([1-9]\d*) amostrados=\1 falhas=0`), com o mínimo por vista num
teste; item marcado sem ponto limpo sai com `motivo=sem_ponto`. A marcação escolhe, por papel,
estado e tipo, o item com ponto a amostrar descoberto (o sprite pelo centro; o rect e o ladrilho
que a vista declara opaco, por qualquer candidato): o item sob outro, como a porta sob a tropa
parada, não tem ponto. O esperado da imagem lê o retângulo de quem empacotou o atlas, nunca o
`Quad` que o render usa: lido do mesmo objeto, o quad deslocado desloca o desenho e o esperado
juntos e passa (CampCrawler 7f540d4). Além do alfa 1, confira a borda de alfa (o pixel que mistura
texel opaco e transparente) pelo blend sobre o item de baixo, quando ele é computável: é o único
ponto em que o blend errado aparece, e só numa escala que mistura (armadilhas, Gráficos e pixel).
A captura externa não pede ferramenta nova: o Xvfb grava o framebuffer em XWD (`-fbdir`, com
`-nocursor`), que a biblioteca padrão lê; o jogo segura o quadro amostrado até o executor copiar
o arquivo (o framebuffer é vivo, e a tela anima no repouso), e o executor confere cada ponto da
interna, somada a posição da janela (CampCrawler b84fccb). **A tolerância se fixa nas
execuções limpas (dezenas), antes de plantar o defeito**, e o limiar de uma referência é do
autor. A captura sai depois do aviso de deprecação (armadilhas, Gráficos e pixel). Cor de
verdade: máscara e quadro fixo (`references/gerais-de-jogo.md`, Captura, cor e enquadramento).

**xdotool.** Sob Xvfb, o condutor espera o `PRONTO`, faz `xdotool mousemove --sync X Y click 1`
no `ALVO` relatado (a posição da janela mais o centro, em pixel) e exige `ENTRADA alvo=<id>` a
≤ 0,5 px e o efeito, em escala 1 e numa escala forçada. É o caminho do sistema (X11 → SDL3 →
LÖVE → adaptador → hit-test) e prova a entrada, não o layout; o aparelho fica com o adb. O
redimensionar também se prova por ele (`xdotool windowsize`), não pelo `updateMode`.

**Texto medido.** Cada vista exporta os pares (chave do texto, caixa) que desenha; a bancada da
passada com janela mede todos com a fonte real, em todo idioma e tamanho, e emite
`TEXTO estouro=` e `TEXTO_RESUMO medidos=<n>`, com `n` = pares × idiomas × tamanhos. Na suíte,
todo `text` da lista tem par, e toda chave da tabela de idiomas tem par ou isenção com motivo.
Uma fonte por escrita, sem fallback, num cache com dono (armadilhas, Texto e fonte).

**Captura para o autor.** Uma ferramenta abre o jogo sob Xvfb com o robô, nos tamanhos e
arranjos da constante, e grava as capturas: o olhar fica repetível, sem substituir o aparelho.
Base, referência e fixture nunca se regravam para o portão passar.

**Hook Stop.** O `hook_portao.sh` da ai-first-defold é o modelo: roda o `--rapido` (suíte,
fronteira, `loadfile`, requires e LuaLS, sem rede) só quando algo mudou desde a última
aprovação; o digest soma a árvore do jogo e, no porte, o domínio.

**Prove que o portão reprova antes de confiar nele.** Plante, rode e restaure:
1. `local L = love` numa vista, `require("ffi")` no domínio, `require("plat" .. "form.render")`
   numa vista, um `love.graphics.print` no `main.lua` e um `platform/hud.lua` que desenha → a
   **fronteira** reprova; a mesma árvore limpa numa `.claude/worktrees/<nome>/` aninhada ou
   desempacotada em `build/` → ela passa (o falso vermelho leva a afrouxar o teste);
2. um `require` de módulo que o empacotador não leva → a **passada do `.love`** reprova, e a da
   pasta passa; um byte mudado no `.love` → o `codigo=` reprova;
3. um `--config=` antes da pasta, ou `LD_LIBRARY_PATH=/usr/lib` → o **lançador** reprova;
4. um SIGTERM aos 2 s → a passada reprova, embora o processo saia com 0;
5. uma API deprecada chamada duas vezes no `love.load`, ou `t.version = "11.5"` → a passada
   reprova **pela linha**, não pelo prazo;
6. tirar o relançamento sem rede → o portão reprova;
7. um soldado parado em cima do número → a **invariante** da suíte reprova;
8. um deslocamento no renderizador que a lista não conhece → a **amostra de pixel** reprova;
9. um hit-test meia célula deslocado → o **xdotool** reprova, e o robô, que empurra o evento já
   na unidade do jogo, aprova: é o autorrelato;
10. uma conta de layout errada que move desenho e toque juntos, sem sair da janela → nenhuma
    das camadas automáticas pega se nenhuma invariante a cobre: diga isso, e a captura vai ao
    autor.

## 4. Android

`love-android` `main` (4c65fff). O como (pasta do jogo, gradle, NDK, SDK, o que falta na
máquina) está em `references/armadilhas.md`, Android. A frente só abre com uma decisão do autor;
antes, nada de `android/`, SDK ou emulador no repositório, e instalar pede o sim dele.
- Prova no aparelho: `adb shell input tap X Y` (um dedo) e `adb shell input swipe X Y X Y 300`
  (toque longo), em pixel físico, convertidos da unidade da lista com teste. O log por
  `adb logcat`, sem o prefixo `[LOVE] ` antes de cobrar, com fato e erro só por `print` e linha
  de até 4.000 B; a tela por `adb exec-out screencap -p`; o arquivo da partida por `adb pull`.
  O mesmo adaptador já ignora o toque do mouse físico; multitoque real fica com a mão do autor.
- O love-android mora fora do repositório, num checkout limpo no sha do lock, remendado só por
  `.patch`; o agente não trabalha de dentro dele (o megasource traz `AGENTS.md` e `CLAUDE.md`).
  A verificação do APK lê o manifesto mesclado (alvo, `appCategory`, permissões, exportados,
  backup, `debuggable`) e o alinhamento de 16 KB de cada `.so`. Chave e senha de release são do
  autor, nunca em repositório, prompt ou log.
- **Abertos do autor**: Android agora ou como custo do porte; aparelho-alvo; orientação, tela
  cheia ou imersivo, o que o botão voltar faz, idioma do sistema (armadilhas, Android); forçar
  `jit.off()` no ARM (o `jit=` do `INICIO` mostra o que vale); console de teste no APK
  de teste e o sinal de debug do build; o mesmo sha no desktop e no Android (o love-android
  compila outro commit do LÖVE); licenças no APK.

## 5. Armadilhas

`references/armadilhas.md`: cada uma com sintoma, causa, remédio e citação. Antes de investigar
um sintoma, procure-o lá.

## 6. Gerais de jogo

`references/gerais-de-jogo.md` é cópia: a fonte única é o `gerais-de-jogo.md` da raiz do
repositório das skills, copiado pelo `distribuir.py --copiar-gerais` e conferido pelo `--check`
(no ramo, pelo `--check-gerais`). Lição nova de jogo vai lá, nunca na cópia.

## Convivência

- Todo LÖVE automatizado: pelo lançador, com prazo, Xvfb e ambiente de lista branca, log lido
  linha a linha; encerre só o processo que você abriu, por PID.
- `.love`, binários e caches em `build/`, `mktemp` ou, fora da worktree, num cache chaveado por
  sha ou worktree, declarado como exceção do teste de caminhos; nunca na raiz.
- O binário do LÖVE e o LuaLS são da máquina e nunca entram no repositório; o `runtime.lock`,
  que os fixa, entra.
- Instalar o LÖVE ou dependência, baixar artefato, serviço externo (CI), rede e telemetria no
  jogo, assinatura e publicação pedem aprovação do autor.
- Remover código, levar para a `main` ou enviar ao remoto: confirme com o usuário.
