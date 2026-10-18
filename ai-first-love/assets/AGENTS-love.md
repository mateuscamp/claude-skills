<!--
Modelo da skill ai-first-love para a seção LÖVE do AGENTS.md de um projeto.
Copie, troque o que está entre <>, e apague o que não se aplica. O AGENTS.md é lido pelo
Codex e pelo Claude Code (v2.1.277 ou mais nova), e pode ser o único arquivo de instruções do
projeto. Mas o Claude Code o ignora em silêncio se houver CLAUDE.md ou CLAUDE.local.md na pasta
do projeto ou acima dela: escolha um dos dois, ou ponha `@AGENTS.md` no topo do CLAUDE.md. O
Codex soma os AGENTS.md da raiz do repositório até a pasta e corta acima de 32.768 bytes.
Nenhum caminho absoluto do projeto entra aqui: a pasta pode mudar de lugar.
Tudo do LÖVE nesta seção é lido no fonte até o projeto medir; a skill guarda a citação.
-->

## LÖVE

- Versão fixada: **LÖVE <main@b7daef0> (12.0, não lançado)**, pela via que <o autor> escolheu
  (<AppImage do CI | AUR `love-git` com `#commit=<sha>` | receita>). O runtime mora fora do
  repositório (`$LOVE_RUNTIME`); o `runtime.lock`, aqui, guarda sha, origem e sha256 de todo
  arquivo dele. `love.getVersion()` só diz `12.0`: o `INICIO` leva `love_sha=`, `exe=` (sha256
  lido de dentro), `libs_fora=`, JIT, renderer, vídeo e modo fundido. Trocar de sha é decisão
  <do autor> e roda o portão inteiro.
- Afirmação sobre o LÖVE (aqui, numa armadilha, na anotação ou no comentário da linha que existe
  por comportamento dele) cita `love:<caminho>:<linha>@<sha7>` ou `[medido@<sha7>]`. 11.5, wiki
  e memória são pista: leia o fonte do sha fixado e `references/armadilhas.md` da skill
  `ai-first-love`; a API existe se o dump rodado pelo binário do lock a lista.
- Rode `<tools/portao.sh, a criar>` antes de dizer que terminou. **Não use o código de saída do
  LÖVE como prova**: peça ausente não emite erro, e o SIGTERM do prazo sai com 0. A prova é a
  linha de log que o portão exige.
- Lançamento: só por `<tools/love> <pasta ou .love> --config=...`, nunca pelo `love` do PATH. O
  lançador confere o lock, limpa `LD_*` e `LUA_*` e põe a pasta logo depois das opções do LÖVE
  (um `--x` antes dela vira o caminho do jogo). Toda prova roda sob Xvfb, muda e com o ambiente
  montado por lista branca. Encerre só o processo que você abriu, por PID.
- A prova pela entrada do sistema (xdotool sob Xvfb), a amostra de pixel e a captura para o
  autor rodam em <toda frente que mexe em entrada, layout ou tela nova>; diga no relatório final
  se rodaram. No aparelho, `adb shell input`, `adb logcat` e `screencap`.
- Pede aprovação antes: instalar o LÖVE ou qualquer dependência, baixar artefato, apagar,
  serviço externo (CI), rede ou telemetria no jogo, configuração de release, assinatura e
  publicação. Chave e senha de release nunca entram em repositório, prompt ou log.

### Organização

- `<modules>/`: regras em Lua puro, sem nada do que a tabela `PURO` de `tests/test_fronteira.lua`
  proíbe (ela é a lista) e sem `require` fora de `<modules>`. Ações, tempo e semente entram como
  parâmetro.
- `<scene>/`: orquestração, vistas, hit-test e o adaptador de entrada, também Lua puro. A vista
  é `build(mostrado, layout, relógio, medidor) → lista de desenho`, com a entrada estrita (o
  mostrado sem função, userdata nem metatable); não conhece `love` nem `platform/`. O adaptador
  recebe os argumentos crus do callback e devolve a ação; por ser Lua puro, o teste dele com a
  sequência do aparelho roda na suíte.
- `<platform>/`: o único que chama `love`: o `love.run`, o repasse do callback cru ao
  adaptador, o renderizador da lista, as fontes, o som, o arquivo da partida e o save.
- `conf.lua` e `main.lua` só montam (boot e callbacks; falam com `love` só para isso).
  `tests/test_fronteira.lua` cobra as três fronteiras: domínio e vistas sem `love` nem
  `require` fora da lista de permissão, e `graphics` só nos arquivos de `DESENHO_SO_EM`:
  renderizador, laço e `conf.lua`; fontes (`<platform/fonts.lua>`) e captura, por nome.
- `tests/`: `tests/test_*.lua`, rodados por `./run_tests.sh` em LuaJIT **e** num Lua 5.x.
- `tools/`: lançador, portão, executor das passadas, LuaLS, empacotador do `.love`, geradores
  com `--check`. Nenhum caminho absoluto fixo: saída em `build/` ou `mktemp`, e um teste recusa
  `$HOME`, `~` e `XDG_*` em `tools/` fora das exceções declaradas.

### Código

- Lua 5.1 portátil: `local` em tudo, sem `goto`, sem operador bit a bit, divisão inteira com
  `math.floor`, e nunca atribuir à variável do `for` (o Lua 5.5 não compila). Nada exclusivo do
  LuaJIT nas regras.
- Tabela que cruza módulos tem forma documentada no construtor; enumeração é string constante do
  módulo, validada na fronteira. Erro de contrato é `error()` com o valor recebido e o esperado.
- **Tipos:** comece pelas tabelas que cruzam módulos (evento, configuração, resultado de ação,
  item da lista de desenho): `---@class`, um `---@field` por campo e `---@return` no construtor.
  `undefined-field` é erro no LuaLS, e um teste da suíte prende a anotação ao construtor.
- **Lista de desenho:** o item é o `DrawItem` de `<scene/draw_list.lua>` (esboço na skill:
  `assets/draw_list.lua`): `id` estável e único, vindo da identidade no domínio (célula,
  soldado, botão), nunca do índice na lista nem de contador do quadro; `kind` (`rect`, `image`,
  `text`); `layer`, inteiro de constante nomeada de `<scene>/`, e `seq` (ordem: camada, depois
  inserção; o `table.sort` não é estável); retângulo em coordenadas de tela, `color` de 0 a 1,
  `image` do manifesto, texto com `font_role`, `size_px`, `align` e `wrap_w`, `role`, `state`
  quando uma invariante precisa dele; `hit` e `target` no que aceita toque, o `target` como a
  intenção em dado (`{ action = <...>, <campos do projeto, como cell_x e cell_y> }`: x e y de
  tela não circulam); e `probe = true` no item que a amostra de pixel confere. O construtor
  estoura, com o recebido, em campo fora da forma (nome ou tipo), `kind` inválido, `id`
  repetido, imagem fora do manifesto, cor fora de [0, 1] e `target` sem `action` ou com x e y.
  O `love.draw` só percorre a lista, sem transformação; a expansão do item em argumentos de
  desenho é pura e testada. O estado **mostrado** só avança pelo evento entregue pela fila de
  apresentação; no repouso, um fato o compara ao domínio (diferença 0 exigida) e nunca o
  sobrescreve: sobrescrever esconderia o handler que falta.
- **Entrada:** um adaptador só, em `<scene>/`, a quem a plataforma repassa o callback cru: só o
  `mousepressed` do botão 1 vira ação, `touch*` é ignorado, e outro callback tem um uso
  declarado. O dedo chega como mouse (com `istouch`) e depois como toque; só o primeiro dedo vira
  mouse; no Android o mouse físico também gera toque. As sequências do teste
  do adaptador saem de uma gravação dos callbacks crus no aparelho e no desktop (até lá, a ordem
  lida, com a citação no nome do teste). **A coordenada morre no hit-test** da lista apresentada
  (a do último `present`): o item de cima com `hit`, alfa > 0 e centro na janela que contém o
  ponto; dali em diante só circula a ação (`kind`, `id`, `target`). Alvo coberto ou em parte
  fora da janela: <decisão do autor, declarada na tela>.
- **Robô:** acha o alvo pelo `id` na lista apresentada, até K quadros, e entra só por
  `love.event.push`, com a tupla inteira (`false`, nunca `nil`) e o ponto preso na janela; nunca
  chama o adaptador. Nada do jogo lê `love.mouse` nem `love.touch`. Cada toque emite `ROBO`,
  `ENTRADA alvo=<id>` e `ALVO`; `TOQUE_ERRADO` e `TOQUE_PERDIDO` são recusados.
- **Laço:** `love.run` próprio (esboço: `assets/loop.lua`), na ordem robô → `pump` → handlers →
  update → draw → present, e só então a lista nova vale. dt fixo no robô; o replay usa o dt
  gravado (no jogo, o real com teto de 1/30 s). Descarte do quadro de volta do segundo plano,
  contador de quadro, gravação de entrada e dt por quadro, e `love.event.setModalDrawCallback`
  que só redesenha a apresentada.
  Sem vídeo (`love.graphics` nil), a lista do quadro vale como apresentada.
  Só o fato `FIM`, num lugar, chama `love.event.quit(0)`; quit sem `FIM` sai com código próprio.
  Domínio e vista nunca leem relógio: o tempo da apresentação entra como parâmetro.
- **Início** (esboço: `assets/conf.lua`): as primeiras linhas do `conf.lua` são
  `io.stdout:setvbuf("line")` e o `love.errorhandler` do projeto, antes de qualquer `require`;
  na passada, também `love.setDeprecationOutput(true)`. O handler imprime o traceback, grava no
  arquivo da partida e, nas passadas, sai com código próprio; na partida do autor,
  <parar na tela de erro | seguir com a linha no log>. `t.identity = "<projeto>"`,
  `t.appendidentity = true` (a save não sombreia o código), `t.version = "<12.0>"` (outra
  versão abre caixa modal) e `t.window = false`: a plataforma abre a janela no `love.load`,
  depois do parser (`love.window.setMode` com `resizable = true` e, na passada, `vsync = 0`).
  `<PROJETO>_VIDEO=nenhum` desliga também `t.modules.window` e `t.modules.graphics`: a passada
  sem vídeo. `t.graphics.renderers` e o `usedpiscale` do `setMode` = <decisão do autor>.
- **Código só pela árvore:** o `main.lua` e cada thread zeram `package.path` (<salvo a via
  medida do domínio>), `package.cpath` e `love.filesystem.setCRequirePath`. `require` literal e
  no topo (condicional só de módulo opcional, atrás da constante de build); `dofile`, `load`,
  `io` para ler e `mount` só na plataforma e no boot; `isFused()` não decide nada.
- **Configuração:** um parser nosso em `love.load(args)`, módulo puro, lê só
  `--config=<projeto>.<chave>=<valor>`, sobre `1..#args`. Chave desconhecida ou repetida,
  argumento solto e valor ruim estouram com o recebido; nenhum padrão calado; cada chave lida sai
  num fato `CONFIG chave= valor= origem=`. Os padrões moram numa tabela Lua do repositório. Toda
  leitura de configuração mora nesse módulo; fora dele, só o `conf.lua` lê as duas variáveis que
  o executor das passadas põe (`<PROJETO>_PASSADA` e `<PROJETO>_VIDEO`), e um teste estático,
  que as conhece pelo nome, reprova qualquer outra leitura de argumento ou de ambiente.
- **Sorteio:** gerador próprio com semente (não `math.random` nem `love.math.random`). A semente
  usada sai no log.
- **Replay:** o log de ações registra toda passagem de estado que a regra aceita, e o replay
  reaplica o que está escrito; o replay da cena refaz a lista por quadro, e o defeito de um
  quadro se acha pelo primeiro quadro cuja lista difere entre duas execuções que deviam dar a
  mesma (gravação e replay; robô e xdotool; antes e depois, na mesma semente e com o mesmo
  medidor). A lista se serializa em ordem (`layer`, `seq`), com números por `string.format`; o
  dt se grava com ida e volta exata (`%.17g`, ou microssegundos inteiros), com teste na suíte.
- **Observabilidade:** cada fato verificável sai numa linha `print("<PROJETO> <FATO> k=v ...")`
  com campos em ordem estável, de dentro do galho que comprova o fato; `print`, não `io.write`
  (só o `print` chega ao logcat), e o emissor estoura acima de 4.000 B. Fato de tela (`LAYOUT`,
  `TEXTO`, `AMOSTRA`) sai da lista desenhada, com o valor do domínio ao lado (`esperado=`). Antes
  do `INICIO`, o `CODIGO` leva a digital da árvore (`codigo=`), `save=` e `log=`. Dado novo vai
  numa linha nova. A mesma linha vai para o arquivo da partida na pasta de save, com flush por
  linha, junto com o erro de Lua, e a primeira linha diz onde ele está
  (`<PROJETO> ARQUIVO caminho=...`). Com robô, o arquivo vai para o `mktemp` da passada (nunca
  para a save real).
- **Save e som:** `t.identity` fixo e a pasta de save criada no início. As passadas rodam no
  modo (fundido ou não) do autor, com o `XDG_DATA_HOME` num `mktemp -d`: ferramenta nunca escreve
  na save real, e a passada exige `save=` e `log=` dentro dele. Som tocado pela plataforma a
  partir de evento entregue, nunca decide regra; toda prova roda muda.
- **Texto:** todo texto de tela nasce em `<data/texts.csv>`, nos <N> idiomas de uma vez; nenhum
  literal com letra chega à tela (um teste varre a cena). Nunca a fonte padrão do LÖVE; uma
  fonte por escrita, escolhida pelo idioma, sem fallback. Só `<platform/fonts.lua>` cria, guarda
  (por escrita, papel e px, com teto) e libera fontes; o render recebe a fonte pelo argumento,
  nunca por `setFont`. A quebra é da vista; o medidor da suíte é injetado, declarado aproximado e
  devolve um intervalo: só afirma "cabe" ou "não cabe" quando o intervalo garante.

### Recursos e arquivos

- Asset sai de um gerador versionado com `--check`, entra no manifesto (o construtor da lista
  recusa nome fora dele) e no `CREDITS.md` com origem e licença no mesmo commit.
- Terceiro (biblioteca, fonte, arte, o próprio runtime) casa uma linha do `CREDITS.md` (SPDX,
  onde, obrigação); SPDX fora de <a lista aprovada> só com decisão do autor; cabeçalho de
  terceiro fora de `vendor/` reprova.
- `require("a.b")`, nunca `require("a/b")` (deprecado no 12: imprime `LOVE - Warning:` e desenha
  o aviso na tela). Dado de jogo lido por `love.filesystem`, não por `io`. Nenhum `.lua` do
  `.love` usa `socket`, `https`, `enet`, `package.loadlib` nem `openURL` (o runtime os traz).
- O `.love` é gerado pelo empacotador, derivado de raízes declaradas e de exclusões com motivo,
  em zip determinístico, com `--check` (lista velha ou entrada de topo sem dono reprova; <o
  console de teste no APK de teste: decisão do autor>). <Transitório, se o domínio vem de outro
  repositório: ele se lê de um commit nomeado (<pino no `dominio.lock` | ponta resolvida no
  lançamento>), nunca do checkout vivo; `<tools/dominio.py> --check` confere o servido contra o
  `git ls-tree` e sai com erro, nunca pula; o `CODIGO` leva `dominio=` e `dominio_hash=`, que a
  passada exige; mudança de regra vai lá.>

### Testes e prova

Teste primeiro (TDD). Cobertura segue risco: TDD não é um teste por função.

- **Funcionalidade nova ou regra que muda:** o teste vem antes do código e é visto **falhar
  pelo motivo certo**, o comportamento ausente. Erro de ambiente, de carregamento ou de função
  que ainda não existe não conta: crie antes o esqueleto que carrega, e só então veja o
  vermelho. Depois, o código mínimo que o faz passar; depois, refatore com tudo verde.
- **Onde o teste mora:**
  - regra de domínio → `tests/test_*.lua`, na suíte sem LÖVE (LuaJIT e Lua 5.x);
  - vista → as invariantes visuais dela na suíte, sobre a lista, nos tamanhos de janela e nos
    dois arranjos de `<a constante única que a suíte e a captura leem>`. **Quais invariantes
    valem para cada vista decide o autor**: a vista nasce com as que ele aprovou e com a captura
    mostrada a ele, e cada invariante cita a decisão (Dnn) ou a data da aprovação; o piso que
    ele não decidiu fica declarado provisório. O **esperado de geometria** é número escrito,
    fórmula independente ou a base do motor de origem (se ele a fez alvo), nunca a conta que o
    teste prova. Toda invariante tem mutante (trecho único, troca, teste que cai; a queda por
    erro de carga não conta), e um meta-teste exige invariantes em toda vista com `build`;
  - peça de cena ou entrada → um fato emitido de dentro do galho novo e o `--exigir` dele numa
    passada do portão que **alcança** a peça. O vermelho é a passada reprovar pela linha
    ausente, não por erro de Lua. Se o robô não chega lá, um atalho de início validado, nunca
    uma exceção no portão. Defeito que é linha a mais: fato com contagem e `--exigir` ancorado
    (`' n=1$'`). **Todo `--recusar` vem com um `--exigir` de presença e contagem mínima
    declarada, nunca zero**;
  - chave de configuração → teste do parser na suíte, com toda chave boa aceita e as ruins
    recusadas com o recebido, e uma passada de recusa para uma amostra: valor errado,
    `--erro-esperado` com o recebido e `--recusar` do `INICIO`;
  - o que a lista não prova sozinha (ela é autorrelato: desenho e toque vêm do mesmo código) →
    amostra de pixel nos itens com `probe`, na passada com janela (resumo `marcados=` igual a
    `amostrados=`, com o mínimo por vista), clique pelo xdotool sob Xvfb no `ALVO` relatado
    (`ENTRADA alvo=<id>` a ≤ 0,5 px e o efeito) e, no aparelho, `adb`; a conta de layout que
    move os dois juntos fica com a invariante da vista ou com a captura para o autor, e o
    relatório diz qual; a causa que é texto (o adaptador, uma chave) ganha também teste na
    suíte. **A tolerância se fixa nas execuções limpas, antes de plantar o defeito**; o limiar
    de uma referência é do autor;
  - ferramenta de `tools/` → teste que alguém roda: em Lua, na suíte; o resto, chamado pelo
    `<tools/portao.sh>`.
- **Bug:** primeiro o teste que falha **pelo defeito**, na camada da lista acima, depois a
  correção; ele fica para sempre, no mesmo commit da correção. Vale para todo bug reproduzível;
  no domínio, com semente e sequência de ações; na cena, com o replay e o primeiro quadro em que
  a lista difere.
- **Teste existente** (asserção da suíte, invariante visual, `--exigir`, `--recusar` ou
  `--erro-esperado`): se a regra muda, trocar a expectativa dele é o vermelho dela e vem antes do
  código. Inverter, afrouxar, apagar ou pular o caso para o código novo passar só com
  justificativa no commit e com o caso antigo coberto onde a expectativa antiga ainda vale (outro
  modo, a chave que volta à regra anterior); se ela não vale mais em modo nenhum, o commit diz
  isso. Invariante visual aprovada pelo autor só muda com ele. Base, referência e fixture nunca
  se regravam para o portão passar.
- **Exceções**, sempre declaradas no relatório e no commit (exceção é uma alegação, não um
  passe):
  - refatoração sem mudança de comportamento: suíte, invariantes e passadas são a rede; onde não
    cobrem, um teste de caracterização vem antes;
  - o que só o olho ou o aparelho julga (legibilidade, nitidez, sensação tátil, arte): o
    julgamento fica com a captura ou o aparelho, e o relatório diz que ali não há teste
    automático; o caminho da peça continua alcançado e cobrado pelo portão;
  - o teste que não deu para ver falhar antes: veja-o reprovar plantando o defeito, restaure e
    diga isso. Em correção de bug essa exceção não vale;
  - o bug que só se vê no aparelho ou numa captura: diga como foi visto e o que se tentou.
- **Evidência:** o commit e o relatório dizem o comando, o vermelho de antes e o verde de depois.
  O portão e o hook Stop só cobram o verde; o vermelho é você quem vê e registra.
- Ao criar ou mudar um verificador, prove que ele reprova: plante o defeito, rode, restaure.
- **O portão** (sem compilador, ele faz o papel do build) se relança sem rede
  (`unshare --user --map-current-user --net`; interface além de `lo` reprova) e roda: suíte em
  dois Luas (exige `luajit` e `lua`), fronteira, `loadfile` em todo `.lua`, todo `require`
  literal resolvido para arquivo, manifesto e pacote com `--check`, cobertura de glifos, LuaLS,
  e as passadas, em série e pelo lançador, cada uma com o vídeo declarado
  (`--video=nenhum|gl|x11`) e o ambiente por lista branca (`XDG_*` num `mktemp -d`, só o
  `DISPLAY` do Xvfb criado). Prazo, sinal ou quit sem `FIM` reprovam; o portão recusa só linhas
  do LÖVE medidas no lock, cada uma com o caso que a provoca; uma passada roda o `.love` gerado
  com o diretório atual numa pasta vazia fora da worktree e exige o `codigo=` da pasta. O
  `--rapido` e o hook nunca abrem o LÖVE.
- O `AGENTS.md` fica abaixo dos 32.768 bytes que o Codex lê, e
  `<tests/test_agents_md.lua, a criar: conta os bytes do AGENTS.md>` reprova acima disso.
- **Lição volta para a skill** (quando o projeto usa as skills ai-first): armadilha do LÖVE
  resolvida vira lição na `ai-first-love` (com `[medido@<sha7>]` ou a citação do fonte); lição de
  jogo que não é do motor vai para o `gerais-de-jogo.md` da raiz do repositório das skills, que
  o `distribuir.py --copiar-gerais` copia para cada skill de motor. Na mesma frente do conserto,
  conferindo antes se já está lá. A lição entra num ramo numa worktree fora do `/tmp`
  (`git -C ~/.claude/skills fetch`, depois `git -C ~/.claude/skills worktree add
  ~/.cache/claude-skills-wt/<ramo> -b <ramo> origin/main`), nunca trocando o ramo de
  `~/.claude/skills`; push e PR esperam o sim <do autor>.
