-- Executor da suíte de domínio, sem engine (LuaJIT ou Lua 5.x).
--
--   luajit tests/run.lua tests/test_*.lua
--
-- Cada arquivo devolve uma lista de { "nome", função }. Arquivo que não carrega
-- conta como FALHA, e não é pulado: teste ignorado em silêncio é o defeito mais
-- caro de um executor. Sai com 1 em qualquer falha. Copiado da skill ai-first-defold.
package.path = "./?.lua;" .. package.path

local files = { ... }
if #files == 0 then
	print("nenhum arquivo de teste recebido: esperado tests/run.lua tests/test_*.lua")
	os.exit(2)
end

local passed, failed = 0, 0
for _, path in ipairs(files) do
	local module = path:gsub("%.lua$", ""):gsub("/", ".")
	local ok, suite = pcall(require, module)
	if not ok or type(suite) ~= "table" or #suite == 0 then
		failed = failed + 1
		print("FALHA ao carregar " .. path .. ": " .. tostring(ok and "nenhum teste devolvido" or suite))
	else
		for _, case in ipairs(suite) do
			local success, err = pcall(case[2])
			if success then
				passed = passed + 1
			else
				failed = failed + 1
				print(string.format("FALHA %s :: %s\n  %s", path, case[1], tostring(err)))
			end
		end
	end
end

print(string.format("%s: %d testes, %d falhas", _VERSION .. (jit and (" / " .. jit.version) or ""),
	passed + failed, failed))
os.exit(failed == 0 and 0 or 1)
