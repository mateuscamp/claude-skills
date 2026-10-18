---
name: "jogos-ai-first"
description: Método para desenvolver jogos quando quem escreve o código é um agente - contrato AI-first do projeto, padrões de posse, determinismo e observabilidade, e a governança arquitetural (ADR, matriz de risco, fitness function, análise de trade-off qualitativa, portão com critério de parada) derivada de Fundamentals of Software Architecture e Software Architecture - The Hard Parts. Use sempre que o assunto for começar, planejar, auditar ou decidir alguma coisa num projeto de jogo, em Godot, Defold, Unity ou engine própria; quando aparecer animação, tween, entrada, toque, semente, RNG, teste headless, prova de cena, "passou nos testes mas quebrou no aparelho" ou "bug que não dá erro nenhum"; e quando for preciso escolher engine, definir escopo, decidir se vale construir, registrar uma decisão, montar matriz de risco, escrever fitness function ou fazer análise de trade-off - inclusive em projeto técnico que não seja jogo.
---

# Jogos AI-first

Um método de trabalho para projetos de jogo em que o agente escreve o código e a
pessoa é o recurso escasso. Vem de uma medição real: o mesmo jogo mobile construído
por um agente em Godot, Unity e Defold, sem contexto entre execuções e sem receber
uma única indicação de API, seguido de um verificador estático construído e medido
sobre os defeitos que a medição encontrou.

Ela combina duas coisas que se sustentam mutuamente: **o que foi medido sobre agentes
construindo jogos** e **um método de decisão arquitetural** tirado de *Fundamentals of
Software Architecture* e *Software Architecture: The Hard Parts*.

## Regra zero

O gargalo de um projeto de jogo com agente não é a quantidade de código que o agente
escreve. É **o que só uma pessoa consegue verificar**.

Toda ida e volta do tipo "roda aí e me diz se ficou bom" gasta o recurso mais escasso
do projeto. Isso reordena as prioridades inteiras: um mecanismo que faz o agente
escrever menos código vale pouco; um mecanismo que faz o agente **provar mais coisas
sozinho** devolve exatamente o que falta.

Aplique esse critério a toda decisão desta skill. Quando duas opções empatam, ganha a
que reduz inspeção humana.

## O que o agente não vê

Um agente escreve código de jogo com competência e não consegue olhar o resultado. As
consequências foram medidas, não supostas:

- **Mudo é pior que opaco.** Diante de uma mensagem de erro ruim, o agente investiga.
  Diante de silêncio, ele conclui que funcionou. Os dois defeitos mais caros da
  medição não produziram erro nenhum e sobreviveram a 107 asserções verdes.
- **A classe de defeito mais cara é posse dupla**: dois donos para um recurso, e o
  motor escolhendo um sem contar. Duas animações tocando a mesma propriedade; dois
  canais físicos de entrada chegando ao mesmo efeito.
- **A lógica correta não protege a integração.** Os testes de regra estavam certos e
  verdes enquanto cada toque no aparelho gastava duas bombas, porque no desktop só
  existia um dos dois canais de entrada.
- **Onde três agentes independentes constroem a mesma peça improvisada, ela pertence
  ao motor.** Três execuções sem contato entre si reimplementaram o gerador aleatório,
  construíram um canal de narração e separaram as regras do motor. Isso é lacuna de
  ferramenta, não preferência.

Leia `references/licoes-medidas.md` quando precisar dos números, das ressalvas ou de
citar a evidência. Ele também registra o que a medição **não** concluiu, e isso importa
tanto quanto o resto.

## Os padrões que fecham o ciclo

São o contrato mínimo de um projeto de jogo AI-first. `assets/CONTRATO.md` é a versão
copiável, para colocar na raiz do projeto e apontar a partir de `AGENTS.md` e
`CLAUDE.md`.

1. **Domínio isolado.** A regra do jogo não importa cena, entrada, áudio, GPU, janela
   nem relógio global. É a única forma de o agente testar sem subir engine.
2. **Aleatoriedade injetada.** Toda regra que sorteia recebe uma semente e passa por um
   gerador único. Nenhuma engine garante reprodutibilidade entre plataformas; sem isso
   não existe reprodução de defeito.
3. **Entrada normalizada em um ponto.** Mouse, toque, teclado e controle viram uma ação
   de domínio num único adapter. O domínio nunca recebe dois eventos físicos
   equivalentes.
4. **Um dono por propriedade animada.** Outro fluxo pede uma intenção ao proprietário;
   não inicia um segundo tween. Composição deliberada existe, mas precisa ser declarada
   e justificada, nunca silenciosa.
5. **Log estruturado como prova.** Uma linha por fato verificável, com campos. Texto
   livre é para pessoas e não é evidência.
6. **Comando de teste e comando de prova de cena versionados no repositório.**
7. **Perfil de plataforma antes do aparelho.** Diferenças semânticas conhecidas do alvo
   precisam ser executáveis no desktop; o aparelho físico continua tendo poder de veto.
8. **Falha explícita.** Conflito de posse, nome ou contrato impede a execução e nomeia
   os dois sítios envolvidos. Ambiguidade vira aviso explicado, nunca adivinhação.

Antes de declarar uma tarefa concluída, percorra `assets/EVIDENCIA.md`.

## A caixa de decisão do agente

O erro de governança mais comum num projeto AI-first é listar proibições sem dizer o
que o agente **pode** decidir sozinho. Sem essa metade, ou o agente trava e consome
atenção humana, ou decide sozinho o que não deveria.

| Decisão | Regime |
|---|---|
| Nome, estrutura interna, teste, refatoração dentro de um módulo | decide sozinho |
| Dependência de propósito específico, resolvida num canto | decide sozinho e registra no diff |
| Dependência de propósito geral, fronteira nova entre módulos | propõe com justificativa; a pessoa aprova |
| Framework, runtime, serviço remoto, mudança de contrato público ou de código de saída | exige ADR; o agente não decide |

Adapte as quatro linhas ao projeto, mas mantenha as quatro. A ideia vem do capítulo
sobre dar orientação sem virar gargalo, em *Fundamentals*.

## Como decidir qualquer coisa neste projeto

Use o ciclo abaixo para decisão que muda estrutura, escopo, dependência ou contrato.
Para decisão pequena, use só os passos 1, 2 e 6.

1. **Contexto e motor de negócio.** Quem sofre o problema, qual resultado importa, qual
   restrição não pode ser ignorada.
2. **Opções mutuamente comparáveis.** Inclua sempre "não fazer" e "usar ferramenta
   existente". Compare coisas da mesma categoria e cubra o espaço de decisão.
3. **Características prioritárias.** No máximo sete, cada uma com definição operacional.
   Tentar maximizar todas dilui a decisão.
4. **Dimensões entrelaçadas.** O que muda junto. Mais determinismo costuma custar
   desempenho; mais controle costuma custar portabilidade.
5. **Cenários.** Exercite as opções nos casos que mais tensionam o desenho, não nos
   fáceis.
6. **Trade-offs.** Vantagem, desvantagem e consequência, no contexto real. Se você acha
   que uma opção não tem desvantagem, você ainda não achou.
7. **Experimento refutável.** O menor protótipo capaz de derrubar a hipótese, com
   orçamento e **critério de parada** — não só critério de conclusão.
8. **Fitness function.** A característica vira verificação objetiva, automática quando
   der. Fixe o limiar **antes** de rodar o experimento que ele vai julgar.
9. **Risco.** Impacto primeiro, probabilidade depois, nota de 1 a 9, mitigação com
   custo explícito e sinal de parada.
10. **ADR.** Contexto, decisão, consequências e como conferir conformidade.
    `assets/ADR.md` é o modelo.

`references/governanca.md` detalha cada passo, com o mecanismo original de cada livro
e as armadilhas que eles nomeiam. Leia antes de auditar um projeto, de fixar pesos de
uma comparação, de escrever a primeira ADR de um projeto novo ou quando estiver
decidindo se um pedaço deve ser separado do resto.

## Começando um projeto novo

`references/inicio-de-projeto.md` tem a sequência completa. O resumo:

Escreva primeiro o que faz o projeto **parar**, não o que faz ele crescer. Antes de
qualquer código: as três a cinco características prioritárias com definição
operacional, os riscos de nota 9 com mitigação, o portão que separa esta fase da
próxima, e a ADR que proíbe a fase seguinte até o portão passar. Isso cabe em uma
tarde e é o que impede um verificador de virar uma engine sem ninguém decidir.

## Erros que este método existe para evitar

Cada um destes já aconteceu num projeto real e foi corrigido com custo.

- **Conformidade sem mecanismo.** Uma ADR que proíbe seis coisas e não tem um teste
  que reprove quando alguém faz uma delas é uma regra lembrada. Vira mecanismo com
  uma hora de trabalho: uma lista de dependências autorizadas num teste, que falha
  citando o número da ADR.
- **Matriz ponderada onde cabia julgamento.** Nota de 0 a 5 com pesos percentuais
  parece objetiva e não é: duas arquiteturas nunca são comparáveis o bastante para
  aritmética. Pior ainda é fixar os pesos depois de ler o resultado. Use os vetos
  binários — eles fazem o trabalho de verdade — e deixe a soma como desempate.
- **Experimento sem critério de parada.** "Continua aberto até acontecerem dez usos"
  não é critério de parada; é adiamento. Ponha uma data. Não acontecer também é um
  resultado, e costuma ser o mais informativo.
- **Deriva de quantum.** Um binário único, offline, sem runtime externo é uma
  propriedade arquitetural, não um detalhe de empacotamento. No dia em que um comando
  novo exigir a engine instalada, ele nasce como binário separado — decidir isso antes
  custa zero e depois custa reescrever o empacotamento.
- **Segunda fonte de verdade.** Informação operacional pertence ao teste ou ao código.
  Um documento em prosa que repete o que o código já decide vai divergir, e a divergência
  aparece no pior momento.
- **Cortar a parte onde mora a prova.** Reduzir escopo é quase sempre certo, e a
  primeira coisa que se corta costuma ser a que menos se usa. Antes de cortar,
  pergunte de onde vem a evidência de que o resto funciona. Num verificador real, a
  engine com um só projeto era a única que tinha produzido verdadeiros positivos; a
  engine favorita, com quatro projetos, nunca tinha detectado nada. A saída foi
  congelar em vez de remover: nada de regra nova ali, mas as regressões históricas
  ficam para sempre, porque são o único teste causal.
- **Referência virando requisito.** Um livro fornece método de decisão. Ele não fornece
  requisito do seu projeto e não determina que você deva construir alguma coisa.
  Mantenha separados: objetivo do proprietário, evidência local, referência
  metodológica e evidência de mercado. Uma afirmação só vira requisito quando puder
  ser rastreada ao objetivo ou a um experimento aceito.

## Duas coisas para não simplificar demais

**Nem toda duplicação é dívida.** Reimplementar de propósito o que o motor já faz é
correto quando você precisa de uma garantia que ele não dá — determinismo, estado
serializável, tempo de vida explícito, testabilidade. E duplicar a regra numa segunda
implementação, para conferir a primeira, é a forma mais sofisticada: ali, compartilhar
código destruiria a verificação. O motor ganha quando sabe algo que você não pode
conferir: ajuste de tela, escala de entrada, área segura, assinatura.

**A escolha de engine não é entre possível e impossível.** As três fecharam o mesmo
jogo, com tempos próximos até a primeira execução. A diferença está na **forma de
atrito** e, sobretudo, em quanto do ciclo o agente fecha sem pedir que uma pessoa
olhe. É esse o eixo que decide.

## Arquivos desta skill

| Arquivo | Quando ler |
|---|---|
| `references/governanca.md` | antes de auditar, comparar opções, escrever ADR, definir fitness function ou decidir separar componente |
| `references/licoes-medidas.md` | quando precisar da evidência, dos números ou das ressalvas da medição |
| `references/inicio-de-projeto.md` | ao começar um projeto de jogo do zero |
| `assets/CONTRATO.md` | contrato AI-first para a raiz do projeto |
| `assets/ADR.md` | modelo de registro de decisão |
| `assets/EVIDENCIA.md` | checklist antes de declarar tarefa concluída |
| `assets/RISCOS.md` | modelo de matriz de risco |
