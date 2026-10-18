# Governança arquitetural

Método de decisão destilado de *Fundamentals of Software Architecture* (FSA) e
*Software Architecture: The Hard Parts* (HP). Os livros dão método; não dão requisito
de produto nenhum.

## Índice

1. As duas leis
2. Características arquiteturais
3. Fitness functions
4. ADR
5. Risco
6. Análise de trade-off
7. Acoplamento, connascência e quantum
8. Quando separar e quando juntar
9. Contratos
10. Antipadrões de decisão

---

## 1. As duas leis

**Primeira lei.** Tudo em arquitetura é trade-off. Corolário: se você acha que achou
uma escolha sem trade-off, você ainda não achou o trade-off.

**Segunda lei.** O porquê importa mais que o como. Um arquiteto consegue olhar um
sistema desconhecido e reconstruir o *como* pela estrutura. O *porquê* só existe se
alguém escreveu.

Consequência prática: nenhuma pergunta de arquitetura tem resposta pesquisável. "REST
ou mensageria", "microsserviço ou monólito", "Godot ou Defold" dependem do ambiente,
dos motores de negócio, da cultura, do orçamento, do prazo, da habilidade disponível.
Programadores conhecem as vantagens de tudo e os trade-offs de nada; o trabalho é
conhecer os dois.

## 2. Características arquiteturais

Uma característica arquitetural — os "-idades" — precisa de três coisas: influenciar
alguma parte estrutural do desenho, ser não-funcional, e ser crítica ou importante
para o sucesso.

Regras que valem a pena:

- **No máximo sete de fato determinantes.** Listas longas diluem a decisão e nenhuma
  arquitetura maximiza tudo.
- **Nunca busque a melhor arquitetura. Busque a menos ruim.** Uma arquitetura que
  parece ótima em tudo geralmente esconde as medições que não foram feitas.
- **Característica sem definição operacional não governa.** "Escalável" não é
  característica; "mantém mediana abaixo de 2 s com 100 jogadores simultâneos" é.
- Elas vêm de três fontes: requisito explícito, conhecimento implícito do domínio, e
  as palavras que o interessado usa sem perceber. "Não pode cair nunca" é
  disponibilidade; "eu precisava disso ontem" é tempo até o mercado; "tem que voar" é
  desempenho.

Traduza motor de negócio em característica antes de discutir tecnologia. A conversa
muda de qualidade quando "cinco noves" vira "cinco minutos e trinta e cinco segundos
de parada por ano".

## 3. Fitness functions

**Definição:** qualquer mecanismo que dê uma avaliação objetiva da integridade de uma
característica arquitetural, ou de uma combinação delas.

Não é um framework; é uma perspectiva sobre ferramentas que já existem — métrica,
monitor, teste, verificação de dependência, engenharia do caos, checagem manual com
protocolo.

O que importa na prática:

- **Atômica ou holística.** A atômica isola uma característica: ciclo entre módulos,
  direção de dependência. A holística exercita a combinação, que é onde os defeitos
  interessantes moram — a escalabilidade que só quebra sob o cache que a segurança
  exigiu.
- **Objetiva não quer dizer estática.** Um limiar pode depender de contexto declarado.
- **Manual é aceitável quando não dá para automatizar**, desde que tenha protocolo,
  responsável e frequência. Uma verificação que não roda não verifica nada.
- **Fixe o limiar antes de rodar o experimento que ele vai julgar.** Isso não está nos
  livros; é a correção óbvia de quem já viu limiar sendo ajustado depois do resultado.
- **Não exagere.** Fitness function demais vira cerimônia, e cerimônia é desobedecida.

Teste comum contra fitness function: "o desenvolvedor pode consertar isso sozinho, sem
consultar ninguém?" Se sim, é teste. Se não, é fitness function.

## 4. ADR

Um arquivo curto, uma decisão, uma a duas páginas. Estrutura básica: **Título, Status,
Contexto, Decisão, Consequências**, mais **Conformidade** e **Notas**. A extensão mais
útil é uma seção de **Opções consideradas**.

- **Título** numerado e específico. "42. Uso de mensageria assíncrona entre Pedido e
  Pagamento", não "Decisões de mensageria".
- **Status**: Proposta, Aceita, Substituída por NNNN. Uma proposta nunca é substituída;
  ela continua sendo editada até virar aceita. Quando uma decisão é substituída, marque
  **os dois lados**: a antiga aponta para quem a substituiu, a nova aponta para o que
  substituiu. É assim que o histórico do porquê sobrevive.
- **Contexto**: qual força exige decidir agora.
- **Decisão** em voz ativa: "Nós faremos...". Explique por quê, não como.
- **Consequências**: positivas e negativas. Uma ADR sem consequência negativa não foi
  pensada.
- **Conformidade**: como a decisão será conferida. Decida explicitamente entre
  verificação manual e fitness function automática; se automática, diga como ela seria
  escrita e o que precisa mudar no código para medi-la. **Esta é a seção que separa
  governança de intenção.**
- **Critério de revisão**: que evidência, data ou mudança de contexto obriga a rever.
- **Notas**: autor, aprovação, datas, o que substitui.

Guarde cada decisão em seu próprio arquivo. No repositório funciona bem quando o
público é o próprio time; wiki funciona melhor quando a decisão atravessa projetos.

## 5. Risco

Matriz de duas dimensões, cada uma de 1 a 3: **impacto** e **probabilidade**. A nota é
o produto, de 1 a 9. De 6 para cima exige mitigação com custo explícito antes de
prosseguir.

**Avalie o impacto primeiro.** Começar pela probabilidade contamina a estimativa de
impacto — é mais fácil convencer a si mesmo de que algo é improvável do que de que é
inofensivo.

O ritual completo tem três etapas: **identificação**, feita individualmente e às cegas;
**consenso**, comparando as identificações; **mitigação**, com custo. Num projeto solo
a etapa de consenso desaparece, e com ela some justamente a diversidade de ponto de
vista que dá valor ao ritual. Substituto barato: peça a identificação a dois agentes
diferentes, sem contexto um do outro, e compare com a sua.

Cada risco precisa de um **sinal de parada**: o que você veria que o tornaria realizado.

## 6. Análise de trade-off

### Qualitativa, quase sempre

Praticamente nenhuma comparação arquitetural real é quantitativa. Duas arquiteturas
sempre diferem o bastante para impedir aritmética honesta. Some notas ponderadas
apenas para organizar a discussão ou desempatar, nunca para decidir — e jamais fixe os
pesos depois de ler os resultados.

### Listas MECE

Compare coisas **mutuamente exclusivas** e **coletivamente exaustivas**. Comparar uma
fila de mensagens com um barramento corporativo é inválido: o segundo contém o
primeiro mais outras dez coisas. E se você avalia filas de alto desempenho sem incluir
uma opção óbvia da categoria, sua lista não cobre o espaço.

Numa decisão de produto, as duas opções que quase sempre faltam na lista são **não
fazer** e **usar o que já existe**.

### A armadilha do fora de contexto

Uma solução ganha na tabela genérica e perde no seu caso. Pesquise a comparação geral
e depois refaça a tabela com o contexto real; a decisão costuma virar. Equilibre o
conjunto certo de trade-offs, não todos os disponíveis.

### Dimensões entrelaçadas

Antes de comparar opções, ache o que muda junto. Escolha primeiro a dimensão
fundamental — síncrono ou assíncrono, determinístico ou não, local ou remoto — porque
ela restringe todas as outras. Depois itere sobre as decisões que a primeira forçou. O
que sobrar sem entrelaçamento é desenho, não arquitetura.

### Como apresentar

Resuma no essencial. Evidência esmagadora convence menos que uma linha de conclusão
com os dois ou três trade-offs que realmente pesaram. Evite evangelismo: quem defende
uma opção sem citar a desvantagem dela perde credibilidade na primeira surpresa.

## 7. Acoplamento, connascência e quantum

### Connascência

Dois trechos são connascentes quando mudar um obriga a mudar o outro. Vale como guia
de refatoração porque tem ordem de força.

**Estática**, da mais fraca para a mais forte: nome, tipo, significado, posição,
algoritmo. **Dinâmica**, mais difícil de detectar: execução, tempo, valor, identidade.

Três propriedades governam o uso:

- **Força.** Prefira formas fracas. Um booleano posicional cujo significado os dois
  lados precisam conhecer é connascência de significado e de posição; trocá-lo por um
  tipo nomeado, ou por dados passados pelo chamador, é uma melhora real e barata.
- **Localidade.** Quanto mais distantes os elementos, mais fraca a connascência
  precisa ser. O que é tolerável dentro de um módulo é problema entre módulos.
- **Grau.** Quantos lugares são afetados.

Três regras: minimize a connascência total quebrando o sistema em elementos
encapsulados; minimize a que atravessa fronteiras de encapsulamento; maximize a que
fica dentro delas.

### Estático x dinâmico

**Acoplamento estático** é o que uma parte precisa que exista para funcionar:
dependências, banco, runtime, binário. Mede-se em tempo de compilação e implantação.
**Acoplamento dinâmico** é como as partes conversam em execução: síncrono ou
assíncrono, e quem espera por quem.

São perguntas diferentes. Estático é dependência operacional; dinâmico é dependência
de comunicação.

### Quantum arquitetural

Um artefato **independentemente implantável**, com **alta coesão funcional** e **alto
acoplamento estático** interno.

Num projeto de ferramenta, isso costuma ser a propriedade mais valiosa e mais fácil de
perder sem perceber: um binário único que roda offline, sem runtime externo, é um
quantum. No dia em que uma funcionalidade nova exige uma engine instalada, ela não é
"mais um subcomando" — é uma mudança de quantum. Decida o empacotamento no momento em
que a funcionalidade é aprovada, não depois de construída.

## 8. Quando separar e quando juntar

A pergunta não é "qual granularidade é a certa", é "quais forças puxam para cada lado".

**Desintegradores** — quando quebrar em partes menores:

| Força | Pergunta |
|---|---|
| Escopo e função | está fazendo coisas demais e sem relação entre si? |
| Volatilidade | as mudanças se concentram em uma parte só? |
| Escala e vazão | partes precisam escalar de forma diferente? |
| Tolerância a falha | uma falha ali derruba funções críticas daqui? |
| Segurança | uma parte precisa de nível de proteção maior? |
| Extensibilidade | o contexto está sempre crescendo? |

Teste de nome: se você não consegue nomear as duas metades resultantes sem inventar
"Serviço de Outras Coisas", a separação está errada.

**Integradores** — quando manter junto ou remontar: transação que precisa ser atômica,
fluxo de trabalho com muita conversa entre as partes, código compartilhado de verdade,
relação de dados que não sobrevive à separação.

O erro comum é olhar só os desintegradores. O acerto está no equilíbrio, e ele é
sempre local.

**Reuso.** Quatro padrões, com trade-offs distintos: replicação de código, biblioteca
compartilhada, serviço compartilhado, sidecar. Biblioteca compartilhada é a escolha
padrão dentro de um binário e vira integrador silencioso: ela resiste à separação
futura. Antes de compartilhar, pergunte se o que você vai compartilhar é
**semanticamente vazio** — formatação, ordenação, estrutura — ou se carrega semântica
de um dos lados. Semântica compartilhada é connascência de significado atravessando
fronteira.

## 9. Contratos

**Estrito**: campos, tipos e versão fixos. Quebra alto e cedo. Custa evolução.
**Frouxo**: tolerante, evolui sozinho, e adia a descoberta do erro para o consumidor.

Quando o consumidor é um **agente**, contrato estrito é quase sempre a escolha certa,
porque a alternativa é o agente adivinhar. Mas escolha estrita exige decisão escrita:
o que conta como mudança incompatível, e quando a versão sobe. Sem isso você tem
rigidez sem garantia.

Cuidado com **stamp coupling**: mandar uma estrutura grande porque é conveniente,
quando o consumidor usa três campos. Acopla todo mundo ao formato inteiro. A exceção
legítima é usar a mensagem para carregar estado de fluxo de propósito.

## 10. Antipadrões de decisão

Os três formam uma escada: sair de um leva ao seguinte.

- **Proteger-se.** Não decidir por medo de errar. Cura: decidir no último momento
  responsável e conversar com quem vai implementar.
- **Dia da marmota.** Decidir e não registrar o porquê, de modo que a mesma discussão
  volta para sempre. Cura: ADR.
- **Arquitetura por e-mail.** Registrar e ninguém saber que existe, ou não saber quem
  decidiu. Cura: um lugar só, conhecido, com status visível.

Mais dois que aparecem em projeto pequeno:

- **Apego irracional ao artefato.** Um documento bonito vira requisito por ser bonito.
  Cura: separar por escrito o que é objetivo, o que é evidência, o que é referência
  metodológica e o que é hipótese.
- **Conformidade sem mecanismo.** Uma ADR com seis proibições e nenhum teste. Cura:
  uma hora de trabalho transformando a proibição mais cara em verificação que falha
  citando o número da ADR.
