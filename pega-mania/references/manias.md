# Manias: cacoetes de escrita do agente a evitar

Lista viva e única, para todos os projetos. O Mateus aponta um cacoete, ele entra aqui com o
exemplo real e a reescrita. Os exemplos vêm do canal mmorpg-news (WoW Forever), onde a lista
nasceu, mas as manias valem para qualquer texto.

Regra geral: diga a coisa uma vez, de forma direta e afirmativa.

## 1. Afirmar e negar em seguida (confirmada pelo Mateus, 24/11/2026)

Dizer o que a coisa é e, colado, o que ela não é. Vale para todas as ordens:
"X, não Y" · "não é X, é Y" · "não foi X, foi Y" · "deixou de ser X e virou Y".

| Saiu assim | Reescrito |
|---|---|
| É hipótese, não é fato. | (cortado: a frase anterior já dizia "é opinião minha") |
| É personagem, não jogador: quem tem três alts conta três vezes. | O censo conta personagens, então quem tem três alts conta três vezes. |
| O Warlock não foi enfraquecido, foi rearrumado. | A Blizzard rearrumou o Warlock, tirando dano de um feitiço e dando resistência aos demônios. |
| A classe mais criada não foi o Hunter. Foi o Paladin. | O Paladin era o número um, à frente do Hunter. |
| O Hunter não é o primeiro personagem, é o segundo. | O Hunter é o segundo personagem de muita gente. |
| O Priest deixou de ser a escolha óbvia e virou uma entre quatro. | Hoje o Priest é uma entre quatro opções de healer. |

Parente próximo: repetir a palavra para dar peso ("É uma amostra, grande, mas uma amostra").

Não é mania: negação que informa um fato ("O Rogue não cura, não tanka").

## 2. Suspense antes de dizer (confirmada pelo Mateus, 24/11/2026)

Preparar a informação com uma frase que só anuncia que ela vem, ou com uma pergunta
que o próprio texto responde em seguida.

| Saiu assim | Reescrito |
|---|---|
| Eu vou tentar responder a pergunta que o número sozinho não responde: por quê? | Em cada posição eu vou dizer por que eu acho que a classe está ali. |
| Por que o Rogue está aqui? Minha primeira hipótese é o papel. | Minha primeira hipótese para o último lugar é o papel. |
| O Rogue só faz uma coisa: dano corpo a corpo. | O Rogue só faz dano corpo a corpo. |
| Mas tem um dado que eu acho bonito. O nível médio... | O nível médio... |
| E olha que curioso: o Shaman tem... | O Shaman também tem... |
| E agora o dado que eu mais gostei de encontrar. | (cortado) |
| Então o honesto é dizer: Druid e Warrior disputam... | Então eu trato os dois como empatados... |
| Minha aposta: é o segundo personagem. | Eu aposto que ele é o segundo personagem. |

Não é mania: o gancho de abertura do vídeo e a contagem regressiva de um ranking, que são
suspense escolhido pelo Mateus como estrutura. Dois-pontos antes de uma lista também pode.

## 3. Achadas com a skill /humanizer (24/11/2026; o Mateus pediu para testar a skill)

A skill confirmou as manias 1 e 2 (são os padrões §1 e §4 dela) e achou estas no mesmo roteiro.
O critério dela vale para todas: **cada frase mantida precisa trazer algo que o ouvinte ainda
não tinha**.

| Mania | Saiu assim | Reescrito |
|---|---|---|
| Frase solta de efeito, que só repete | ...é a menos jogada do jogo. De longe. | ...é de longe a menos jogada do jogo. |
| Fecho que explica o que o dado já mostrou | É uma classe de quem sabe o que quer. | (cortado) |
| Fecho que repete a frase anterior | Quem criava Warrior para tankar agora tem escolha. | (cortado: "perdeu o monopólio de tank" já dizia) |
| Rabo negativo colado no fim (parente da mania 1) | ...uma amostra grande do jogo, sem chegar a todos os personagens. | ...uma amostra grande do jogo. |
| Anúncio do que vem | Primeiro, a fonte. · Três avisos. | (cortados: a frase seguinte já começa o assunto) |
| Mesma abertura repetida por regra | "Minha hipótese é..." em quase toda classe; 14 frases começando com "E" | Variar: "Eu acho que", "Para mim", "Eu aposto que"; "E" só onde soma de verdade |
| Conclusão dita como fato | Como no Rogue, quem ficou está na frente. | Como no Rogue, isso sugere que quem ficou na classe continuou upando. |
| Frase de efeito vaga no fecho | ...o Rogue, que no PvP é outra história. | ...o Rogue. |

Frase curta pode ficar quando traz dado novo ("No PvE chega a 15%").

## Caça rápida

Depois de escrever, rode no texto da narração e leia cada linha que aparecer:

```bash
grep -nE ', não |, sem |não (é|foi|são|era) [^.]*[,;.] (é|foi|são|era) |\? |: por qu|olha que|Ou seja|deixa de ser|deixou de ser|(aposta|hipótese):|tem um dado|Primeiro, |outra história' <arquivo>.md
grep -oE '(^|[.?!] )(E|Minha hipótese) ' <arquivo>.md | sort | uniq -c   # aberturas repetidas
```

A busca só aponta suspeitos. Quem decide é a leitura.
