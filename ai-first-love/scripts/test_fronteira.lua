-- Fitness function das fronteiras de um jogo em LÖVE: domínio e vistas são Lua puro, e só o
-- renderizador desenha.
--
-- Três fronteiras: dois grupos de Lua puro (GRUPOS), cada um com as suas pastas, e o desenho:
--   1. domínio (modules/): a regra não conhece o LÖVE, o relógio, o sorteio global nem o
--      que é exclusivo do LuaJIT. É o que permite testá-la sem motor, em LuaJIT e em Lua 5.x.
--   2. vistas (scene/): a vista devolve a lista de desenho e também não conhece o LÖVE; só
--      platform/ chama love.graphics. Sem este grupo, um love.graphics.print numa vista volta
--      a espalhar o desenho, e o agente perde a lista que ele lê para achar o erro visual.
--   3. desenho: a palavra graphics só aparece nos arquivos de DESENHO_SO_EM (o renderizador da
--      lista, o laço que o chama e o conf.lua), em todo .lua fora de tests/, tools/ e dist/,
--      main.lua inclusive. Sem ela, um love.draw no main.lua ou um segundo arquivo de platform/
--      que desenha (até por local L = love) passavam. Worktrees aninhadas, build/ e .git/ também
--      ficam fora (FORA_DO_JOGO): no checkout principal, o platform/render.lua da worktree do
--      Claude Code (.claude/worktrees/<nome>/) e o do .love desempacotado em build/ têm outro
--      caminho relativo, não casam com DESENHO_SO_EM e davam vermelho sem defeito nenhum.
--
-- A palavra "love" inteira pega love.graphics, local L = love e _G.love; o prefixo "love%."
-- deixava passar o local L = love. Os requires são lidos com o nome literal e conferidos contra
-- a lista de PERMISSÃO do grupo (requires_permitidos): a de proibição deixava a vista requerer
-- um glue.lua da raiz que desenha. Require com nome calculado reprova, porque a varredura não
-- veria o módulo, e o literal precisa ser o argumento inteiro: require("plat" .. "form.x")
-- reprova.
--
-- As pastas são listadas com find -L: o domínio emprestado por symlink (no porte) é varrido;
-- sem o -L, a fronteira reprovava a árvore limpa ("nenhum .lua encontrado").
--
-- O que ela não vê, por escrito: nome montado por concatenação ou índice de string
-- (L["gra" .. "phics"]) num arquivo de platform/, e o que a função injetada pela plataforma (o
-- medidor de texto) faz por dentro.
--
-- Adaptado da skill ai-first-love (o original, de Defold, é o da ai-first-defold). Ajuste
-- GRUPOS, DESENHO_SO_EM e PERMITIDOS ao projeto. Roda em LuaJIT e em Lua 5.x, pelo
-- tests/run.lua, a partir da raiz do projeto.

-- Proibido em todo arquivo de Lua puro. id é o rótulo que a exceção cita.
local PURO = {
	{ id = "love", padrao = "%f[%w_]love%f[^%w_]", diz = "a palavra love (love.*, local L = love)" },
	{ id = "jit", padrao = "%f[%w_]jit%f[^%w_]", diz = "jit (exclusivo do LuaJIT)" },
	{ id = "ffi", padrao = "%f[%w_]ffi%f[^%w_]", diz = "ffi (exclusivo do LuaJIT)" },
	{ id = "bit", padrao = "%f[%w_]bit%.", diz = "bit.* (global do LuaJIT; o Lua 5.x não tem)" },
	{ id = "_G", padrao = "%f[%w_]_G%f[^%w_]", diz = "_G (global por nome escapa da varredura)" },
	{ id = "getfenv", padrao = "%f[%w_][gs]etfenv%f[^%w_]", diz = "getfenv/setfenv (ambiente por nome)" },
	-- load só como chamada solta: M.load( e self:load( são funções do projeto.
	{ id = "load", padroes = { "^%s*load%s*%(", "[^%.:%w_]load%s*%(", "%f[%w_]loadstring%f[^%w_]",
		"%f[%w_]loadfile%f[^%w_]" }, diz = "load/loadstring/loadfile (código montado)" },
	{ id = "dofile", padrao = "%f[%w_]dofile%f[^%w_]", diz = "dofile" },
	{ id = "package", padrao = "%f[%w_]package%.", diz = "package.* (módulo por nome escapa)" },
	{ id = "debug", padrao = "%f[%w_]debug%.", diz = "debug.*" },
	{ id = "io", padrao = "%f[%w_]io%.", diz = "io.* (arquivo é da plataforma, que injeta a escrita)" },
	{ id = "math.random", padrao = "%f[%w_]math%.random", diz = "math.random (sorteio global; use o gerador com semente)" },
	{ id = "os.time", padrao = "%f[%w_]os%.time", diz = "os.time (relógio: o tempo entra como parâmetro)" },
	{ id = "os.clock", padrao = "%f[%w_]os%.clock", diz = "os.clock (relógio)" },
	{ id = "os.date", padrao = "%f[%w_]os%.date", diz = "os.date (relógio)" },
	{ id = "os.getenv", padrao = "%f[%w_]os%.getenv", diz = "os.getenv (configuração mora no parser de chaves)" },
}

local MODULOS_DO_LUAJIT = { "ffi", "bit", "jit" }

local GRUPOS = {
	{
		nome = "domínio",
		pastas = { "modules" },
		proibido = PURO,
		-- A regra não conhece cena nem plataforma: a dependência só desce.
		requires_permitidos = { "modules" },
	},
	{
		nome = "vistas",
		pastas = { "scene" },
		proibido = PURO,
		-- A vista que chama a plataforma desenha por fora da lista sem dizer "love".
		requires_permitidos = { "modules", "scene" },
	},
}

-- Só estes arquivos dizem graphics: o renderizador da lista, o laço que o chama e o conf.lua
-- (o do esboço desliga t.modules.graphics na passada sem vídeo; fora daqui, a árvore limpa
-- reprovava). As fontes (platform/fonts.lua) e a captura da amostra de pixel entram pelo nome,
-- no projeto.
local DESENHO_SO_EM = { ["platform/render.lua"] = true, ["platform/loop.lua"] = true, ["conf.lua"] = true }

-- Exceção EXATA: o arquivo, um trecho que a linha contém, o id da regra, o motivo e
-- quantas linhas ela cobre (1 se omitido). Reprova se cobrir outro número de linhas,
-- inclusive zero (a linha mudou e a exceção ficou órfã).
-- Ex.: { arquivo = "modules/x.lua", trecho = "...", regra = "io", motivo = "...", linhas = 1 }
local PERMITIDOS = {}

local function listar(pasta, fora)
	local arquivos = {}
	local handle = io.popen('find -L "' .. pasta .. '" -name "*.lua" -type f ' .. (fora or "")
		.. ' 2>/dev/null | sort')
	if not handle then error("io.popen indisponível: a fronteira não consegue listar " .. pasta, 0) end
	for linha in handle:lines() do arquivos[#arquivos + 1] = linha end
	handle:close()
	return arquivos
end

local function quebras(trecho)
	return (trecho:gsub("[^\n]", ""))
end

local function linha_em(fonte, posicao)
	return #quebras(fonte:sub(1, posicao)) + 1
end

-- Fim de uma string curta que abre em i (aspas c); devolve o índice da aspa ou da quebra.
local function fim_da_string(fonte, i, c)
	local j = i + 1
	while j <= #fonte do
		local d = fonte:sub(j, j)
		if d == "\\" then
			j = j + 2
		elseif d == c or d == "\n" then
			return j
		else
			j = j + 1
		end
	end
	return #fonte + 1
end

-- Nome do require, se a string que abre em i é o argumento literal de um require.
local function anota_require(fonte, i, corpo, requires)
	local antes = fonte:sub(math.max(1, i - 40), i - 1)
	if antes:find("%f[%w_]require%s*%(?%s*$") then
		requires[#requires + 1] = { linha = linha_em(fonte, i), nome = corpo }
	end
end

-- Tira comentários e troca cada string por "", mantendo as quebras de linha (o erro cita
-- a linha certa). "love." dentro de uma mensagem de erro não é uso. Devolve também os
-- requires com nome literal.
local function lexar(fonte)
	local saida, requires = {}, {}
	local i = 1
	while i <= #fonte do
		local s = fonte:find("[%-\"'%[]", i)
		if not s then
			saida[#saida + 1] = fonte:sub(i)
			break
		end
		saida[#saida + 1] = fonte:sub(i, s - 1)
		local c = fonte:sub(s, s)
		local nivel_bloco = fonte:match("^%-%-%[(=*)%[", s)
		local nivel_longa = fonte:match("^%[(=*)%[", s)
		if nivel_bloco then
			local _, fim = fonte:find("]" .. nivel_bloco .. "]", s + 4 + #nivel_bloco, true)
			fim = fim or #fonte
			saida[#saida + 1] = quebras(fonte:sub(s, fim))
			i = fim + 1
		elseif fonte:sub(s, s + 1) == "--" then
			i = fonte:find("\n", s, true) or (#fonte + 1)
		elseif c == '"' or c == "'" then
			local j = fim_da_string(fonte, s, c)
			local corpo = fonte:sub(s + 1, j - 1)
			anota_require(fonte, s, corpo, requires)
			saida[#saida + 1] = '""' .. quebras(corpo)
			i = (fonte:sub(j, j) == c) and (j + 1) or j
		elseif nivel_longa then
			local abre = s + 2 + #nivel_longa
			local _, fim = fonte:find("]" .. nivel_longa .. "]", abre, true)
			fim = fim or #fonte
			local corpo = fonte:sub(abre, fim - 2 - #nivel_longa)
			anota_require(fonte, s, corpo, requires)
			saida[#saida + 1] = '""' .. quebras(corpo)
			i = fim + 1
		else
			saida[#saida + 1] = c
			i = s + 1
		end
	end
	return table.concat(saida), requires
end

local function proibido_por_nome(nome, lista)
	for _, p in ipairs(lista) do
		if nome == p or nome:sub(1, #p + 1) == p .. "." or nome:sub(1, #p + 1) == p .. "/" then
			return p
		end
	end
	return nil
end

local function casa(linha, regra)
	if regra.padrao then return linha:find(regra.padrao) ~= nil end
	for _, p in ipairs(regra.padroes) do
		if linha:find(p) then return true end
	end
	return false
end

local function excecao(arquivo, original, regra)
	for _, e in ipairs(PERMITIDOS) do
		if e.arquivo == arquivo and e.regra == regra and original:find(e.trecho, 1, true) then
			e.cobertas = (e.cobertas or 0) + 1
			return true
		end
	end
	return false
end

local function confere_arquivo(arquivo, grupo, achados)
	local f = assert(io.open(arquivo, "rb"))
	local fonte = f:read("*a")
	f:close()
	local codigo, requires = lexar(fonte)
	local originais = {}
	for linha in (fonte .. "\n"):gmatch("(.-)\n") do originais[#originais + 1] = linha end
	local numero = 0
	for linha in (codigo .. "\n"):gmatch("(.-)\n") do
		numero = numero + 1
		for _, regra in ipairs(grupo.proibido) do
			if casa(linha, regra) and not excecao(arquivo, originais[numero] or "", regra.id) then
				achados[#achados + 1] = string.format("%s:%d usa %s", arquivo, numero, regra.diz)
			end
		end
		-- require literal vira require(""); o que sobra é nome calculado.
		local de = 1
		while true do
			local _, fim = linha:find("%f[%w_]require%f[^%w_]", de)
			if not fim then break end
			local resto = linha:sub(fim + 1)
			if not (resto:find('^%s*""') or resto:find('^%s*%(%s*""%s*%)'))
				and not excecao(arquivo, originais[numero] or "", "require") then
				achados[#achados + 1] = string.format("%s:%d usa require com nome calculado", arquivo, numero)
			end
			de = fim + 1
		end
	end
	for _, r in ipairs(requires) do
		local p = (not proibido_por_nome(r.nome, grupo.requires_permitidos)) and r.nome
		if p and not excecao(arquivo, originais[r.linha] or "", "require") then
			local motivo = proibido_por_nome(r.nome, MODULOS_DO_LUAJIT) and "exclusivo do LuaJIT"
				or ("fora de " .. table.concat(grupo.requires_permitidos, ", "))
			achados[#achados + 1] = string.format('%s:%d faz require("%s") (%s: %s)', arquivo, r.linha,
				r.nome, p, motivo)
		end
	end
end

local function confere_grupo(grupo, achados)
	local total = 0
	for _, pasta in ipairs(grupo.pastas) do
		for _, arquivo in ipairs(listar(pasta)) do
			total = total + 1
			confere_arquivo(arquivo, grupo, achados)
		end
	end
	-- Zero arquivos lidos não é aprovação: a pasta mudou de nome e ninguém viu.
	if total == 0 then
		achados[#achados + 1] = string.format("%s: nenhum .lua encontrado em %s", grupo.nome,
			table.concat(grupo.pastas, ", "))
	end
end

-- Pastas que não são o jogo desta árvore: testes, ferramentas, o que o empacotador gera, saída
-- de build, as worktrees aninhadas e o git. Por find, não por git ls-files: o arquivo novo
-- ainda sem git add (um platform/hud.lua que desenha) é varrido.
local FORA_DO_JOGO = { "tests", "tools", "dist", "build", ".claude", ".git" }

-- Todo .lua do jogo, fora de FORA_DO_JOGO.
local function confere_desenho(achados)
	local fora = {}
	for _, pasta in ipairs(FORA_DO_JOGO) do fora[#fora + 1] = '-not -path "./' .. pasta .. '/*"' end
	for _, caminho in ipairs(listar(".", table.concat(fora, " "))) do
		local arquivo = caminho:gsub("^%./", "")
		if not DESENHO_SO_EM[arquivo] then
			local f = assert(io.open(caminho, "rb"))
			local codigo = lexar(f:read("*a"))
			f:close()
			local numero = 0
			for linha in (codigo .. "\n"):gmatch("(.-)\n") do
				numero = numero + 1
				if linha:find("%f[%w_]graphics%f[^%w_]") then
					achados[#achados + 1] = string.format("%s:%d diz graphics fora do renderizador (DESENHO_SO_EM)",
						arquivo, numero)
				end
			end
		end
	end
end

local function confere_excecoes(achados)
	for _, e in ipairs(PERMITIDOS) do
		local esperado = e.linhas or 1
		if (e.cobertas or 0) ~= esperado then
			achados[#achados + 1] = string.format('exceção %s "%s" (%s) cobre %d linha(s), esperado %d',
				e.arquivo, e.trecho, e.regra, e.cobertas or 0, esperado)
		end
		e.cobertas = nil
	end
end

return {
	{ "domínio e vistas são Lua puro (sem love, LuaJIT, relógio nem sorteio) e só o renderizador desenha", function()
		local achados = {}
		for _, grupo in ipairs(GRUPOS) do confere_grupo(grupo, achados) end
		confere_desenho(achados)
		confere_excecoes(achados)
		if #achados > 0 then
			error(#achados .. " violação(ões) da fronteira:\n  " .. table.concat(achados, "\n  "), 0)
		end
	end },
}
