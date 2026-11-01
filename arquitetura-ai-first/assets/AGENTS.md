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
- Testes funcionais: `<make e2e>` — fora do hook Stop; sempre no CI e antes do
  commit que fecha a história.
- Checagem completa (lint + tipos + fronteiras): `<make check>`.
- Rodar local: `<make dev>`.

Rodar `<make check>` antes de declarar qualquer tarefa concluída.

## Contextos e fronteiras (ADR-<NNNN>)

| Contexto | Subdomínio | Padrão | Testes |
|---|---|---|---|
| `<vendas>/` | núcleo | modelo de domínio, portas e adaptadores | pirâmide |
| `<cadastro>/` | suporte | transaction script, 3 camadas | fluxo pela API, banco real |
| `<pagamento>/` | genérico | `<produto>` atrás de `<pagamento>/acl/` | contrato do adaptador |

- Outro contexto só entra por `<contexto>/api.py`. Nunca importar o interno de
  outro contexto.
- No núcleo: `dominio/` não importa `infra/`, `interface/` nem terceiros;
  `aplicacao/` importa apenas `dominio/`; `infra/` implementa as portas de
  `dominio/`. Uma transação grava um agregado só.
- Regra de negócio do núcleo que não está escrita: perguntar, não inferir.
- SDK de `<fornecedor>` só em `<contexto>/acl/`, que traduz para o modelo do
  contexto.
- Subdomínio genérico (auth, cobrança, criptografia) não se escreve: pergunte
  qual produto usar.
- <Contexto X> é o único que escreve na tabela `<tabela>`. Ler de outro
  contexto: via `api.py` de <X>, nunca por SQL direto.
- Contexto novo, ou padrão novo num contexto, exige ADR antes do código.

## Linguagem

| Contexto | Termo | Não usar |
|---|---|---|
| `<vendas>` | `<Pedido>` | `<Order>`, `<Compra>` |

- Termo novo do negócio: perguntar o nome e acrescentar aqui antes do código.
- O mesmo termo pode significar outra coisa em outro contexto; vale a linha do
  contexto.

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

- Antes do commit, erro deliberado: troque a implementação por uma versão errada
  plausível. Se nenhum teste falha, falta teste.
- História com teste funcional: ele é escrito primeiro e é o critério de pronto.
  Enquanto vermelho, fica com falha esperada estrita, restrita à asserção, e o
  motivo nomeando a história. Um por vez.

- Bug: primeiro o teste de regressão que reproduz, visto falhando; depois o fix.
- O relatório da tarefa mostra a linha de falha do vermelho e o resumo do verde.
- Proibido para ficar verde: mudar asserção, `skip`/`xfail`, apagar ou renomear
  teste para fora da coleta, asserção mais fraca, mockar o próprio sujeito sob
  teste, `try/except` no teste, `sleep` fixo, aumentar prazo de espera sem dizer.
  Teste estava errado? Dizer no relatório e voltar ao vermelho.
- Exceção declarada, nunca silenciosa: spike em `<spikes/>` não é mergeado;
  código legado ganha teste de caracterização antes da mudança.

## Revisão antes do PR

- Todo diff: a code-audit, em modo auditoria. Ela confere o vermelho dos testes
  novos numa cópia descartável.
- Diff que toca <`dominio/`, fronteira de ADR, dono de dado>: antes dela, a
  `/code-review` no nível de esforço desta sessão, nunca abaixo de high, com o
  nível sempre explícito na chamada (sem ele, ela reaproveita o último
  digitado). Não vê o nível da sessão? Pergunte; não chute. `ultra` só o humano
  dispara. A code-audit confere cada achado dela; achado sem evidência não entra
  no relatório.
- Sem a `/code-review` no ambiente (ela é do Claude Code), a code-audit sozinha.
- Revisão em contexto separado (subagente ou outra sessão): o diff, a
  especificação e os ADRs, nunca o raciocínio de quem implementou.
- Achado não se corrige, nem por `--fix`, sem o sim do humano.

## Testes

- F.I.R.S.T: rápido, independente, repetível, autoverificável, escrito antes.
- I/O externo (API, banco, filesystem, relógio) com fake nomeado e injetado, não
  com stub inline. Nunca fake do que está sendo testado. Dublê entre camadas do
  próprio código só com o motivo no docstring e a suposição testada embaixo.
- Setup maior que o teste ou muitos dublês: refatore o código, não o teste.
- Não teste constante nem texto literal de template.
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
- Evento sai pela outbox, gravado na mesma transação do estado. Nunca
  `commit()` seguido de `publish()`.
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

Caminhos previsíveis: para `src/<contexto>/<camada>/<modulo>.py` existe
`tests/<contexto>/<camada>/test_<modulo>.py`.
