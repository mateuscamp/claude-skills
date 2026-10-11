<!--
Modelo da skill ai-first-defold para a seção Defold do AGENTS.md de um projeto.
Copie, troque o que está entre <>, e apague o que não se aplica. O AGENTS.md é lido pelo
Claude Code (quando não há CLAUDE.md) e pelo Codex; mantenha nele só regra do projeto, curta
(o manual oficial de agentes da Defold pede o mesmo).
-->

## Defold

- Versão fixada: **Defold <1.13.2>**, pelo bob do editor instalado (`bob.jar` de 370 bytes +
  link `defold-editor.jar`, da máquina, nunca do repositório). Não use API de outra versão; na
  dúvida, consulte <https://defold.com/llms.txt> e as anotações que o `tools/luals_check.sh`
  extrai do jar, não a memória.
- Rode `tools/portao.sh` antes de dizer que terminou. **Não use o código de saída do motor como
  prova**: peça ausente não emite erro. A prova é a linha de log que o portão exige.
- Execute o bundle a partir da pasta dele (o motor carrega `build/` relativo ao diretório atual)
  e uma instância por vez (disputam porta). Encerre só o processo que você abriu, por PID.
- Com o editor aberto no projeto, fale com ele pela API HTTP: porta em `.internal/editor.port`,
  operações lidas do `/openapi.json` (não decoradas), log do jogo rodado pelo editor em
  `/console`. É experimental e não substitui o portão. `/eval` só com pedido explícito; o
  `.internal/editor.token` nunca vai para prompt nem log.

### Organização

- `<modules>/`: regras em Lua puro, sem `go`, `gui`, `msg`, `sys`, `vmath`, `timer`, `hash`,
  relógio nem `math.random`. Ações, tempo e semente entram como parâmetro. `tests/test_fronteira.lua`
  cobra isso.
- `<main>/`: coleção, scripts e GUI. Um script é dono da sessão e da apresentação.
- `tests/`: `tests/test_*.lua`, rodados por `./run_tests.sh` em LuaJIT **e** num Lua 5.x.
- `tools/`: portão, smoke, LuaLS, geradores com `--check`, prova da Bridge.

### Código

- Lua 5.1 portátil: `local` em tudo, sem `goto` (o bob aceita), sem operador bit a bit nativo,
  divisão inteira com `math.floor`. Nada exclusivo do LuaJIT na regra.
- Tabela que cruza módulos tem forma documentada no construtor; enumeração é string constante do
  módulo, validada na fronteira. Erro de contrato é `error()` com o valor recebido e o esperado.
- **Entrada:** um só binding por gesto. Ligue `MOUSE_BUTTON_LEFT` a `touch` e **não** ligue
  `TOUCH_MULTI` à mesma ação: no celular o primeiro dedo já chega como mouse, e os dois juntos
  disparam cada toque duas vezes. Um único `on_input` traduz o gesto numa ação de domínio.
- **Toque em nó:** `gui.pick_node` nó por nó, nunca aritmética sobre `action.x`.
- **Animação:** uma propriedade animada tem um único dono. O segundo `go.animate`/`gui.animate`
  na mesma propriedade cancela o primeiro **e descarta o callback dele**. Prefira posição
  calculada por função pura e aplicada por um só script.
- **Sorteio:** gerador próprio com semente (não `math.random`: é global, tem semente padrão fixa e
  15 bits). A semente usada sai no log.
- **Mensagens:** `msg.post` entrega no próximo despacho; nada lê o efeito na linha seguinte.
  Objeto que posta com atraso carrega a época da montagem; quem recebe compara.
- **Observabilidade:** cada fato verificável sai numa linha `print("<PROJETO> <FATO> k=v ...")`
  com campos em ordem estável, de dentro do galho que comprova o fato (ex.: depois de o
  `pick_node` acertar). Toda borda de toque também vira fato.
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

- Regra nova vem com teste de domínio; bug determinístico vem com teste de regressão com semente.
- Toda peça nova da cena precisa ser **alcançada** por uma passada do portão, com `--exigir` da
  linha que ela emite. Se o robô não chega lá, dê a ele um atalho de início validado (andar,
  upgrade), não uma exceção no portão.
- Ao criar ou mudar um verificador, prove que ele reprova: plante o defeito, rode, restaure.
- Dependência nova, extensão nativa, serviço externo, signing e publicação pedem aprovação.
