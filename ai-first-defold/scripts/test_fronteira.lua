-- Fitness function da fronteira do domínio: nenhum arquivo das pastas de regra usa
-- a engine, o relógio ou o sorteio global. É o que permite testar a regra sem subir
-- o Defold — e uma regra lembrada vira mecanismo quando um teste reprova.
--
-- Copiado da skill ai-first-defold. Ajuste PASTAS e PERMITIDOS ao projeto.
local PASTAS = { "modules" }

-- Exceções EXATAS, com motivo: { arquivo = { "padrão", ... } }.
local PERMITIDOS = {}

local PROIBIDO = {
	{ "%f[%w_]go%.", "go.* (game object)" },
	{ "%f[%w_]gui%.", "gui.*" },
	{ "%f[%w_]msg%.", "msg.*" },
	{ "%f[%w_]sys%.", "sys.*" },
	{ "%f[%w_]vmath%.", "vmath.*" },
	{ "%f[%w_]timer%.", "timer.*" },
	{ "%f[%w_]sound%.", "sound.*" },
	{ "%f[%w_]factory%.", "factory.*" },
	{ "%f[%w_]render%.", "render.*" },
	{ "%f[%w_]hash%(", "hash()" },
	{ "%f[%w_]math%.random", "math.random (sorteio global; use o gerador com semente)" },
	{ "%f[%w_]math%.randomseed", "math.randomseed" },
	{ "%f[%w_]os%.time", "os.time (relógio)" },
	{ "%f[%w_]os%.clock", "os.clock (relógio)" },
	{ "%f[%w_]socket%.", "socket.*" },
}

local function listar(pasta)
	local arquivos = {}
	local handle = io.popen('find "' .. pasta .. '" -name "*.lua" -type f 2>/dev/null | sort')
	if not handle then error("io.popen indisponível: a fronteira não consegue listar " .. pasta, 0) end
	for linha in handle:lines() do arquivos[#arquivos + 1] = linha end
	handle:close()
	return arquivos
end

-- Tira comentários e strings: "gui." dentro de uma mensagem de erro não é uso.
local function codigo(conteudo)
	-- Comentário de bloco some, mas as quebras de linha ficam: o erro cita a linha certa.
	conteudo = conteudo:gsub("%-%-%[(=*)%[(.-)%]%1%]", function(_, corpo)
		return (corpo:gsub("[^\n]", ""))
	end)
	conteudo = conteudo:gsub("%-%-[^\n]*", "")
	conteudo = conteudo:gsub('"[^"\n]*"', '""'):gsub("'[^'\n]*'", "''")
	return conteudo
end

local function permitido(arquivo, padrao)
	for _, p in ipairs(PERMITIDOS[arquivo] or {}) do
		if p == padrao then return true end
	end
	return false
end

return {
	{ "domínio não usa engine, relógio nem sorteio global", function()
		local total = 0
		for _, pasta in ipairs(PASTAS) do
			for _, arquivo in ipairs(listar(pasta)) do
				total = total + 1
				local f = assert(io.open(arquivo, "rb"))
				local texto = codigo(f:read("*a"))
				f:close()
				local numero = 0
				for linha in (texto .. "\n"):gmatch("(.-)\n") do
					numero = numero + 1
					for _, regra in ipairs(PROIBIDO) do
						if linha:find(regra[1]) and not permitido(arquivo, regra[1]) then
							error(string.format("%s:%d usa %s — a regra não pode depender da engine", arquivo,
								numero, regra[2]), 0)
						end
					end
				end
			end
		end
		-- Zero arquivos lidos não é aprovação: a pasta mudou de nome e ninguém viu.
		assert(total > 0, "nenhum .lua encontrado em " .. table.concat(PASTAS, ", "))
	end },
}
