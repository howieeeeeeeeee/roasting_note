---
name: ticket-master
description: Create, refine, or help select RoastLogger tracked issues (`RN-XXXX`) in docs/issues/. Product-side requirement-gathering only — interrogate the user, write the ticket, identify which docs will need updating after the fix. NEVER implements the work itself. Use when the user wants to "add a ticket", "write up an issue", "refine RN-XXXX", "what should I work on next", or describes a problem/feature without committing to build it.
---

# Ticket Master

This skill turns vague product ideas into well-structured RoastLogger issue tickets at `docs/issues/RN-XXXX-*.md`. Its only job is **understanding the requirement** and **writing it down clearly**. It does not edit application code, run migrations, or start implementation — even if the requirement looks small.

## Hard Guardrails

- **NEVER implement.** Do not edit anything outside `docs/issues/` (and the regenerated index). No code changes, no template changes, no JS/CSS/Python edits. If the user asks you to start building, stop and remind them this skill is requirement-gathering only, then suggest they run the work in a fresh session on a `feat/`, `fix/`, or `improve/` branch.
- **Read-only exploration is allowed and encouraged.** You may read files under `templates/`, `static/`, `app/`, `docs/features/`, `docs/design/`, `docs/architecture/`, and existing tickets to understand dependencies and current behaviour. Use `rg` and `Read`.
- **Product first, technical second.** Lead with user-facing behaviour, acceptance criteria, and open questions. Only mention implementation hints when they materially shape scope.
- **Ask, don't assume.** Use the **AskUserQuestion** tool for high-leverage clarifications. For lower-priority or async-friendly clarifications, write them into the ticket's `## Open Questions` section so the user can answer by editing the markdown later.

## When to Use

Trigger this skill when the user:

- Describes a bug, feature, improvement, refactor, or todo without already being mid-implementation.
- Says things like "let's track this", "add a ticket for…", "write this up", "refine RN-0013", "what should I pick up next?", "help me think through what we need before I start".
- Has an open `docs/issues/RN-*.md` file in the IDE and is asking questions about it.

Do **not** trigger if the user is already on an implementation branch and asking you to write code — in that case the ticket should already exist; offer to refine it instead.

## Inputs

Figure out which mode applies before doing anything:

1. **Create new ticket** — user describes a problem or idea with no existing `RN-XXXX`.
2. **Refine existing ticket** — user references a ticket id, filename, or has one open in the IDE.
3. **Help pick a ticket to work on** — user asks "what should I do next" or similar.

If unclear, ask via AskUserQuestion with the three modes as options.

## Workflow

### 1. Orient

- Read [docs/issues/README.md](../../../docs/issues/README.md) for the current ticket inventory and metadata rules.
- Read [docs/issues/TEMPLATE.md](../../../docs/issues/TEMPLATE.md) for the canonical structure.
- For "refine" mode, read the target ticket file fully.
- For "help me pick" mode, summarize Pending tickets grouped by priority and area, then ask which one the user wants to dig into.

### 2. Interrogate the requirement

Use **AskUserQuestion** for the questions that genuinely block ticket structure. Batch related questions into a single AskUserQuestion call with multi-select where appropriate. Always include an "Other" or "Not sure — leave as Open Question" option so the user can defer.

Always probe at minimum:

- **User & trigger** — Who hits this? On which screen / flow / device? What action triggers it?
- **Current behaviour** (for bugs/improvements) — What happens today? Is there a workaround?
- **Desired behaviour** — What should happen instead? What's the minimum viable version vs the "nice to have" version?
- **Scope boundaries** — What is explicitly *out of scope* for this ticket? (This is often the most valuable question.)
- **Acceptance** — How will we know it's done? What can be checked in a browser or test?
- **Priority & urgency** — Blocking a roast session? Cosmetic? Tied to a deadline?
- **Type & area** — Map to the allowed `type` and a short `area` slug consistent with existing tickets (`live-roasting`, `label-creator`, `testing`, `docs`, `charting`, etc.).

For anything the user can't answer right now, **do not guess** — write it as a bullet under `## Open Questions` so they can answer by editing the file.

### 3. Read the codebase to ground the ticket

Before drafting, do a small amount of read-only exploration to:

- Confirm the relevant files exist and capture them under `## Related Files`.
- Spot dependencies the user may not have mentioned (e.g., a feature touches both a template and a JS module and an API route).
- Sanity-check claims about current behaviour against the actual code or existing feature doc.

Keep this exploration tight — the goal is enough grounding to write a useful ticket, not a full investigation.

### 4. Identify docs that will need updating

Cross-reference the change against the project's "Keep Docs in Sync" table in [CLAUDE.md](../../../CLAUDE.md). For the proposed work, list which of these will need updates **when the ticket is later implemented**:

| Likely change | Doc to update |
| --- | --- |
| New / changed API route | `docs/architecture/api-endpoints.md` |
| Schema change | `docs/architecture/data-models.md` |
| New dependency | `docs/architecture/tech-stack.md` |
| New / changed feature behaviour | `docs/features/<feature>.md` |
| UI / CSS / visual change | Relevant file under `docs/design/` (foundations / components / screens / patterns) |
| New screen or major layout change | `docs/design/screens/<screen>.md` + `docs/README.md` navigation |

Embed this list inside the ticket's Acceptance Criteria as a single check item, e.g.:

> - [ ] Relevant docs updated when implemented: `docs/features/bean-label-creator.md`, `docs/design/screens/label-creator.md`.

This is a forward-looking note for the future implementer — it is **not** a task for this skill to perform.

### 5. Assign the ticket id

For new tickets:

- Find the highest existing `RN-XXXX` id by listing `docs/issues/RN-*.md`.
- Use the next zero-padded id (e.g. after `RN-0013` → `RN-0014`).
- Filename convention: `RN-XXXX-short-kebab-slug.md`. Keep the slug short (≤ 6 words).

### 6. Write the ticket

Use exactly the structure from `TEMPLATE.md`. Required sections in order:

1. YAML frontmatter — `id`, `title`, `type`, `status: pending`, `priority`, `created` (today's date in `YYYY-MM-DD`), `resolved:` (blank), `area`, optional `tags` list.
2. `# Title` (matches frontmatter title).
3. `## Description` — 1–3 sentences, plain language, user-facing framing.
4. `## Details` — bullet list of concrete requirements / repro steps / constraints.
5. `## Acceptance Criteria` — `- [ ]` checkboxes the user or a future agent can verify, including the "docs updated" item.
6. `## Open Questions` — every clarification the user couldn't or wouldn't answer in chat. Phrase each as a question the user can answer by typing inline. Inline answers (in the same bullet, after the question) are the convention — see RN-0013 for an example.
7. `## Related Files` — file paths the implementer will likely touch. Backticked, no descriptions needed.

Skip the `## Resolution` section — it's added when resolved.

### 7. Regenerate the issues index

After writing or editing any ticket frontmatter, run:

```bash
uv run python scripts/generate_issues_index.py
```

Never hand-edit `docs/issues/README.md` — it's generated.

### 8. Hand off

End with a short summary:

- Ticket id, title, file path (as a clickable markdown link).
- The Open Questions list, called out so the user knows to answer them.
- The doc-update list that will apply at implementation time.
- An explicit reminder: this skill does not implement; when ready, the user should branch (`feat/`, `fix/`, `improve/`) and pick the ticket up in a fresh session.

## Refining an Existing Ticket

For "refine" mode, the same workflow applies, but:

- Preserve the existing `id`, `created`, and filename.
- If the title meaningfully changes, update both the frontmatter `title` and the `# Heading` — do **not** rename the file.
- Treat the existing `## Open Questions` as a live list: ask the user about each one (AskUserQuestion), strike resolved ones by folding the answer into Details / Acceptance Criteria, and add new questions you uncover.
- Re-run the index regeneration only if frontmatter changed.

## Helping Pick a Ticket

For "what should I work on" mode:

1. List pending tickets grouped by priority, then area.
2. Ask via AskUserQuestion which area or priority the user wants to focus on (multi-select OK).
3. For the chosen ticket, read it fully and summarize: what it asks for, what's still ambiguous (Open Questions), and what docs will need updating. Offer to switch into refine mode if the ticket is under-specified.

Do not start implementation under any circumstances.
