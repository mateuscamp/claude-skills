# Análise de trade-off

Ler nas etapas 5 a 7 do procedimento.

O ofício não é escolher a opção boa — é descobrir **em que moeda cada opção
cobra** e decidir qual fatura o projeto aguenta. Quando duas opções parecem
equivalentes, é porque as dimensões que as separam ainda não foram nomeadas.

## Sumário

- [O método em três passos](#o-método-em-três-passos)
- [Técnicas que evitam erro caro](#técnicas-que-evitam-erro-caro)
- [Granularidade: quebrar ou juntar serviço](#granularidade-quebrar-ou-juntar-serviço)
- [Dado: quebrar ou manter junto](#dado-quebrar-ou-manter-junto)
- [Comunicação, consistência, coordenação](#comunicação-consistência-coordenação)
- [Contratos](#contratos)
- [Reuso](#reuso)
- [As oito falácias](#as-oito-falácias-da-computação-distribuída)

## O método em três passos

**1. Achar as dimensões emaranhadas.** Que partes estão trançadas nessa decisão?
A pergunta operacional de acoplamento é a mais simples possível: *se alguém
mudar X, Y é forçado a mudar?* Se sim, X e Y estão acoplados e a dimensão entra
na lista. Em sistema distribuído, três dimensões aparecem em quase toda decisão
difícil: **comunicação** (síncrona/assíncrona), **consistência** (atômica/
eventual) e **coordenação** (orquestrada/coreografada). Elas se determinam
mutuamente — daí "emaranhadas".

**2. Modelar as combinações.** Montar a matriz das combinações plausíveis. As
inviáveis são descartadas com um motivo de uma linha — o motivo escrito vale
tanto quanto a análise das viáveis, porque impede a reabertura. A primeira
versão da matriz nunca é a boa; iterar é parte do método, não sinal de
despreparo.

**3. Avaliar.** Para cada combinação sobrevivente: o que ganha, o que perde, e
em qual driver isso bate. Fixar a dimensão decidida e repetir a análise sobre a
decisão seguinte que ela força. Quando não sobrar decisão emaranhada, o que
restou é design — e design não precisa dessa cerimônia.

## Técnicas que evitam erro caro

**MECE.** As opções listadas devem ser mutuamente exclusivas e coletivamente
exaustivas. Comparar "fila de mensagem" com "Kafka" não é MECE — um é categoria,
outro é implementação. A comparação enviesada por categorias sobrepostas é a
forma mais comum de análise que parece rigorosa e não é.

**A armadilha do fora-de-contexto.** Toda conclusão de blog, palestra ou livro
nasce dentro de um contexto que raramente é dito. Biblioteca compartilhada versus
serviço compartilhado é o exemplo clássico: a resposta certa depende da taxa de
mudança do código compartilhado e do número de consumidores, e qualquer
recomendação categórica sobre isso já perdeu o contexto no caminho. Antes de
importar uma conclusão, perguntar: *quais eram os drivers de quem concluiu isso?*

**Modelar no domínio real.** Números do usuário: volume de requisição, tamanho
da base, tamanho do time, orçamento, janela de manutenção. Trade-off abstrato
produz resposta abstrata.

**Qualitativo quando não dá para medir.** Nem toda dimensão tem número — e é
melhor uma escala honesta ("alto/médio/baixo, por este motivo") do que um número
inventado com aparência de rigor.

**Bottom line acima da evidência.** Entregar a recomendação primeiro, evidência
depois. Montanha de evidência sem conclusão transfere para o usuário o trabalho
que a análise deveria ter feito.

**Sem evangelismo, sem óleo de cobra.** Se uma fonte só apresenta vantagens, ela
não é fonte — é material de marketing. A pergunta que filtra: *qual é a
desvantagem?* Quem não responde não sabe do que está falando.

## Granularidade: quebrar ou juntar serviço

Duas forças opostas. A decisão é sempre o saldo entre elas, nunca a aplicação de
uma só.

**Desintegradores** — justificam quebrar:

| Força | Pergunta que ela responde |
|---|---|
| Escopo e função | O serviço faz mais de uma coisa coesa? |
| Volatilidade do código | Uma parte muda toda semana e o resto uma vez por ano? |
| Escalabilidade e vazão | Partes com necessidade de escala muito diferente? |
| Tolerância a falha | Uma parte que morre não pode derrubar o resto? |
| Segurança | Uma parte manipula dado sensível que o resto não deveria alcançar? |
| Extensibilidade | Vão entrar variantes novas continuamente naquele ponto? |

**Integradores** — justificam manter junto:

| Força | Pergunta que ela responde |
|---|---|
| Transação de banco | A operação precisa ser atômica de verdade? |
| Workflow e coreografia | Quebrar cria uma sequência longa de saltos de rede? |
| Código compartilhado | A separação exige biblioteca compartilhada volátil? |
| Relacionamento de dados | Quebrar separa tabelas que só fazem sentido juntas? |

Se nenhum desintegrador tem evidência, a resposta é não quebrar. Se um
desintegrador é forte e um integrador é forte, o conflito é a decisão — e é ele
que vai para o ADR, não a conclusão limpa.

## Dado: quebrar ou manter junto

**Desintegradores de dado:** controle de mudança (quantos serviços quebram
quando uma tabela muda) · gestão de conexão (o banco aguenta o pool de N
serviços) · escalabilidade do banco · tolerância a falha (quantos serviços caem
quando o banco cai) · quantum arquitetural (o banco único está forçando um
quantum indesejado) · otimização por tipo de banco.

**Integradores de dado:** relacionamento entre dados (junções, integridade
referencial, chave estrangeira) · transação de banco (atomicidade real).

O caminho de decomposição é incremental e cada passo é reversível se feito
nessa ordem: analisar e criar domínios de dado → atribuir tabelas aos domínios →
separar conexões por domínio → mover schemas para servidores separados →
cortar para bancos independentes. Parar em qualquer degrau é uma decisão
legítima, e o degrau em que se parou merece um ADR.

**Posse do dado.** Regra de partida: quem escreve, possui. Escrita única é o
caso fácil. Escrita comum (todo mundo escreve) pede um serviço dedicado de posse.
Escrita conjunta (dois ou três donos) resolve-se por divisão de tabela, domínio
de dado compartilhado ou delegação a um dos donos — cada uma com custo distinto
em acoplamento e latência.

## Comunicação, consistência, coordenação

**Orquestração** — um mediador conhece o fluxo. Ganha: estado do workflow em um
lugar só, tratamento de erro e compensação centralizados, fluxo legível.
Perde: o orquestrador vira ponto de acoplamento e gargalo, e o sistema fica
responsivo ao ritmo do mais lento.

**Coreografia** — cada serviço reage a evento, ninguém manda. Ganha: baixo
acoplamento, escala melhor, sem ponto central. Perde: estado do workflow fica
espalhado, erro e compensação viram trabalho manual em cada participante, e
descobrir "onde parou" exige rastreamento distribuído.

Combinada com comunicação (síncrona/assíncrona) e consistência (atômica/
eventual), essas três dimensões geram oito padrões de saga. Os nomes desses
padrões são mnemônicos e não importam para a decisão. O que importa é: **quanto
mais atomicidade e mais orquestração, mais acoplamento e menos escala; quanto
mais eventual e mais coreografado, mais escala e mais complexidade de erro.** Não
existe combinação sem essa fatura.

Padrões de consistência eventual, do mais simples ao mais acoplado:
sincronização em background (simples, mas o dono do dado fica ambíguo) ·
requisição orquestrada (fluxo claro, latência somada) · baseada em evento
(desacoplada, exige entrega garantida e idempotência em todo consumidor).

## Contratos

**Estrito** (schema versionado, contrato gerado, tipos fechados): garante
correção na fronteira, quebra cedo e alto, exige versionamento e coordenação de
deploy. Bom quando o consumidor é externo ou a fronteira é crítica.

**Frouxo** (JSON aberto, campos opcionais): tolera evolução independente, mas
transfere a validação para o runtime e permite quebra silenciosa. Exige teste de
contrato do lado do consumidor para não virar aposta.

**Stamp coupling** — passar a estrutura inteira quando só três campos são
usados. Custa banda e, pior, acopla o consumidor a mudanças de campos que ele
nem lê. Usado de propósito, porém, é uma forma barata de carregar estado de
workflow entre participantes.

## Reuso

| Padrão | Ganha | Perde |
|---|---|---|
| Replicação de código | independência total | correção precisa ser feita N vezes |
| Biblioteca compartilhada | reuso com deploy independente | versionamento vira governança; mudança volátil é dolorosa |
| Serviço compartilhado | mudança em um lugar, efeito imediato | acoplamento em runtime, risco de mudança, latência |
| Sidecar / service mesh | infraestrutura transversal sem tocar no domínio | mais uma camada operacional |

Regra de corte: código compartilhado **volátil** empurra para serviço; código
compartilhado **estável** empurra para biblioteca. Reuso não é virtude — é
acoplamento comprado em troca de consistência. Se o driver ★ é desacoplamento, o
reuso perde.

## As oito falácias da computação distribuída

Checklist obrigatório antes de recomendar qualquer topologia distribuída. Cada
uma já derrubou sistema em produção:

1. A rede é confiável — não é; toda chamada precisa de timeout e política de retry.
2. A latência é zero — chamada local e chamada remota diferem em ordens de grandeza.
3. A banda é infinita — stamp coupling em volume vira conta de nuvem.
4. A rede é segura — a superfície de ataque cresce com cada salto.
5. A topologia não muda — muda, e sem avisar a aplicação.
6. Existe um administrador só — quanto mais serviços, mais coordenação humana.
7. Transporte não custa nada — serialização, gateway e egresso têm preço.
8. A rede é homogênea — pilhas diferentes se comportam diferente sob estresse.

Somadas: sistema distribuído troca complexidade de código por complexidade
operacional. A troca compensa quando existe um driver de modularidade com
evidência. Sem ele, é a pior compra do catálogo.
