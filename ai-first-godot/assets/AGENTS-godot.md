<!--
Modelo da skill ai-first-godot para a seção Godot do AGENTS.md de um projeto.
Copie, troque o que está entre <>, e apague o que não se aplica. O AGENTS.md é lido pelo
Claude Code (quando não há CLAUDE.md) e pelo Codex; mantenha nele só regra do projeto.
-->

## Godot

- Versão fixada: **Godot <4.7.2>**. Não use API de outra versão; na dúvida, consulte
  `godot --doctool <pasta> --no-docbase` em vez da memória.
- Rode `tools/portao.sh` depois de mudar regra, entrada ou cena. **Não use o código de saída do
  Godot como prova**: ele sai com 0 com erro de script no log. O portão lê o log.
- Todo Godot automatizado leva `--audio-driver Dummy` e `timeout`; prova visual sob `xvfb-run -a`.
  Renders, logs e caches em `~/.cache/<projeto>/`, não no `/tmp`.

### Organização

- `<game/domain>/`: regras em `RefCounted`, sem `Node`, `Input`, `Time`, `Tween` nem RNG global.
  Ações, tempo (`delta`) e semente entram como parâmetro. `tests/fronteira_spec.gd` cobra isso.
- `<game/content>/`: dados e nomes do conteúdo.
- `<main>/`: cenas, entrada, apresentação, áudio e persistência.
- `tests/`: specs `extends SceneTree` que terminam em `quit()` ou `quit(1)`.

### Código

- Tipe tudo: variáveis, parâmetros, retornos e laços (`for x: Tipo in ...`). `:=` só com lado
  direito de tipo conhecido.
- Registro com campos fixos (entidade, carta, inimigo) é classe com campos tipados, não
  `Dictionary`: chave errada em dicionário compila e falha calada.
- **Entrada:** um só adaptador normaliza toque e mouse em `<main/controle.gd>`, e
  `input_devices/pointing/emulate_mouse_from_touch=false`. Nada mais lê `InputEvent`.
- **Animação:** uma propriedade animada tem um único dono (um tween guardado e morto antes do
  próximo, ou um AnimationPlayer; nunca os dois).
- **Sorteio:** um `RandomNumberGenerator` com semente; `--semente=N` como argumento de usuário
  fixa a partida, e a semente usada sai no log.
- **Observabilidade:** eventos verificáveis saem como uma linha `print(JSON.stringify({...}))`
  com a chave `evento`; teste e ferramenta leem esses eventos, não o texto da tela. O
  `user://logs/godot.log` (ligado por padrão no desktop) guarda a partida do autor depois que o
  editor fecha; comando automatizado fora do portão usa `--log-file` em `~/.cache/<projeto>/`.
- Texto para o jogador passa por `tr()` e pela tabela de traduções no mesmo trabalho.

### Cena e arquivos

- Prefira montar e alterar cena por script headless a escrever `.tscn` à mão. Escrevendo à mão:
  use `path` e omita `uid`; não use propriedade do Godot 3 (`rect_min_size`, `align`); conexão de
  sinal para método inexistente falha calada.
- Depois de criar, mover ou renomear arquivo, rode `--import` (sem ele a cena carrega sem script
  e sai com 0). Não mova com `mv` sem reimportar; nunca edite `.godot/`.

### Testes

- Spec novo entra sozinho no portão (`tests/*_spec.gd`); não precisa de lista.
- Spec que grava em `user://` apaga no início os arquivos que usa e recusa um `user://` fora de
  `/tmp` ou `~/.cache` (nunca o do jogador).
- Antes do `quit()`, solte a cena e espere `create_timer(0.3)`: senão o áudio fica preso e a saída
  acusa `resources still in use at exit`.
- Erro provocado de propósito por um spec vai em `ERROS_ESPERADOS` no `tools/portao.sh`, com
  padrão estreito.
