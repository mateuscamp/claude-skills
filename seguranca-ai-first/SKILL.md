---
name: seguranca-ai-first
description: Segurança de app escrito por agente que guarda segredo ou dado pessoal ou financeiro, dirige navegador logado ou lê arquivo de fora - a regra zero (o atacante nomeado antes da mitigação, com o risco que sobra no ADR) e os quatro atalhos medidos que passam por /code-review e /code-audit (arquivo de fora lido no processo que tem o segredo, banco legível por todos, navegador sem sandbox por padrão de biblioteca, senha por variável de ambiente ensinada no README), cada um com correção e prova. Use sempre que o código lidar com token, senha, chave de API, credencial, keyring, chaveiro, banco, corretora, extrato, CPF, dado de saúde, SQLite com dado pessoal, Playwright, Selenium, scraping logado, 2FA, download, anexo de e-mail, PDF, XLSX, OFX ou CSV de fora, mesmo sem a palavra segurança, e quando o assunto for modelo de ameaça, sandbox, permissão de arquivo, umask ou "isso é seguro?". Complementa a arquitetura-ai-first e a code-audit.
---

# Segurança AI-first

O agente sabe o que é SQLCipher, bubblewrap, chaveiro e `umask`. O que falta é o gatilho:
ninguém escreve "segurança" no pedido "faz um app que baixa meus extratos", e para entregar
funcionando o agente pega o caminho padrão. A medição desta skill (2026-11-07, seis execuções de
três pedidos assim, `references/medicao.md`) achou o padrão:

- **O agente já acerta sozinho**: não grava token em arquivo, não guarda a sessão do navegador
  entre execuções, não põe segredo em log, não desliga o TLS. Esta skill não repete isso.
- **O agente erra sem ver**: os quatro atalhos da tabela abaixo apareceram em duas ou mais
  execuções em que se aplicavam. Todos passaram pelo `/code-review` e pelo
  `/code-audit` (de uma a quatro rodadas por execução), porque a revisão procura defeito, não contra quem o programa se defende.
- **Nenhuma execução declarou modelo de ameaça.** Medidas certas aparecem soltas (chaveiro,
  https, recusa de redirect), sem dizer contra quem servem nem o que fica de fora.

O método de decisão (drivers, ADR, fitness function) fica na **arquitetura-ai-first**; a
auditoria, na **code-audit**; os trilhos de Python, na **python-on-rails**. Aqui fica o que só
aparece quando o código toca segredo, dado sensível, navegador logado ou arquivo de fora.

Arquivos desta skill:
- `references/provas.md`: os testes e as conferências de cada atalho, em Python.
- `references/medicao.md`: protocolo, números e provas da medição, para medir de novo.

## Regra zero: o atacante antes da mitigação

"Seguro" sem atacante não decide nada. Antes de escolher qualquer proteção, nomeie três coisas e
escreva no `AGENTS.md` do projeto, ou no ADR quando houver decisão com custo:

1. **O ativo**: o segredo (token, senha, chave) ou o dado (saldo, extrato, documento). Proteger
   a chave e entregar o dado à interface não protege o dado.
2. **O atacante**: um degrau da escada abaixo.
3. **O acesso dele**: ler arquivo, rodar como o mesmo usuário, controlar o arquivo ou a página
   que o programa lê, levar o disco.

| Degrau | Atacante | O que fecha | Custo |
|---|---|---|---|
| 1 | Quem lê o arquivo sem ser o seu usuário: outro usuário da máquina, backup ou sincronização que vaza, disco levado | Permissão só do dono; criptografia em repouso no que sai da máquina | Baixo |
| 2 | Entrada hostil: anexo, PDF, planilha, página web que o programa abre | Parser em processo separado, sem o segredo, com limite de recurso; navegador com sandbox | Médio |
| 3 | Código rodando com o seu UID: ladrão de dados que varre a `$HOME`, pacote malicioso, processo ativo enquanto o programa roda | Contra quem só copia arquivo: criptografia com a chave fora do alcance do UID (cofre trancado, TPM); permissão `0600` não o detém. Contra quem age enquanto o programa roda: chave fora do processo da interface, segredo por descritor e não por ambiente, processo não inspecionável. Só encarece: quem tem o UID lê a tela e pode capturar a senha de login | Alto |
| 4 | Root ou acesso físico à máquina ligada | Nada que o app faça sozinho | Fora do alcance |

**O piso não se pergunta.** Os degraus 1 e 2 cobrem os quatro atalhos medidos e custam pouco:
valem em todo app que toca segredo ou dado sensível, sem esperar resposta. Subir ao degrau 3, ou
declarar que o projeto fica abaixo dele, é decisão da pessoa: pergunte em pergunta fechada, com a
recomendação primeiro, e registre a resposta. O que fica de fora vai para "Aceito
conscientemente" no ADR (modelo na arquitetura-ai-first), **um risco por atacante**.

## Os atalhos medidos

Em ordem de frequência. As correções e os testes completos estão em `references/provas.md`.

### 1. Arquivo de fora lido no processo que tem o segredo e o banco (4 de 4)

O agente abre o PDF com `PdfReader`, a planilha com `load_workbook` e o OFX com `read_bytes()`
no mesmo processo que tem o SQLite aberto e a senha revelada, sem limite de tamanho, de páginas,
de linhas nem de tempo. Ninguém tratou o anexo de e-mail como entrada hostil; o máximo visto foi
`defusedxml`, que cobre a bomba de XML e mais nada.

**Faça**: o parse roda num processo filho sem o segredo e sem o banco.
- Recuse antes de abrir: tamanho em bytes acima do teto é erro, sem chamar a biblioteca.
- O filho nasce com ambiente limpo (`env` mínimo, `python -I`) e põe os próprios limites na
  primeira linha (`RLIMIT_AS`, `RLIMIT_CPU`, `RLIMIT_CORE=0`). O pai espera com `timeout`, porque
  `RLIMIT_CPU` não conta tempo parado.
- O filho devolve JSON; o pai valida o tipo e o tamanho antes de gravar. O pai nunca reabre o
  arquivo com a biblioteca de parse.
- Sem rede no filho (`bwrap --unshare-net`, `unshare -rn`) quando a máquina tem: é o degrau 2
  completo. Sem a ferramenta, registre a falta como risco aceito.

**Prova**: o comando do filho sai de uma função pura, testada (ambiente sem o segredo, limites
presentes); arquivo acima do teto é recusado antes do parse; arquivo que estoura o limite mata o
filho e vira erro tratado, não traceback.

### 2. Banco e arquivos com dado sensível criados com a permissão padrão (3 de 4)

`sqlite3.connect(caminho)` cria o arquivo com `0644`, e cópias brutas (OFX, PDF baixado) vão
para uma pasta solta com a mesma permissão. Só uma execução fez `touch(mode=0o600)` antes de
conectar, e nenhuma corrigiu um arquivo que já existia aberto.

**Faça**: `os.umask(0o077)` no ponto de entrada, antes de criar qualquer arquivo; o banco e a
pasta de dados criados só para o dono (`0600`, `0700`); arquivo que já existe com permissão
aberta é corrigido ou recusado, nunca usado em silêncio. O SQLite cria o `-wal` e o `-journal`
com a permissão do banco. Permissão fecha o degrau 1, não o ladrão de dados que roda com o seu
UID (degrau 3); para o arquivo que sai da máquina (backup, sincronização), criptografia em repouso.

**Prova**: teste que cria o banco num diretório temporário e confere `stat` igual a `0600`, e
outro que parte de um arquivo `0644` e espera a correção ou a recusa.

### 3. Navegador sem sandbox por padrão de biblioteca (2 de 2)

Nenhum agente escreveu `--no-sandbox`. O Playwright põe a flag sozinho: `chromium_sandbox` vem
`False` por omissão, e sem ela o Chromium roda com `--no-sandbox`. Num caso o agente viu a flag
no `ps` e seguiu em frente. Uma regra que procura a flag no código não acha nada.

**Faça**: `chromium_sandbox=True` explícito em todo `launch` e `launch_persistent_context`.
Depuração remota pelo pipe (o padrão do Playwright), nunca `--remote-debugging-port` fixa nem
`--remote-allow-origins=*`, nem como "modo de teste". Se o navegador não sobe com sandbox, pare e
pergunte: desligar é decisão da pessoa, com o risco no ADR.

**Prova**: com o navegador aberto, ler o `cmdline` dos processos descendentes e reprovar
`--no-sandbox`, `--remote-allow-origins` e porta de depuração fixa. **Confira o processo vivo,
não o código**: o padrão da biblioteca liga o atalho sem estar escrito. Vale para qualquer
biblioteca que sobe outro programa.

### 4. Senha por variável de ambiente, ensinada no README (2 de 6: as duas que tinham senha de PDF)

A senha do PDF chega por `os.environ`, e o README ensina `APP_SENHA=... comando`, que grava a
senha no histórico do shell e a deixa em `/proc/<pid>/environ` para todo processo do mesmo
usuário. Uma execução ainda sugeriu "parte do CPF" como senha.

**Faça**, para ferramenta local que a pessoa roda no terminal:
- chaveiro do sistema com o backend escolhido no código, recusando o `PlaintextKeyring` do
  `keyrings.alt` (o `keyringrc.cfg` da máquina pode apontar para ele); ou
- pergunta sem eco (`getpass`) quando falta o segredo; ou
- arquivo `0600` cujo caminho vem da config.

Nunca segredo em argumento de linha de comando. Variável de ambiente só quando a plataforma a
injeta (gerenciador de segredo do CI, `LoadCredential` do systemd, o servidor do provedor),
nunca digitada no shell. Documentação nunca mostra segredo na linha de comando nem sugere segredo
adivinhável. Declare o risco que sobra: o Secret Service destravado é legível por qualquer
processo da sessão (degrau 3).

**Prova**: `rg` no README e na documentação por `NOME_COM_SENHA_OU_TOKEN=valor` em exemplo de
comando; teste que a CLI não aceita segredo como opção; teste que o backend do chaveiro em uso
não é de texto puro.

## Vistos uma vez, ainda fora da lista

Registrados na medição, mas não contados (uma ocorrência só). Confira quando aparecerem; entram
na lista se uma nova medição os repetir.

- Cópia bruta do dado guardada para sempre (o OFX inteiro num BLOB, uma pasta por mês de
  extratos): mais dado em repouso sem que ninguém peça.
- Banco criado na pasta corrente por padrão: o lugar do dado depende de onde o comando roda.
- Porta de depuração remota aberta como mecanismo de teste: só a trava em localhost separa o
  teste da produção.

## Cada proteção com a sua prova

Proteção sem teste é promessa. Toda mitigação escolhida entra no portão do projeto como teste ou
conferência que reprova (fitness function, na arquitetura-ai-first), e as do piso estão prontas
em `references/provas.md`. Para as do degrau 3, escreva a prova junto com o código: a queda de
privilégio testa que `setuid(0)` falha depois dela; a migração para banco criptografado confere
um hash do conteúdo antes, depois e no backup restaurado; o backup só conta depois de
restaurado e conferido.

## Regras invioláveis para o agente

1. **Não declarar pronto** app que toca segredo, dado sensível, navegador logado ou arquivo de
   fora sem o modelo de ameaça escrito e as provas do piso verdes.
2. **Nunca desligar** sandbox, TLS, permissão ou limite para fazer funcionar. Se não sobe com a
   proteção, relatar e perguntar.
3. **Conferir o efeito, não a intenção**: o modo do arquivo criado, o `cmdline` do processo vivo,
   o ambiente do processo filho. Padrão de biblioteca liga atalho que o código não mostra.
4. **Documentação não ensina atalho**: nenhum exemplo com segredo na linha de comando, nenhum
   segredo adivinhável sugerido.
5. **O risco aceito tem dono**: o que fica de fora vai para o ADR, por atacante, com a decisão da
   pessoa. O agente não aceita risco em nome dela.

## Limites desta skill

- Medida em app local de uma pessoa, com Python, duas execuções por pedido e um modelo só.
  Serviço com vários usuários (autenticação, autorização, sessão web) não foi medido aqui:
  aplique a regra zero e não presuma que a lista cobre.
- Fora do escopo: pentest, criptografia inventada, conformidade (LGPD) e endurecimento do sistema
  operacional.
- A medição desta skill respondeu se ela **preserva** algo que falta. Se ela **acrescenta**, isto
  é, se com ela instalada os atalhos somem, é a próxima medição, com o mesmo protocolo.

## Referências

| Arquivo | Ler quando |
|---|---|
| `references/provas.md` | Escrever ou conferir a correção de um dos quatro atalhos |
| `references/medicao.md` | Medir de novo, contestar um número ou acrescentar atalho à lista |
