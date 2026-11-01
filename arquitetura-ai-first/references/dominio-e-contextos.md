# Domínio e contextos: de onde saem as fronteiras

Ler na etapa 4, quando a resposta é "não distribuir" e a conversa vira desenho
de módulos dentro do quantum; na etapa 5, quando a dúvida é quebrar serviço ou
dado; e na etapa 10, para preencher as seções Contextos e Linguagem do
`assets/AGENTS.md`.

Origem: Vlad Khononov, *Learning Domain-Driven Design* (O'Reilly, 2021), caps.
1 a 6, 8 a 11, 13 e 14 e apêndice A, adaptado para quem escreve o código ser um
agente. Ficam de fora o EventStorming (cap. 12), que é oficina com gente na
sala, e os caps. 15 e 16 (eventos e data mesh), que o Hard Parts já cobre em
`analise-de-tradeoffs.md`.

O resto da skill mede **quanto** acoplamento cada opção custa. Esta referência
diz **onde** a fronteira passa e **quanto rigor** cada parte merece, e as duas
respostas saem do negócio, não da tecnologia.

## Índice

- [Três tipos de subdomínio](#três-tipos-de-subdomínio)
- [Linguagem ubíqua](#linguagem-ubíqua)
- [Contexto delimitado](#contexto-delimitado)
- [Mapa de contextos](#mapa-de-contextos)
- [Padrão por subdomínio](#padrão-por-subdomínio)
- [Agregado e outbox](#agregado-e-outbox)
- [Quando o contexto vira serviço](#quando-o-contexto-vira-serviço)
- [Evolução](#evolução)
- [Em projeto existente](#em-projeto-existente)

## Três tipos de subdomínio

Subdomínio é um conjunto coerente de casos de uso: o mesmo ator, as mesmas
entidades, os mesmos dados. Ele é **descoberto** no negócio, não desenhado.

| Tipo | Vantagem competitiva | Complexidade | Muda | No livro | Com agente |
|---|---|---|---|---|---|
| Núcleo | sim | alta | sempre | dentro de casa, com os melhores | o agente escreve; a regra vem do humano |
| Genérico | não | alta | pouco | comprar ou adotar | o agente integra atrás de ACL; não escreve |
| Suporte | não | baixa | pouco | dentro de casa ou terceirizado, sem padrão elaborado | o agente escreve, com a cerimônia mínima |

A coluna do agente é a adaptação, e ela mostra que o risco muda de lugar:

- **No núcleo, o padrão do agente é o defeito.** Sem a regra escrita, ele
  preenche a lacuna com a versão média do setor, e a versão média é, por
  definição, a que o concorrente também tem. O livro manda implementar o núcleo
  "o mais perto possível das fontes do conhecimento" (cap. 11); o agente está
  longe delas e não avisa. Regra, caso de borda e invariante que não estão
  escritos se perguntam ao humano, não se inferem. É no núcleo que vão a
  verificação humana, o ciclo TDD completo e a `/code-review`.
- **No genérico, escrever ficou barato e possuir continua caro.** O agente
  entrega autenticação, cobrança ou criptografia plausíveis numa tarde. É
  problema difícil e já resolvido: o custo está no defeito sutil e na
  manutenção, não na digitação. O agente escreve a ACL e o teste de contrato do
  adaptador. Quando a tarefa pede o subdomínio inteiro, ele para e pergunta qual
  produto usar.
- **No suporte, a média do agente é a resposta certa.** CRUD e ETL óbvios:
  transaction script ou active record, teste pelo fluxo, sem portas e
  adaptadores. O livro reserva o suporte para terceirizar ou treinar quem
  chega; o agente faz os dois papéis.

Perguntas que separam (cap. 1): alguém pagaria por isso sozinho? Então é
núcleo. Escrever o próprio sai mais simples e barato que integrar um pronto?
Então é suporte, não genérico. A vantagem nem sempre está no software: o sistema
que só exibe documentos para analistas de fraude não é núcleo; o núcleo é o
trabalho dos analistas. Subdomínio fora do software se reconhece e se deixa de
lado.

**Destilar o núcleo até o caso de uso.** Atendimento parece genérico, mas lá
dentro o roteamento de chamados por casos parecidos é núcleo, a escala de turnos
é suporte, e o help desk e o telefone são genéricos. No suporte e no genérico,
parar de destilar quando os pedaços menores dão o mesmo tipo.

**Conferir ao contrário** (apêndice A). Escolher o padrão de lógica pelo que os
requisitos pedem (tabela em [Padrão por subdomínio](#padrão-por-subdomínio)),
mapear para o tipo e comparar com o que o negócio diz. "É núcleo" mas cabe num
dia de transaction script: procurar um subdomínio mais fino ou questionar o
negócio. "É suporte" mas só cabe em modelo de domínio: ou o requisito tem
complexidade acidental, que se simplifica, ou há um núcleo que o negócio ainda
não viu.

## Linguagem ubíqua

- **Um termo, um significado, dentro do contexto.** Termo ambíguo ("apólice"
  como regra regulatória e como contrato de seguro) vira dois termos. Sinônimo
  pede cuidado: "visitante" e "conta" parecem o mesmo usuário e quase sempre
  são dois conceitos, com comportamentos diferentes. A correção pode ser
  escolher um nome ou dar nome aos dois.
- **Para o agente, nome é API de navegação.** Sem glossário, ele usa o termo
  genérico do setor (`Order`, `Customer`, `User`), e cada sessão pode escolher
  outro: o grep acha metade dos usos e nasce um segundo modelo do mesmo
  conceito. O primeiro nome que entra no código é copiado por todas as sessões
  seguintes, então o glossário do contexto existe **antes** do primeiro código.
  Termo novo do negócio: o agente pergunta o nome, não inventa.
- **Glossário guarda substantivo; teste guarda comportamento.** O livro avisa
  que o glossário funciona para nomes e falha para regras e invariantes. A regra
  mora no teste nomeado pelo comportamento (`tdd-e-refatoracao.md`), escrito com
  os termos do glossário. Gherkin é opcional, e o próprio autor avisa que o
  especialista do domínio não vai escrevê-lo.
- **Onde mora:** no `AGENTS.md`, a tabela curta, só com os termos que o agente
  erra na prática; no CI, a fitness function de sinônimo proibido
  (`assets/test_arquitetura.py`), cuja falha diz qual termo usar. O livro cita
  análise estática que verifica a linguagem: é o mesmo papel.
- **Vale também no suporte.** No estudo de caso do apêndice A, o projeto que
  começou como suporte sem investir na linguagem foi o que mais custou quando a
  complexidade cresceu. E no CRM, a linguagem errada sobreviveu anos ao código
  já corrigido: consertar a língua é mais lento que consertar o código.

## Contexto delimitado

Contexto delimitado é a fronteira de um modelo e da sua linguagem. Subdomínio se
descobre; contexto se **desenha**. Um contexto pode conter vários subdomínios, e
um subdomínio pode ter mais de um modelo.

- **A linguagem dá o limite mais largo.** Além dele, o mesmo termo passa a ter
  dois sentidos no mesmo código. Cortar mais estreito é permitido, e cada corte
  cobra integração.
- **Começar largo, principalmente em volta do núcleo** (cap. 10). O núcleo é
  volátil e mal conhecido no início, e fronteira lógica errada se refatora mais
  barato que fronteira física. Pôr no contexto do núcleo os subdomínios com que
  ele mais conversa, e cortar depois, já com conhecimento.
- **Não separar casos de uso coerentes.** Os que operam sobre os mesmos dados
  ficam no mesmo contexto. Separados, toda mudança atravessa dois contextos e
  pede deploy conjunto.
- **A adaptação que vale aqui.** O livro trata o contexto como fronteira física
  (projeto ou serviço próprio, de um time só). Nesta skill prevalece a postura
  default da etapa 4: o contexto é um **pacote de primeiro nível do monólito**,
  com tabelas próprias e uma porta de entrada (`<contexto>/api.py`), e só vira
  quantum separado com driver de modularidade com evidência. O próprio livro
  sustenta o meio-termo (cap. 8): fatias verticais por subdomínio deixam o
  contexto monolítico modular e podem virar fronteira física depois.
- **Um dono por contexto.** No livro, um time. Com agentes em paralelo, uma
  sessão escritora por contexto de cada vez: duas no mesmo contexto repetem o
  problema de dois times no mesmo modelo.
- **Sinal de fronteira errada:** mudança que atravessa contextos (cap. 10) e
  contextos "tagarelas", que não completam nada sem chamar o vizinho (cap. 11).
  Com agente, o sintoma se mede: o diff de uma tarefa toca dois contextos, ou o
  agente carrega arquivos de três contextos para entender um.

## Mapa de contextos

Cada relação entre contextos segue um padrão de integração. Nomear um por
relação e escrevê-lo no ADR; relação sem padrão nomeado vira parceria por
omissão.

| Padrão | Quando | No código | Fitness function |
|---|---|---|---|
| Parceria | dois contextos evoluem juntos, coordenação ad hoc | chamadas livres entre os dois | nenhuma: é o padrão que a erosão escolhe sozinha |
| Núcleo compartilhado | duplicar custa mais que coordenar; modelo volátil | pacote comum mínimo, só contratos e estruturas que cruzam a fronteira | mudança no pacote comum roda os testes de todo contexto que o importa |
| Conformista | o modelo do fornecedor serve (padrão do setor, bom o bastante) | usa o modelo dele direto | — |
| Camada anticorrupção (ACL) | o consumidor é núcleo, o fornecedor é bagunçado ou legado, ou o contrato dele muda muito | `<contexto>/acl/` traduz o modelo de fora para o de dentro | o SDK do fornecedor só é importado em `acl/` |
| Serviço de host aberto (OHS) | o fornecedor protege os consumidores | `<contexto>/api.py` expõe a linguagem publicada, separada do modelo interno, com versões em paralelo | outro contexto só importa `api.py`; teste de contrato |
| Caminhos separados | integrar custa mais que duplicar | duplicação | — (nunca com núcleo) |

- **Parceria no mesmo repositório não se sustenta com agente.** Ele edita os dois
  lados no mesmo diff, e a fronteira some em poucas sessões. O livro diz o mesmo
  dos contextos de um time só: a parceria apaga a fronteira, e um núcleo
  compartilhado explícito define o contrato. Aqui o default entre contextos é
  OHS, com `api.py` como única porta, conferido pela fitness function.
- O núcleo compartilhado é a biblioteca compartilhada, e os caminhos separados
  são a replicação de código, da tabela de reuso em `analise-de-tradeoffs.md`.
  A regra de corte pela volatilidade é a mesma.

## Padrão por subdomínio

O livro fecha a parte tática (cap. 10) numa árvore que vai do tipo de
subdomínio ao padrão de lógica, à arquitetura e à forma da suíte. Perguntas
nesta ordem:

| Pergunta | Se sim, a lógica é | A arquitetura | A suíte |
|---|---|---|---|
| Rastreia dinheiro, deve trilha de auditoria consistente ou exige análise profunda do comportamento? | modelo de domínio com event sourcing | CQRS | pirâmide |
| A lógica é complexa (regras, invariantes, algoritmos)? | modelo de domínio | portas e adaptadores | pirâmide |
| As estruturas de dados são complexas? | active record | camadas, com camada de serviço (4) | diamante |
| Nenhuma das três | transaction script | camadas mínimas (3) | pirâmide invertida |

- CQRS entra em qualquer linha quando o subdomínio precisa de mais de um modelo
  persistido.
- **Complexo ou simples:** regra, invariante e algoritmo são complexos; validar
  entrada é simples. Outro teste: a linguagem do contexto descreve CRUD ou
  processos e regras?
- **O padrão é por subdomínio, nunca pelo sistema** (cap. 8). Layout único para
  tudo vira complexidade acidental no suporte ou dívida no núcleo. Sem regra, o
  agente aplica a tudo o layout que o framework ou o template sugere. O modelo
  de `AGENTS.md` desta skill pedia `dominio/aplicacao/infra` para todo módulo;
  por isso a seção Contextos dele agora declara o padrão de cada contexto.
- **A suíte segue a lógica**, e aqui esta referência ajusta
  `testes-em-camadas.md`. A pirâmide vale onde há modelo de domínio, porque
  agregado e objeto de valor são unidades perfeitas. No active record, a lógica
  se espalha entre o serviço e o registro, e o peso vai para a integração dos
  dois com banco real (diamante). No transaction script não há unidade sem banco
  para testar: forçar a pirâmide produz teste que só confere as chamadas ao
  banco, preso à implementação.
  **Errata:** no texto do cap. 10, o parágrafo do diamante diz "testing
  pyramid"; as figuras 10-6 e 10-7 dizem diamante, e é o que vale.
- **São heurísticas.** O autor declara preferir o simples e cita times fluentes
  em event sourcing que o usam em tudo. A escolha e a condição que a inverte vão
  no ADR do contexto.

## Agregado e outbox

Só nos contextos com modelo de domínio.

- **Agregado é fronteira de transação.** Uma transação grava um agregado só.
  Precisar gravar dois na mesma transação é sinal de fronteira de agregado
  errada, não de transação maior.
- **Dentro, só o que precisa ser fortemente consistente.** A pergunta do cap. 6:
  a regra produz estado inválido se trabalhar com esse dado atrasado? Se não, o
  dado fica fora e é referenciado por ID. O alvo é o agregado pequeno, e crescer
  por conveniência é complexidade acidental (cap. 11).
- **Saga não conserta agregado errado** (cap. 9). Fora do agregado, tudo é
  eventual; operação que exige consistência forte pertence a um agregado só.
- **Evento sai pela outbox.** Estado e evento gravados na mesma transação; um
  relé lê os não publicados, publica e marca. A entrega é pelo menos uma vez,
  então todo consumidor é idempotente. O código que o agente escreve por padrão,
  `commit()` seguido de `publish()`, é o exemplo do livro de código em que não
  se pode confiar: o processo cai entre as duas linhas e o evento some.
- **Transação distribuída implícita** (cap. 5). Gravar no banco e avisar outro
  sistema na mesma operação já é transação distribuída, mesmo sem o nome. Entra
  na seção Código defensivo do `AGENTS.md`.

## Quando o contexto vira serviço

Complementa a granularidade de `analise-de-tradeoffs.md` (cap. 14):

- **O contexto é o limite mais largo válido**: o maior monólito que preserva uma
  linguagem coerente. Mais largo que ele, bola de lama.
- **O agregado é o limite mais estreito.** Partir um agregado em dois contextos
  foi a fronteira que o estudo de caso chamou de "suicida". Abaixo do menor
  limite válido, bola de lama distribuída.
- **O subdomínio é a fronteira de serviço segura** na maioria dos casos: casos
  de uso coerentes dão módulo profundo, interface pequena sobre lógica grande.
  Extrair serviço de um maior é mais seguro que começar pequeno demais.
- Nada disso substitui o driver de modularidade com evidência da etapa 4. O
  subdomínio diz **onde** cortar; o driver diz **se** corta.

## Evolução

- **Subdomínio muda de tipo**, nas seis direções (cap. 11). No estudo de caso,
  dois suportes viraram núcleo quando se achou como monetizá-los, um suporte
  virou genérico quando saiu um projeto aberto melhor, e um núcleo virou
  genérico quando um serviço de nuvem passou a fazer o mesmo.
- **O sinal é dor.** O desenho atual já não suporta o que o negócio pede, e cada
  regra nova custa mais que a anterior. Não ignorar: voltar ao tipo e ao padrão.
  As migrações têm caminho: transaction script → active record, quando os dados
  ficam difíceis de manipular; active record → modelo de domínio, quando
  aparecem inconsistência e lógica duplicada; modelo de domínio → event
  sourcing, só com os agregados já bem cortados, e o difícil é o histórico que
  não existe.
- **No ADR do contexto**, o tipo, o padrão e a condição que inverte a escolha,
  escrita como o sinal esperado ("invariante que cruza três tabelas: active
  record vira modelo de domínio"). É o "inverte se" do bottom line aplicado à
  parte tática.
- **Crescimento** pede revisitar as três fronteiras: o subdomínio (há um mais
  fino, de outro tipo?), o contexto (perdeu o foco?) e o agregado (inchou?).

## Em projeto existente

Cap. 13, na etapa 3:

1. Tratar cada componente de alto nível como se fosse um contexto e medir o que
   importa: ele evolui, testa e faz deploy sem os outros?
2. Para cada um, quais subdomínios contém e qual padrão usa. O desenho cabe na
   complexidade do problema? Há suporte com cerimônia de núcleo, ou núcleo em
   transaction script?
3. Desenhar o mapa de contextos atual com os padrões da tabela acima e procurar
   os sintomas do livro: dois times (aqui, duas sessões) no mesmo componente,
   núcleo duplicado, núcleo terceirizado, integração que quebra sempre, modelo de
   fornecedor ou de legado vazando para dentro.
4. Modernizar pelas bordas: ACL na frente do legado, OHS para os consumidores e
   estrangulamento, com uma fachada que desvia aos poucos para o contexto novo.
   Começar a linguagem já, porque ela é a parte mais lenta de consertar.
