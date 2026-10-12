---
name: ai-first-godot
description: Boas práticas AI-first para qualquer jogo em Godot 4 quando quem escreve o código é um agente - como o código deve ser escrito (domínio em RefCounted sem engine, um adaptador de entrada, um dono por animação, RNG com semente, eventos em log JSON, tipagem, registros como classes, regras de .tscn e --import), o modelo de AGENTS.md, e o ciclo de verificação que o agente fecha sozinho (portão que importa, compila todos os scripts, roda os specs e lê o log em vez de confiar no código de saída; hook Stop do Claude Code; warnings estritos; fitness function da fronteira do domínio; log da partida em arquivo). Use sempre que o projeto for Godot - ao começar um jogo novo, ao chegar num projeto existente, ao auditar se ele segue as boas práticas, e quando o assunto for teste headless, CI, hook, "passou mas tinha erro no log", "o Godot travou no teste", warnings, tipagem, Dictionary, `--check-only`, `--script`, xvfb, "resources still in use at exit", saves de teste em user://, log em arquivo, user://logs, godot.log, --log-file ou "o log sumiu". Complementa a skill jogos-ai-first (método e governança).
---

# AI-first em Godot

O agente escreve GDScript bem. O que ele não vê é o erro que **não aparece**: o Godot sai com 0
com erro de script no log, trava sem avisar quando o erro é dentro de `_initialize`, descarta em
silêncio propriedade desconhecida em `.tscn` e aceita chave errada em dicionário. Esta skill dá
duas coisas: **como escrever** o projeto para que esses erros não nasçam, e **como verificar**
para que os que nascerem virem reprovação antes de o agente dizer "terminei".

O método geral (contrato, posse, determinismo, ADR, fitness function, risco) está na skill
**jogos-ai-first**. Aqui fica só o que é do Godot.

Arquivos desta skill:
- `assets/AGENTS-godot.md`: a seção Godot do `AGENTS.md` do projeto, pronta para adaptar. É
  **a lista das boas práticas de código**; leia-a inteira antes de escrever código Godot.
- `references/armadilhas.md`: os comportamentos medidos da CLI e da engine, com números. Leia
  antes de afirmar qualquer coisa sobre código de saída, compilação, warnings ou `.tscn`.
- `scripts/`: `portao.sh`, `compilar_tudo.gd`, `hook_portao.sh`, `fronteira_spec.gd`.

## Por onde começar

**Projeto novo**
1. Fixe a versão (`godot --version`) e escreva o `AGENTS.md` a partir de
   `assets/AGENTS-godot.md`, com as pastas reais. Configure no `project.godot`:
   `input_devices/pointing/emulate_mouse_from_touch=false` (jogo de toque) e os warnings estritos
   da seção 4 **desde o primeiro script**, quando custam zero.
2. Instale o portão e o hook (seção 2) e o `fronteira_spec.gd`, antes da primeira mecânica.
3. Siga o `AGENTS.md`. Cada mecânica nova vem com spec e com eventos JSON que o spec lê.

**Projeto existente**
1. Audite medindo (seção 1) e mostre ao usuário a tabela: o que existe, onde, e o número medido.
2. Instale o portão e o hook primeiro: são baratos e protegem todo o resto.
3. O que a auditoria apontar no código (entrada, animação, RNG, tipagem) vira etapas pequenas,
   cada uma com o portão verde. Mudança de contrato entre domínio, cena e testes pede ADR antes.

## 1. Auditar

Confira e **meça**; não responda pela leitura do código.

| Prática | Como conferir |
|---|---|
| Versão fixada | `godot --version` contra o `AGENTS.md` e o `config/features` |
| Domínio sem engine | regras em `RefCounted`? rode `fronteira_spec.gd` ajustado às pastas |
| Um só adaptador de entrada | `emulate_mouse_from_touch=false`; `grep -rl InputEvent` aponta um arquivo só? |
| Um dono por propriedade animada | contar `create_tween`/`tween_property`/`AnimationPlayer` e quem os guarda |
| RNG com semente | `RandomNumberGenerator` num lugar só; `randi`/`randf` globais no código de jogo |
| Eventos verificáveis | os testes leem eventos JSON ou texto da tela? |
| Verificação lê o log | os comandos do README/CI só olham o código de saída? |
| Log em arquivo | `debug/file_logging` desligado no `project.godot`? comando avulso (captura, robô) grava no `user://logs` do autor? |
| Compilação total | algo carrega todos os `.gd`, ou só o que os specs usam? |
| Specs fora da lista | `tests/*_spec.gd` que o README ou o CI não rodam |
| Hook | `.claude/settings.json` roda verificação no `Stop`? |
| Warnings estritos | ligar numa **cópia** e contar por pasta e por tipo (abaixo) |
| Registros em `Dictionary` | `Array[Dictionary]` de entidades no domínio, e quantas chaves cada um tem |
| Conexões no `.tscn` | `grep -c '^\[connection'`; se for zero, lint de cena rende pouco |

Contar warnings sem tocar no projeto: `rsync` para `~/.cache/<projeto>-auditoria` (sem `.git` e
`.godot`), acrescente `[debug]` com os cinco warnings em `=2`, rode `--import` duas vezes e o
`compilar_tudo.gd`, e agrupe as linhas `Warning treated as error` pelo `res://` da linha seguinte.

## 2. Instalar o portão e o hook

```sh
S=~/.claude/skills/ai-first-godot/scripts
cp $S/compilar_tudo.gd $S/fronteira_spec.gd tests/
cp $S/portao.sh $S/hook_portao.sh tools/ && chmod +x tools/portao.sh tools/hook_portao.sh
```

- `compilar_tudo.gd` e `fronteira_spec.gd`: ajuste `PASTAS` ao projeto.
- `portao.sh`, bloco `AJUSTE`: `COM_TELA` (specs que precisam de display) e `ERROS_ESPERADOS`
  (erro que um spec provoca **de propósito**, com padrão estreito que cite o arquivo).
- Hook: registre em `.claude/settings.json` do projeto (o JSON está no topo do
  `hook_portao.sh`). Ele roda o `--rapido` só quando `.gd`, `.tscn`, `.tres` ou `project.godot`
  mudaram desde a última aprovação, e na segunda parada seguida deixa a sessão terminar.
- Atualize `AGENTS.md` e a seção de verificação do README.

**Prove que o portão reprova antes de confiar nele.** Plante, rode e apague:
1. erro de tipo (`var x: int = "t"`) e chamada a método inexistente de uma `class_name` →
   `compilar_tudo` reprova;
2. spec com `var n: Node = null` e `n.queue_free()` em `_initialize` → `TRAVOU`
   (`PB_PORTAO_LIMITE=20`);
3. spec com `push_error("x")` e `quit()` → `FALHOU` com exit 0.

Depois rode o portão completo **cinco vezes seguidas**: falha intermitente aparece aí, e costuma
ser áudio preso ou estado sobrando em `user://`.

## 3. Consertar o que o portão acha

- `resources still in use at exit`: `queue_free()` na cena e `await create_timer(0.3).timeout`
  antes do `quit()`. `--verbose` mostra qual recurso ficou.
- Spec que reprova na segunda execução: depende do `user://` limpo. Apague no início os arquivos
  que ele usa, atrás da trava que recusa `user://` fora de `/tmp` e `~/.cache`.
- `Cannot find member` numa classe recém-usada: confira se a `class_name` é a que você pensa;
  cena e domínio costumam ter nomes parecidos.

## 4. Tipagem

Os cinco warnings que valem como erro (`project.godot`, seção `[debug]`, valor `2`):
`gdscript/warnings/untyped_declaration`, `unsafe_property_access`, `unsafe_method_access`,
`unsafe_cast`, `unsafe_call_argument`.

- Projeto novo: ligue todos no primeiro dia.
- Projeto existente: meça. Se o grosso for leitura de `Variant` saída de `Array[Dictionary]` de
  entidades, **pare e escreva um ADR**: locais tipadas só calam o aviso; o ganho real (chave
  errada vira erro de compilação) exige classes `RefCounted` com campos tipados, o que muda o
  contrato entre domínio, cena e testes. Etapas do menor registro para o maior, cada uma provando
  que não mudou o jogo com os **logs de evento por semente idênticos byte a byte** e o desempenho
  dentro de uma margem. Eventos que viram log JSON podem continuar `Dictionary`.
- Ligue pasta a pasta: `gdscript/warnings/directory_rules` exclui as pastas ainda sujas (`0`
  exclui). Só funciona com pasta, não com arquivo.

## 5. Log da partida em arquivo

O autor joga pelo editor, fecha, e pede "olhe o log". O console do editor já era; o arquivo não.

- **Já vem ligado no desktop.** `debug/file_logging/enable_file_logging.pc = true`: cada
  execução grava `user://logs/godot.log` (no Linux, `~/.local/share/godot/app_userdata/<nome>/
  logs/`) com prints, `push_error` e o backtrace de GDScript. A anterior vira
  `godot<data>.log`, e ficam `max_log_files` (5). Não desligue; para playtest, suba o limite.
- **Os eventos JSON já estão lá**, porque são `print`: o leitor de playtest lê o `godot.log` (ou
  os rotacionados) em vez de pedir ao autor que copie o console.
- **Teste e robô não podem empurrar os logs do autor para fora da rotação.** O `portao.sh` da
  skill já roda cada execução com `XDG_DATA_HOME` próprio. Comando avulso (captura, robô fora
  do portão) leva `--log-file <caminho em ~/.cache>`, que grava ali e não toca no `user://logs`.
- Mobile não tem a variante `.pc` (não medido aqui): ligue `enable_file_logging` se o playtest for no aparelho e
  puxe o arquivo pelo `adb`.

## Convivência

- Todo Godot automatizado: `--audio-driver Dummy`, `timeout`, log lido. Blender com `-noaudio`.
- Renders, logs e caches grandes em `~/.cache/`, não no `/tmp` (tmpfs com cota).
- Arquivo do domínio muito editado por outro chat ou agente: refatoração grande só numa janela
  combinada, nunca em paralelo.
- Remover código, levar para a `main` ou enviar ao remoto: confirme com o usuário. Se o modo
  automático bloquear, pare e explique; não contorne.
