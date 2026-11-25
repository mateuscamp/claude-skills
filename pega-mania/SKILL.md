---
name: pega-mania
description: Caça os cacoetes de escrita do agente que o Mateus rejeita, antes que o texto chegue a ele - afirmar e negar em seguida ("X, não Y", "não é X, é Y"), suspense que só anuncia o que vem, pergunta que o próprio texto responde, frase solta de efeito, fecho que repete ou explica o dado, aberturas repetidas, conclusão dita como fato, clichê, números enfileirados na fala - pela lista viva em references/manias.md, uma busca por grep e a skill /humanizer:humanizer; diz quando reescrever do zero em vez de remendar, e registra mania nova que ele apontar. Use sempre que o agente escrever ou revisar texto que o Mateus vai narrar, ler em voz alta ou publicar (roteiro de vídeo, texto de leitura, descrição, título, post, legenda), em qualquer projeto, e quando ele disser "cacoete", "mania", "tique de escrita", "isso soa como IA", "texto de robô", "clichê", "frase feita", "pega-mania" ou apontar uma frase que não gostou.
---

# Pega-mania

O agente escreve com cacoetes que o Mateus reconhece e rejeita. A lista dele mora em
`references/manias.md`, uma só para todos os projetos: projeto nenhum guarda cópia, cita esta skill.

## Antes de escrever

Leia `references/manias.md` inteira. A regra geral dela: diga a coisa uma vez, de forma direta
e afirmativa, e cada frase mantida traz algo que o ouvinte ainda não tinha.

## Depois de escrever, em ordem

1. **Caça rápida.** Rode os `grep` do fim de `references/manias.md` sobre o texto que vai ser
   narrado ou publicado (só a narração, sem notas internas nem fontes). A busca aponta suspeitos;
   leia cada linha e decida pela leitura.
2. **Leitura inteira contra a lista.** Várias manias escapam do grep: frase solta de efeito, fecho
   que repete, conclusão dita como fato, suspense sem palavra-chave.
3. **Humanizer.** Passe a skill `/humanizer:humanizer` no mesmo texto. Ela foi escrita para inglês,
   mas os padrões de estrutura valem em português. Travessão em fala narrada não importa; em texto
   publicado, sim.
4. **Conferir que nada sumiu.** Compare com o rascunho: nenhum fato, número, data, nome ou fonte
   pode ter caído nem surgido na reescrita.
5. **Derivados.** Se o projeto gera um texto a partir de outro (por exemplo, `leitura.md` a partir
   do `roteiro.md`), regere o derivado depois da revisão, nunca o edite sozinho.

Ao entregar, diga em uma linha quantos trechos mudaram e qual mania mais apareceu, e liste à
parte as frases suspeitas de clichê que ficaram no texto (mania 4), para o Mateus julgar ouvindo:
o agente não tem ouvido para clichê. Na dúvida entre clichê e coloquial, pergunte.

## Quando remendar não basta

Remendo frase a frase serve para texto que nasceu bom e tem deslizes. Reescreva do zero, sem
partir do rascunho, quando:

- duas passadas da lista ainda deixam mania nova aparecendo, ou a correção de uma cria outra;
- o esqueleto é o que todo texto sobre o assunto usa (a abertura de sempre, o exemplo de sempre);
- o texto sustenta opinião, motivo ou experiência que ninguém forneceu.

A versão nova parte de material novo, e não das frases antigas: fonte aberta na página, dado que
só existe neste assunto, eixo escolhido pelo Mateus. Pergunte a ele o eixo antes de escrever. O
rascunho antigo vai para uma pasta de arquivo, não é apagado, e o que saiu dele fica anotado com
o motivo.

O agente não escreve em primeira pessoa experiência, opinião nem motivação do Mateus. Onde o
texto pede isso, fica uma lacuna marcada (`[SUA VOZ: ...]`) e uma lista no fim com cada uma.

Origem (24/11/2026): o ep. 1 do mmorpg-news chegou ao sexto rascunho remendado antes de o Mateus
mandar reescrever inteiro; no compositando-yt o ep. 1 de física tinha o mesmo defeito, com uma
comparação clínica e uma dúvida "dele" que o agente tinha inventado.

## O que não é mania

- Negação que informa um fato ("o Rogue não cura, não tanka").
- Gancho de abertura e estrutura de suspense que o Mateus escolheu (contagem regressiva de ranking).
- Dois-pontos antes de uma lista.
- Frase curta que traz dado novo.
- Expressão coloquial ("levou um corte", "mexeu pesado"): é bem-vinda; clichê é a fórmula gasta.

## Mania nova

Quando o Mateus apontar um cacoete, ou o agente reconhecer um em si:

- **Confirmada por ele**: entra numa seção numerada de `references/manias.md`, com a data, o trecho
  real como saiu, a reescrita e o que *não* conta como essa mania.
- **Só suspeita do agente**: entra em "em observação", sem regra, e o agente aponta ao Mateus
  quando ela aparecer. Só vira regra com o sim dele.
- Se a mania tem uma forma que o `grep` pega, acrescente o padrão à caça rápida.

A lista muda neste repositório (ramo, worktree, PR), como qualquer skill: ver `AGENTS.md` da raiz.
