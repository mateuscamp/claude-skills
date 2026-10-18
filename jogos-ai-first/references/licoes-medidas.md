# Lições medidas

Evidência de duas medições reais, não opinião. Use este arquivo quando precisar dos
números, das ressalvas ou de citar a origem de uma afirmação da skill.

## 1. O estudo comparativo

**Desenho.** Um agente construiu o mesmo jogo mobile de grade — cascata, gravidade,
reposição, durabilidade em três níveis, progressão em runs, pacote Android e anúncio
integrado — em Godot, Unity e Defold. Uma execução por engine, sem contexto entre
elas, sem receber uma única indicação de API. Verificação final no mesmo aparelho
físico. Teto de três direções técnicas por execução.

**Resultado de fundo.** As três fecharam os dois estágios. As três verificaram no
aparelho. Nenhuma consumiu uma única direção técnica: 0 de 3 nas três.

| Medida | Godot | Unity | Defold |
|---|---|---|---|
| Até a primeira execução do jogo | 36 min | 52 min | 37 min |
| Direções técnicas consumidas | 0 / 3 | 0 / 3 | 0 / 3 |
| Intervenções humanas | 8 | 6 | 2 |
| Ciclos fechados sem humano | 40+ | ~36 | 32+ |
| Editor gráfico usado | sim | sim | não |
| Arquivos versionados | 83 | 365 | 82 |
| Arquivos-sombra | 24 `.uid` | 176 `.meta` | 0 |
| Linhas escritas à mão para monetização | 856 | ~0 | 278 |

**O empate que mais informa.** 36, 37 e 52 minutos até rodar. Se houvesse diferença
estrutural de acessibilidade entre as engines para um agente, ela apareceria aí. Não
apareceu.

## 2. As quatro conclusões que sobrevivem à ressalva

### 2.1 O ciclo fechado é o eixo que decide

Godot tem modo headless de fábrica. Defold precisou de display virtual e escreveu o
dobro de ferramenta de verificação — 4.479 linhas contra 2.201. Unity é a única com
framework de teste oficial por linha de comando.

Este é o único eixo com duas medições independentes concordando: um porte
Defold→Godot feito meses antes chegou à mesma conclusão por outro caminho.

> É o único dos dois em que eu fecho o ciclo sozinho. No Defold, conferir qualquer
> coisa de cena termina em "compila, roda, e alguém olha" — e esse alguém é você. É aí
> que mora o prejuízo: não no código que eu escrevo, mas no que só você consegue
> verificar.

### 2.2 As três falham de jeitos diferentes, e o jeito importa mais que a contagem

- **Godot**: armadilhas de versão e plataforma. Aparecem na atualização seguinte, são
  pesquisáveis. Falha alto e opaco.
- **Unity**: armadilhas de ferramenta e ambiente. Caras — cerca de três horas em
  emulador — mas externas ao código. Falha mudo.
- **Defold**: armadilhas de semântica silenciosa. Sobrevivem a todos os testes verdes e
  chegam ao jogador. As falhas de build são as mais legíveis das três; as duas piores
  não produziram erro nenhum.

**Para um agente, mudo é pior que opaco.** Diante de uma mensagem ruim ele investiga;
diante de silêncio, conclui que funcionou.

### 2.3 O defeito mais caro

No Defold, o botão esquerdo do mouse e o toque múltiplo chegavam ao mesmo tratador. No
desktop só existe o primeiro, e foi no desktop que todo o primeiro estágio verificou o
toque. No Android o mesmo dedo chega pelos dois: cada toque gastava duas bombas, e os
cartões de fim de run apareciam e sumiam no mesmo quadro.

**As 107 asserções continuaram verdes o tempo todo**, porque testavam a lógica, e a
lógica estava certa.

Junto com duas animações de interface que se cancelavam em silêncio, formam a mesma
classe: **dois donos para um recurso, e o motor escolhendo um sem contar.**

### 2.4 Convergências

Três agentes independentes, sem contato entre si, fizeram a mesma coisa:

1. reimplementaram o gerador de números aleatórios, porque nenhuma das três garante
   reprodutibilidade entre plataformas;
2. construíram um canal de narração — o jogo publicando o próprio estado no log —
   porque nenhuma oferece introspecção do jogo rodando;
3. separaram as regras do motor, para poder testá-las sem subir engine nenhuma;
4. não usaram o editor visual para montar a interface.

**Onde três agentes independentes constroem a mesma peça improvisada, ela pertence ao
motor.**

### 2.5 Nem tudo que o agente constrói à mão é perda

Nove reimplementações no total, três por agente, todas com justificativa escrita.

- **A engine ganha quando sabe algo que você não pode conferir**: ajuste de tela,
  escala de entrada, área segura, assinatura. Você não verifica sua versão contra um
  telefone que não possui.
- **A mão ganha quando você precisa de uma garantia que a engine não dá**:
  determinismo, estado serializável, tempo de vida explícito, testabilidade.
- **A duplicação deliberada é a mais sofisticada, e parece a pior.** Um agente
  reimplementou as regras em outra linguagem para conferir a primeira implementação;
  outro escreveu a detecção de grade separada da fórmula do jogo de propósito.
  Compartilhar código ali destruiria a verificação.

## 3. O que o estudo NÃO concluiu

Importa tanto quanto o resto, e é o que separa medição de propaganda.

- **Não há nota, vencedor nem recomendação de migração.** O protocolo proíbe pontuar
  antes que toda a evidência comparável exista, e proíbe fixar pesos depois de ler os
  resultados.
- **Cada engine correu uma vez, com o mesmo modelo.** Um defeito visto uma vez pode ser
  propriedade da ferramenta ou do dia. Só as convergências escapam dessa ressalva.
- **Os tempos estão contaminados**: duas execuções simultâneas na mesma máquina, uma
  mudança de premissa no meio de uma delas, migração de emulador para aparelho em duas
  das três, e horas de espera pelo telefone na terceira.

## 4. O verificador que saiu disso

Primeiro passo do roteiro: não uma engine, mas um verificador estático de posse que lê
os projetos existentes, monta a tabela de quem anima o quê e de quem trata qual
entrada, e reclama quando há dois. Custou dias e teria pego os dois defeitos mais caros
de toda a medição antes de qualquer um chegar ao aparelho.

Números do lançamento interno, em cinco projetos reais:

| Medida | Resultado |
|---|---|
| Arquivos aceitos ou recusados explicitamente | 694 de 694, sem omissão silenciosa |
| Erros bloqueantes falsos no corpus | 0 |
| Mediana no maior projeto, cinco varreduras | 0,69 s |
| JSON repetido | idêntico byte a byte |
| Execução sem rede | código 0 em namespace sem rede |
| Binário distribuível | 3,8 MB, sem runtime de linguagem externo |

**A distinção que dá o critério de projeto:** conflito comprovado bloqueia;
ambiguidade vira aviso explicado. Um verificador que inventa bloqueio queima a
confiança do agente e da pessoa em uma semana.

## 5. O gargalo real

Quatro projetos de jogo paralelos, uma pessoa só, alternando entre eles conforme a
vontade. Nenhum parou por dificuldade de ferramenta.

Se o limite é a atenção de uma pessoa, o que vale mais não é o que reduz o trabalho do
agente — é o que reduz o que só o humano consegue verificar. Um motor que faz o agente
escrever menos código vale pouco para quem tem tempo de agente de sobra e atenção
humana escassa. Um motor que faz o agente **provar mais coisas sozinho** devolve
exatamente o recurso que falta.
