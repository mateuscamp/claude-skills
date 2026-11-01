# Testes em camadas: ciclo duplo, forma da suíte e dublês

Ler na etapa 10 quando o sistema tem mais de uma camada testável (web, API, CLI
com I/O), e sempre que o pedido for "o agente diz que está pronto e não
funciona", "a suíte ficou lenta", "tem mock demais", "como testo isso sem subir
tudo" ou "vale teste ponta a ponta". O ciclo de cada teste está em
`tdd-e-refatoracao.md`; aqui fica como os testes se distribuem entre as camadas.
A tradução para Python (pytest, marcador `e2e`, Django) está na skill
python-on-rails, em `references/testes.md`.

Origem: Harry Percival, *Test-Driven Development with Python*, 3ª edição
(caps. 4, 6, 19 a 27 e apêndices A e D), adaptado para quem escreve o código ser
um agente.

## Índice

- [Ciclo duplo](#ciclo-duplo)
- [Outside-in](#outside-in)
- [A forma da suíte segue o padrão](#a-forma-da-suíte-segue-o-padrão)
- [Onde cada camada roda](#onde-cada-camada-roda)
- [Dublês](#dublês)
- [Teste com dente](#teste-com-dente)
- [Teste funcional](#teste-funcional)
- [Spike](#spike)

## Ciclo duplo

- **Ciclo externo:** um teste funcional (FT) por história, escrito do ponto de
  vista de quem usa, visto vermelho antes de qualquer código. Ele é o critério
  de pronto: "todos os testes passando" com o FT da história vermelho não é
  pronto. É o mesmo papel do robô nas skills de jogo.
- **Ciclo interno:** os testes unitários conduzem cada peça que o FT pede, com o
  ciclo de `tdd-e-refatoracao.md`. A cada verde interno, rodar o FT de novo: a
  nova falha dele diz qual é a próxima peça.
- **O FT fica vermelho por vários ciclos internos.** Para cada commit continuar
  verde, ele recebe uma marca de **falha esperada estrita, restrita à falha de
  asserção** (no pytest: `xfail(raises=AssertionError)` com `xfail_strict`) e um
  motivo que nomeia a história. Estrita: quando o FT passa, a marca reprova a
  suíte e obriga a tirá-la. Restrita à asserção: `ImportError` ou erro de
  servidor continuam falhando. É a única exceção à proibição de `xfail`, e ela é
  declarada: um FT em curso por vez, e nunca um teste unitário.
- **O primeiro teste de cada área se faz com cuidado.** O agente escreve bem o
  segundo teste copiando o primeiro, e o primeiro decide o desenho. Se o modelo
  para copiar é fraco, a suíte inteira herda a fraqueza.

## Outside-in

- Começar pela camada que o usuário vê e descer. Cada camada escreve a chamada
  que **gostaria** de fazer à camada de baixo, que ainda não existe
  ("programação por desejo"), e essa chamada vira o teste da camada de baixo. A
  interface nasce do uso, não da imaginação de quem a implementa.
- O risco do inside-out, comum no agente, é construir a camada de baixo
  "completa": API boa para si mesma, mais geral que o necessário e com partes que
  ninguém chama.
- **Ressalva:** outside-in só puxa o que o usuário vê. Autorização, limite de
  taxa e validação contra entrada hostil não aparecem no FT do caminho feliz:
  entram como testes próprios, de propósito.

## A forma da suíte segue o padrão

- A forma depende de onde a lógica mora, e o padrão de cada contexto está
  declarado na seção Contextos do `assets/AGENTS.md`. A tabela vem de Vlad
  Khononov, *Learning Domain-Driven Design*, cap. 10
  (`dominio-e-contextos.md`, "Padrão por subdomínio"):

  | Padrão do contexto | Forma | O peso vai para |
  |---|---|---|
  | modelo de domínio, com ou sem event sourcing | pirâmide | unitário no agregado e no objeto de valor, sem dublê |
  | active record | diamante | integração do serviço com o registro, com banco real |
  | transaction script | pirâmide invertida | o fluxo de ponta a ponta pela API ou pelo comando, com banco real |

- **A pirâmide é a meta onde há modelo de domínio:** muitos unitários, alguns de
  integração, poucos FTs. Teste de aceitação é qualquer teste preso a um
  critério de aceite, em qualquer camada. Cobrir todo comportamento com FT não
  se sustenta: fica lento, instável e caro de manter.
- **Toda regra de negócio tem teste na camada em que mora.** No modelo de
  domínio, unitário, sem banco nem rede; a integração fica nas bordas, e o FT só
  no caminho principal de cada história. No transaction script não existe
  unidade sem banco: com o banco num dublê, o teste só confere as chamadas que o
  script faz e fica preso à implementação ([Dublês](#dublês)). O teste certo é o
  do fluxo, com banco real.
- **O "ponta a ponta" do transaction script não é o FT de navegador.** É a
  chamada pela API ou pelo comando, com banco real, dentro do processo de teste,
  rápida o bastante para o `make check` e o hook Stop. O navegador continua fora
  do hook ([Onde cada camada roda](#onde-cada-camada-roda)).
- No começo, um teste que passa pelo framework e pelo banco (o "unitário" do
  Django é de integração) é aceitável. O custo dele cresce com as tabelas e as
  relações. Combine cedo, enquanto a suíte é rápida, a **linha vermelha**: o
  tempo da suíte local que obriga a rearquitetar. O `assets/AGENTS.md` já pede o
  número.
- **A saída da suíte lenta é de arquitetura, não de mock.** Separar um núcleo
  funcional puro (decide e calcula, sem I/O, testado sem dublê nenhum) de uma
  casca imperativa fina (lê, chama o núcleo e grava), coberta por poucos testes
  integrados. Afrouxar o prazo ou trocar teste integrado por mock só esconde o
  sintoma. Transaction script que ficou lento de testar porque acumulou regra é
  o sinal de trocar o padrão do contexto (`dominio-e-contextos.md`, "Evolução").

## Onde cada camada roda

| Camada | Comando | Roda em |
|---|---|---|
| Unitários e integração | `make check` | agente, hook Stop e CI, o mesmo comando |
| FTs (navegador, servidor vivo) | `make e2e` | CI, sempre; local, antes do commit que fecha a história |
| FT em curso | o teste sozinho | a cada volta ao ciclo externo, com a saída no relatório |

- Os FTs ficam fora do hook Stop porque navegador deixa o hook lento a ponto de
  ser desligado. Isso é desvio declarado do portão único, não exceção do agente.
- No CI, as etapas mais rápidas rodam primeiro. O FT que falha guarda captura de
  tela e HTML da página como artefato, porque o agente lê o HTML e não vê o
  navegador.

## Dublês

- **Padrão: dublê só na borda** (rede, banco, relógio, disco, e-mail), nomeado e
  injetado. Preferir o dublê que o framework já oferece ao patch feito à mão.
- **Cada dublê é um contrato implícito.** Toda suposição que ele faz ("o
  repositório devolve `None` quando não acha") precisa de um teste do lado real
  que a sustente. A suposição ainda sem teste fica registrada como teste que
  falha, nunca como lembrete.
- **Dublê entre camadas do próprio código é desvio declarado**, só para conter
  a explosão combinatória: quando a camada de cima teria que repetir todas as
  combinações que a de baixo já trata. Condições, todas juntas:
  1. As combinações são testadas na camada dona da lógica. A de cima fica com o
     caminho feliz e um infeliz.
  2. Cada suposição do dublê tem teste na camada de baixo.
  3. Um teste integrado, sem dublê, cobre o caminho principal, porque teste
     isolado não prova que as peças se encaixam.
  4. O docstring do teste diz o motivo e qual teste de baixo sustenta a
     suposição.
- Dublê prende o teste à implementação: trocar uma chamada por outra
  equivalente quebra o teste sem mudar o comportamento. É mais uma razão para
  ele ficar na borda.
- **Escute os testes.** Setup maior que o próprio teste, ou muitos dublês para
  um sujeito só, é sinal de que o sujeito faz coisa demais. Refatora-se o
  código, não o teste. É gatilho de refatoração preparatória.

## Teste com dente

- **Erro deliberado.** No verde, antes do commit, trocar a implementação por uma
  versão errada **plausível** (a condição invertida, o caso de borda esquecido,
  o valor salvo mesmo inválido) e rodar a suíte. Se nada falha, falta teste.
  Desfazer e escrever o teste que faltou, com o próprio vermelho. É o mutation
  testing feito à mão, dentro do ciclo. O mutation testing do CI mede o
  acumulado.
- Cada `if` pede um teste, e cada `try/except` pede outro. A cobertura de
  **ramo** do diff mede isso; a cobertura de linha não.
- Teste que continua verde depois de uma mudança grande **no próprio teste** é
  suspeito: quebrar o código de propósito e ver se ele pega.
- Uma escolha de implementação que importa ("ordena pela data, não pelo id")
  ganha teste com nome de intenção, mesmo quando a mudança passaria como
  refatoração.
- **Não testar constante.** `assert LIMITE == 3` e asserção sobre o texto
  literal do HTML reafirmam o código, não verificam lógica. O teste unitário
  verifica lógica, fluxo e configuração; o que a página mostra é papel do FT.
  Layout se testa com um FT de fumaça (o estilo carregou, o elemento principal
  está onde deveria), não pixel a pixel.

## Teste funcional

- **Sem espera fixa (`sleep`).** Espera explícita que tenta de novo até um prazo,
  com o prazo numa constante única. Mudar o prazo é decisão declarada no
  relatório: "na dúvida, aumente o timeout" é afrouxar o portão.
- **Isolamento.** Cada FT parte de um estado limpo. Estado fora do banco do
  framework (caixa de e-mail, fila, arquivo, serviço externo) ninguém limpa: um
  FT pode passar lendo o resíduo da execução anterior. Para provar as partes
  novas de um FT, quebrar a produção de mais de um jeito e ver cada parte
  falhar.
- **Dependência externa no FT**, pela maturidade dela:

  | Dependência | No FT |
  |---|---|
  | Nova, instável ou com contrato que você não controla | a real, num job separado, porque é ali que o erro aparece |
  | Antiga e bem suportada (SMTP, POP3) | fake do framework ou em arquivo, e um teste de fumaça contra a real |
  | Lenta ou cara demais para cada execução | fake, mais o teste de contrato do adaptador contra a real, agendado |

- **FT legível.** Localizadores e ações de cada página num objeto da página, e
  nenhum id ou classe de HTML repetido entre FTs. Uma classe base de FT que
  passa de algumas centenas de linhas é o sinal. O login real só se percorre no
  FT de login; os outros partem de uma sessão já autenticada.

## Spike

Complementa a linha "Spike exploratório" de `tdd-e-refatoracao.md`.

1. Antes de começar, listar o que se quer **aprender** (a API responde assim? a
   biblioteca aguenta isso?). Spike sem pergunta escrita vira código de
   produção sem teste.
2. Ao terminar, escrever o plano de "de-spike" enquanto ele está fresco: o que
   ficou provado e qual é a ordem dos testes.
3. Escrever o FT contra o spike, verde, e reverter o spike. Commitar só o FT,
   agora vermelho, e reconstruir com o ciclo.
4. O spike ancora: o agente tende a reescrevê-lo igual. Se o desenho do spike não
   é o que se quer, dizer isso no plano.
