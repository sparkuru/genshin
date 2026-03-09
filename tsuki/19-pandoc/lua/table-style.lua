-- Apply custom table style (borders, width, alignment from reference.docx)

local TABLE_STYLE = "表格整体样式"

function Table(el)
  el.attr = el.attr or pandoc.Attr()
  el.attr.attributes = el.attr.attributes or {}
  el.attr.attributes["custom-style"] = TABLE_STYLE
  return el
end
