# O agente como leitor primário

Ler na etapa 10. Template pronto em `assets/AGENTS.md`.

O Clean Code foi escrito para um leitor humano sentado no editor. Em repositório
onde o agente lê, edita e estende, o leitor primário mudou — e as restrições
dele são outras. Boa parte do livro continua valendo; algumas regras mudaram de
peso, uma inverteu de sinal, e apareceram exigências que não existiam.

O ponto de arquitetura: essas restrições **têm fatura**. Token por iteração,
latência de tool call, taxa de retrabalho, alucinação no output. O que era
opinião sobre estilo virou característica mensurável — e por isso entra na
tabela de drivers como qualquer outra.

## As restrições reais

- **Truncamento de leitura.** As CLIs de agente leem arquivo em faixas
  limitadas. Arquivo grande não entra inteiro na janela: o agente pagina ou
  reconstrói por grep, e monta modelo mental fragmentado.
- **Atenção degrada antes do limite anunciado.** A janela de contexto declarada
  não é a janela útil. E o contexto não é só o código: tem `AGENTS.md`, prompt de
  sistema, histórico, output de tool, log de erro, saída de teste — tudo
  disputando o mesmo espaço.
- **Grep é mais barato que leitura.** O agente prefere buscar a carregar. Nome
  único e distintivo é a API primária de navegação dele, não conveniência.
- **Tool call custa token e segundo.** Arquivo curto, log enxuto e output de
  teste pequeno mantêm a sessão produtiva e a conta baixa.
- **Sem instrução, o agente faz a média.** Ele implementa o caminho feliz,
  função de oitenta linhas, sem injeção de dependência, duplicando lógica.
  Isso não é defeito: é ausência de regra escrita.

## O que virou restrição técnica

**1. Unidade pequena.** Função de 4 a 20 linhas, arquivo abaixo de ~500. A
justificativa mudou: não é mais "facilita a leitura", é "casa com a unidade de
processamento do modelo". Unidade que cabe em uma chamada é raciocinada com
atenção cheia.

**2. Responsabilidade única.** Módulo com uma razão para mudar permite ao agente
isolar, testar e editar sem carregar o sistema inteiro. Uma classe de 800 linhas
que faz três coisas é pior que três de 250 — mesmo com o total idêntico. É o
princípio que mais economiza contexto na prática.

**3. Nome grepável.** "Pesquisável" passou a ser a propriedade mais importante
de um nome. `UserRegistrationValidator` traz três matches; `Manager` traz
cinquenta e obriga o agente a ler todos. No código de negócio, o nome certo é o
termo do glossário do contexto: sinônimo divide os matches ao meio
(`references/dominio-e-contextos.md`, "Linguagem ubíqua").

**4. Comentário de proveniência — a inversão.** A regra antiga era que
comentário em excesso é code smell. Ela se inverteu, e por um motivo estrutural:
o agente tem fluência perfeita de sintaxe e não precisa de legenda para `i++`.
O que ele **não** tem é o porquê — qual bug motivou aquela ordem estranha, qual
constraint de negócio força aquela sequência, qual lib upstream tem defeito
conhecido. Isso só existe na cabeça de quem escreveu, na mensagem de commit ou
em um comentário no ponto certo — e o comentário é a fonte mais acessível
durante um tool call. Corolário prático: **não podar os comentários que o
próprio agente escreveu no refactor.** Ele os deixou porque julgou a informação
digna de preservar para a próxima edição. O único tipo que ainda merece corte é
o comentário que descreve o óbvio.

**5. Tipos explícitos.** Assinatura tipada é gabarito imediato. Migrar um
projeto Python sem anotação para tipado costuma render mais produtividade que
qualquer refactor de lógica.

**6. DRY com peso novo.** Quando algo duplicado muda, o agente pode atualizar
uma cópia e esquecer as outras — não há gravidade que o puxe para as demais.
Fatorar não é estética; é segurança de refactor automatizado.

**7. Teste que o agente consegue rodar.** Comando no `README`/`AGENTS.md`/
`Makefile`, output previsível, sem seed manual de banco, sem config fora do
repo, sem credencial secreta. Esse ciclo — escreve, roda, lê, ajusta — é a base
de tudo. Sem ele o agente fica cego e volta a chutar, e chute exige revisão
manual, que mata a velocidade que ele deveria trazer. O ciclo só fecha de
verdade com o teste **antes**: teste escrito depois espelha a implementação.
Ciclo TDD, refatoração e par de agentes: `references/tdd-e-refatoracao.md`.

**8. Árvore previsível.** Se `src/servicos/agendamento.py` implica
`src/modelos/agendamento.py` e `tests/servicos/test_agendamento.py`, o agente
antecipa caminhos sem listar diretório. Convenção forte de framework ajuda;
projeto sem convenção obriga o agente a explorar, e exploração custa token.

**9. Injeção de dependência.** Dependência injetada permite substituir por fake
no teste sem tocar na lógica. Código que instancia a própria dependência força
o agente a monkey-patch e a subir infraestrutura de mentira — lento, frágil, e
polui a sessão com ruído.

**10. Aninhamento raso.** Cada nível de indentação é estado que o modelo rastreia.
Guard clause, early return e pattern matching melhoram a resposta de forma
mensurável.

**11. Erro com contexto.** `ValueError("invalid input")` não ajuda ninguém.
`ValueError(f"esperado dígitos não-vazios, recebido {value!r}")` economiza um
round inteiro de investigação. Mensagem de exceção é sinal de debug para o
agente.

**12. Formatação: não discutir.** Formatador default da linguagem, configurado
no pre-commit, e segue a vida. Tab versus espaço virou ruído.

## O que não existia em 2008

- **Arquivo de meta-documentação** (`AGENTS.md`, `CLAUDE.md`, `.cursor/rules`).
  Lido antes de qualquer tool call, relido a cada query. Formato: curto,
  imperativo, orientado a ação. Nada de prosa filosófica — cada linha custa token
  em toda iteração, então densidade é o critério de qualidade.
- **README com arquitetura de alto nível.** Diagrama simples em ASCII ou Mermaid
  encurta muito o caminho até o agente entender o shape do projeto.
- **Logging estruturado.** JSON com campos nomeados é parseável trivialmente;
  `print` em texto livre obriga parsing heurístico.
- **Comandos de observabilidade acessíveis.** `make test`, `make lint`,
  `make check`. Quanto mais previsível o comando, mais o agente valida sozinho.
- **Setup idempotente.** `scripts/bootstrap.sh` que roda em máquina limpa e
  chega a um estado de trabalho. Onboarding que depende de instrução na cabeça
  de alguém exclui o agente do jogo.

## Código defensivo precisa ser listado

O agente implementa circuit breaker, retry com backoff, timeout agressivo e
degradação graciosa muito bem — **quando é pedido**. Sozinho ele não propõe,
porque não conhece os pontos de falha operacional do sistema. Se o `AGENTS.md`
listar as categorias que o projeto exige (timeout, retry, rate limit, breaker,
fallback, idempotência), o agente cobre. Se não listar, ele entrega o caminho
feliz. Essa lista é decisão arquitetural e vem dos drivers de disponibilidade e
tolerância a falha — não é detalhe de implementação.

## Costura com a arquitetura

A regra que fecha o ciclo:

> Fronteira arquitetural existe em três lugares ou não existe: no **ADR** (o
> porquê), no **AGENTS.md** (a regra que o agente lê em toda iteração) e na
> **fitness function** (o teste que impede a travessia). Faltando qualquer um
> dos três, a fronteira é decorativa e some em poucas semanas de codificação
> assistida.

Duas consequências de desenho que valem para a estrutura, não só para o estilo:

- **Módulo é unidade de contexto.** Se para mudar uma coisa o agente precisa
  carregar quatro pacotes, o problema não é o agente — é a coesão. Custo de
  contexto é sintoma mensurável de acoplamento e serve como evidência real no
  passo de trade-off.
- **Fronteira precisa ser visível na árvore.** Convenção implícita que só existe
  na cabeça do time é invisível para o agente. Diretório, nome e teste de import
  são a forma de tornar a fronteira legível.
