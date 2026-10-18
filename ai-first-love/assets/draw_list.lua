-- Esboço da skill ai-first-love para scene/draw_list.lua: a forma do item da lista de desenho,
-- o construtor que valida na entrada, o hit-test e a ação do toque. Copie e adapte: o manifesto
-- vem do gerador de assets; as constantes de layer e os campos do target são do projeto. Lua
-- puro: a vista monta, a plataforma desenha, o toque consulta.
-- Provado em LuaJIT 2.1.1791988261, Lua 5.4.9 e Lua 5.5.1, e limpo no LuaLS 3.18.0 (um campo
-- inventado no uso vira undefined-field).
---@class DrawTarget a intenção do toque, como dado: x e y de tela não circulam
---@field action string o que o adaptador entrega ("explore", "close_review")
---@field cell_x? integer campo do projeto: a célula na grade, nunca o ponto na tela
---@field cell_y? integer

---@class DrawItem
---@field id string identidade no domínio: "cell_4_4", "soldier_2", "hud_turn"
---@field kind "rect"|"image"|"text"
---@field layer integer constante nomeada do projeto (LAYER.HUD); string ordenaria pelo alfabeto
---@field seq integer ordem de inserção, dada por add
---@field x number retângulo em coordenadas de tela, na unidade da entrada
---@field y number
---@field w number
---@field h number
---@field color number[] { r, g, b, a }, cada um de 0 a 1 (o 0..255 de antes da 11.0 estoura aqui)
---@field image? string nome no manifesto do atlas
---@field text? string
---@field font_role? string papel da fonte, não o arquivo
---@field size_px? number tamanho do texto, na unidade da lista
---@field align? "left"|"center"|"right"
---@field wrap_w? number largura de quebra
---@field role string
---@field state? string estado de apresentação que uma invariante lê
---@field hit? boolean aceita toque; com target nil, só barra o toque (modal)
---@field target? DrawTarget o que o toque aciona
---@field probe? boolean a amostra de pixel confere este item

---@class PresentedList a lista do último quadro desenhado, a que estava na tela
---@field sorted DrawItem[] em ordem de desenho (layer, seq)
---@field w number a janela para a qual a vista montou, na unidade da lista
---@field h number

---@class InputAction o que sai do toque: a coordenada morre no hit-test
---@field kind "touch"
---@field id string o item tocado
---@field target? DrawTarget
local M = {}
local KINDS = { rect = true, image = true, text = true }
local ALIGNS = { left = true, center = true, right = true }

-- A forma em ordem fixa (a mensagem não depende da ordem do pairs): campo e tipo, e "?" no fim
-- é opcional. Campo fora dela estoura: o size que sobrou de antes do size_px desenharia calado.
local FIELDS = {
	{ "id", "string" }, { "kind", "string" }, { "layer", "integer" }, { "x", "number" },
	{ "y", "number" }, { "w", "number" }, { "h", "number" }, { "color", "table" },
	{ "role", "string" }, { "image", "string?" }, { "text", "string?" },
	{ "font_role", "string?" }, { "size_px", "number?" }, { "align", "string?" },
	{ "wrap_w", "number?" }, { "state", "string?" }, { "hit", "boolean?" },
	{ "target", "table?" }, { "probe", "boolean?" },
}
local KNOWN = {}
for i = 1, #FIELDS do KNOWN[FIELDS[i][1]] = true end

local function matches(value, want)
	local optional = want:sub(-1) == "?"
	if value == nil then return optional end
	local base = optional and want:sub(1, -2) or want
	if base == "integer" then return type(value) == "number" and math.floor(value) == value end
	return type(value) == base
end

local function check_form(item)
	local extra = {}
	for name in pairs(item) do
		if not KNOWN[name] then extra[#extra + 1] = tostring(name) end
	end
	table.sort(extra)
	if #extra > 0 then
		error(("campo %s em %s fora da forma de DrawItem (seq é dado por add)"):format(
			table.concat(extra, ", "), tostring(item.id)), 3)
	end
	for i = 1, #FIELDS do
		local name, want = FIELDS[i][1], FIELDS[i][2]
		if not matches(item[name], want) then
			error(("%s de %s: %s (%s); esperado %s"):format(name, tostring(item.id),
				tostring(item[name]), type(item[name]), want), 3)
		end
	end
end

local function color_text(c)
	local parts = {}
	for i = 1, #c do parts[i] = tostring(c[i]) end
	return "{ " .. table.concat(parts, ", ") .. " }"
end

local function check_color(item)
	local c = item.color
	local ok = #c == 4
	for i = 1, 4 do
		ok = ok and type(c[i]) == "number" and c[i] >= 0 and c[i] <= 1
	end
	if not ok then
		error(("cor de %s: %s; esperado { r, g, b, a } de 0 a 1"):format(item.id, color_text(c)), 3)
	end
end

-- O target é a intenção (action e os campos do projeto); o ponto da tela fica no hit-test.
local function check_target(item)
	local t = item.target
	if t == nil then return end
	if type(t.action) ~= "string" or t.x ~= nil or t.y ~= nil then
		error(("target de %s: action=%s x=%s y=%s; esperado { action = <string>, ... }, sem x nem y")
			:format(item.id, tostring(t.action), tostring(t.x), tostring(t.y)), 3)
	end
end

-- Valida na entrada e dá a ordem de inserção; erro com o recebido, na linha de quem chamou.
---@param list { items: DrawItem[], by_id: table<string, DrawItem>, manifest: table<string, table> }
---@param item table os campos de DrawItem, sem seq
---@return DrawItem
function M.add(list, item)
	check_form(item)
	if not KINDS[item.kind] then
		error(("kind %s em %s; esperado rect, image ou text"):format(item.kind, item.id), 2)
	end
	if item.align ~= nil and not ALIGNS[item.align] then
		error(("align %s em %s; esperado left, center ou right"):format(item.align, item.id), 2)
	end
	if list.by_id[item.id] then error(("id repetido: %s"):format(item.id), 2) end
	if item.kind == "image" and not list.manifest[item.image] then
		error(("imagem %s de %s fora do manifesto"):format(tostring(item.image), item.id), 2)
	end
	check_color(item)
	check_target(item)
	item.seq = #list.items + 1
	list.items[item.seq] = item
	list.by_id[item.id] = item
	return item
end

-- A lista que o renderizador desenha e que, depois do present, o toque consulta. O table.sort
-- não é estável: a ordem é (layer, seq), e seq é único.
---@param list { items: DrawItem[] }
---@param w number
---@param h number
---@return PresentedList
function M.present(list, w, h)
	local sorted = {}
	for i = 1, #list.items do sorted[i] = list.items[i] end
	table.sort(sorted, function(a, b)
		if a.layer ~= b.layer then return a.layer < b.layer end
		return a.seq < b.seq
	end)
	return { sorted = sorted, w = w, h = h }
end

-- Item de cima com hit que contém o ponto. Item invisível (alfa 0) não pega toque, nem o que
-- tem o centro fora da janela (o robô toca o centro). Alvo em parte fora da janela, e o toque
-- que atravessa ou não um item sem hit, são do autor: a tela os declara.
---@param presented PresentedList
---@param px number
---@param py number
---@return DrawItem?
function M.hit(presented, px, py)
	local sorted = presented.sorted
	for i = #sorted, 1, -1 do
		local it = sorted[i]
		local cx, cy = it.x + it.w / 2, it.y + it.h / 2
		local seen = it.color[4] > 0 and cx >= 0 and cx < presented.w and cy >= 0 and cy < presented.h
		if it.hit and seen and px >= it.x and px < it.x + it.w and py >= it.y and py < it.y + it.h then
			return it
		end
	end
	return nil
end

-- Daqui em diante só circula a ação, nunca x e y: o target leva a intenção, não o ponto.
---@param presented PresentedList
---@param px number
---@param py number
---@return InputAction?
function M.touch(presented, px, py)
	local it = M.hit(presented, px, py)
	if not it then return nil end
	return { kind = "touch", id = it.id, target = it.target }
end

return M
