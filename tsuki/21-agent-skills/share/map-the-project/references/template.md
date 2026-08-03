# Module Template

Create a module only when an object class needs recurring discovery sources, mapping dimensions, or assessment cautions beyond the shared workflow. Do not create modules that merely rename the same process.

## Landing Location

- Create one Markdown file at `references/<module-name>.md`.
- Use lowercase hyphenated names.
- Register the module in `SKILL.md` under **Select a Module** with a one-sentence selection rule.
- Keep shared evidence rules, output structure, and stopping conditions in `SKILL.md`; keep object-specific material in the module.
- Keep module files one level beneath `references/`. Do not add README files or duplicate material across modules.

## Required Shape

Use this structure and replace every placeholder with object-specific instruction:

```markdown
# <Module Name> Module

Use this module for <object classes>. Focus on <decision-relevant orientation>.

## Discover

- Identify <primary evidence sources>.
- Distinguish <important evidence categories>.
- Trace <the object-specific mechanism or flow>.

## Map

Use the relevant dimensions:

- <dimension and why it matters>;
- <dimension and why it matters>;
- <dimension and why it matters>.

## Assess

Assess <fit criterion> against <goal or context>. State <common unknown or misreading> rather than inferring it.
```

## Writing Rules

- Write imperative, evidence-oriented instructions, not background essays.
- Specify the object boundary and the decision the module improves.
- Prefer 3–7 mapping dimensions. Each must affect the user's understanding or decision.
- Include cautions that prevent predictable overreach, such as conflating intent with current state.
- Avoid universal scores, generic best practices, implementation prescriptions, and overlap with another module.
- Keep the module concise. Move a large specialized protocol into a separately linked reference only when repeated use justifies it.

## Completion Check

Confirm that the module has a distinct trigger, discovery sources, mapping axes, assessment lens, and at least one meaningful guardrail. Then validate the complete skill with `quick_validate.py`.
