---
name: arquitetura-ai-first
description: Governa decisão de arquitetura em projeto backend ou full stack construído com agentes de IA — extrai drivers antes de tecnologia, mede o quantum atual, faz análise de trade-off sobre as dimensões emaranhadas, fecha em ADR numerado, converte cada decisão em fitness function executável no CI e traduz a fronteira resultante em regra no AGENTS.md que o agente relê a cada iteração, inclusive o ciclo TDD e de refatoração. Use sempre que o usuário for iniciar, estruturar, revisar ou justificar a estrutura de um projeto de software — "como estruturo esse projeto", "monólito ou microserviço", "vale separar esse serviço", "qual banco uso", "fila ou chamada direta", "como divido os módulos", "esse acoplamento me incomoda", "isso escala?", "escreve o AGENTS.md desse repo", "o agente está fazendo bagunça no projeto", "o agente escreve teste que sempre passa", "TDD com agente", "mock demais", "teste ponta a ponta" — inclusive quando ele não usar as palavras arquitetura, trade-off, ADR ou fitness function.
---

# Arquitetura AI-first

Governança de decisão arquitetural para repositório cujo código é escrito por
agente e lido por agente. Duas disciplinas costuradas: a **decisão registrada**
(o porquê, que sobrevive à rotação de contexto) e o **enforcement executável**
(o que impede a erosão entre uma sessão e a próxima). A saída é sempre uma
recomendação, com o custo declarado e a condição que a inverte.

A auditoria de diff, PR e issue, inclusive a conferência do teste visto falhar,
fica na skill **code-audit**. Aqui fica quando ela roda: na fitness function
que esta skill escreve (etapa 9) e no contrato do agente (etapa 10).

## Premissas que mudam o desenho

1. **Não existe best practice, existe trade-off.** Toda opção paga em alguma
   moeda. Se uma opção parece não ter custo, o custo ainda não foi encontrado —
   procure mais um pouco antes de recomendá-la.
2. **O porquê vale mais que o como.** Estrutura sem registro do motivo vira
   Groundhog Day: a mesma discussão reaberta a cada três meses, agora sem os
   fatos que a decidiram.
3. **O leitor primário do repositório é o agente.** Ele não abre o ADR por
   conta própria; ele relê o `AGENTS.md` a cada query, faz grep antes de ler
   arquivo, e implementa o caminho feliz sempre que a regra não estiver escrita.
   Fronteira arquitetural que não vira linha no arquivo que o agente lê e teste
   que o CI roda não sobrevive a três sessões de codificação.

## Quando usar

- Projeto novo: decidir estilo, fronteiras de módulo, dono do dado, esqueleto do repo.
- Projeto em andamento: separar/juntar serviço, trocar banco, introduzir fila,
  quebrar schema, definir contrato entre partes.
- Sintoma sem nome: "toda mudança aqui quebra outra coisa", "o agente está
  criando arquivo gigante", "não consigo testar isso sem subir tudo".
- Justificar por escrito uma decisão já tomada (vira ADR + fitness function).

## Quando NÃO usar

- **Dúvida de implementação sem consequência estrutural.** Qual biblioteca de
  data usar, como escrever um decorator, por que esse teste falha. Responder
  direto; cerimônia de decisão em pergunta pequena queima contexto e ensina o
  usuário a evitar a skill.
- **Decisão barata de reverter.** Se desfazer custa uma tarde, é design, não
  arquitetura. Dizer isso em uma linha e seguir para a implementação.
- **Bug, incidente ou performance de uma query específica.** Outro passe.

O teste: a decisão muda estrutura, característica não-funcional, dependência,
interface entre partes, ou dono do dado? Se nenhuma das cinco, não é
arquitetural.

## Procedimento (sempre nesta ordem)

1. **Triar.** Classificar o pedido em: decisão nova · revisão de decisão
   existente · registro de decisão já tomada · dúvida não-arquitetural. No
   quarto caso, sair da skill explicitamente e responder direto.

2. **Drivers antes de tecnologia.** Extrair as características de arquitetura do
   domínio e dos requisitos — no máximo 7, exatamente **um** driver principal
   marcado ★. Cada driver precisa de origem (a frase do problema que o gerou) e
   de medida (o número que diz se está sendo cumprido). Adjetivo sem medida não
   é driver, é desejo, e não entra na tabela. Se o usuário abriu pela solução
   ("quero usar Kafka", "vou de microserviços"), reconstruir os drivers antes de
   discutir a solução — a solução volta na etapa 5 como uma das opções.
   Catálogo, mapeamento de domínio→característica e medidas: `references/drivers-e-caracteristicas.md`.

3. **Medir o quantum atual.** Nomear as unidades independentemente deployáveis
   e o dado que cada uma possui. Banco compartilhado por N serviços = **um**
   quantum, independente de quantos contêineres existem. Essa etapa decide se a
   conversa é sobre módulos dentro de um quantum ou sobre topologia distribuída
   — e frequentemente mostra que o sistema não é o que o nome dele diz.

4. **Aplicar a postura default: monólito modular.** Distribuir exige nomear pelo
   menos um driver de modularidade — manutenibilidade, testabilidade,
   deployabilidade, escalabilidade, disponibilidade — com **evidência**, não com
   previsão. Sem evidência, a decisão é "não distribuir" e a conversa vira
   desenho de componentes dentro do monólito. Distribuir por antecipação cobra
   o preço da rede hoje pelo benefício de um problema que talvez nunca chegue.

5. **Achar as dimensões emaranhadas.** Listar os pontos de acoplamento que a
   decisão toca, usando a pergunta simples: *se alguém mudar X, Y é forçado a
   mudar?* Montar a matriz das combinações plausíveis e descartar as inviáveis
   com um motivo de uma linha cada. Método completo e tabelas de decisão
   (granularidade, dado, saga, contrato, reuso, consistência): `references/analise-de-tradeoffs.md`.

6. **Avaliar trade-off, opção por opção.** Para cada opção: o que ganha, o que
   perde, e em qual driver da etapa 2 isso bate. Modelar com os números do
   domínio do usuário — volume real, tamanho de time, orçamento, SLA. Benchmark
   genérico de blog não decide nada aqui. Proibido "depende" sem a variável que
   decide dito na mesma frase.

7. **Bottom line.** Uma recomendação. Uma linha de justificativa ancorada no
   driver ★. Uma condição explícita que inverteria a escolha. Evidência
   detalhada fica abaixo, não no lugar da recomendação.

8. **Registrar em ADR.** Numerado, com Alternativas e Governança preenchidas,
   status `Proposto` até o usuário aceitar. Template e ciclo de vida:
   `references/adr.md` · `assets/ADR-template.md`.

9. **Escrever a fitness function.** Para o driver ★ e para cada restrição que a
   decisão criou: qual checagem, qual tipo (atômica/holística, contínua/acionada),
   onde roda (pre-commit, CI, produção), e a condição exata de falha. Se não dá
   para automatizar, escrever a checagem manual com cadência e responsável.
   Decisão sem enforcement é intenção — o agente vai violá-la na terceira sessão
   sem nenhuma má-fé. Quando a checagem entra no repositório nesta sessão, a
   code-audit confere o vermelho dela (seção 4.4 da code-audit) antes de a
   decisão fechar: fitness function que nunca reprovou não é enforcement.
   Catálogo por característica, com código:
   `references/fitness-functions.md` · `assets/test_arquitetura.py` · `assets/workflow-arquitetura.yml`.

10. **Traduzir para o contrato do agente.** Converter a fronteira em regras no
    `AGENTS.md`/`CLAUDE.md`: quem pode importar quem, nomes grepáveis, comando
    único de teste, formato de log e de erro, categorias de código defensivo
    exigidas, e o **ciclo de mudança**: TDD (vermelho visto falhando na
    asserção antes do código), refatoração com os dois chapéus separados, a
    revisão antes do PR (code-audit em todo diff; `/code-review` onde o risco
    pede, no esforço da sessão e nunca abaixo de high) e, se houver segundo
    agente, o par ping-pong. Com mais de uma camada testável, o ciclo duplo: o
    teste funcional da história é o critério de pronto. Curto, imperativo,
    orientado a ação — cada linha custa token em toda iteração.
    Regras e template: `references/legibilidade-para-agentes.md` ·
    `references/tdd-e-refatoracao.md` · `references/testes-em-camadas.md` · `assets/AGENTS.md`.

11. **Próximo passo único.** Uma tarefa para a próxima sessão. Uma. Lista de
    próximos passos equivale a nenhum próximo passo.

## Contrato de saída

````markdown
# <Projeto> — decisão <n>: <a pergunta em uma linha>

**Bottom line** — <recomendação em uma frase> · inverte se <condição>

## Drivers
| ★ | Característica | Origem (frase do problema) | Como se mede |
|---|---|---|---|
<máximo 7 linhas, exatamente um ★>

## Quantum atual
<uma linha por unidade deployável: o que ela é e qual dado ela possui>

## Dimensões emaranhadas
- **<dimensão>** — se <X> mudar, <Y> muda porque <mecanismo>

## Opções
| Opção | Ganha | Perde | Driver afetado | Viável? |
|---|---|---|---|---|

## Trade-off da escolhida
<2 a 4 linhas com os números do domínio>

## ADR
`docs/adr/<NNNN>-<slug>.md` · status <Proposto|Aceito|Substituído por NNNN>

## Fitness functions
| Driver | Checagem | Tipo | Onde roda | Falha quando |
|---|---|---|---|---|

## Contrato para o agente
```md
<bloco pronto para colar no AGENTS.md>
```

## Próximo passo
<uma tarefa>
````

Seções vazias são omitidas, não preenchidas com "N/A" — exceto **Drivers**,
**Bottom line** e **Fitness functions**, que nunca podem faltar.

## Regras invioláveis

1. **Nenhuma tecnologia antes dos drivers.** Nome de banco, de fila ou de
   framework mencionado antes da tabela da etapa 2 é chute com sotaque técnico.
2. **Toda recomendação declara o que se perde.** Recomendação sem custo
   declarado é propaganda. Se o custo não apareceu, procure mais.
3. **"Best practice" e nome de empresa não são argumento.** "A Netflix faz
   assim" descreve os drivers da Netflix. O critério é o driver ★ do usuário.
   Fonte que só lista vantagens é descartada como fonte.
4. **Não distribuir sem driver de modularidade com evidência.** Previsão de
   crescimento não é evidência.
5. **Banco compartilhado é um quantum.** Não chamar de microserviço o que
   escreve no schema do vizinho. Nomear a coisa pelo que ela é, mesmo quando o
   nome errado já está no README.
6. **Decisão não fecha sem fitness function.** Nem que seja manual, com
   cadência e responsável escritos.
7. **Decisão não fecha sem ADR.** Inclusive — principalmente — a decisão de
   *não* fazer algo. É o registro do "não" que impede a mesma discussão em maio.
8. **Fronteira que não aparece na árvore de diretórios não é fronteira.** Se o
   agente precisa entender uma convenção implícita para respeitar o limite, o
   limite já está quebrado. Fronteira boa é grepável e testável.
9. **Nunca podar comentário de proveniência.** O porquê mora em três lugares —
   ADR, mensagem de commit e comentário no ponto exato do código. Refactor que
   remove comentário de contexto destrói a única fonte que o agente lê durante
   um tool call.
10. **Números do domínio, não do blog.** Modelar com o volume, o time e o
    orçamento reais. Conclusão importada de outro contexto é a armadilha mais
    cara desse ofício.
11. **Decisão já tomada não é relitigada sem evidência nova.** Quando o usuário
    chega com a escolha feita, o trabalho é registrar, listar as consequências
    que ele vai pagar e escrever o enforcement — não vender a alternativa.
    Discordância entra como uma linha em Consequências do ADR, e a skill segue.
12. **Teste que nunca foi visto falhar não conta.** O contrato do agente exige
    o vermelho antes do verde e a evidência dele no relatório. Teste escrito
    depois espelha a implementação — inclusive o bug — e deixa a fitness
    function verde enquanto o comportamento está errado.
13. **Least worst.** O alvo nunca é a melhor arquitetura; é a menos ruim para
    esses drivers, neste ano, com esse time. Dizer isso quando o usuário estiver
    procurando a solução ótima.

## Referências

Ler sob demanda, nunca todas de uma vez:

| Arquivo | Ler quando |
|---|---|
| `references/drivers-e-caracteristicas.md` | Etapa 2 — extrair e medir drivers |
| `references/analise-de-tradeoffs.md` | Etapas 5-7 — dimensões, matriz, tabelas de decisão |
| `references/adr.md` | Etapa 8 — registrar, numerar, substituir |
| `references/fitness-functions.md` | Etapa 9 — converter driver em checagem executável |
| `references/legibilidade-para-agentes.md` | Etapa 10 — regras do repo para o agente |
| `references/tdd-e-refatoracao.md` | Etapa 10 — ciclo TDD, refatoração, par de agentes, revisão antes do PR e o enforcement deles |
| `references/testes-em-camadas.md` | Etapa 10 — ciclo duplo com teste funcional, pirâmide, onde cada camada roda, dublês, erro deliberado, spike |

Assets prontos para copiar: `assets/ADR-template.md`, `assets/AGENTS.md`,
`assets/test_arquitetura.py`, `assets/workflow-arquitetura.yml`.
