# Começando um projeto de jogo AI-first

A sequência abaixo cabe em uma tarde e é o que impede um projeto de crescer sem que
ninguém tenha decidido que ele deveria crescer.

## Antes de qualquer código

### 1. Escreva o que faz o projeto parar

Antes de escrever o que o projeto vai fazer, escreva o que faria você encerrá-lo. Um
projeto sem critério de encerramento não tem como declarar sucesso nem fracasso, e
por isso consome tempo indefinidamente.

Formato mínimo, uma linha cada:

- que resultado, se não aparecer até uma data, encerra;
- que evidência, se aparecer, muda a direção;
- quanto de orçamento — horas, custo de agente — a fase inteira tem.

### 2. Três a cinco características prioritárias, com definição operacional

Não sete de saída. Comece com as três que decidem, e só acrescente quando uma decisão
concreta exigir. Cada uma precisa virar uma frase que alguém possa medir.

Para jogo AI-first, as candidatas que a medição sustenta:

| Característica | Definição operacional possível |
|---|---|
| Verificabilidade autônoma | o agente executa, observa e decide se um critério passou sem intervenção humana |
| Determinismo | mesmo estado, entrada, semente e perfil produzem o mesmo próximo estado |
| Observabilidade consultável | estado e geometria consultáveis por contrato estável, não inferidos de pixels ou log livre |
| Falha explícita | conflito de posse, nome ou contrato impede a carga e nomeia os dois sítios |
| Fidelidade de plataforma | diferença semântica conhecida do alvo é executável antes do aparelho |

Diversão, estética e ritmo continuam sendo julgamento humano. Diga isso por escrito,
para não construir mecanismo tentando automatizar o que não se automatiza.

### 3. Riscos de nota 9, com mitigação

Impacto de 1 a 3 vezes probabilidade de 1 a 3. Só os de 6 para cima entram no
documento inicial; os outros aparecem quando aparecerem. Cada um com sinal de parada:
o que você veria que significaria que o risco se realizou.

`assets/RISCOS.md` é o modelo.

### 4. A primeira ADR: o que esta fase NÃO faz

Escreva a decisão que proíbe a fase seguinte até o portão passar. Ela é a mais
importante do projeto inteiro, e é a que ninguém escreve.

Conteúdo mínimo: o que fica de fora, por quanto tempo, qual portão libera, e — na
seção de conformidade — **como isso será verificado**. Se a proibição não tem
verificação, ela é uma intenção. Uma lista de dependências autorizadas num teste custa
uma hora e transforma a intenção em mecanismo.

`assets/ADR.md` é o modelo.

### 5. O contrato AI-first na raiz

Copie `assets/CONTRATO.md`, ajuste ao projeto e aponte para ele a partir de
`AGENTS.md` e `CLAUDE.md` com um fragmento curto. Nunca sobrescreva instruções que já
existam: o fragmento é incorporado deliberadamente.

O contrato precisa das duas metades: as regras de código **e** a caixa que diz o que o
agente decide sozinho. Só proibição trava o agente e gasta atenção humana; só
liberdade produz decisão de arquitetura tomada por quem não devia.

## Nos primeiros dias de código

### 6. Fronteiras antes de funcionalidade

Domínio puro, adapter da engine, apresentação. Relógio, gerador aleatório e efeito
externo entram por parâmetro. Isso é o que permite o agente testar sem subir a engine,
e não dá para acrescentar depois sem reescrever.

### 7. O comando de prova no repositório

Um comando que roda o domínio sem janela, e um que exercita a cena pelo caminho de
produção. Versionados, nomeados, citados no contrato. Uma verificação que não roda não
verifica nada.

### 8. A primeira fitness function

Escolha a característica número 1 e escreva a verificação dela antes de escrever a
funcionalidade que ela vai julgar. Fixe o limiar antes. Se você fixar depois, vai
fixar no valor que o resultado permitiu.

## Erros de partida que já custaram caro

- **Deixar a semente implícita.** Sem semente registrada não há reprodução de defeito,
  e sem reprodução o agente não consegue trabalhar sozinho. Corrigir depois significa
  reescrever tudo que sorteia.
- **Deixar o gargalo de verificação para o fim.** Se o ciclo depende de alguém olhar,
  cada funcionalidade nova aumenta o custo de todas as anteriores.
- **Começar pelo editor visual.** Não é preferência estética: um projeto montado em
  editor visual não é modificável por um agente sem intermediário, e arquivos-sombra
  transformam renomear em risco.
- **Escrever a especificação antes da decisão.** Especificação pesada não protege
  contra uma decisão de produto errada. Uma ADR de duas páginas com consequência
  negativa escrita protege mais que trinta páginas de requisito.
- **Confundir referência com requisito.** Um livro, um artigo ou um projeto admirado
  fornece método. Nada disso vira requisito do seu projeto até ser rastreado ao seu
  objetivo ou a um experimento que você aceitou.

## Portões, e por que eles existem

Um portão é uma pergunta com resposta binária, escrita antes de a fase começar, com
orçamento próprio. Ele existe para que a fase seguinte seja uma **decisão**, e não a
continuação automática da anterior.

Formato:

```text
Portão N - nome

Orçamento: N horas antes da primeira avaliação.

Passa se:
- critério objetivo 1
- critério objetivo 2

Se falhar: [o que acontece, escrito antes]
```

A última linha é a que dá valor às outras. "Se falhar, publicar o aprendizado e não
construir" é uma frase que só tem força se estiver escrita antes de você ter investido.
