<!--
Modelo da skill ai-first-godot para a seção Godot do AGENTS.md de um projeto.
Copie, troque o que está entre <>, e apague o que não se aplica. O AGENTS.md é lido pelo
Claude Code (quando não há CLAUDE.md) e pelo Codex; mantenha nele só regra do projeto.
-->

## Godot

- Versão fixada: **Godot <4.7.2>**. Não use API de outra versão; na dúvida, consulte
  `godot --doctool <pasta> --no-docbase` em vez da memória.
- Rode `tools/portao.sh` depois de mudar regra, entrada ou cena. **Não use o código de saída do
  Godot como prova**: ele sai com 0 com erro de script no log. O portão lê o log.
- Todo Godot automatizado leva `--audio-driver Dummy` e `timeout`; prova visual sob `xvfb-run -a`.
  Renders, logs e caches em `~/.cache/<projeto>/`, não no `/tmp`.

### Organização

- `<game/domain>/`: regras em `RefCounted`, sem `Node`, `Input`, `Time`, `Tween` nem RNG global.
  Ações, tempo (`delta`) e semente entram como parâmetro. `tests/fronteira_spec.gd` cobra isso.
- `<game/content>/`: dados e nomes do conteúdo.
- `<main>/`: cenas, entrada, apresentação, áudio e persistência.
- `tests/`: specs `extends SceneTree` que terminam em `quit()` ou `quit(1)`.

### Código

- Tipe tudo: variáveis, parâmetros, retornos e laços (`for x: Tipo in ...`). `:=` só com lado
  direito de tipo conhecido.
- Registro com campos fixos (entidade, carta, inimigo) é classe com campos tipados, não
  `Dictionary`: chave errada em dicionário compila e falha calada.
- **Entrada:** um só adaptador normaliza toque e mouse em `<main/controle.gd>`, e
  `input_devices/pointing/emulate_mouse_from_touch=false`. Nada mais lê `InputEvent`.
- **Animação:** uma propriedade animada tem um único dono (um tween guardado e morto antes do
  próximo, ou um AnimationPlayer; nunca os dois).
- **HUD e tela:** a cena não lê o estado vivo do domínio para mostrar o resultado de uma ação: o
  `RefCounted` decidiu no aceite, e o HUD anuncia antes da animação. Esconder durante o tween só
  tapa o que é novo; quando o domínio **troca** um valor (quem caiu vira o substituto), o antigo
  já não existe para mostrar. A cena guarda o que já mostrou, campo a campo, e só o avança no
  evento que aplica (os eventos decidem o que apresentar e em que ordem; o tween, só quando
  termina); no repouso sem evento (começo de fase, entre duas escolhas) sincroniza com o domínio
  de uma vez. Campo lido do domínio ao lado de campo lido da cópia mostrada vaza o futuro
  (CampCrawler, em Defold, D56: vida e nível vinham da cópia, desenho e regra não).
- **Sorteio:** um RNG (`RandomNumberGenerator`) por trilha, todos derivados da semente;
  `--semente=N` como argumento de usuário fixa a partida, e a semente usada sai no log.
- **Replay:** o log de ações registra **toda** passagem de estado que a regra aceita, inclusive
  a que parece não mudar nada (uma leitura, uma recompensa pulada), e o replay só reaplica o que
  está escrito: nunca deduz um passo pela falta de outro. Sem a marca do pulo, a cópia não sabe
  se o original parou à espera da apresentação ou já tinha pulado e esperava outra escolha. Um
  spec tira o log em cada parada de muitas runs, recria o `RefCounted` pela semente, reaplica e
  confere fase e estado contra o original. CampCrawler (Defold), três vezes: uma leitura fora do
  log divergiu 21 de 150 runs (D47); o pulo deduzido levou a cópia uma fase adiante (D51) e
  depois deixou de pular antes de uma escolha (D56).
- **Observabilidade:** eventos verificáveis saem como uma linha `print(JSON.stringify({...}))`
  com a chave `evento`; teste e ferramenta leem esses eventos, não o texto da tela. O
  `user://logs/godot.log` (ligado por padrão no desktop) guarda a partida do autor depois que o
  editor fecha; comando automatizado fora do portão usa `--log-file` em `~/.cache/<projeto>/`.
  Spec e leitor cobram as chaves que provam (`ev["evento"] == "abate" and ev["vida"] == 1`),
  nunca o dicionário inteiro nem a linha como texto, salvo a prova de linha inteira (log por
  semente byte a byte): o `JSON.stringify` ordena as chaves por padrão (`sort_keys` é `true`)
  [4.7.2], e chave nova num evento que já existe cai no meio e quebra toda igualdade ou regex
  sobre a linha. Para a prova de linha inteira, dado novo vai num evento novo. Chave que só às
  vezes existe sai só quando existe. O leitor de playtest trata evento ou chave ausente como o
  jogo de antes dela (CampCrawler, em Defold: linhas próprias para não quebrar as exigências
  ancoradas, e o resumo leu errado o log de antes de uma linha nova até a auditoria).
- Texto para o jogador passa por `tr()` e pela tabela de traduções no mesmo trabalho.
- Texto que quebra ou que a tradução alonga muda de altura, e o vizinho em posição fixa fica por
  baixo. Ponha os dois num `VBoxContainer`, que desce o vizinho sozinho; em posição fixa, meça a
  altura do `Label` depois de um quadro e desça o vizinho por ela. Sem `autowrap_mode` o `Label`
  não quebra: cresce na largura e passa da borda [4.7.2]. Título que não cabe nem assim se encurta
  no texto, em todos os idiomas (CampCrawler, em Defold, D56).

### Cena e arquivos

- Prefira montar e alterar cena por script headless a escrever `.tscn` à mão. Escrevendo à mão:
  use `path` e omita `uid`; não use propriedade do Godot 3 (`rect_min_size`, `align`); conexão de
  sinal para método inexistente falha calada.
- Depois de criar, mover ou renomear arquivo, rode `--import` (sem ele a cena carrega sem script
  e sai com 0). Não mova com `mv` sem reimportar; nunca edite `.godot/`.

### Testes

Teste antes do código (TDD): toda mecânica vem com o spec que prova que ela funciona, e toda
correção com o spec que garante que o bug não volta. Cobertura segue risco: TDD não é um teste
por função.

- **Funcionalidade nova ou regra que muda:** o spec vem antes do código e é visto falhar pelo
  motivo certo, o comportamento ausente: `FALHOU <spec>` no portão cujas linhas de erro são só a
  mensagem da asserção (`push_error` antes do `quit(1)`). `SCRIPT ERROR`, `Parse Error`,
  `compilar_tudo` reprovado ou `TRAVOU` são vermelho errado; se a classe ou o método ainda não
  existe, escreva antes o esqueleto que compila. Depois o código mínimo que passa (verde), e só
  então a refatoração, com tudo verde.
- **Onde o teste mora:** regra de domínio → spec que usa o `RefCounted` sem cena. Peça de cena,
  tela ou entrada → evento JSON emitido de dentro do galho novo e um spec que cobra que ele
  apareça (ou que não apareça): captura os eventos com um `Logger` próprio (`OS.add_logger`,
  Godot 4.5 ou mais nova; pega `print` e `push_error` [4.7.2]), espera um número fixo de quadros
  e confere; nunca espera o evento sem prazo, ou o ausente vira `TRAVOU`. Ferramenta em `tools/`
  → um `tests/<nome>_spec.gd` que a roda (`OS.execute`) e confere a saída: assim o portão já o
  alcança, sem mexer no `portao.sh`.
- **Bug:** primeiro o spec que o reproduz e falha pelo defeito (domínio: semente e sequência de
  ações; cena: os eventos; ferramenta: o teste dela); só então a correção. Vale para todo bug
  reproduzível, não só o determinístico. O teste fica para sempre (o item Spec existente diz
  quando pode sair) num spec do portão, no mesmo commit da correção.
- **Spec existente:** trocar a expectativa porque a regra mudou é o vermelho da regra nova e vem
  antes do código. Mesmo nesse caso, e para inverter, afrouxar, apagar ou pular o caso para o
  código novo passar: justificativa no commit (a do PR sozinha não fica no histórico) e o
  caso antigo coberto por outro spec onde a expectativa antiga ainda vale (outro modo, a
  configuração que volta à regra anterior), se houver; se ela não vale mais em modo nenhum, o
  commit diz isso. A asserção invertida escondeu o defeito do modo que ela protegia
  (CampCrawler, D53).
- **Exceções, sempre declaradas no relatório e no commit.** Exceção é uma alegação, não um
  passe: refatoração que muda comportamento não é exceção.
  - refatoração sem mudança de comportamento: os verificadores que existem (o portão) são a
    rede; onde eles não cobrem o trecho, um spec de caracterização vem antes;
  - o que só o olho ou o aparelho julga (legibilidade, sensação tátil, arte): o julgamento fica
    com captura ou aparelho, e o relatório diz que ali não há teste automático; o caminho da
    peça continua alcançado e cobrado pelo portão;
  - o spec que não deu para ver falhar antes (o comportamento já existia): escreva-o mesmo
    assim, veja-o reprovar plantando o defeito (ou revertendo o código), restaure e diga isso.
    Em correção de bug essa exceção não vale: spec de regressão que passa na base não reproduz
    o defeito;
  - bug que não se reproduz em teste automático (só no aparelho, defeito de um quadro visto em
    captura): diga como foi visto e o que se tentou para reproduzir; o caminho continua
    alcançado pelo portão.
- **Evidência:** o commit e o relatório dizem o comando (em geral `tools/portao.sh`), o vermelho
  de antes e o verde de depois (o PR pode repetir). O portão e o hook Stop só cobram o verde; o
  vermelho é você quem vê e registra.
- **Verificador novo ou mudado**, o portão inclusive, prova que reprova: plante o defeito, rode,
  restaure.
- O `AGENTS.md` fica abaixo dos 32.768 bytes que o Codex lê (o resto ele corta calado), e
  `tests/agents_md_spec.gd` reprova acima disso.
- **Lição volta para a skill:** armadilha do Godot resolvida no projeto vira lição na skill
  `ai-first-godot` (com a versão medida, ou `[doc]`); lição de jogo que não é do motor vai
  para o `gerais-de-jogo.md` da raiz do repositório das skills, nunca para o `armadilhas.md`; o
  `distribuir.py --copiar-gerais` a copia para cada skill de motor, e o `--check-gerais` confere o
  ramo antes do PR. Na mesma frente do conserto, conferindo antes se já está lá.
  A lição entra num ramo numa worktree fora do `/tmp` (`git -C ~/.claude/skills fetch`, depois
  `git -C ~/.claude/skills worktree add ~/.cache/claude-skills-wt/<ramo> -b <ramo> origin/main`),
  nunca trocando o ramo de `~/.claude/skills`, que toda sessão carrega e fica no `main`; push
  e PR esperam o sim <do autor>.
- Spec mora em `tests/<nome>_spec.gd` e entra sozinho no portão, sem lista. O glob não é
  recursivo: spec em subpasta ou sem o sufixo `_spec.gd` nunca roda.
- Spec que grava em `user://` apaga no início os arquivos que usa e recusa um `user://` fora de
  `/tmp` ou `~/.cache` (nunca o do jogador).
- Antes do `quit()`, solte a cena e espere `create_timer(0.3)`: senão o áudio fica preso e a saída
  acusa `resources still in use at exit`.
- Erro provocado de propósito por um spec vai em `ERROS_ESPERADOS` no `tools/portao.sh`, com
  padrão estreito.
- **Jogador automático** (spec que joga a run, robô de cena, simulador) tem trava de passos por
  fase. Robô que sabe as respostas ainda repete para sempre a ação que o domínio recusa ou
  persegue um inimigo que só foge, e o laço sem limite vira `TRAVOU` no portão ou simulador que
  não termina. A trava vira resultado: no spec, falha com a semente; no simulador, run contada
  como travada. Ação recusada troca de alvo em vez de se repetir (CampCrawler, em Defold: a
  saída trancada e o ladrão que só foge, D47 e D53), e o portão que exige o fim da run também
  recusa a linha da recusa (lá, o robô que perde de propósito voltou 28 vezes à mina marcada).
