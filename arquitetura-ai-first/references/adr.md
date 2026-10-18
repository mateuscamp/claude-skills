# ADR — Architecture Decision Record

Ler na etapa 8 do procedimento. Template pronto em `assets/ADR-template.md`.

Um ADR é um documento curto que registra **uma** decisão arquitetural, o
contexto que a forçou e o que ela custa. Não é documentação de sistema, não é
manual e não é ata de reunião. É o registro do porquê — o único artefato que
sobrevive à saída do autor, ao esquecimento e à janela de contexto do agente.

## Estrutura

Cinco seções obrigatórias, mais duas que valem sempre a pena:

**Título** — numerado sequencialmente e descritivo o suficiente para dispensar
leitura. `0007 — Manter escrita de agendamento no monólito`. Título vago
("0007 — Sobre o banco") transforma o diretório de ADRs em arquivo morto.

**Status** — `Proposto` · `Aceito` · `Substituído por NNNN`. Proposto é o estado
enquanto a decisão depende de aprovação, custo ou prazo que ainda não existe. O
próprio ciclo Proposto→Aceito é o que força a conversa de trade-off a acontecer
com alguém e não só dentro da cabeça de quem escreveu. ADR aceito **nunca** é
editado nem apagado: cria-se um novo que o substitui, e o antigo passa a
`Substituído por NNNN`. O histórico do erro é metade do valor do arquivo.

**Contexto** — a situação em duas ou três frases, incluindo as restrições reais
(prazo, time, orçamento, contrato, lei). Escrito de modo que alguém sem o
contexto de hoje entenda por que a pergunta existia.

**Decisão** — a decisão em voz ativa, com a justificativa. Escrever o **porquê**,
não só o quê. O quê já está no código; o porquê não está em lugar nenhum.

**Consequências** — o que se ganha e **o que se perde**. Seção de consequências
sem nenhum item negativo significa que a análise não terminou. É aqui que entra
também a discordância registrada quando o usuário decidiu contra a recomendação.

**Governança** (ou Compliance) — como essa decisão será verificada, e por qual
mecanismo. É a costura com a etapa 9: o nome do teste, do lint, do contrato de
import, da checagem manual e sua cadência. ADR com governança vazia é intenção
escrita em papel timbrado.

**Notas** — autor, data de criação, data de aprovação, datas de alteração.
Metadado que o Git também guarda, mas que sobrevive a migração de repositório.

Adicionar **Alternativas** sempre que mais de um caminho era plausível: cada
alternativa com o motivo de uma linha da rejeição. É a seção que impede a
reabertura da discussão — e a que o agente lê quando pergunta "por que não foi
feito assim?".

## Onde guardar

`docs/adr/NNNN-slug-em-kebab-case.md`, versionado junto do código. Vantagens de
morar no repositório: entra no mesmo pull request da mudança que ele justifica,
o histórico do arquivo é o histórico da decisão, e o agente alcança com um grep.

Em estratégia de repositório espelhado, o ADR vive no repositório de origem e
viaja no espelho como qualquer outro arquivo — nunca em wiki externa, drive ou
ferramenta que o agente não lê e o clone não carrega.

Manter `docs/adr/README.md` com o índice: número, título, status, uma linha.
É o que o agente lê quando precisa da visão geral sem carregar trinta arquivos.

## O que merece um ADR

Se a decisão afeta **estrutura**, **característica não-funcional**,
**dependência**, **interface entre partes** ou **posse do dado**, é
arquiteturalmente significativa e merece registro. Se não afeta nenhuma das
cinco, é design: implementar e seguir, sem cerimônia.

Casos que sempre merecem ADR e costumam ser esquecidos:

- A decisão de **não** fazer algo ("não vamos separar o serviço de notificação
  agora"). Sem esse registro, a mesma discussão volta em três meses sem os fatos
  que a decidiram.
- Padrões e convenções obrigatórios do projeto — o ADR explica o porquê, e o
  `AGENTS.md` carrega a regra operacional derivada dele.
- Trocas forçadas por restrição externa (limite de plano, lei, contrato). É a
  informação que mais se perde e a que mais confunde quem chega depois.

## Antipadrões

**Cobrir as próprias costas.** Não decidir por medo de errar, ou decidir sem
registrar para não ficar marcado. O antídoto é o par ADR + fitness function: a
decisão está escrita, o critério de falha está escrito, e a reversão é uma
decisão nova, não uma vergonha.

**Groundhog Day.** A mesma decisão reaberta periodicamente porque ninguém
lembra o porquê. É o antipadrão que o ADR existe para matar — e por isso a seção
Contexto importa mais que a seção Decisão.

**Arquitetura por e-mail (ou por chat).** A decisão existe, mas mora em uma
conversa que ninguém encontra. Em projeto com agente isso é fatal: o agente não
tem acesso ao chat de ontem, só ao repositório. Se não está no repositório, não
existe.

**ADR-romance.** Documento de seis páginas que ninguém lê e que o agente pagina.
Uma decisão por arquivo, uma página no máximo. Se não cabe em uma página, são
duas decisões disfarçadas de uma.

## Relação com o AGENTS.md

São artefatos diferentes com públicos diferentes, e confundi-los quebra os dois:

| | ADR | AGENTS.md |
|---|---|---|
| Pergunta que responde | por quê | o quê fazer agora |
| Público | humano futuro, e o agente quando investiga | agente, em toda iteração |
| Tamanho | uma página por decisão | poucas dezenas de linhas no total |
| Frequência de leitura | sob demanda | a cada query |
| Muda quando | a decisão muda | a regra operacional muda |

Toda decisão que restringe o código gera **duas** escritas: o ADR (com o
raciocínio inteiro) e a linha imperativa no `AGENTS.md` (sem raciocínio nenhum).
A linha no `AGENTS.md` pode citar o ADR por número — é barato e dá ao agente o
caminho para o contexto quando ele precisar.
