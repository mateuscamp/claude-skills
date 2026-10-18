---
name: revisao-de-livro
description: Segunda camada de revisão de ficção. Consome as revisões de capítulo já prontas de um livro inteiro e diagnostica o que só existe ENTRE capítulos — promessa feita e nunca paga, regra interna que muda de valor no meio do caminho, personagem que entra e some, refrão que vira hábito, desequilíbrio de peso entre partes, erro de pesquisa que se repete, e a curva de adesão do leitor do começo ao fim. Não relê a prosa: lê as revisões. Nunca reescreve o texto do autor. Use quando existirem revisões de capítulo de um livro inteiro e o autor pedir "e o conjunto?", "o que o livro tem", "olha o arco todo", "revisa o livro inteiro", "monta o dossiê", "o que fica entre os capítulos" ou "por onde eu começo a mexer".
---

# Revisão de livro

Camada de arquitetura. Roda **depois** de `revisao-de-capitulo` ter passado por
todos os capítulos, e consome a saída dela — não o romance.

A separação existe por um motivo específico: a regra 10 da camada de capítulo
proíbe afirmar qualquer coisa sobre coerência com capítulos fora de vista. Essa
proibição é o que mantém a revisão de capítulo honesta. Aqui, com todas as
revisões à mão, a proibição cai — e cai só aqui.

## Quando usar

- Existem revisões de capítulo de um livro inteiro (ou de uma parte inteira).
- O autor quer saber por onde começar a mexer, não o que há em um capítulo.
- Um mesmo problema pareceu aparecer em vários capítulos e ninguém contou.

## Quando NÃO usar

- Faltam revisões. Livro parcialmente revisado dá diagnóstico parcial que se
  lê como completo. Se faltar capítulo, dizer quais e revisar antes.
- O autor quer opinião sobre um capítulo. Isso é a outra camada.
- O livro ainda está sendo escrito. Arquitetura de obra inacabada é projeto,
  não diagnóstico.

## Entrada

Um conjunto de arquivos produzidos por `revisao-de-capitulo`, cada um com
Veredito, Leitura literal, Âncoras externas, Função no arco, O que trava,
Decisões, Próximo passo e Leitura subjetiva.

## Procedimento (sempre nesta ordem)

1. **Inventário de promessas.** Varrer a coluna **Prepara** de todas as revisões.
   Cada célula é uma promessa feita ao leitor. Registrar capítulo de origem.

2. **Pagamento.** Para cada promessa, procurar nas colunas **Revela** e **Muda**
   dos capítulos *posteriores* qual paga. Três resultados possíveis:
   `PAGA (cap. n)` · `EM ABERTO` · `PAGA ANTES` (o pagamento precede a promessa —
   o leitor recebe a resposta antes de ter a pergunta).
   Registrar também o inverso: revelação que chega sem nenhuma promessa anterior
   é `CHEGA DE GRAÇA`.

3. **Regras internas.** Listar toda regra que o mundo do livro estabelece: o que
   é possível, o que custa, quem sabe o quê, o que não pode ser dito. Anotar onde
   cada uma é **estabelecida** e onde é **aplicada**. Regra aplicada com valor
   diferente do estabelecido é violação — reportar com os dois pontos, sem
   arbitrar qual dos dois é o certo. Essa escolha é do autor.

4. **Curva de veredito.** Distribuir `FICA` / `VOLTA PRA BANCADA` por parte e por
   posição no livro. Concentração não é média: três VOLTA seguidos no mesmo
   ponto valem mais que dez espalhados.

5. **Peso e ritmo.** Palavras por parte e por capítulo; desvio da média. Capítulo
   com o triplo ou um terço da média é evento estrutural — nomear o que ele faz
   que justifique o tamanho, ou registrar que nada justifica.

6. **Elenco.** Para cada personagem nomeado: capítulo de entrada, capítulos em
   cena, capítulo de saída. Quem entra e para de aparecer sem sair de cena é fio
   solto — com o número do capítulo onde o fio cai.

7. **Refrão.** Se houver forma recorrente (capítulo-refrão, título repetido,
   estrutura que volta), medir o que cada ocorrência faz de novo. Ocorrência que
   não revela, não muda e não prepara é onde o refrão passou de estrutura a
   hábito. Contar quantas são, e em que trecho do livro se concentram.

8. **Âncoras agregadas.** Juntar todas as âncoras que falharam nas revisões e
   agrupar por tipo (data, lugar, obra citada, dado técnico, marca, ciência).
   Um erro é deslize; o mesmo tipo três vezes é método de pesquisa, e é isso que
   se reporta.

9. **Curva subjetiva.** Ler as seções de leitura subjetiva **em ordem de
   capítulo**, como série temporal: onde o leitor entra, onde desliga, onde
   volta, onde fica. É a única leitura do dossiê que enxerga o livro como
   experiência e não como planta. Fica em seção própria, com a mesma parede da
   camada de capítulo.

10. **Veredito de livro e alavancagem.** Uma linha de veredito. Depois, no
    máximo **três** consertos, ordenados por quantos capítulos cada um destrava
    por unidade de trabalho. Um conserto que resolve nove capítulos vem antes de
    um que resolve um, mesmo que o segundo seja mais grave isoladamente.

## Contrato de saída

```markdown
# <Livro> — dossiê de revisão · <data>

**Veredito de livro** — <uma linha>

## Alavancagem
| # | Conserto | Capítulos que destrava | Custo |
|---|---|---|---|
<no máximo três linhas>

## Promessas
| Promessa | Feita em | Situação | Paga em |
|---|---|---|---|

## Regras internas
| Regra | Estabelecida em | Aplicada em | Confere? |
|---|---|---|---|

## Curva de veredito
| Parte | FICA | VOLTA | Concentração |
|---|---|---|---|

## Peso e ritmo
| Parte | Palavras | % | Capítulos | Média | Fora de curva |
|---|---|---|---|---|---|

## Elenco
| Personagem | Entra | Em cena | Sai | Fio solto? |
|---|---|---|---|---|

## O refrão
<presente só quando houver forma recorrente>

## Âncoras agregadas
| Tipo | Ocorrências | Capítulos | Padrão |
|---|---|---|---|

## O que trava o livro
- **<nome do problema>** — <mecanismo, com os capítulos onde aparece>

---

## Curva subjetiva
> Resposta de leitor ao longo do livro. Nada abaixo é constatação sobre a
> página, nada abaixo é verificável, e nada abaixo justifica qualquer decisão
> das tabelas acima.

- <onde entra, onde desliga, onde volta, o que fica>
```

## Regras invioláveis

1. **Não relê a prosa.** A entrada são as revisões. Se uma pergunta exigir o
   texto, a linha diz "requer releitura do cap. n" e para ali. Abrir o romance
   para conferir uma impressão é reescrever a camada de capítulo por cima.
2. **Não reescrever.** Vale integralmente o que vale na outra camada: nenhuma
   prosa proposta, nenhum exemplo de como ficaria.
3. **Promessa em aberto não é defeito.** Livro pode deixar aberto de propósito, e
   distinguir isso é decisão do autor. A saída lista; não condena.
4. **Alavancagem, não lista.** No máximo três consertos, cada um com o número de
   capítulos que destrava. Uma lista de quinze problemas é a mesma coisa que
   nenhum — o autor não sabe por onde pegar.
5. **Divergência entre revisões é achado.** Se duas revisões descrevem o mesmo
   fato de formas incompatíveis, isso vai para a saída como divergência, com os
   dois capítulos. Não harmonizar, não escolher uma, não limpar.
6. **A parede subjetiva continua de pé.** Curva subjetiva em seção própria, com
   o aviso, e nenhuma linha das tabelas pode citá-la como razão.
7. **Nenhum veredito de qualidade.** O nível de livro descreve arquitetura:
   o que sustenta o quê, o que fica sem apoio. "Bom livro" e "livro fraco" não
   são saídas deste procedimento.
8. **Léxico do autor.** Nomes, termos e vocabulário da obra ficam como estão.
9. **Cobertura declarada.** A saída abre dizendo quantos capítulos de quantos
   foram revisados. Dossiê sobre revisão parcial diz isso na primeira linha.
