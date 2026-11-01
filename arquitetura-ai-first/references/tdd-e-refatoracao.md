# TDD, refatoração e par de agentes

Ler na etapa 10, e sempre que o pedido for sobre como o agente deve mudar código
neste repositório — "o agente escreve teste que sempre passa", "refatorou e
quebrou", "como faço o agente trabalhar com teste primeiro", "vale usar dois
agentes". Template pronto em `assets/AGENTS.md` (seções Ciclo de mudança,
Refatoração e Par de agentes). Como os testes se distribuem entre as camadas
(ciclo duplo com teste funcional, pirâmide, dublês, erro deliberado):
`testes-em-camadas.md`.

A fronteira arquitetural protege a estrutura entre sessões. O ciclo de mudança
protege o comportamento dentro de cada sessão. Sem o segundo, a fitness function
fica verde enquanto o sistema faz a coisa errada com a estrutura certa.

## Índice

- [Por que TDD pesa mais com agente](#por-que-tdd-pesa-mais-com-agente)
- [O ciclo](#o-ciclo)
- [Proibições](#proibições)
- [Onde TDD se adapta](#onde-tdd-se-adapta)
- [Refatoração](#refatoração)
- [Par de agentes (opcional)](#par-de-agentes-opcional)
- [Enforcement](#enforcement)

## Por que TDD pesa mais com agente

- **Teste escrito depois testa o que foi escrito, não o que foi pedido.** O
  agente que implementa e depois testa espelha a implementação no teste —
  inclusive o bug. Teste primeiro fixa a especificação antes de existir código
  para copiar.
- **O vermelho é a prova de que o teste testa alguma coisa.** Teste que nunca
  falhou pode passar com qualquer implementação: asserção ausente, mock que
  devolve o valor esperado, arquivo que o runner nem coleta. O agente produz os
  três com naturalidade e relata "todos os testes passando".
- **Teste é especificação que sobrevive à rotação de contexto.** Como o ADR
  guarda o porquê da estrutura, a suíte guarda o porquê do comportamento — e é
  executável. A próxima sessão não lembra da conversa, mas roda o teste.
- **Ciclo pequeno é contexto pequeno.** Um comportamento por vez cabe na
  atenção cheia do modelo. Implementação inteira seguida de "agora os testes" é
  o mesmo big bang que a regra de tamanho de função tenta impedir.

## O ciclo

1. **Vermelho.** Escrever **um** teste para **um** comportamento, nomeado pelo
   comportamento (`test_agendamento_recusa_horario_ocupado`, não
   `test_agendamento_2`). Rodar só esse teste e ver falhar **pelo motivo
   certo**: a asserção sobre o comportamento. `ImportError`, `NameError`,
   fixture quebrada ou erro de sintaxe ainda não é vermelho — é teste que não
   rodou. Criar o esqueleto mínimo (assinatura que levanta
   `NotImplementedError`) e rodar de novo até a falha ser a da asserção.
2. **Verde.** O mínimo de código que faz esse teste passar. Nesta fase o teste
   não é editado. Rodar o teste, depois a suíte inteira — verde local que
   quebra o vizinho não é verde.
3. **Refatorar.** Com a suíte verde, melhorar a estrutura sem mudar
   comportamento (seção abaixo). Rodar a suíte a cada passo.
4. **Fechar o ciclo.** `make check` verde e commit. Commit por ciclo, ou por
   grupo pequeno de ciclos, é o ponto de volta quando o próximo der errado.
   Antes do commit, o erro deliberado (`testes-em-camadas.md`): uma versão
   errada plausível tem que derrubar algum teste.

Com teste funcional, este é o ciclo **interno**: o funcional da história fica
vermelho por vários ciclos e só ele diz quando a história está pronta
(`testes-em-camadas.md`, "Ciclo duplo").

Bug segue o mesmo ciclo: **primeiro** o teste de regressão que reproduz o
defeito, visto falhando; depois a correção. Correção sem o vermelho prévio não
prova que corrigiu — prova só que o teste novo passa.

O relatório da tarefa mostra a evidência: a linha de falha do vermelho e o
resumo do verde. "Escrevi os testes e passaram" sem a falha anterior é
test-after com outro nome.

## Proibições

São as saídas que o agente encontra quando o verde demora:

- Editar a asserção para casar com o resultado obtido. Se o teste estava
  errado, isso é uma decisão: dizer no relatório, corrigir o teste e voltar ao
  vermelho.
- `skip`, `xfail`, comentar ou apagar teste para ficar verde. Renomear o teste
  para fora da coleta (`_test_x`, `xtest_x`, `DONT_test_x`) é o mesmo, e escapa
  do grep. A única exceção é o teste funcional em curso, com falha esperada
  estrita e restrita à asserção (`testes-em-camadas.md`).
- Asserção enfraquecida: `assert resultado` no lugar de
  `assert resultado == esperado`, `assert len(x) > 0` no lugar do conteúdo.
- Trocar por dublê o próprio sujeito sob teste, ou uma função **definida** no
  mesmo módulo. Fake é para a borda (rede, banco, relógio, filesystem),
  injetado — nunca para o que está sendo testado. Substituir o nome que o módulo
  importou de uma borda é outra coisa: é ali que um patch deve mirar. Dublê
  entre camadas do próprio código só como desvio declarado
  (`testes-em-camadas.md`, "Dublês").
- `try/except` dentro do teste engolindo a falha.
- Teste que depende da ordem, do relógio real ou de semente aleatória não
  fixada.
- Espera fixa (`sleep`) em teste: espera explícita com prazo numa constante, e
  aumentar o prazo é decisão declarada.
- Teste de constante: asserção que reafirma um valor literal do código ou o
  texto literal de um template, sem lógica no meio.

## Onde TDD se adapta

TDD não é dogma; exceção existe, mas é **declarada**, nunca silenciosa.

| Situação | Adaptação |
|---|---|
| Spike exploratório (API desconhecida, protótipo de viabilidade) | Branch ou diretório marcado como spike. Aprendido o caminho, o código é descartado e reescrito com o ciclo. Spike não é mergeado. Roteiro do de-spike em `testes-em-camadas.md`. |
| Teste funcional da história, vermelho por vários ciclos | Falha esperada estrita, restrita à asserção, com motivo que nomeia a história. Um por vez. `testes-em-camadas.md`. |
| Código legado sem teste | Teste de **caracterização** primeiro (fixa o comportamento atual, inclusive o estranho), depois a mudança com o ciclo. |
| Integração com infra real (banco, fila, API externa) | Domínio com TDD puro atrás de porta; o adaptador ganha teste de contrato contra a infra real, em job separado. |
| Saída visual ou textual grande | Teste de aprovação/snapshot, com o snapshot revisado por humano na primeira vez. |
| Código gerado, configuração, migração declarativa | Sem TDD; a checagem é o build, o schema ou a fitness function. |

## Refatoração

**Definição operacional:** mudar a estrutura sem mudar o comportamento
observável. Suíte verde antes, suíte verde depois, **sem mudar asserção**. Se
uma asserção precisou mudar, não foi refatoração — foi mudança de
comportamento, e ela começa no vermelho.

### Os dois chapéus

Nunca refatorar e mudar comportamento no mesmo passo nem no mesmo commit. O
agente mistura os dois com naturalidade ("aproveitei e ajustei a regra") e o
diff fica impossível de revisar: não dá para saber qual linha mudou o que o
sistema faz. Commit de refatoração começa com `refactor:` e não toca em
arquivo de teste, exceto para acompanhar renome ou movimentação.

### Quando refatorar

- **Preparatória** — antes de uma mudança que a estrutura atual dificulta:
  primeiro deixar a mudança fácil, depois fazer a mudança fácil. É a mais
  valiosa e a que o agente menos faz sozinho; ele prefere encaixar a mudança na
  estrutura ruim.
- **No passo 3 do ciclo** — duplicação que o verde introduziu, nome que ficou
  genérico, função que passou do limite.
- **Por gatilho do `AGENTS.md`** — função acima de 20 linhas, arquivo acima de
  500, aninhamento acima de 2, nome com mais de 5 hits de grep.
- **Duplicação:** duplicação de **conhecimento** (a mesma regra de negócio em
  dois lugares) é extraída na hora — com agente ela custa mais, porque ele
  atualiza uma cópia e esquece a outra. Coincidência de **forma** (dois trechos
  parecidos que mudam por motivos diferentes) espera a terceira ocorrência;
  extrair cedo acopla o que deveria evoluir separado.

### Como refatorar

- **Passos pequenos, suíte a cada passo.** Renomear, extrair função, mover,
  inlinar — um de cada vez. Quebrou, desfazer o último passo, não depurar em
  cima.
- **Edição localizada, nunca reescrita.** O modo de falha típico do agente é
  regenerar o arquivo inteiro "limpo". Reescrita perde comportamento de borda,
  comentário de proveniência e o diff legível. Refatoração é sequência de
  edições pequenas no arquivo existente.
- **Sem cobertura, caracterizar antes.** Trecho sem teste não é refatorado: é
  coberto por teste de caracterização primeiro.
- **Escopo:** refatoração oportunista só nos arquivos que a tarefa já toca.
  Refatoração maior vira tarefa própria, com commit próprio. Agente que
  "aproveita para limpar" o repositório produz o diff que ninguém revisa.

### O que a refatoração preserva

- **Comportamento** — a suíte, sem asserção alterada.
- **Comentário de proveniência** — regra inviolável 9 da skill. Refatoração
  que remove o porquê destrói a única fonte que o agente lê durante um tool
  call.
- **API pública** — mudar assinatura usada fora do módulo é mudança de
  contrato, não refatoração.
- **Fronteira** — fitness functions verdes. Mover código entre módulos, trocar
  o dono de um dado ou inverter uma dependência é decisão arquitetural: volta
  para a etapa 1 e fecha em ADR.

## Par de agentes (opcional)

Vale **quando houver um segundo agente disponível** — subagente, outra sessão,
outra CLI ou outro modelo. Sem ele, o ciclo solo acima vale por inteiro; o par é
reforço, não pré-requisito.

O que o par compra é **independência de viés**: quem escreveu a implementação
não é quem decide se ela está certa. Por isso o mesmo agente se revisando na
mesma janela de contexto **não é par** — herda o raciocínio que produziu o erro.

### Formatos

| Formato | Agente A | Agente B | Quando usar |
|---|---|---|---|
| **Ping-pong** (TDD dividido) | escreve o teste vermelho e a confirmação da falha | implementa o verde; **não pode editar teste** | regra de negócio, domínio, bug recorrente — é o formato que mais rende |
| **Piloto e navegador** | implementa o ciclo | revisa o diff de cada ciclo contra `AGENTS.md` e ADRs antes do commit; não escreve código | mudança perto de fronteira |
| **Revisor de refatoração** | refatora | confirma que o diff não muda comportamento nem asserção | refatoração grande ou em código sem dono claro |

### Regras do par

- **Contexto separado.** B recebe a especificação, o teste e o diff — não o
  raciocínio de A. Passar o histórico de A transforma revisão em eco.
- **Modelo ou CLI diferente aumenta a independência.** Dois do mesmo modelo
  com contexto separado já ajudam; modelos diferentes erram em lugares
  diferentes.
- **Papéis fixos dentro do ciclo.** Quem escreveu o teste não implementa o
  verde do mesmo ciclo.
- **Desacordo vira teste.** Quem discorda escreve o teste que demonstra o
  problema. Desacordo que não cabe em teste sobe para o humano — não é
  resolvido por votação entre agentes.
- **Custo declarado:** cerca do dobro de token e de tempo de parede. Usar onde
  erro custa caro (domínio, fronteira, dado); não em boilerplate, glue ou
  configuração.

## Enforcement

Disciplina de processo é difícil de checar mecanicamente; o que dá para
automatizar, automatizar — e o resto vira regra no `AGENTS.md` e evidência no
relatório.

| O que proteger | Checagem | Tipo / onde roda | Falha quando |
|---|---|---|---|
| Teste junto com código | todo PR que muda `src/` muda `tests/` | atômica, acionada no PR | `src/` mudou e `tests/` não, sem rótulo `refactor` |
| Teste sem dente | mutation testing (`mutmut`, `cosmic-ray`, Stryker em TS) | holística, CI agendado | mutation score abaixo do alvo, ou caiu em relação à última medição |
| Teste desligado | grep por `skip`/`xfail`/`.only` | atômica, pre-commit e CI | ocorrência sem motivo e issue no mesmo marcador |
| Teste sumido da coleta | contagem de testes coletados contra a da base do PR (`pytest --collect-only -q`) | atômica, acionada no PR | a contagem caiu e o PR não apaga teste de forma declarada |
| Refatoração pura | commit `refactor:` não altera asserção | atômica, acionada no PR | diff de `tests/` com linha de `assert` alterada |
| Cobertura do diff | `diff-cover` sobre o relatório de cobertura **de ramo** | atômica, CI | linhas ou ramos novos abaixo de N% cobertos |

Mutation testing é a única dessas que mede o que importa — se os testes pegam
uma mudança de comportamento. Cobertura mede só se a linha rodou. Por isso
cobertura alta com mutation score baixo é o sintoma clássico de test-after
feito por agente: tudo executado, nada verificado.

Não tentar provar a **ordem** (teste antes do código) pelo histórico do git: é
frágil e ensina o agente a fabricar commits. A prova da ordem é a evidência do
vermelho no relatório da tarefa e, no par, a separação de papéis.
