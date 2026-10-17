-- Esboço da skill ai-first-lua para o conf.lua do projeto. NUNCA RODOU NO LÖVE: só carrega
-- (loadfile) em LuaJIT 2.1.1791988261 e Lua 5.5.1. Cada linha existe por uma armadilha de
-- references/armadilhas.md (o item vai no comentário). O conf.lua roda antes do main.lua.

-- Saída, erro e log: sem buffer de linha, o SIGKILL leva a cauda do log e o próprio erro.
io.stdout:setvbuf("line")

-- O conf.lua não lê arg: o parser de chaves, no love.load, é o único leitor. As duas variáveis
-- que o executor das passadas põe (na lista branca do ambiente) são a única leitura de ambiente
-- fora dele, por nome no teste estático; no jogo do autor, nenhuma está posta.
local PASS = os.getenv("<PROJETO>_PASSADA") == "1"
local VIDEO = os.getenv("<PROJETO>_VIDEO") -- o --video da passada: nenhum, gl ou x11
local default_handler = love.errorhandler -- o padrão já existe: o boot carrega callbacks.lua antes

-- Saída, erro e log: o handler definido no main.lua chega tarde; o do conf.lua pega também o
-- erro do próprio conf.lua, que o boot relança depois de carregar os módulos.
function love.errorhandler(msg)
	local log = package.loaded["platform.match_log"] -- achado tarde: pode não ter carregado
	if log then log.error(msg) end
	if PASS then
		print((debug.traceback("Error: " .. tostring(msg), 2):gsub("\n[^\n]+$", "")))
		return function() return 3 end -- código próprio: o portão separa erro de Lua de quit
	end
	return default_handler(msg) -- <decisão do autor: tela de erro ou seguir com a linha no log>
end

-- Saída, erro e log: ligada aqui, antes de qualquer API deprecada. Ligada depois, a deprecada já
-- usada duas vezes nunca imprime, e a caixa na tela mostra todas.
if PASS then love.setDeprecationOutput(true) end

-- Fronteira: valor de fora estoura com o recebido (depois do handler, que o pega).
if VIDEO ~= nil and VIDEO ~= "nenhum" and VIDEO ~= "gl" and VIDEO ~= "x11" then
	error(("<PROJETO>_VIDEO=%s; esperado nenhum, gl ou x11"):format(VIDEO))
end

function love.conf(t)
	t.identity = "<projeto>" -- Arquivos e save: sem ele, um save por worktree
	t.appendidentity = true -- Arquivos e save: o código vem antes da save, que não o sombreia
	t.version = "12.0" -- Lançamento: outro valor abre a caixa modal "Compatibility Warning"
	-- Laço, tempo e janela: sem t.window o boot não abre janela. A plataforma a abre no
	-- love.load, depois do parser, com o que as chaves pedirem:
	--   love.window.setMode(w, h, { resizable = true, vsync = PASS and 0 or 1 })
	-- (resizable vem false; vsync 0 na passada: tempo é quadro, sem esperar o monitor). Nos
	-- mesmos flags, usedpiscale: uma unidade só ou DPI com conversão, decisão do autor.
	t.window = false
	-- Sem vídeo, nem janela nem gráficos (love.window e love.graphics nil): PNG e fonte por
	-- love.image e love.font, e o laço não desenha (assets/loop.lua). Pela palavra graphics, o
	-- conf.lua entra no DESENHO_SO_EM da fronteira.
	if VIDEO == "nenhum" then
		t.modules.window = false
		t.modules.graphics = false
	end
	-- t.graphics.renderers (nunca t.renderers, deprecado): decisão do autor (Laço, tempo e janela)
end
