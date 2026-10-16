<!--
Modelo da skill ai-first-defold para a seção Defold do AGENTS.md de um projeto.
Copie, troque o que está entre <>, e apague o que não se aplica. O AGENTS.md é lido pelo
Codex e pelo Claude Code (v2.1.277 ou mais nova), e pode ser o único arquivo de instruções do
projeto. Mas o Claude Code o ignora em silêncio se houver CLAUDE.md ou CLAUDE.local.md na pasta
do projeto ou acima dela, inclusive no checkout principal que contém as worktrees: escolha um
dos dois, ou ponha `@AGENTS.md` no topo do CLAUDE.md. Mantenha nele só regra do projeto, curta
(o manual oficial de agentes da Defold pede o mesmo).
-->

## Defold

- Versão fixada: **Defold <1.14.0>**, pelo bob do editor instalado (`bob.jar` de 370 bytes +
  link `defold-editor.jar`, da máquina, nunca do repositório). Não use API de outra versão; na
  dúvida, consulte <https://defold.com/llms.txt>, o `/ref` do editor aberto e as anotações que o
  `tools/luals_check.sh` extrai do jar, não a memória. O editor se atualiza sozinho: o JDK entra
  no PATH por `$(command ls -d /opt/Defold/packages/jdk-* | head -1)/bin`, e seguir a versão nova
  é decisão <do autor>.
- Rode `tools/portao.sh` antes de dizer que terminou. **Não use o código de saída do motor como
  prova**: peça ausente não emite erro. A prova é a linha de log que o portão exige.
- Execute o bundle a partir da pasta dele (o motor carrega `build/` relativo ao diretório atual)
  e uma instância por vez (disputam porta). Encerre só o processo que você abriu, por PID.
- Com o editor aberto no projeto, fale com ele pela API HTTP: porta em `.internal/editor.port`,
  operações lidas do `/openapi.json` (não decoradas), log do jogo rodado pelo editor em
  `/console`; `POST /command/compile` compila sem rodar. É experimental e não substitui o
  portão. `/eval` só com pedido explícito; o `.internal/editor.token` nunca vai para prompt nem
  log.
- A prova pela Automation Bridge (`tools/bridge.sh`) fica fora do portão porque compila no
  servidor de build da Defold: rode-a em <toda frente que mexe em entrada, layout ou tela nova> e
  diga no relatório final se rodou. O jogo roda mudo em toda prova (`ALSOFT_DRIVERS=null`).
- Pede aprovação antes: apagar, mudar dependência ou extensão nativa, configuração de release,
  assinatura, publicação e serviço externo.

### Organização

- `<modules>/`: regras em Lua puro, sem `go`, `gui`, `msg`, `sys`, `vmath`, `timer`, `hash`,
  relógio nem `math.random`. Ações, tempo e semente entram como parâmetro. `tests/test_fronteira.lua`
  cobra isso.
- `<main>/`: coleção, scripts e GUI. Um script é dono da sessão e da apresentação.
- `tests/`: `tests/test_*.lua`, rodados por `./run_tests.sh` em LuaJIT **e** num Lua 5.x.
- `tools/`: portão, smoke, LuaLS, geradores com `--check`, prova da Bridge.

### Código

- Lua 5.1 portátil: `local` em tudo, sem `goto` (o bob aceita), sem operador bit a bit nativo,
  divisão inteira com `math.floor` (no Lua 5.3+ a `/` devolve float, e o texto sai `3.0`). Nada
  exclusivo do LuaJIT na regra.
- Tabela que cruza módulos tem forma documentada no construtor; enumeração é string constante do
  módulo, validada na fronteira. Erro de contrato é `error()` com o valor recebido e o esperado.
- **Entrada:** um só binding por gesto. Ligue `MOUSE_BUTTON_LEFT` a `touch` e **não** ligue
  `TOUCH_MULTI` à mesma ação: no celular o primeiro dedo já chega como mouse, e os dois juntos
  disparam cada toque duas vezes. Um único `on_input` traduz o gesto numa ação de domínio.
- **Toque em nó:** `gui.pick_node` nó por nó, nunca aritmética sobre `action.x`, e só em nó
  ligado: `gui.is_enabled(no, true) and gui.pick_node(...)`, porque o `pick_node` acerta nó
  desligado.
- **Animação:** uma propriedade animada tem um único dono. O segundo `go.animate`/`gui.animate`
  na mesma propriedade cancela o primeiro **e descarta o callback dele**. Prefira posição
  calculada por função pura e aplicada por um só script.
- **Sorteio:** gerador próprio com semente (não `math.random`: é global, tem semente padrão fixa e
  15 bits). A semente usada sai no log.
- **Replay:** o log de ações registra **toda** passagem de estado que a regra aceita, inclusive
  a que parece não mudar nada (uma leitura, uma recompensa pulada), e o replay reaplica o que
  está escrito. Deduzir um passo pela falta de outro só vale onde a falta tem uma leitura só (a
  run seguiu, então o mapa do meio sem escolha foi pulado); onde o original parou há duas, e só
  a marca decide: sem ela, a cópia não sabe se o original esperava a apresentação ou já tinha
  pulado e esperava outra escolha. Um teste da suíte tira o log em cada parada de muitas runs e
  confere a cópia (mapa e estado) contra o original. CampCrawler, três vezes: a leitura do
  Batedor fora do log divergiu 21 de 150 runs (D47); deduzir o pulo no último mapa levou a
  cópia um mapa adiante (D51), e não deduzir a fez deixar de pular antes da escolha da classe
  (D56, auditoria A3: `skips` no log marca o último mapa).
- **Mensagens:** `msg.post` entrega no próximo despacho; nada lê o efeito na linha seguinte.
  Objeto que posta com atraso carrega a época da montagem; quem recebe compara.
- **Observabilidade:** cada fato verificável sai numa linha `print("<PROJETO> <FATO> k=v ...")`
  com campos em ordem estável, de dentro do galho que comprova o fato (ex.: depois de o
  `pick_node` acertar). Toda borda de toque também vira fato. Sem robô, a mesma linha vai também
  para o arquivo da partida (`fact_log.lua`), junto com os erros de Lua, e o
  `project.write_log_file = 1` guarda o log inteiro do motor: o console do editor some ao fechar.
  Dado novo vai numa **linha nova** (`<PROJETO> CAUSA ...`), não num campo a mais de uma linha
  que já existe: os campos saem em ordem alfabética, o novo cai no meio, e todo `--exigir`
  ancorado nela reprova. Campo que só às vezes existe sai só quando existe. Quem lê log de
  playtest trata linha ou campo ausente como o jogo de antes dele. CampCrawler: `CAUSA`,
  `ENCONTRO` e `EXPERIMENTOS` em linhas próprias (D47 a D56), `pedras=` só no mapa com pedra
  (D50), e o resumo leu errado o log de antes da `EXPERIMENTOS` até a auditoria (B1–B6).
- Texto de tela vem de uma tabela de idiomas; fonte com `extra_characters` gerado dessa tabela.
- Nó de GUI criado em código que alguém de fora precisa achar ganha `gui.set_id` estável.

### Recursos e arquivos

- `.collection`, `.go`, `.gui`, `.atlas` e `game.project` são texto: edite e confira com o
  build. O bob **não** pega id duplicado de game object ou de nó, chave errada no `game.project`
  nem animação de atlas inexistente (essa só falha quando o caminho roda).
- `game.project` referencia recurso compilado: `/input/game.input_bindingc`, `/main/x.collectionc`.
- Asset gerado sai de um gerador versionado com `--check`; todo asset entra no `CREDITS.md` com
  origem e licença no mesmo commit.

### Testes e prova

Teste primeiro (TDD). Cobertura segue risco: TDD não é um teste por função.

- **Funcionalidade nova ou regra que muda:** o teste vem antes do código e é visto **falhar
  pelo motivo certo**, o comportamento ausente. Erro de ambiente, de carregamento ou de função
  que ainda não existe não conta: crie antes o esqueleto que carrega e compila, e só então veja
  o vermelho. Depois, o código mínimo que o faz passar; depois, refatore com tudo verde.
- **Onde o teste mora:**
  - regra de domínio → `tests/test_*.lua`, na suíte sem engine (LuaJIT e Lua 5.x);
  - peça de cena, tela ou entrada → um fato emitido de dentro do galho novo e o `--exigir` dele
    numa passada do portão que **alcança** a peça. O vermelho é a passada reprovar pela linha
    ausente, não por build quebrado ou erro de Lua. Se o robô não chega lá, dê a ele um atalho
    de início validado (andar, upgrade), não uma exceção no portão. Defeito que é linha a mais:
    um fato emitido uma vez, ao fim do trecho, carrega a contagem, e o `--exigir` casa nela
    com âncora (`' n=1$'`);
  - layout e o que só a entrada real reproduz (toque duplo no aparelho) → prova da Bridge,
    como acima; a causa que é texto (o binding, uma chave) ganha também teste na suíte;
  - ferramenta de `tools/` → teste que alguém roda: em Lua, `tests/test_*.lua` na suíte; o
    resto, chamado pelo `tools/portao.sh`.
- **Bug:** primeiro o teste que falha **pelo defeito**, na camada da lista acima, depois a
  correção. O teste fica para sempre (o item Teste existente diz quando pode sair): na suíte,
  numa passada ou verificação do portão ou, se só a Bridge o mede, na prova da Bridge, no mesmo
  commit da correção. Vale para todo bug reproduzível, não só o determinístico; no domínio, com
  semente e sequência de ações.
- **Teste existente** (asserção da suíte, `--exigir` de passada): se a regra muda, trocar a
  expectativa dele é o vermelho dela e vem antes do código. Mesmo nesse caso, e para inverter,
  afrouxar, apagar ou pular o caso para o código novo passar: só com justificativa no commit
  (a do PR sozinha não fica no histórico) e com o caso antigo coberto por outro teste onde a
  expectativa antiga ainda vale, se houver (outro modo, a chave que volta à regra anterior); se
  ela não vale mais em modo nenhum, o commit diz isso. A asserção invertida esconde o defeito do
  modo que ela protegia.
- **Exceções**, sempre declaradas no relatório e no commit. Exceção é uma alegação, não um
  passe: refatoração que muda comportamento não é exceção.
  - refatoração sem mudança de comportamento: os verificadores que existem (suíte e passadas do
    portão) são a rede; onde eles não cobrem o trecho, um teste de caracterização vem antes;
  - o que só o olho ou o aparelho julga (legibilidade, sensação tátil, arte): o julgamento fica
    com captura ou aparelho, e o relatório diz que ali não há teste automático; o caminho da
    peça continua alcançado e cobrado pelo portão;
  - o teste que não deu para ver falhar antes (o comportamento já existia): escreva-o mesmo
    assim, veja-o reprovar plantando o defeito (ou revertendo o código), restaure e diga isso.
    Em correção de bug essa exceção não vale: teste de regressão que passa na base não
    reproduz o defeito;
  - o bug que não se reproduz em teste automático (nem pela Bridge no aparelho: defeito de um
    quadro visto em captura): diga como ele foi visto e o que se tentou para reproduzir; o
    caminho continua alcançado pelo portão.
- **Evidência:** o commit e o relatório dizem o comando, o vermelho de antes e o verde de depois
  (o PR pode repetir). O portão e o hook Stop só cobram o verde; o vermelho é você quem vê e
  registra.
- Ao criar ou mudar um verificador, prove que ele reprova: plante o defeito, rode, restaure.
- O `AGENTS.md` fica abaixo dos 32.768 bytes que o Codex lê (o resto ele corta calado), e
  `tests/test_agents_md.lua` reprova acima disso.
- **Lição volta para a skill** (quando o projeto usa as skills ai-first): armadilha do Defold
  resolvida no projeto vira lição na skill `ai-first-defold` (com a versão medida, ou `[doc]`);
  lição de jogo que não é do motor vai também para a `ai-first-godot`. Na mesma frente do
  conserto, conferindo antes se já está lá. A lição entra num ramo numa worktree fora do `/tmp`
  (`git -C ~/.claude/skills worktree add ~/.cache/claude-skills-wt/<ramo> -b <ramo> main`), nunca
  trocando o ramo de `~/.claude/skills`, que toda sessão carrega e fica no `main`; push e PR
  esperam o sim <do autor>.
- Dependência nova, extensão nativa, serviço externo, signing e publicação pedem aprovação.
