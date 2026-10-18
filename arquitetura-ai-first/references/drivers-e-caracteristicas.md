# Drivers: características de arquitetura

Ler na etapa 2 do procedimento.

Uma característica de arquitetura é um critério **não-domínio** que influencia
estrutura e é **crítico ao sucesso** do sistema. "Processar pagamento" é
requisito de domínio. "Processar pagamento em até 300 ms no p95 com 99,9% de
disponibilidade" traz duas características. A distinção importa porque
características são o que a estrutura paga para entregar — e o que se perde
quando a estrutura muda.

## Sumário

- [As três famílias](#as-três-famílias)
- [Extrair do domínio](#extrair-do-domínio)
- [As implícitas](#as-implícitas-que-ninguém-escreve-no-ticket)
- [De adjetivo para medida](#de-adjetivo-para-medida)
- [Legibilidade por agente](#legibilidade-por-agente-a-característica-nova)
- [Limite de sete](#o-limite-de-sete-e-o-driver-★)

## As três famílias

**Operacionais** — sobrevivem ao contato com produção:
disponibilidade · continuidade (recuperação de desastre) · performance (pico,
latência, capacidade, tempo de resposta) · recuperabilidade (RTO/RPO) ·
confiabilidade/segurança de operação · robustez · escalabilidade · elasticidade.

Escalabilidade e elasticidade não são a mesma coisa: escalabilidade é crescer
com o usuário ao longo de meses; elasticidade é absorver um pico de dez
segundos. Sistemas de leilão, de venda de ingresso e de prova online precisam da
segunda, e ela empurra o desenho para uma direção bem diferente.

**Estruturais** — sobrevivem ao contato com o próprio time:
modularidade · manutenibilidade · extensibilidade · portabilidade ·
deployabilidade · testabilidade · configurabilidade · atualizabilidade ·
suportabilidade · instalabilidade · reusabilidade · localização.

**Transversais** — não cabem em nenhuma das duas e atravessam tudo:
segurança · privacidade · auditabilidade · legal/conformidade · acessibilidade ·
usabilidade · autenticação e autorização · registro/rastreabilidade.

## Extrair do domínio

O stakeholder fala em preocupação de negócio; o trabalho é traduzir. Mapeamento
que funciona na maioria dos casos:

| O que o stakeholder diz | Características que isso implica |
|---|---|
| "Preciso lançar rápido / testar hipótese" | deployabilidade, testabilidade, simplicidade, viabilidade |
| "Se cair, perco cliente" | disponibilidade, tolerância a falha, recuperabilidade |
| "Vai ter pico em data X" | elasticidade, escalabilidade |
| "Vamos crescer o time / abrir o código" | modularidade, manutenibilidade, legibilidade por agente |
| "Não pode vazar" | segurança, privacidade, auditabilidade |
| "O concorrente lança feature toda semana" | extensibilidade, deployabilidade |
| "Não tenho orçamento nem time" | viabilidade, simplicidade — e elas cortam quase todas as outras |

Regra de conversa: quando o usuário disser um substantivo de negócio, devolver a
característica traduzida e confirmar. "Você disse que a janela de submissão é de
duas horas no dia da prova — leio isso como elasticidade, não escalabilidade.
Confere?" Se ele corrigir, a correção dele vale mais que o mapeamento acima.

## As implícitas (que ninguém escreve no ticket)

Ninguém pede disponibilidade, segurança ou viabilidade explicitamente — e as
três decidem a maior parte do desenho. Listar as implícitas relevantes e marcar
como implícitas na tabela. **Viabilidade** (custo, prazo, tamanho e experiência
do time) é implícita em todo projeto pessoal ou de time pequeno e é a que mais
frequentemente derruba a arquitetura "correta". Um sistema que o time não
consegue operar não é uma arquitetura, é uma dívida com juros.

## De adjetivo para medida

Sem medida não há governança: não dá para escrever fitness function para
"escalável". Converter antes de seguir.

| Adjetivo | Medida operacional |
|---|---|
| escalável | p95 de latência sob N req/s sustentados por M minutos |
| elástico | tempo até absorver 10× o tráfego base sem erro 5xx |
| disponível | % de sucesso mensal + tempo máximo de indisponibilidade tolerado |
| recuperável | RTO (tempo até voltar) e RPO (dado que se aceita perder) |
| manutenível | ciclomática máxima, tamanho de arquivo, acoplamento aferente/eferente |
| testável | % de módulos com teste headless, tempo total da suíte, nº de passos de setup |
| deployável | lead time do commit até produção, taxa de rollback, tempo de CI |
| modular | ausência de ciclo entre pacotes, direção de dependência respeitada |
| seguro | vulnerabilidades conhecidas em dependências, rotas sem autenticação |
| legível por agente | linhas por arquivo, hits de grep por nome público, cobertura de tipos |

Medida sem número combinado é medida decorativa. Perguntar o número. Se o
usuário não souber, propor um valor inicial explícito e marcá-lo como
provisório no ADR — número provisório escrito vale mais que número exato
imaginado.

## Legibilidade por agente: a característica nova

Não está nos livros porque ainda não havia o problema. É estrutural, é
mensurável e, em repositório escrito por agente, costuma disputar o topo:

- **Tamanho de unidade** — arquivo abaixo de ~500 linhas, função de 4 a 20
  linhas. Não é estética: é o que cabe em uma leitura sem paginação. Unidade que
  o agente lê inteira ele raciocina com atenção cheia; unidade que ele pagina
  vira modelo mental fragmentado.
- **Nomes grepáveis** — o agente navega por busca lexical antes de ler arquivo.
  `data`, `handler`, `Manager`, `Service`, `utils` retornam cinquenta matches e
  forçam leitura de todos. Regra prática: se o grep do nome traz lixo, o nome
  está ruim. Menos de ~5 hits relevantes é o alvo.
- **Tipos explícitos** — assinatura tipada é gabarito imediato; código dinâmico
  sem anotação obriga o agente a inferir tipo pelo uso, o que custa raciocínio e
  erra.
- **Ciclo de feedback fechado** — comando único de teste, output parseável,
  sem setup manual. Se o teste não roda headless, o agente fica cego e passa a
  chutar; chute precisa de revisão humana, e é aí que a velocidade morre.
- **Proveniência preservada** — o porquê acessível no ponto do código.

Essas cinco viraram medida de custo real: token por iteração, latência de tool
call, taxa de retrabalho. É a diferença entre "opinião sobre estilo" e
"restrição técnica com fatura no fim do mês".

## O limite de sete e o driver ★

Toda característica adicional cobra em complexidade estrutural, e várias delas
são mutuamente hostis: elasticidade briga com consistência forte; segurança
briga com performance; extensibilidade briga com simplicidade. Por isso:

- **Máximo 7 características.** Se a lista passa de sete, o time ainda não
  decidiu o que o sistema é.
- **Exatamente um driver ★.** É o desempate quando duas características se
  contradizem no meio da implementação — e elas vão se contradizer. Sem ★
  definido, cada decisão pequena reabre a discussão inteira.
- **Least worst.** Não existe arquitetura que maximize as sete. Existe a menos
  ruim para esses drivers, neste ano, com esse time. Dizer isso em voz alta
  quando o usuário estiver procurando a ótima — a busca pela ótima é o que
  produz sistema que ninguém consegue operar.
