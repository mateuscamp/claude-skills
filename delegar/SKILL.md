---
name: delegar
description: Poupa a cota do plano Claude passando trabalho pesado para o GPT (Codex CLI, assinatura ChatGPT) ou para o Gemini/Claude via Antigravity CLI (assinatura Google), e só conferindo o resultado aqui. Use quando a tarefa tiver muita leitura, escrita ou teste com resultado verificável (escrever testes, refatorar, código repetitivo, migrar, investigar um repositório grande, resumir muitos arquivos ou documentos), quando a cota estiver acabando, ou quando o usuário disser "delega", "manda pro GPT", "passa pro Gemini", "economiza cota", "segunda opinião", "pergunta pro Codex", "usa o Antigravity".
---

# Delegar para GPT e Gemini

O usuário usa o Claude Code como ferramenta única, num plano Claude de cota curta, e tem assinaturas do ChatGPT e do Google AI Pro, já logadas no Codex CLI e no Antigravity CLI. Você continua sendo quem conversa, decide e confere. O trabalho braçal fica com os outros. Nunca mande o usuário abrir o Codex ou o Antigravity: a chamada sai daqui.

## Quando delegar

Delegue quando o trabalho for grande e o resultado puder ser conferido barato:
- escrever ou ampliar testes, código repetitivo, migração mecânica, refatoração com testes que já existem;
- varrer um repositório ou muitos arquivos e devolver um resumo;
- primeira versão de algo bem especificado, que você depois revisa;
- segunda opinião sobre um diagnóstico ou um design (modo só leitura).

Faça você mesmo quando:
- for edição pequena (escrever o briefing custaria mais que fazer);
- for decisão de arquitetura, ambiguidade ou algo que pede a conversa toda;
- envolver segredo, credencial ou dado pessoal sensível;
- o resultado não tiver como ser conferido sem refazer o trabalho.

Na dúvida, pergunte ao usuário em uma linha se ele quer delegar.

## Quem recebe

| Executor | Comando base | Para quê |
|---|---|---|
| **GPT** (padrão para código) | `codex exec` (modelo `gpt-6.1-sol`, esforço `high`, vindos de `~/.codex/config.toml`) | implementar, testar, refatorar, depurar |
| **Gemini 3.8 Flash** | `agy -p ... --model gemini-3.8-flash-high` | ler e resumir muito material, varredura rápida, tarefa simples |
| **Claude via Google** | `agy -p ... --model claude-opus-4-6-thinking` (ou `claude-sonnet-4-6`) | quando a tarefa pede qualidade de Claude mas não pode gastar a cota do plano Claude |

`agy models` lista o que a conta Google oferece (não há Gemini Pro).

## Como delegar

1. **Escreva o briefing em arquivo** no scratchpad (`brief.md`). Ele não vê esta conversa, então o briefing precisa se sustentar sozinho:
   - objetivo em uma frase;
   - pasta do projeto e arquivos que importam;
   - restrições (não fazer commit, não trocar de branch, não instalar dependência sem dizer, não mexer fora da pasta, seguir o estilo do projeto);
   - critério de pronto verificável ("`make check` passa", "os testes novos falham sem a mudança e passam com ela");
   - formato da resposta final: o que mudou, por arquivo, e o que ficou de fora.

2. **Rode.** Use `run_in_background` em tudo que puder passar de ~2 min e espere a notificação, sem ficar consultando.

   GPT editando o projeto:
   ```bash
   codex exec -C "<pasta do projeto>" -s workspace-write --ephemeral \
     --skip-git-repo-check -o "<scratchpad>/resposta.md" "$(cat "<scratchpad>/brief.md")" \
     > "<scratchpad>/codex.log" 2>&1
   ```
   GPT só consultando: troque por `-s read-only`.

   Gemini/Claude via Antigravity editando o projeto:
   ```bash
   cd "<pasta do projeto>" && agy -p "$(cat "<scratchpad>/brief.md")" \
     --model gemini-3.8-flash-high --mode accept-edits --print-timeout 1200s \
     --settings '{"permissions":{"allow":["command(python3)","command(ls)","command(cat)","command(git status)","command(git diff)"]}}' \
     > "<scratchpad>/resposta.md" 2> "<scratchpad>/agy.log"
   ```
   **Sem o `--settings` com `permissions.allow`, o agy não roda nenhum comando no modo `-p`** (medido em 09/11/2026, agy 1.5.3): ele nega sozinho, sai com código 0 e deixa a resposta vazia. O aviso aparece só no `agy.log`. Libere na lista os comandos que a tarefa precisa, como o portão do projeto (`command(make check)`, `command(uv run pytest)`, `command(npm test)`). Cada regra é um prefixo de comando, e `command(*)` não é aceito. Resposta vazia com saída 0 quer dizer que é hora de ler o log.
   Só consulta: rode `agy` de dentro do scratchpad com `--mode plan`, colando no briefing o conteúdo que ele precisa ver.

3. **Leia pouco.** O que poupa cota é não trazer o log inteiro para o contexto: leia `resposta.md`, depois `git diff --stat` e só então o diff dos arquivos que importam. O log fica para quando algo falhar (`tail`).

4. **Confira de verdade.** O relatório do executor é uma alegação. Rode os testes ou o portão do projeto e veja o diff. Se estiver errado, mande uma rodada de correção com o erro exato (no Codex, `codex exec resume --last "..."` mantém o contexto; no agy, `agy -c -p "..."`) antes de consertar você mesmo.

5. **Conte ao usuário** quem fez o quê ("o GPT escreveu os testes, eu conferi e ajustei X"), o que foi verificado e o que não foi.

## Cuidados

- Os dois são agentes completos. Nunca use `--dangerously-bypass-approvals-and-sandbox` (Codex) nem `--dangerously-skip-permissions` (agy) fora de uma pasta descartável.
- Num repositório git com mudanças suas ainda não commitadas, prefira mandar o executor trabalhar numa worktree (`codex exec --worktree`) ou faça o commit antes, para separar o que é seu do que é dele.
- Se um comando falhar por login (401, "sign in"), peça ao usuário `codex login` ou `agy` (sem argumentos, Google OAuth).
