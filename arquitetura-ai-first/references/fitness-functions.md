# Fitness functions

Ler na etapa 9. Código pronto em `assets/test_arquitetura.py` e
`assets/workflow-arquitetura.yml`.

Uma fitness function é qualquer mecanismo que responde, objetivamente, se uma
característica de arquitetura ainda está sendo cumprida. Não é teste de unidade
(que verifica domínio) nem lint de estilo (que verifica gosto): é o teste da
**decisão**. Sem ela, a arquitetura vira intenção e a erosão é silenciosa — o
sistema continua passando em todos os testes verdes enquanto a fronteira que
justificava a estrutura já foi atravessada em quatro lugares.

Em repositório escrito por agente ela deixa de ser boa prática e vira
infraestrutura: o agente não tem gravidade natural que o puxe para a fronteira
que você desenhou. Ele lê a regra ou trombe no teste. Quando não há nem regra
nem teste, ele implementa o caminho médio — arquivo grande, import direto, sem
injeção, sem timeout.

## Sumário

- [Taxonomia](#taxonomia)
- [Catálogo por característica](#catálogo-por-característica)
- [Fronteira de módulo](#fronteira-de-módulo-a-mais-importante)
- [Legibilidade por agente](#legibilidade-por-agente)
- [Onde cada checagem roda](#onde-cada-checagem-roda)
- [Regras de escrita](#regras-de-escrita)

## Taxonomia

**Atômica** verifica um aspecto isolado (nenhum arquivo acima de 500 linhas).
**Holística** verifica a interação de vários (latência do endpoint *depois* de
ligar a criptografia em repouso — cada parte passa sozinha e o conjunto falha).

**Acionada** roda em evento: commit, push, pipeline. **Contínua** roda em
produção o tempo todo: monitor de latência, alerta de taxa de erro, verificação
de contrato entre serviços em runtime.

**Automatizada** é o alvo. **Manual** é aceitável quando o custo de automatizar
não se paga — e nesse caso precisa de cadência e responsável escritos, senão é
ficção. Uma revisão trimestral marcada no calendário é uma fitness function;
"a gente revisa de vez em quando" não é.

Começar sempre pela atômica automatizada acionada no CI. É a que dá retorno no
mesmo dia.

## Catálogo por característica

| Característica | Checagem | Ferramenta típica (Python) | Falha quando |
|---|---|---|---|
| Modularidade | ausência de ciclo entre pacotes | `import-linter`, teste com `ast` | existe ciclo A→B→A |
| Modularidade | direção de dependência | `import-linter` (contrato `layers`) | camada de baixo importa a de cima |
| Manutenibilidade | complexidade e tamanho | `ruff` (`C901`, `PLR0915`), teste de linhas | função acima do limite |
| Testabilidade | suíte headless em um comando | `pytest` + `make test` | precisa de passo manual |
| Testabilidade | tempo da suíte | duração do job no CI | passa do orçamento (ex.: 90 s) |
| Testabilidade | testes pegam mudança de comportamento | `mutmut`, `cosmic-ray` (agendado) | mutation score abaixo do alvo |
| Disciplina de teste | teste desligado ou refatoração que muda asserção | grep de `skip`/`xfail`, diff de `tests/` | ver `references/tdd-e-refatoracao.md` |
| Deployabilidade | lead time / duração do pipeline | tempo do workflow | CI passa de N minutos |
| Performance | p95 sob carga | `k6`, `locust`, `pytest-benchmark` | p95 acima do alvo do driver |
| Escalabilidade | vazão sustentada | teste de carga acionado | erro 5xx acima do limite |
| Disponibilidade | timeout e retry em toda saída | teste `ast` sobre chamadas HTTP | chamada sem `timeout` |
| Disponibilidade | monitor de erro em produção | alerta do provedor | taxa de erro acima do SLO |
| Segurança | dependência vulnerável | `pip-audit` | CVE conhecido acima do severidade X |
| Segurança | rota sem autenticação | teste que varre o router | rota pública não declarada |
| Posse do dado | só o dono referencia a tabela | teste de grep sobre o nome da tabela | módulo estranho toca a tabela |
| Contrato | consumidor e provedor concordam | `schemathesis`, snapshot de OpenAPI | schema mudou sem versionar |
| Legibilidade por agente | tamanho de arquivo, nomes, tipos | teste próprio + `mypy` | ver seção abaixo |

Em front-end/TypeScript os equivalentes diretos: `dependency-cruiser` para
fronteira e ciclo, `eslint` com `no-restricted-imports`, `tsc --noEmit` para
tipos, `depcheck` para dependência morta.

## Fronteira de módulo (a mais importante)

Se apenas uma fitness function for escrita no projeto, que seja essa. Fronteira
que não é testada é fronteira que já foi atravessada.

Declarar o grafo permitido de forma explícita e legível — ele documenta a
arquitetura e a testa ao mesmo tempo:

```python
# tests/arquitetura/test_fronteiras.py
DEPENDENCIAS_PERMITIDAS = {
    "dominio":     set(),                          # domínio não importa ninguém
    "aplicacao":   {"dominio"},
    "infra":       {"dominio", "aplicacao"},
    "interface":   {"aplicacao", "dominio"},
}
```

Com `import-linter`, a mesma coisa em declaração:

```ini
# setup.cfg
[importlinter]
root_package = meuprojeto

[importlinter:contract:camadas]
name = Camadas respeitadas
type = layers
layers =
    meuprojeto.interface
    meuprojeto.aplicacao
    meuprojeto.dominio

[importlinter:contract:sem-ciclo]
name = Sem ciclo entre módulos de domínio
type = independence
modules =
    meuprojeto.dominio.agendamento
    meuprojeto.dominio.faturamento
```

A mensagem de falha precisa dizer **o arquivo, o import proibido e o número do
ADR** que criou a regra. Falha genérica ("violação de arquitetura") faz o agente
contornar; falha que cita o ADR faz o agente ler o ADR.

## Legibilidade por agente

Quatro checagens baratas que economizam token em toda sessão futura:

```python
LIMITE_LINHAS_ARQUIVO = 500
LIMITE_LINHAS_FUNCAO = 40          # 4-20 é o alvo; 40 é o teto duro
NOMES_PROIBIDOS = {"data", "info", "handler", "manager", "helper",
                   "utils", "process", "service", "base", "common"}
```

1. **Tamanho de arquivo** — arquivo acima do limite não cabe em uma leitura e
   força paginação.
2. **Tamanho de função** — teto duro no CI, alvo menor na regra do `AGENTS.md`.
3. **Nomes genéricos** — falhar em símbolo público cujo nome está na lista.
   Complementar com a checagem de grepabilidade: `rg -w "<nome>" | wc -l` acima
   de ~5 hits para um símbolo público significa nome ruim.
4. **Tipos** — `mypy --strict` no pacote de domínio, no mínimo. Sem anotação, o
   agente infere pelo uso e erra.

Essas quatro são atômicas, rodam em segundos e não dependem de infraestrutura.
São o primeiro conjunto a entrar em qualquer repositório novo.

## Onde cada checagem roda

| Momento | O que roda | Por quê |
|---|---|---|
| pre-commit | formatador, lint, tamanho de arquivo | feedback em segundos, sem custo de CI |
| CI (todo push) | fronteiras, tipos, testes, auditoria de dependência | é a barreira que o agente não contorna |
| CI (agendado) | carga, p95, dependência desatualizada | caro demais para todo commit |
| produção | latência, erro, contrato em runtime | as únicas que veem o sistema real |

Duas exigências para que o agente participe do ciclo: **comando único**
(`make check`, `pnpm test`) e **output parseável**. Se validar a mudança exige
dez passos manuais, o agente não valida — e passa a entregar código plausível
que quebra silenciosamente o que funcionava ontem.

## Regras de escrita

1. **Uma fitness function por decisão que restringe.** Se a decisão não restringe
   nada, não era arquitetural.
2. **Falha com contexto.** Mensagem que diz o valor encontrado, o esperado e o
   ADR de origem. `AssertionError: modulo dominio importa infra.postgres —
   proibido por ADR-0004`.
3. **Ligar quebrando.** Fitness function nova que já falha entra com o alvo no
   valor atual e um plano de aperto registrado no ADR. Regra que nasce vermelha
   e fica vermelha ensina o time e o agente a ignorar o vermelho.
4. **Sem exceção silenciosa.** Toda exclusão (`# noqa`, arquivo na allowlist)
   precisa de comentário com motivo e ADR. Allowlist sem motivo é a porta pela
   qual a arquitetura vaza.
5. **Testar a fitness function.** Introduzir a violação de propósito uma vez e
   confirmar que o CI fica vermelho. Checagem que nunca falhou pode estar
   quebrada — e a maior parte delas está.
