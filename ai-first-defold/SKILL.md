---
name: ai-first-defold
description: Boas práticas AI-first para qualquer jogo em Defold quando quem escreve o código é um agente - como o código deve ser escrito (domínio em Lua puro sem go/gui/msg/sys, um binding de entrada só, gui.pick_node, um dono por animação, RNG próprio com semente, fatos em log estruturado, Lua 5.1 portátil, ids de GUI estáveis) e o ciclo de verificação que o agente fecha sozinho (suíte sem engine em LuaJIT e Lua 5.x, fitness function da fronteira do domínio, LuaLS com as anotações oficiais extraídas do jar do editor, build headless pelo bob que confere SEVERE e o bundle, motor rodando com robô e --exigir por linha de log, hook Stop do Claude Code, Automation Bridge num build separado, API HTTP do editor descoberta pelo /openapi.json, log da partida em arquivo). Use sempre que o projeto for Defold - ao começar um jogo novo, ao chegar num projeto existente, ao auditar se ele segue as boas práticas, e quando o assunto for bob, game.project, teste headless, smoke, "compilou mas não funciona", "passou no desktop e quebrou no celular", toque contando duas vezes, animação que não termina, LuaLS, anotações, xvfb, Automation Bridge, extensão nativa, build server, API do editor, openapi.json, console do editor, log em arquivo, log.txt, write_log_file, "o log sumiu" ou MCP para Defold. Complementa a skill jogos-ai-first (método e governança).
---

# AI-first em Defold

O agente escreve Lua bem. O que ele não vê é o erro **mudo**: o bob compila API inventada e
deixa o bundle velho no lugar quando falha com `SEVERE`; um toque no Android chega como mouse e
como multitoque; o segundo `gui.animate` cancela o primeiro e some com o callback; animação de
atlas inexistente só falha quando aquele caminho roda; o headless às vezes para sem erro. Esta
skill dá duas coisas: **como escrever** o projeto para que esses erros não nasçam, e **como
verificar** para que os que nascerem virem reprovação antes de o agente dizer "terminei".

O método geral (contrato, posse, determinismo, ADR, fitness function, risco) está na skill
**jogos-ai-first**. Aqui fica só o que é do Defold. A referência viva é o CampCrawler
(ex-Mineboom, `~/defold/campcrawler`, D23–D27 no `IMPLEMENTATION_PLAN.md`); as armadilhas pagas antes estão no
BomberBoom (`~/defold/bomberboom-df/docs/PEGADINHAS.md`).

Arquivos desta skill:
- `assets/AGENTS-defold.md`: a seção Defold do `AGENTS.md` do projeto, pronta para adaptar. É
  **a lista das boas práticas de código**; leia-a inteira antes de escrever código Defold.
- `references/armadilhas.md`: os comportamentos medidos do bob, da entrada, das mensagens, da GUI,
  do LuaLS, da Automation Bridge e da API HTTP do editor. Leia antes de afirmar qualquer coisa sobre eles.
- `scripts/`: `portao.sh`, `plataforma.sh`, `smoke.py`, `smoketest.ini`, `luals_check.sh`,
  `run_tests.sh`, `run.lua`, `test_fronteira.lua`, `hook_portao.sh`, `bridge.ini`,
  `bridge_build.sh`, `prova_bridge_exemplo.py`, `editor.py` (prova pela API do editor) e
  `fact_log.lua` (fato formatado e arquivo da partida).

## Por onde começar

**Projeto novo**
1. Fixe a versão (o `[build] version` de `/opt/Defold/config`) e escreva o `AGENTS.md` a partir de
   `assets/AGENTS-defold.md`, com as pastas reais. No `input/game.input_binding`, **só**
   `MOUSE_BUTTON_LEFT → touch`, sem `TOUCH_MULTI`.
2. Instale o portão, o teste de fronteira e o hook (seção 2) antes da primeira mecânica.
3. Domínio em `modules/` com teste; a cena só aplica eventos. Cada peça nova da cena emite um
   fato no log e ganha `--exigir` numa passada do portão.

**Projeto existente**
1. Audite medindo (seção 1) e mostre ao usuário a tabela: o que existe, onde, e o número medido.
2. Instale o portão e o hook primeiro: são baratos e protegem todo o resto.
3. O que a auditoria apontar (entrada, animação, RNG, domínio misturado à cena) vira etapas
   pequenas, cada uma com o portão verde. Mudança de contrato entre domínio, cena e testes pede
   ADR antes.

## 1. Auditar

Confira e **meça**; não responda pela leitura do código.

| Prática | Como conferir |
|---|---|
| Versão fixada | `/opt/Defold/config` contra `AGENTS.md`; `java -jar $BOB_JAR --version` responde? |
| Domínio sem engine | rode `scripts/test_fronteira.lua` ajustado às pastas de regra |
| Um binding por gesto | `grep -n TOUCH_MULTI input/*.input_binding` junto de `MOUSE_BUTTON_LEFT` na mesma ação |
| Toque por nó | `grep -rn "action.x" --include=*.gui_script --include=*.script` fazendo conta de célula |
| Um dono por animação | contar `go.animate`/`gui.animate` por propriedade e por script; `~/engine-sensor/dist/engine-sensor-linux-x86_64 check . --format json` (zero afirmações = nada a comparar, não "aprovado") |
| RNG com semente | `grep -rn "math.random" modules/ main/` |
| Fatos no log | os testes de cena exigem linhas, ou só "não deu erro"? |
| Portão lê log e bundle | o comando do README confere `SEVERE` e a existência do executável? |
| Caminhos alcançados | cada flipbook/galho novo aparece em alguma passada? (`grep play_flipbook` × `--exigir`) |
| LuaLS | rode `scripts/luals_check.sh` e conte os problemas |
| Suíte em dois Luas | `luajit` e `lua` rodam os testes? teste que não carrega reprova? |
| Hook | `.claude/settings.json` roda o `--rapido` no `Stop`? |
| Proveniência | `CREDITS.md` cobre todo arquivo de `assets/`? geradores têm `--check`? |
| Bridge | dependência no `game.project` (portão com rede) ou num `--settings` separado? |
| API do editor | algum script ou doc fixa endpoint em vez de ler `/openapi.json`? o portão depende do editor aberto? |
| Log em arquivo | a partida que o autor joga deixa arquivo com os fatos e os erros de Lua? `project.write_log_file` ligado? |

## 2. Instalar o portão e o hook

```sh
S=~/.claude/skills/ai-first-defold/scripts
mkdir -p tests tools
cp $S/run.lua $S/test_fronteira.lua tests/
cp $S/run_tests.sh . && chmod +x run_tests.sh
cp $S/portao.sh $S/plataforma.sh $S/smoke.py $S/smoketest.ini $S/luals_check.sh $S/hook_portao.sh tools/
chmod +x tools/*.sh
```

- `tests/test_fronteira.lua`: ajuste `PASTAS` e, se preciso, `PERMITIDOS` (exceção exata, com
  motivo). Teste novo entra sozinho: `tests/test_*.lua`, cada um devolvendo `{ {"nome", fn}, ... }`.
- `tools/portao.sh`, bloco `AJUSTE`: `geradores` (os `--check`) e `passadas` (cada uma com
  `--config=<projeto>.<chave>=...` e os `--exigir` do que ela precisa produzir).
- `tools/luals_check.sh`: `LUALS_IGNORAR` para pastas que não são código do jogo; API que o
  motor tem e a anotação não, num `---@meta` em `tools/luals/` (ver `references/armadilhas.md`).
- O jogo precisa de um robô opt-in (`<projeto>.autoplay = 1` no `game.project`, lido com
  `sys.get_config_int`; nenhuma chave da seção pode ser prefixo de outra, porque o
  `--config` casa por prefixo) que toca **pelo mesmo ponto de entrada do toque**, e de linhas
  `print("<PROJETO> <FATO> k=v")` emitidas de dentro do galho que comprova o fato.
- Hook: registre em `.claude/settings.json` do projeto (o JSON está no topo do
  `hook_portao.sh`). Ele roda o `--rapido` só quando Lua, script ou recurso mudou desde a última
  aprovação, e na segunda parada seguida deixa a sessão terminar.
- `BOB_JAR` e `PATH` com o java do editor (`/opt/Defold/packages/jdk-*/bin`) no `AGENTS.md`.

**Prove que o portão reprova antes de confiar nele.** Plante, rode e restaure:
1. `gui.set_textt(...)` num `.gui_script` (não num módulo `.lua`) → o **LuaLS** reprova (o bob
   aceitaria); se passar, falta `files.associations` na luarc;
2. `gui.set_text(...)` dentro de `modules/` → o **teste de fronteira** reprova;
3. `play_flipbook(node, "nome_que_nao_existe")` num caminho que só uma passada alcança → o
   **smoke** reprova com `Animation ... invalid`; se nenhuma passada alcança, crie a passada;
4. uma regra quebrada de propósito (ex.: número expandindo como zero) → a **suíte** reprova.

## 3. Consertar o que o portão acha

- Build "OK" rodando código velho: o bob falhou com `SEVERE`; confira o bundle, não o log.
- Motor sobe e não avança no headless: `vsync = 0` no `smoketest.ini`.
- Exigência que falha só às vezes: a passada depende de sorte (o robô precisa vencer algo).
  Troque por um atalho de início validado — nunca afrouxe a exigência.
- Texto de prova que some: o fato saiu antes da apresentação, ou fora do galho que o comprova.
- Painel que anuncia o resultado antes da animação: a apresentação tem de perguntar "ainda
  apresentando?" antes de "o domínio já decidiu?".
- Lista completa com sintoma e causa: `references/armadilhas.md`.

## 4. Automation Bridge (prova pela entrada real e no aparelho)

O robô do portão chama a entrada do jogo por dentro; a Bridge injeta pelo HID do engine e chega
ao aparelho. Ela é extensão **nativa** e compila no servidor de build da Defold, então:

- **Peça aprovação** antes (dependência nova + serviço externo; o manual oficial de agentes exige).
- Dependência só em `tools/bridge.ini` (`--settings`), nunca no `game.project`: o portão continua
  sem rede. Release nunca a recebe.
- `cp $S/bridge.ini $S/bridge_build.sh tools/` e adapte `prova_bridge_exemplo.py` (ids, fatos,
  chaves). Dê `gui.set_id` estável aos nós que a prova procura.
- Toque é sessão de ponteiro, não `/input/click`; leia o efeito no jogo, não o recibo.

## 5. API HTTP do editor (quando o editor está aberto)

É o caminho oficial da Defold para agentes falarem com o **editor** (manuais
<https://defold.com/manuals/ai-agents> e <https://defold.com/manuals/editor-http-api>). O jogo
rodando é outra coisa: engine service ou Bridge. MCP é opcional e não há servidor oficial.

- **Descubra, não decore.** O editor serve `/openapi.json` (OpenAPI 3.0.3) e ele é a fonte da
  verdade das operações. Leia antes de chamar; não copie lista de endpoints para script nem doc.
- **Porta:** `.internal/editor.port` na raiz do projeto **que o editor abriu** (numa worktree,
  o editor costuma estar no checkout principal: é esse código que ele compila). O servidor só
  existe com projeto aberto; na tela de boas-vindas não há porta nem arquivo. Releia a cada
  reinício do editor.
- **Partida com robô pelo editor:** o `run` não aceita argumento; as chaves `--config` vão na
  preferência `run/engine-arguments`, **uma por linha**, e só valem num processo novo (com o
  jogo aberto, o `run` reinicia o mesmo motor sem argumento). Guarde o valor antes, restaure
  depois, e encerre só o jogo que você lançou. Detalhes em `references/armadilhas.md`.
- **Usos que valem a pena:** `/console` e `/console/stream` (as linhas `<PROJETO> <FATO>` de uma
  partida rodada pelo editor só existem ali, **até o editor fechar**: por isso a seção 6), `/ref?q=` para conferir API da versão instalada,
  `/preview/{path}` para olhar GUI e coleção em PNG, e os comandos (`compile`, `hot-reload`...)
  quando o autor está com o editor aberto.
- **Console parado trava quem espera cabeçalho.** O `/console/stream` não manda nem o status HTTP
  até chegar uma linha nova: abra a conexão dentro da thread que lê e conte o prazo desde o
  início, senão a janela de leitura nunca começa (`scripts/editor.py`).
- **Resposta:** confira o status HTTP **e** o campo `success`; `202` é só aceite. Espera com
  limite; `503` repete poucas vezes.
- **Privilégio:** `/eval` executa Lua no editor e pede o token de `.internal/editor.token` — use
  só com pedido explícito, e o token nunca entra em prompt, log ou relatório.
- **Não é portão.** A API é experimental, muda entre versões e depende do editor aberto. O
  portão continua sendo bob + motor headless; a API é para o ciclo interativo com o autor.

## 6. Log da partida em arquivo

O console do editor some quando ele fecha, e o autor costuma pedir "olhe o log" depois. Duas
camadas, as duas de graça:

- **`project.write_log_file = 1`** no `game.project` (0 nunca, 1 só build debug, 2 sempre; o
  antigo `write_log` está obsoleto). O motor grava **tudo** — motor, erros com traceback e
  prints — num `log.txt` **no diretório de trabalho dele** (a pasta do executável no bundle), e
  o regrava a cada abertura. Ignore `/log.txt` no git.
- **Arquivo por partida** (`scripts/fact_log.lua`): o `log()` da cena formata a linha e, sem
  robô, grava também em `sys.get_save_file(app, "partida-<data>.log")`, com `flush` por linha
  para sobreviver a processo morto. `sys.set_error_handler` copia o erro de Lua com traceback
  para o mesmo arquivo; o motor continua imprimindo `ERROR:SCRIPT` no console. A primeira linha
  diz onde o arquivo está (`<PROJETO> ARQUIVO caminho=...`, ou `erro=` sem parar o jogo).
- **Robô não grava**, senão cada portão deixa centenas de arquivos. A passada sem robô do portão
  exige a linha `ARQUIVO` sem `erro=` e apaga o arquivo que criou (`find -newer` com marca).
- Um leitor do arquivo em tabela (por partida, por mapa, médias por modo) fecha o ciclo com o
  autor; no CampCrawler é `tools/resumo_playtest.py --partidas`.

## Convivência

- Todo motor automatizado: `timeout`, cwd na pasta do executável, uma instância, log lido.
- Caches e bundles de prova em `~/.cache/` ou `dist/` (ignorado), não na raiz do projeto.
- O wrapper do bob e o cache do LuaLS são da máquina: nunca entram no repositório.
- Remover código, levar para a `main` ou enviar ao remoto: confirme com o usuário.
