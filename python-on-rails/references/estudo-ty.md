# Estudo: ty

O ty é o type checker da Astral (a empresa do ruff e do uv), escrito em Rust. Em 2026-11-01 ele
não está instalado nesta máquina e não entra no portão. Este arquivo é o procedimento para
decidir se entra.

## Por que estudar

- **Velocidade**: checagem instantânea muda o ciclo do agente, que pode rodar tipos a cada
  edição e não só no portão.
- **Uma empresa só**: uv, ruff e ty com a mesma configuração e a mesma cadência de lançamento.

## Por que ainda não

- O basedpyright no modo `recommended` é o que hoje reprova `Any`, `Unknown`, falta de
  `@override` e supressão sem regra. Trocar sem medir é trocar uma proteção conhecida por uma
  promessa.
- Ferramenta nova em beta muda regra e saída entre versões; portão precisa de veredito estável.

## Procedimento

Avaliar ferramenta são duas perguntas, em sequência, e parar na primeira é como ela entra sem
servir:

1. **Preserva?** Rodar o ty (`uvx ty check`) em paralelo ao basedpyright no mesmo projeto, na
   mesma versão do código. Plantar os defeitos que o portão precisa pegar (`Any` explícito,
   `json.loads` vazando, `dict` sem parâmetro, `match` não exaustivo, override sem decorator,
   supressão sem regra, atributo inexistente) e conferir se o ty reprova cada um. Um que ele
   não pegue e o basedpyright pegue já é perda.
2. **Acrescenta?** Contra o que está em produção hoje (o basedpyright), não contra nada. O que
   o ty pega que o basedpyright deixa passar? Quanto tempo economiza por ciclo, medido?

Escolha o projeto de teste pela medição: um projeto típico, não o mais problemático.

## Resultados possíveis

- **Não preserva**: fica fora. Reavaliar na próxima versão estável.
- **Preserva e não acrescenta**: fica fora. Duas ferramentas para o mesmo veredito é custo.
- **Preserva e acrescenta**: entra primeiro como etapa extra do portão, ao lado do
  basedpyright, por um ciclo de projeto. Só substitui depois disso, com ADR nesta skill.

Registrar aqui a data, as versões e o resultado de cada rodada.
