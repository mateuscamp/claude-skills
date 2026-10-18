# Contrato AI-first do projeto

Este projeto é alterado por agentes e precisa ser verificável sem depender de uma
pessoa olhando a engine. Ajuste as regras ao projeto, mas mantenha as duas metades:
as regras de código e a caixa de decisão.

## Regras de código

1. Domínio não importa cena, entrada, áudio, GPU, janela nem relógio global.
2. Toda aleatoriedade de regra recebe uma semente e passa por um gerador único.
3. Entrada física é normalizada em um ponto antes de alterar o estado.
4. Uma propriedade animada tem um proprietário. Composição deliberada precisa de
   exceção exata e justificada, registrada em arquivo, nunca implícita.
5. Logs para verificação são estruturados; texto livre é apenas para pessoas.
6. O comando de teste e o comando de prova de cena vivem no repositório.
7. Conclusão de tarefa exige rodar o portão do projeto e relatar o resultado.
8. Mudança que toque entrada ou animação registra resultado, tempo, avisos e se
   precisou de inspeção humana.

## Caixa de decisão do agente

| Decisão | Regime |
|---|---|
| Nome, estrutura interna, teste, refatoração dentro de um módulo | decide sozinho |
| Dependência de propósito específico, resolvida num canto | decide sozinho e registra no diff |
| Dependência de propósito geral, fronteira nova entre módulos | propõe com justificativa; a pessoa aprova |
| Framework, runtime, serviço remoto, mudança de contrato público ou de código de saída | exige registro de decisão; o agente não decide |

## Como ler o resultado do portão

- saída 0: nenhum conflito comprovado; avisos ainda precisam ser relatados;
- saída 1: conflito comprovado; a tarefa não está concluída;
- saída 2: a ferramenta não conseguiu provar que analisou o projeto inteiro; a tarefa
  também não está concluída.

Aviso não autoriza adivinhar. Explique o limite, reduza a construção dinâmica quando
isso melhorar o projeto, ou registre uma exceção específica com motivo.

## Evidência mínima para concluir

- teste de domínio sem janela;
- teste ou captura da cena pelo caminho de produção;
- semente e entradas suficientes para reproduzir o caso;
- log ou artefato que permita a outro agente verificar a conclusão.
