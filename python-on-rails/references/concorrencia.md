# Concorrência

Ler só quando o projeto usa ou vai usar asyncio, threads ou processos. Não é trilho porque a
maioria dos projetos não precisa: código síncrono é mais fácil de testar e de o agente acertar.
Concorrência entra por necessidade medida, com ADR.

## Qual das três

| Gargalo | Ferramenta | Sinal de que é a certa |
|---|---|---|
| Espera de I/O, muitas conexões ao mesmo tempo (HTTP, banco, socket) | `asyncio` | O processo passa a maior parte do tempo esperando resposta |
| Espera de I/O com biblioteca só síncrona | `threading` / `ThreadPoolExecutor` | Mesma espera, mas a biblioteca não tem versão async |
| CPU (cálculo, imagem, parsing pesado) | `multiprocessing` / `ProcessPoolExecutor` | Um núcleo a 100% e os outros parados |

Python 3.13 e 3.14 têm o build *free-threaded* (sem GIL), em que threads usam vários núcleos em
CPU. É opcional e nem toda extensão em C suporta: adotar só com medição e ADR.

## Regras quando há asyncio

- **Nunca bloquear o loop.** Chamada síncrona de I/O (`requests`, `time.sleep`, `open` de
  arquivo grande) dentro de `async def` trava tudo. O ruff `ASYNC` pega os casos conhecidos;
  biblioteca síncrona inevitável vai para `asyncio.to_thread`.
- **Tarefa com dono.** `asyncio.TaskGroup` em vez de `create_task` solto. A tarefa sem
  referência pode ser coletada no meio, e a exceção dela some.
- **Timeout em toda espera externa**: `async with asyncio.timeout(s):`.
- **Cancelamento não é erro.** Não capturar `CancelledError` sem relançar.
- **Teste**: `pytest-asyncio` ou `anyio`, com o loop de teste isolado por teste. Relógio
  injetado, nunca `asyncio.sleep` real para "esperar acontecer".
- **Uma cor por camada.** O domínio continua síncrono e puro; o async fica na borda (rota,
  cliente HTTP). Função async no domínio espalha `await` por tudo sem ganho.

## Regras quando há threads ou processos

- Estado compartilhado mutável é proibido por omissão: passe mensagens (`queue.Queue`) ou
  dados imutáveis (`frozen` dataclass).
- Processos: o que atravessa a fronteira precisa ser serializável (pickle). Isso é dado que o
  próprio programa criou, não entrada externa, então o trilho de `pickle` não se aplica.
- Teste de concorrência é instável por natureza: teste a lógica sem concorrência e a
  coordenação com poucos casos determinísticos (barreira, evento), nunca com `sleep`.
