# Auditar mudança em projeto de jogo

Lente extra para quando o alvo é um jogo (motor, framework ou engine própria). Ela não
substitui o `SKILL.md`: acrescenta o que mais escapa num jogo, o defeito que compila, passa
na suíte e funciona diferente da intenção. Cada item é uma pergunta a responder com
evidência, no formato de achado da seção 7; o que não se aplica ao projeto se pula e se diz.
As convenções concretas (nomes de fato, chaves, camadas) vêm do `AGENTS.md` do projeto e,
quando houver, da skill do motor (`ai-first-defold`, `ai-first-godot`, `ai-first-love`).

## Produto e escopo

- **Decisão de produto calada.** O diff muda regra de jogo, número de balanço, o que a tela
  mostra ou o que o jogador pode fazer sem a decisão registrada (Dnn, ADR, plano)? Mudança
  de regra "para facilitar a implementação" é achado.
- **Experimento sem volta.** Regra nova pedida como experimento mantém o modo anterior por
  chave de configuração, com a passada que compara os dois? Chave nova documentada onde o
  projeto documenta chaves, e valor inválido estourando com o recebido?
- **Critério que só o autor fecha.** O PR dá como cumprido algo que depende de playtest,
  aparelho ou pessoa nova (legibilidade, tutorial, sensação de toque)? Isso é alegação sem
  suporte (4.1), não "feito".

## Determinismo

- Sorteio só pelo RNG do projeto com semente injetada; nada de `math.random`, relógio ou
  ordem de iteração de tabela/dicionário decidindo regra.
- A mesma semente e a mesma sequência de ações dão os mesmos eventos e o mesmo estado: há
  teste ou impressão digital de mapa cobrindo a mudança? Gerador que muda o consumo do
  sorteio muda todo mapa de toda semente: o PR diz isso e atualiza as digitais com o porquê?
- Replay ou gravação de run: o que a ação nova decide entra na gravação e na conferência?

## Domínio, orquestração e apresentação

- **Autoridade.** A cena, a GUI ou a vista decidem regra, escrevem no estado da partida ou
  leem o estado vivo do domínio para mostrar? A tela mostra o estado já apresentado (o que
  os eventos entregues fizeram avançar), não o futuro que o domínio já decidiu.
- **Dono único.** Duas peças animam, posicionam ou pintam a mesma coisa (dois tweens, um
  segundo script)? Velocidade normal, rápida e instantânea dão o mesmo estado final?
- **Entrada.** O robô e o teste tocam pelo mesmo caminho do dedo? Toque pode contar duas
  vezes (mouse sintetizado do toque, dois bindings para o mesmo gesto)? Ordem nova é
  recusada enquanto a anterior se apresenta?

## Prova de cena e tela

- **Fato do galho certo.** O fato de log que a passada cobra sai de dentro do galho que
  comprova o comportamento, com o valor que a tela mostrou, e não do domínio? Fato emitido
  antes da apresentação ou fora do galho aprova sem provar.
- **Presença, não só ausência de erro.** A passada exige a linha (`--exigir` ou equivalente)
  com contagem mínima? Todo `--recusar` vem com um `--exigir` de presença, para não passar
  no vazio? O código de saída do motor sozinho não prova nada.
- **Caminho alcançado.** A peça nova (animação, tela, galho, idioma) é alcançada por alguma
  passada ou atalho de início validado? Recurso com nome errado que só falha quando o
  caminho roda é o caso típico.
- **Intenção visual.** Onde o projeto tem invariantes de tela (texto mínimo, alvo de toque
  mínimo, nada fora da janela, presença do que acontece no mundo), a vista nova as cumpre
  nos tamanhos e arranjos que o projeto prova? Quem aprovou as invariantes novas foi o
  autor? O que só o olho julga vem com captura, e o PR diz que ali não há teste.
- **Lista ou modelo de tela.** Em projeto com lista de desenho ou modelo de vista: a vista
  ficou sem chamar o motor (fronteira cobrada por teste)? Toque e robô consultam a mesma
  lista? O esperado de geometria no teste não é a mesma conta que o código prova?

## Texto, arte e plataforma

- Texto novo nasce no arquivo de textos em todos os idiomas, sem literal na tela, e cabe
  (quebra de linha, CJK, piso de tamanho)?
- Asset novo com origem e licença no `CREDITS.md` (ou equivalente) no mesmo commit; arte
  gerada com o gerador e o `--check` em dia; nada copiado de jogo de referência.
- Mudança que só aparece no aparelho (toque, orientação, área segura, pausa e volta, dt
  depois do segundo plano): o PR diz se rodou a prova no aparelho ou declara que não.
- Versão do motor, runtime ou biblioteca trocada: registrada, e as medidas que dependiam
  dela refeitas?

## Verificador do próprio jogo

- Teste, passada ou ferramenta nova foi vista reprovar (defeito plantado e restaurado)?
- Asserção invertida, `--exigir` afrouxado ou passada removida: justificativa no commit e
  o caso antigo coberto no modo em que ainda vale (a chave que volta à regra anterior)?
- Semente da passada trocada para o teste voltar a passar: o fato é cobrado por faixa, e o
  commit diz o que a semente nova dá?
