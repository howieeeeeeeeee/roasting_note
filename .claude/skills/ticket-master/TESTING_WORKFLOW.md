# RoastLogger Testing Workflow

Read this file whenever creating, refining, or resolving a ticket. Use it to
record verification before implementation and to keep durable automated and
browser coverage synchronized with the behavior delivered.

## Canonical Test Sources

Do not copy the changing test catalog into `SKILL.md` or ticket records:

- `tests/README.md` owns the automated test inventory, commands, fixtures, and
  routine execution policy.
- `tests/e2e/README.md` owns the Codex in-app-browser workflow and its visible
  UI regression checklist.
- The ticket owns only the exact automated files, browser scenarios, commands,
  and evidence required for that change.

Read the relevant portions of both canonical sources before specifying tests.

## Classify The Change

Use one or more of these classifications under `## Testing Impact`:

| Classification | Required verification |
| --- | --- |
| `documentation-only` | No tests unless behavior or policy also changes; record the reason |
| `backend-api` | Focused automated regression tests and `uv run pytest` |
| `database-sync` | Focused safety tests, full pytest, and applicable guarded dry-run evidence |
| `ui-visual` | Browser level `none` for a small cosmetic fix or `targeted` when visual risk merits a focused check; automated coverage where practical |
| `ui-interaction` | Automated contract coverage, browser level `targeted`, an updated checklist scenario, and full pytest |
| `cross-workflow` | Automated coverage plus the complete affected browser workflow |
| `refactor` | Structural/route regression coverage, full pytest, and browser level based on the visible reach of the refactor |
| `release` | Full pytest and the complete browser workflow when UI behavior changed since the previous release evidence |

## Choose The Browser Verification Level

Record exactly one level in the ticket:

| Level | Use when | Required record |
| --- | --- | --- |
| `none` | No visible UI changes, or a small low-risk visual-only correction such as copy, color, icon, or spacing that preserves layout and interaction contracts | Set browser scenarios and evidence to `None` and give a concrete Not applicable reason |
| `targeted` | One screen, component, responsive state, or interaction changes without altering an end-to-end workflow | Name and run the focused scenario; record its screenshot or log evidence and cleanup |
| `full` | A change spans screens or stages, alters a critical workflow, or supplies release-level regression evidence | Run the complete affected workflow and record the run ID, evidence, console/network findings, and cleanup |

Do not turn a small visual fix into a full browser task by default. Use
`targeted` instead of `none` when the visual change can hide content, affect
responsive layout, alter a shared component, or otherwise has meaningful
regression risk.

Treat live roasting, sensor states, inventory deduction, Settings, and database
sync UI as critical surfaces when their behavior or interaction changes. Those
changes use `full`; a cosmetic-only correction on the same screen may still use
`none` or `targeted` according to its actual reach.

When focused repository reads do not make the correct level clear, ask the user
one concise question during ticket creation: whether to use `none`, `targeted`,
or `full`, with a recommended level and one-sentence reason. Ask only when the
choice materially changes effort or evidence; do not ask when the classification
is clear.

## Write Or Refine The Ticket

New active tickets use `testing_policy: v1` and include:

```markdown
## Testing Impact

- Change classification:
- Browser verification level:
- Automated tests to add or update:
- Browser E2E scenarios to add or update:
- Required commands:
- Required browser evidence:
- Not applicable reason:
```

Fill every field with exact paths, scenario names, commands, and evidence.
Use exactly `none`, `targeted`, or `full` for the browser level. Use `None` for
omitted coverage only with a concrete Not applicable reason.

For `targeted` or `full` browser verification:

1. Name the exact subsection or scenario to add or update in
   `tests/e2e/README.md`.
2. Specify the user action, observable result, failure state, and screenshot or
   log evidence.
3. Add automated contract coverage where practical. Browser checks supplement
   focused automated tests; they do not replace them.
4. Update or remove obsolete checklist steps when UI behavior changes or is
   removed.

For level `none`, do not add a browser task or checklist scenario. Record why
the change is visual-only and low risk. Documentation and applicable focused
automated checks remain required.

Add this acceptance criterion:

```markdown
- [ ] Testing Impact reviewed against the implementation diff; declared automated and browser coverage is complete.
```

## Resolve The Ticket

Before resolution:

1. Compare the implementation diff with the ticket's Testing Impact.
2. Update the declared automated tests and browser scenarios when scope
   changed.
3. Confirm `tests/README.md` still describes new automated coverage and update
   it when the inventory, commands, fixtures, or policy changed.
4. For `targeted` or `full`, confirm every durable new or changed UI
   interaction is represented in `tests/e2e/README.md`.
5. Run the declared focused commands and `uv run pytest`.
6. Run every declared `targeted` or `full` browser scenario and record its
   required evidence and cleanup result.
7. Check the Testing Impact acceptance criterion and include concise evidence
   in `## Resolution`.

Keep the ticket open when required automated coverage, browser checklist
maintenance, execution evidence, or cleanup evidence is missing.
