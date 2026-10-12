-- Fatos da partida: a linha `<PROJETO> <FATO> k=v` e o arquivo que a guarda.
--
-- Modelo da skill ai-first-defold (veio do CampCrawler). Adapte APP_ID e TAG; a
-- cena chama format() no seu log(), open() no init quando não há robô, e fecha o
-- arquivo no final.
--
-- O console do editor some quando ele fecha, e o `log.txt` do motor
-- (`project.write_log_file`) é regravado a cada abertura. O arquivo de partida é o
-- histórico: um por abertura do jogo, na pasta de save, com toda linha de fato
-- gravada e descarregada na hora, para sobreviver a um processo encerrado à força.
local M = {}

M.APP_ID = "<projeto>"
M.TAG = "<PROJETO>"

-- Uma linha por fato verificável, com campos em ordem alfabética, estável.
function M.format(kind, fields)
	local keys = {}
	for key in pairs(fields or {}) do keys[#keys + 1] = key end
	table.sort(keys)
	local parts = { M.TAG, kind }
	for _, key in ipairs(keys) do parts[#parts + 1] = key .. "=" .. tostring(fields[key]) end
	return table.concat(parts, " ")
end

-- Segundos com uma casa, para campos `segundos=`.
function M.seconds(value)
	return string.format("%.1f", value)
end

-- Lista separada por vírgula, ou `empty` quando vazia (`lideres=nenhum`).
function M.list(items, empty)
	if #items == 0 then return empty end
	return table.concat(items, ",")
end

-- Erro de Lua em tempo de execução também vai para o arquivo, com o traceback:
-- é o que mais importa ler depois e o que o console do editor perde ao fechar. O
-- motor continua imprimindo o erro no console (ERROR:SCRIPT); o handler só copia.
local function watch_errors(file)
	sys.set_error_handler(function(source, message, traceback)
		local text = string.format(M.TAG .. " ERRO fonte=%s\n%s\n%s", tostring(source), tostring(message),
			tostring(traceback))
		file:write(text, "\n")
		file:flush()
	end)
end

-- Abre o arquivo da partida que começa em `stamp` (texto de data). Devolve o
-- arquivo e o caminho, ou nil, o caminho e o motivo quando não abre: a cena diz
-- isso no log em vez de parar o jogo, que continua jogável sem o arquivo.
function M.open(stamp)
	local path = sys.get_save_file(M.APP_ID, "partida-" .. stamp .. ".log")
	local file, problem = io.open(path, "w")
	if not file then return nil, path, problem end
	watch_errors(file)
	return file, path
end

return M
