---
name: map-the-project
description: "Rapidly map a project, business, discipline, or system into an evidence-grounded, decision-ready brief. Use when a user needs to understand an unfamiliar or complex object; clarify its goals, boundaries, structure, operation, and current state; or assess what it does, how it is doing, and what to investigate or decide next."
---

# Map The Project

Turn available evidence into a shared model before proposing solutions. Optimize for a user who needs orientation and judgment, not exhaustive documentation or a formal audit.

## Select a Module

- **Template**: Read [references/template.md](references/template.md) only when creating or changing a module.
- **Repository**: Read [references/repository.md](references/repository.md) for a codebase, package, service repository, or technical project.
- **Business**: Read [references/business.md](references/business.md) for a product, company, initiative, team operating model, market, or business process.
- **Discipline**: Read [references/discipline.md](references/discipline.md) for a knowledge domain, methodology, field of study, theory, or body of practice.
- **System**: Read [references/system.md](references/system.md) for a technical, organizational, operational, or socio-technical system whose interacting parts and flows matter most.

Select the narrowest fitting module. For a mixed object, select one primary module and name any secondary lens; do not load every module by default.

## Map the Object

1. Establish the decision context: identify the object, intended user, decision or question, time horizon, and desired depth. State reasonable assumptions when these are missing.
2. Set the boundary: distinguish the object from adjacent objects, dependencies, and exclusions. Search only sources that can change the user's decision.
3. Gather evidence: inspect primary artifacts first. Record a path, source, observation, or user-provided statement for each material claim.
4. Build a compact model: map purpose, actors, components or concepts, important relationships, inputs and outputs, key flows, constraints, and feedback loops. Use the selected module's dimensions.
5. Assess the present state against the object's stated or inferred goals. Separate facts, reasoned inferences, and unanswered questions. Do not invent metrics, intent, ownership, or causality.
6. Present the smallest useful brief. Lead with the current understanding and decision implications. Add a table, flow, or tree only when it makes relationships clearer than short prose.

Stop discovery once added evidence is unlikely to change the model or recommendation. Name important uncertainty rather than filling it with generic advice.

## Evidence Discipline

- Mark material statements as `confirmed`, `inferred`, or `open question` when their status is not obvious from the wording.
- Treat documents as intent, implementation or observed behavior as current state, and plans or roadmaps as future direction; do not conflate them.
- Explain assessment criteria in context. Avoid universal maturity scores, architecture slogans, or recommendations that assume a scale, risk profile, or goal not supported by evidence.
- Keep the mapping distinct from an engineering audit. Hand off a repository needing severity-ranked architecture findings and evolution work to `repo-audit`.

## Output

Produce the following sections in the user's language. Omit a section only when it cannot materially help the stated decision.

1. **At a glance**: object, boundary, selected module, and the answer to the user's central question.
2. **Purpose and success**: goals, users or stakeholders, constraints, and observable success criteria.
3. **How it works**: the small model of major parts, relationships, and flows.
4. **Current state**: what appears healthy, weak, changing, blocked, or unknown, tied to evidence.
5. **Assessment**: fit between the current state and goals; key tradeoffs, risks, and opportunities.
6. **Next decisions**: the smallest high-leverage actions, investigations, or questions, with the uncertainty each resolves.

Scale the output to the object. A small object may need only a concise brief; a complex object may need a compact map plus an assessment table. Do not prescribe implementation unless the user asks for it.

Create only the resource directories this skill actually needs. Delete this section if no resources are required.

### scripts/
Executable code (Python/Bash/etc.) that can be run directly to perform specific operations.

**Examples from other skills:**
- PDF skill: `fill_fillable_fields.py`, `extract_form_field_info.py` - utilities for PDF manipulation
- DOCX skill: `document.py`, `utilities.py` - Python modules for document processing

**Appropriate for:** Python scripts, shell scripts, or any executable code that performs automation, data processing, or specific operations.

**Note:** Scripts may be executed without loading into context, but can still be read by Codex for patching or environment adjustments.

### references/
Documentation and reference material intended to be loaded into context to inform Codex's process and thinking.

**Examples from other skills:**
- Product management: `communication.md`, `context_building.md` - detailed workflow guides
- BigQuery: API reference documentation and query examples
- Finance: Schema documentation, company policies

**Appropriate for:** In-depth documentation, API references, database schemas, comprehensive guides, or any detailed information that Codex should reference while working.

### assets/
Files not intended to be loaded into context, but rather used within the output Codex produces.

**Examples from other skills:**
- Brand styling: PowerPoint template files (.pptx), logo files
- Frontend builder: HTML/React boilerplate project directories
- Typography: Font files (.ttf, .woff2)

**Appropriate for:** Templates, boilerplate code, document templates, images, icons, fonts, or any files meant to be copied or used in the final output.

---

**Not every skill requires all three types of resources.**
