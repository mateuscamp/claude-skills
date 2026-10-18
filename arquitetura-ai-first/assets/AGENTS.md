<!--
Template de AGENTS.md / CLAUDE.md gerado pela skill arquitetura-ai-first.
Regras: curto, imperativo, orientado a ação. Cada linha é relida a cada query e
custa token — remover o que não estiver sendo violado na prática.
Substituir tudo entre <>. Apagar as seções que não se aplicam ao projeto.
-->

# <Projeto>

<Uma linha: o que o sistema faz.>
Arquitetura: <estilo> · Quantum: <n> unidade(s) deployável(is). ADRs em `docs/adr/`.

## Comandos

- Setup: `<scripts/bootstrap.sh>` — idempotente, roda em máquina limpa.
- Testes: `<make test>` — headless, sem setup manual, sem credencial.
- Checagem completa (lint + tipos + fronteiras): `<make check>`.
- Rodar local: `<make dev>`.

Rodar `<make check>` antes de declarar qualquer tarefa concluída.

## Fronteiras (ADR-<NNNN>)

- `dominio/` não importa nada de `infra/`, `interface/` ou de terceiros.
- `aplicacao/` importa apenas `dominio/`.
- `infra/` implementa as portas definidas em `dominio/`; a direção nunca inverte.
- <Módulo X> é o único que escreve na tabela `<tabela>`. Ler de outro módulo: via
  API pública de <X>, nunca por SQL direto.
- Fronteira nova exige ADR antes do código.

## Estilo de código

- Funções: 4-20 linhas. Acima disso, quebrar.
- Arquivos: abaixo de 500 linhas. Acima disso, dividir por responsabilidade.
- Uma coisa por função, uma responsabilidade por módulo.
- Nomes específicos e únicos. Proibidos: `data`, `info`, `handler`, `manager`,
  `helper`, `utils`, `process`, `service`, `base`, `common`. Preferir nomes que
  retornem menos de 5 hits de grep no repositório.
- Tipos explícitos em toda função pública. Sem `Any`, sem dict sem tipo.
- Sem duplicação: extrair para função ou módulo.
- Early return em vez de if aninhado. Máximo 2 níveis de indentação.
- Mensagem de exceção sempre com o valor recebido e o formato esperado.

## Comentários

- Não apagar os comentários existentes em refactor — eles carregam intenção e
  proveniência.
- Escrever o PORQUÊ, não o QUÊ. Nada de `# incrementa i` acima de `i += 1`.
- Docstring em função pública: intenção + um exemplo de uso.
- Citar número de issue, ADR ou commit quando a linha existe por causa de um bug
  específico ou de uma limitação de biblioteca upstream.

## Ciclo de mudança (TDD)

1. Vermelho: um teste, um comportamento, nomeado pelo comportamento. Rodar e ver
   falhar NA ASSERÇÃO — `ImportError`/`NameError`/fixture quebrada não conta.
2. Verde: o mínimo de código que passa. Não editar o teste nesta fase. Rodar a
   suíte inteira.
3. Refatorar com a suíte verde (seção abaixo). Depois `<make check>` e commit.

- Bug: primeiro o teste de regressão que reproduz, visto falhando; depois o fix.
- O relatório da tarefa mostra a linha de falha do vermelho e o resumo do verde.
- Proibido para ficar verde: mudar asserção, `skip`/`xfail`, apagar teste,
  asserção mais fraca, mockar o próprio sujeito sob teste, `try/except` no teste.
  Teste estava errado? Dizer no relatório e voltar ao vermelho.
- Exceção declarada, nunca silenciosa: spike em `<spikes/>` não é mergeado;
  código legado ganha teste de caracterização antes da mudança.

## Testes

- F.I.R.S.T: rápido, independente, repetível, autoverificável, escrito antes.
- I/O externo (API, banco, filesystem, relógio) com fake nomeado e injetado, não
  com stub inline. Nunca fake do que está sendo testado.
- A suíte inteira roda em menos de <N> segundos. Passou disso, é bug de teste.

## Refatoração

- Muda estrutura, não comportamento: suíte verde antes e depois, nenhuma
  asserção alterada. Asserção mudou = não é refatoração, volta ao vermelho.
- Nunca refatorar e mudar comportamento no mesmo commit. Commit `refactor:` não
  toca em `tests/`, exceto para acompanhar renome ou movimentação.
- Passos pequenos (renomear, extrair, mover, inlinar), suíte a cada passo.
  Quebrou: desfazer o último passo.
- Editar o arquivo existente. Proibido regenerar o arquivo inteiro "limpo".
- Trecho sem teste: teste de caracterização antes de refatorar.
- Só nos arquivos que a tarefa já toca. Refatoração maior vira tarefa própria.
- Preservar comentários de proveniência e API pública. Mover código entre
  módulos ou trocar dono de dado é decisão arquitetural: ADR antes.

## Par de agentes (opcional — só com segundo agente disponível)

- Ping-pong: A escreve o teste e mostra o vermelho; B implementa o verde sem
  editar teste. Usar em <domínio/regras de negócio>, não em boilerplate.
- B recebe especificação, teste e diff — não o raciocínio de A.
- Desacordo vira teste; o que não cabe em teste sobe para o humano.

## Dependências

- Injetar por construtor ou parâmetro. Nunca instanciar dependência dentro da
  lógica, nunca importar singleton global.
- Biblioteca de terceiro sempre atrás de uma interface fina que pertence a este
  projeto.
- Dependência nova exige ADR.

## Código defensivo obrigatório

<Manter apenas o que este projeto realmente exige — o agente cobre o que estiver
listado e ignora o resto.>

- Timeout explícito em toda chamada de rede.
- Retry com backoff em <quais integrações>.
- Idempotência em <quais endpoints/consumidores>.
- Fallback quando <qual dependência> estiver indisponível.
- Rate limit em <quais rotas>.

## Logging e erro

- Log estruturado em JSON com campos nomeados para debug e observabilidade.
- Texto puro apenas em output de CLI para humano.
- Nunca logar <dado sensível do domínio>.

## Estrutura

```
<árvore de 10-15 linhas mostrando as fronteiras reais do projeto>
```

Caminhos previsíveis: para `src/<camada>/<modulo>.py` existe
`tests/<camada>/test_<modulo>.py`.
