local CAPTION_PREFIX = "表："
local CAPTION_STYLE = "表题"

function Blocks(blocks)
  local result = {}
  local i = 1

  while i <= #blocks do
    local block = blocks[i]

    if block.t == "Para" and i < #blocks and blocks[i + 1].t == "Table" then
      local text = pandoc.utils.stringify(block)
      if text:sub(1, #CAPTION_PREFIX) == CAPTION_PREFIX then
        local caption_text = text:sub(#CAPTION_PREFIX + 1):gsub("^%s+", ""):gsub("%s+$", "")
        local caption_para = pandoc.Para({ pandoc.Str(caption_text) })
        local caption = pandoc.Div({ caption_para }, pandoc.Attr("", {}, { ["custom-style"] = CAPTION_STYLE }))
        table.insert(result, caption)
        i = i + 1
      else
        table.insert(result, block)
      end
    else
      table.insert(result, block)
    end

    i = i + 1
  end

  return result
end
