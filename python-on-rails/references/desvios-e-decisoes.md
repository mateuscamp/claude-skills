# Desvios e decisões do projeto

Ler quando o projeto precisa sair de um padrão ou tomar uma decisão que a skill deixa aberta.
Toda saída e toda escolha fecham em ADR (formato na arquitetura-ai-first), com o que se perde e
a condição que inverte a decisão. Desvio sem ADR é achado de auditoria.

## Desvios dos padrões

| Padrão | Desvio legítimo | O que se perde | O que o ADR registra |
|---|---|---|---|
| Layout `src/` | Framework com layout próprio (Django: `manage.py` na raiz, apps como pacotes) | Teste pode importar da pasta corrente em vez do pacote instalado | O `include` do basedpyright e o `testpaths` que substituem `src` e `tests` |
| Domínio puro | Script de cola, CLI de uma função, CRUD que é quase só o framework | Teste do domínio passa a precisar de banco, rede ou relógio real | Onde fica a regra de negócio que existir, e o gatilho para extrair o domínio (ex.: segunda regra não trivial) |
| pydantic na borda | msgspec (desempenho), attrs (sem dependência de validação) | Integração pronta com FastAPI e pydantic-settings | A biblioteca escolhida, que cumpre a mesma função de validar a borda |
| Regra do ruff ou do basedpyright | Regra que conflita com o framework (ex.: `RUF012` em `Meta` do Django) | A proteção daquela regra no trecho excluído | O `per-file-ignores` mais estreito possível, por arquivo e não global |
| Portão completo | Projeto legado adotando os trilhos | Os erros antigos continuam lá | A linha de base (`basedpyright --writebaseline`, `noqa` com `motivo: legado`) e o prazo para zerá-la |

Desvio é sempre o mais estreito possível: um arquivo e não o projeto, uma regra e não o grupo.

## Decisões que a skill não toma

### Hypothesis: onde compensa

O Hypothesis testa uma *propriedade* (algo que vale para toda entrada) gerando centenas de
entradas e reduzindo a falha ao menor exemplo. Compensa onde a propriedade é fácil de dizer e o
espaço de entradas é grande:

- **Ida e volta**: `carregar(salvar(x)) == x` para serialização, parser e codec.
- **Invariante**: "o desconto nunca deixa o total maior", "ordenar não muda o tamanho".
- **Oráculo**: a versão otimizada dá o mesmo resultado da versão simples.

Não compensa em código de cola, rota HTTP fina ou regra com três casos fixos (aí o exemplo
explícito lê melhor). Teste por propriedade também segue o TDD: escreva a propriedade, veja-a
falhar e só então implemente. Fixe a reprodutibilidade com o banco de exemplos do Hypothesis no
`.gitignore` e, no CI, `derandomize=True` ou `--hypothesis-seed`.

### Formato do log

| Projeto | Formato | Por quê |
|---|---|---|
| Serviço (API, worker, fila) | JSON, uma linha por evento | Agregador e agente filtram por campo |
| CLI para humano | Texto legível no terminal, JSON opcional por flag | Quem lê é gente |
| Biblioteca | Nenhum: só `getLogger(__name__)`, sem configurar handler | Quem configura é a aplicação que a usa |

Para JSON, `structlog` ou um `logging.Formatter` próprio. A escolha vai para o ADR, e o trilho
(`logging`, nunca `print`, fatos nomeados) vale igual.

### Aplicação ou biblioteca

| | Aplicação | Biblioteca |
|---|---|---|
| Versão do Python | Uma, fixada em `.python-version` | Faixa em `requires-python`; CI na menor e na maior |
| `pythonVersion` do basedpyright | A fixada | A **menor** suportada |
| `uv.lock` | Versionado, é o que roda | Versionado para o desenvolvimento; quem instala resolve as próprias versões |
| Dependências | Podem ser fixadas com folga pequena | Faixa larga, só o limite inferior real |
| `py.typed` | Opcional | Obrigatório: sem ele, quem usa não vê os tipos |

### Framework, banco, ORM

São decisões arquiteturais: drivers primeiro, pela arquitetura-ai-first. Escolhido o framework,
os trilhos ganham as regras de `fastapi.md` ou `django.md`.
