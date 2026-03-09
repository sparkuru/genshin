local utf8 = require("utf8")

local HEADER_STYLE = "表格表头样式"
local CELL_STYLE_SHORT = "表格单元格正文样式 A"
local CELL_STYLE_LONG = "表格单元格正文样式 B"
local CHAR_THRESHOLD = 30

local function char_count(blocks)
  local count = 0
  for _, block in ipairs(blocks) do
    if block.t == "Para" or block.t == "Plain" then
      for _, inline in ipairs(block.content) do
        if inline.t == "Str" then
          count = count + (utf8.len(inline.text) or #inline.text)
        end
      end
    end
  end
  return count
end

local function wrap_blocks_with_style(blocks, style_name)
  local styled = {}
  local div_attr = pandoc.Attr("", {}, { ["custom-style"] = style_name })
  for _, block in ipairs(blocks) do
    if block.t == "Para" or block.t == "Plain" then
      table.insert(styled, pandoc.Div({ block }, div_attr))
    else
      table.insert(styled, block)
    end
  end
  return styled
end

function Table(el)
  if el.head and el.head.rows and #el.head.rows > 0 then
    for _, cell in ipairs(el.head.rows[1].cells) do
      cell.contents = wrap_blocks_with_style(cell.contents, HEADER_STYLE)
    end
  end

  if el.bodies then
    for _, body in ipairs(el.bodies) do
      if body.body then
        for _, row in ipairs(body.body) do
          for _, cell in ipairs(row.cells) do
            local n = char_count(cell.contents)
            local style_name = (n > CHAR_THRESHOLD) and CELL_STYLE_LONG or CELL_STYLE_SHORT
            cell.contents = wrap_blocks_with_style(cell.contents, style_name)
          end
        end
      end
    end
  end

  return el
end
