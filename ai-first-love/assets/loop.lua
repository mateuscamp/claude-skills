-- Esboço da skill ai-first-love para platform/loop.lua: o love.run do projeto, a partir do padrão
-- de love:src/modules/love/callbacks.lua:168-206@b7daef0. NUNCA RODOU NO LÖVE: só carrega
-- (loadfile) em LuaJIT 2.1.1791988261 e Lua 5.5.1. Fica fora do LuaLS até o overlay do projeto
-- anotar setModalDrawCallback e parsedGameArguments (a 11.5 não os tem; armadilhas, LuaLS).
--
-- A ordem do quadro é a regra:
--   robô (lê a lista apresentada e empurra o toque) → pump → handlers → update (relógio,
--   gravação, orquestração, build da lista nova) → draw → present;
-- só depois do present a lista nova vale para o toque e para o robô. O robô que roda no update
-- empurra contra uma lista que a tela ainda não mostrou.
--
-- O app é Lua puro de scene/, com teste na suíte: robot_step (escolhe o alvo pelo id na lista
-- apresentada e devolve o evento com a tupla inteira, ou nil), clock_step (dt fixo no robô; o
-- replay usa o dt gravado (no jogo, o real com teto de 1/30 s); 0 no quadro da volta), frame
-- (devolve a PresentedList nova) e quit_code (0 só depois do FIM do plano; quit sem FIM, como o
-- SIGTERM do prazo, devolve um código próprio; "restart" passa como veio).
local render = require("platform.render")

local M = {}

---@param app table
function M.install(app)
	local presented = nil -- a lista que está na tela: toque, robô e desenho modal leem esta

	-- Desenha uma lista; nada mais chama love.graphics para desenhar. Devolve se a lista passa a
	-- ser a apresentada. Sem vídeo (<PROJETO>_VIDEO=nenhum, assets/conf.lua) love.graphics é nil:
	-- não há tela, a lista do quadro vale como apresentada para o robô e o toque, e amostra de
	-- pixel e xdotool não rodam ali. Com gráficos e sem janela ativa (antes do setMode do
	-- love.load, ou em segundo plano), a apresentada segue a de antes.
	local function draw(list)
		local g = love.graphics
		if not g then return true end
		if not g.isActive() then return false end
		g.origin()
		g.clear(g.getBackgroundColor())
		render.draw(list)
		g.present()
		return true
	end

	function app.presented() return presented end

	function love.run()
		if love.load then love.load(love.parsedGameArguments, love.rawGameArguments) end
		love.timer.step()
		-- Live-resize: o SDL chama isto de dentro do pump. Só redesenha a apresentada e não devolve
		-- nada (valor devolvido vira quit); sem ele, o boot registra o laço inteiro, reentrante.
		love.event.setModalDrawCallback(function()
			if presented then draw(presented) end
		end)
		return function()
			-- A tupla inteira (mousepressed: x, y, botão, istouch, presses), com false e não nil,
			-- e o ponto dentro da janela: o push não converte nem prende a coordenada.
			local ev = app.robot_step(presented)
			if ev then love.event.push(ev[1], ev[2], ev[3], ev[4], ev[5], ev[6]) end
			love.event.pump()
			for name, a, b, c, d, e, f, g, h in love.event.poll() do
				if name == "quit" and (c or not love.quit or not love.quit()) then
					return app.quit_code(a), b
				end
				love.handlers[name](a, b, c, d, e, f, g, h)
			end
			local list = app.frame(app.clock_step(love.timer.step(), app.came_back()))
			if draw(list) then presented = list end
			love.timer.sleep(0.001)
		end
	end
end

return M
