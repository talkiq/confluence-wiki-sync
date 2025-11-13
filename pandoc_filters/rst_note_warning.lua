-- reStructuredText has a concept of notes and warnings.
-- Confluence has info, tip, note, and warning macros
-- But pandoc doesn't do the translation between the two
-- See https://github.com/jgm/pandoc/issues/10561
-- This filter works around the problem
-- A Confluence warning looks like an error and a note looks like a warning, so we
-- instead map note to info and warning to note
function Div(el)
  if el.classes:includes("note") then
    table.remove(el.content, 1) -- remove title
    table.insert(el.content, 1, pandoc.RawBlock("jira", "{info}"))
    table.insert(el.content, pandoc.RawBlock("jira", "{info}"))
    return el
  end

  if el.classes:includes("warning") then
    table.remove(el.content, 1) -- remove title
    table.insert(el.content, 1, pandoc.RawBlock("jira", "{note}"))
    table.insert(el.content, pandoc.RawBlock("jira", "{note}"))
    return el
  end
end
