local banned_character = "兺"

local function filter(input, _env)
    for cand in input:iter() do
        if string.find(cand.text, banned_character, 1, true) == nil then
            yield(cand)
        end
    end
end

return filter
