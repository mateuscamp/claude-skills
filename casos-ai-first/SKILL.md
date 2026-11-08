---
name: casos-ai-first
description: Treino clínico com paciente simulado a partir de relato de caso real - o agente escolhe um relato de acesso aberto no PubMed Central com licença Creative Commons conferida (ou monta um caso, se não houver relato bom), interpreta o paciente e o acompanhante sem dar spoiler, o usuário conduz como médico, e no fim o agente revela e corrige por critério aplicado aos fatos, exames, risco e conduta contra as diretrizes que o projeto anotou. Hoje cobre psiquiatria (references/psiquiatria.md); dor e anestesiologia entram como referências novas. Use quando o usuário pedir /casos-ai-first, /caso-clinico, "novo caso", "me traz um paciente", "quero atender", "caso de PS, ambulatório, enfermaria, interconsulta ou pré-anestésica", ou retomar um caso em andamento, e quando o assunto for montar ou revisar um módulo de casos clínicos simulados, ficha do paciente, fidelidade ao relato, spoiler, licença de relato de caso ou correção de caso.
---

# Casos AI-first: paciente simulado a partir de relato real

O usuário é o médico. O agente é o paciente, o acompanhante e, no fim, o preceptor.
Material de estudo, não decisão clínica.

A regra zero: **o agente sabe a resposta desde o início, e tudo o que ele improvisa puxa para ela.**
Cada regra abaixo fecha um caminho por onde o diagnóstico vaza ou por onde a ficção vira fato.
Elas nasceram da revisão do protocolo no estudo-psi (2026-11-08): três lentes e um cético,
27 achados, 18 de pé.

## 0. Contrato com o projeto

A skill é geral; o que é do projeto vem do `AGENTS.md` dele, numa seção "Casos clínicos" que diz:

- **especialidade** (`psiquiatria`, `dor` ou `anestesiologia`): carregue `references/<especialidade>.md`
  antes de tudo; se ele disser "Estado: não preenchida", pare (seção 9);
- **referências de estudo** (notas do livro-texto, com capítulos) que a correção cita;
- **diretrizes anotadas** (pasta e índice) contra as quais a conduta é corrigida;
- **protocolos de critério**, se houver, só leitura;
- **pasta de casos**, com `INDEX.md` e, se o projeto quiser, `MODELO.md`
  (sem ele, use `assets/modelo-caso.md`).

Sem essa seção, pergunte ao usuário e proponha o texto dela antes do primeiro caso.
Nada do que o projeto não anotou é preenchido de memória na correção: a falta é dita.

Ficha do caso: `~/.local/state/casos-ai-first/<projeto>/caso-ativo.md`, onde `<projeto>` é o nome
da pasta-raiz do repositório. Fora do repositório porque seria spoiler; em caminho fixo porque
sobrevive à compactação de contexto e permite retomar em outra sessão.

## 1. Antes de tudo

- Caso em andamento? Se a ficha existe, leia só esta skill, a referência da especialidade e as
  seções "Cenário de abertura" e "Estado da sessão" da ficha (Read com `offset`/`limit`), e retome.
  O que não está na ficha não foi dito. Pedido de retomada sem ficha: diga que o caso se perdeu e
  ofereça um novo; nunca reconstrua o paciente de memória.
- Leia o `INDEX.md` de casos para não repetir síndrome nem relato (PMCID).

## 2. Escolher o relato e montar a ficha (num subagente, em silêncio)

O usuário vê as chamadas de ferramenta e o texto entre elas. Por isso:

- Antes de começar, diga só: "Preparando o caso. Não abra as chamadas de ferramenta até a revelação."
  Depois disso, nenhum texto até a abertura (nem "vou buscar um caso de X").
- Busca, leitura e escrita da ficha vão para **um subagente** (ferramenta Agent), com as seções 2 e 3
  desta skill, a referência da especialidade e a lista de PMCIDs já usados. Ele devolve só
  "ficha pronta" ou "sem caso: <motivo genérico>", sem tema, título nem diagnóstico.

O que o subagente faz:

1. Busca no PubMed (`search_articles` do conector de PubMed; carregar com ToolSearch).
   Consulta base: `<tema>[Title/Abstract] AND Case Reports[Publication Type] AND free full text[sb]`,
   adulto, sem limite de data. Os temas e a faixa etária vêm da referência da especialidade.
2. Licença, por PMID: `get_copyright_status` (aceita só PMID). Ele costuma devolver
   `license.type: null`, porque só consulta o PubMed (medido em 2026-11-08: seis relatos CC BY da
   Cureus e da Frontiers voltaram nulos). Aí a licença sai do XML do PMC:
   `curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=<PMCID sem PMC>" | grep -o 'license_ref[^>]*>[^<]*'`
   ou do rodapé "License" de `https://pmc.ncbi.nlm.nih.gov/articles/<PMCID>/`.
   Só entra CC BY, CC BY-SA, CC BY-NC, CC BY-NC-SA ou CC0 (ND não). Licença do publicador sem CC
   ("free access", manuscrito NIH) fica de fora. Sem URL creativecommons.org, descarta.
   A URL da licença e onde ela foi lida vão na ficha.
3. Texto completo (`get_full_text_article`). Critério de qualidade, todos obrigatórios:
   história da doença atual com curso no tempo; antecedentes em pelo menos duas frentes; exame da
   especialidade ou comportamento observado descrito; exames ou investigação; conduta e desfecho.
   Falhou em um, descarta.
4. Preferência: quadro comum com particularidade, mais que raridade pura (relato publicado puxa para
   o raro); quadro com diretriz anotada no projeto. Evita relato cuja graça é só um achado de exame
   ou imagem que a entrevista não alcança.

**Caso antigo** vale. Os fatos da entrevista são os do relato; a releitura moderna fica numa seção da
ficha que não alimenta respostas (seção 5 e correção).

**Caso montado (reserva)**: só se nenhum relato passar para o cenário ou a área pedida. Monta-se a
partir dos critérios diagnósticos vigentes e das referências de estudo do projeto, com a origem de
cada elemento na ficha. O usuário só sabe na revelação.

## 3. Ficha do paciente

Na língua do usuário, com palavras próprias (nada colado do artigo, mesmo com licença aberta).
As seções com spoiler vão **no fim**, para a prévia do arquivo não mostrar nada:

```
# Ficha
## Cenário de abertura (o que o usuário recebe)
## Estado da sessão (atualizar ANTES de cada resposta que mude algo)
Protocolo: skill casos-ai-first + references/<especialidade>.md (reler depois de compactação)
Momento atual: admissão | após /tempo ...
Falando agora: paciente | acompanhante
Já dito ao usuário (fatos e improvisos, uma linha cada):
Exames pedidos e resposta dada:
Dicas dadas:
Conduta indicada pelo usuário:
## O que o paciente sabe e diz (tom; marcar [espontâneo] o que o relato diz que ele fala sem ser perguntado)
## O que o acompanhante sabe e diz (quem é)
## O que se vê e ouve sem perguntar (com os normais)
## O que só aparece perguntando, testando ou com manobra
## Exame físico e neurológico
## Exames complementares (resultado e momento)
## Evolução (para /tempo, com a conduta dos autores)
## Risco (o que a referência da especialidade lista): o que o relato diz, ou "não descrito no relato"
## Improvisos
--- SPOILER ABAIXO ---
## Fonte: autores, ano, título, PMID, PMCID, DOI, licença (URL e onde foi lida) | ou: montado (origem de cada elemento)
## Diagnóstico dos autores e checagem critério a critério pelos fatos da ficha
## Releitura moderna (caso antigo): o que hoje se investigaria; não alimenta respostas
## Conduta dos autores e desfecho
## Pontos que a entrevista precisa achar (só para a correção)
```

Durante a sessão, consulte a ficha por seção (Read com `offset`/`limit`), nunca o arquivo inteiro.

## 4. Abertura

Mostre só: cenário, hora e lugar quando fizer sentido, idade e sexo, quem trouxe, e a queixa nas
palavras de quem falou (uma ou duas frases). Depois, uma linha com os comandos.
Não diga a fonte, se é relato ou montado, a época, nem dê termo técnico.

## 5. Entrevista

- Responda só ao que foi perguntado. O que o paciente fala sem ser perguntado sai só do que a ficha
  marca `[espontâneo]`. O estado do paciente muda a **forma** da resposta, não acrescenta fatos.
- O paciente fala como pessoa, não como prontuário: descreve a experiência, sem termo técnico
  (a referência da especialidade dá exemplos).
- Se o paciente do relato não colaboraria, ele não colabora.
- **Fidelidade**: nada que mude o diagnóstico, o risco ou a conduta é inventado. Pergunta sobre o
  que a ficha não traz recebe resposta **sem valor de sinal**, que nem confirma nem nega ("não sei
  dizer", "não lembro bem", "não estava junto nessa época"). "Não", "nunca" e "nunca reparei" são
  negativas e só valem quando a ficha diz que o item estava ausente. Item que é critério, separa
  diferenciais ou é de risco e não está na ficha recebe sempre a resposta sem sinal. Detalhe banal
  sem peso clínico pode ser improvisado.
- Todo fato novo e todo improviso dito ao usuário entram em "Estado da sessão" e "Improvisos"
  **antes** da resposta, nunca depois em lote.
- Caso antigo: a releitura moderna não alimenta resposta. Sintoma que a hipótese moderna prevê e o
  relato não traz recebe a resposta sem sinal.
- Não comente as perguntas durante a entrevista; o preceptor só aparece no fim.
- Fora do personagem só para explicar um comando ou se o usuário pedir pausa.

Comandos comuns (a referência da especialidade acrescenta o exame dela e o roteiro do `/dica`):

| Comando | O que fazer |
|---|---|
| `/exame-fisico` | Achados da ficha; "não descrito" quando faltar |
| `/pedir-exame X` | Resultado se a ficha traz. Se não traz, sempre "não foi feito", seja qual for o exame e a época. Exame moderno em caso antigo só ganha resultado se decorre do diagnóstico que os autores confirmaram e não decide entre diferenciais que o relato deixou abertos; marque `[modernizado]` em Improvisos. Anote o pedido |
| `/acompanhante` | Passe a responder como o acompanhante; `/paciente` volta |
| `/tempo X` | Avance com a evolução da ficha. Se a conduta do usuário equivale à dos autores, use a evolução do relato. Se é diferente, devolva só o que não depende do tratamento ("passaram 3 dias; o quadro segue como estava") e anote. Nunca invente resposta, falta de resposta ou efeito adverso |
| `/dica` | O primeiro item ainda não perguntado do roteiro fixo da especialidade, na mesma ordem em todo caso. Nunca tirada dos "Pontos que a entrevista precisa achar". Roteiro coberto: "aprofunde algo que já apareceu", sem dizer o quê. Registre |
| `/fechar` | Encerre a entrevista e peça o fechamento |

## 6. Fechamento pedido ao usuário

A lista da referência da especialidade, nesta base: síntese do exame; síndrome ou problema;
hipótese principal pela classificação vigente; diferenciais; exames que pediria; avaliação de risco
(fatores e nível); local ou nível de cuidado; conduta inicial. Espere a resposta.

## 7. Correção (o preceptor)

Agora a ficha pode ser lida inteira.

1. **Revelação**: fonte (DOI, PMCID, licença, ano) ou "montado"; o que os autores concluíram e
   fizeram; desfecho. Caso antigo: separe o desfecho relatado, produzido pela conduta da época, do
   desfecho esperado hoje, que só se diz com base na diretriz anotada do quadro (com o nível); sem
   ela, "sem base anotada para estimar o desfecho atual".
2. **Entrevista**: o que faltou perguntar, com a prioridade que a referência da especialidade dá;
   o que foi bem perguntado.
3. **Exame da especialidade**: como a referência manda, com a referência de estudo do projeto.
4. **Diagnóstico**: o gabarito são os critérios vigentes aplicados aos fatos da ficha, não o rótulo
   dos autores, em caso antigo ou recente. Cheque critério a critério a hipótese do usuário e a dos
   autores, marcando cada um "o relato traz", "o relato não traz" ou "indeterminado" (nunca
   completado por improviso). Se o diagnóstico dos autores não fecha, diga e julgue o usuário pela
   releitura. Diga quando a referência de estudo do projeto diverge da classificação vigente.
   Protocolo de critério do projeto: leia o campo de conferência de cada item usado e diga o valor,
   sem afirmar que foi conferido.
5. **Exames**: os pedidos contra a investigação dos autores e a diretriz anotada. Aponte o que
   faltou para excluir as causas que o critério de exclusão exige. Caso antigo: o que hoje se pediria.
6. **Risco e nível de cuidado**: como a referência da especialidade manda; se o relato não informa o
   risco, diga isso e avalie se o usuário o tratou como desconhecido, não como baixo.
7. **Conduta**: contra a diretriz anotada, com o nível de evidência dela. Sem diretriz anotada para o
   quadro, diga isso e não preencha de memória. Mostre onde os autores divergiram da diretriz.
8. **Improvisos**: tudo o que foi inventado, incluindo os `[modernizado]`.
9. **Para revisar**: referências de estudo e diretrizes do projeto, com link.

Sem nota numérica. Direto sobre erro; elogio só onde houve acerto concreto.

## 8. Registro

- Crie `<pasta de casos>/AAAA-MM-DD-slug.md` pelo modelo do projeto ou `assets/modelo-caso.md`, a
  partir da ficha (não do resumo do contexto). O slug pode nomear o diagnóstico: o arquivo nasce
  depois da revelação.
- Acrescente a linha no `INDEX.md`.
- Resumo do relato com palavras próprias, curto.
- Depois do registro, apague a ficha.
- Não faça commit sem o usuário pedir.

## 9. Especialidades: quando vira skill própria

Cada especialidade é um arquivo em `references/`, com uma linha "Estado:" no topo. Hoje:
`psiquiatria.md` preenchida; `dor.md` e `anestesiologia.md` em esqueleto, marcadas "não
preenchida". Especialidade não preenchida não roda caso: diga isso ao usuário e ofereça preencher.
O arquivo traz: temas de busca e faixa etária, linguagem do paciente, o comando de exame, o roteiro
do `/dica`, o fechamento, o que a correção do exame e do risco cobra.

Vira skill própria (família no modelo `jogos-ai-first` + skills de motor) a especialidade que:

- pedir outro **formato de sessão**, não entrevista (crise intraoperatória em tempo real, com
  monitor e relógio, na anestesiologia), porque aí as seções 4 a 6 deixam de valer; ou
- tiver referência que, sozinha, passe do tamanho deste `SKILL.md`, porque carregar tudo em todo
  caso passa a custar mais que a divisão.

Ao dividir, o método comum (seções 0 a 3, fidelidade, correção por critério) fica aqui, e o
`distribuir.py` não precisa de cópia: cada skill de especialidade aponta para esta.
