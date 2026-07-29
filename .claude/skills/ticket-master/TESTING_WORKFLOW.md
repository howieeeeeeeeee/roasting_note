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
| `ui-visual` | Targeted browser visual check, screenshot evidence, and automated coverage where practical |
| `ui-interaction` | Automated contract coverage, an updated browser checklist scenario, targeted browser execution, and full pytest |
| `cross-workflow` | Automated coverage plus the complete affected browser workflow |
| `refactor` | Structural/route regression coverage, full pytest, and an affected-workflow browser smoke test when visible behavior is involved |
| `release` | Full pytest and the complete browser workflow when UI behavior changed since the previous release evidence |

Treat live roasting, sensor states, inventory deduction, Settings, and database
sync UI as critical cross-workflow surfaces. Changes to those surfaces require
the complete affected browser workflow.

## Write Or Refine The Ticket

New active tickets use `testing_policy: v1` and include:

```markdown
## Testing Impact

- Change classification:
- Automated tests to add or update:
- Browser E2E scenarios to add or update:
- Required commands:
- Required browser evidence:
- Not applicable reason:
```

Fill every field with exact paths, scenario names, commands, and evidence.
Use `None` only with a concrete Not applicable reason.

For new or changed visible UI:

1. Name the exact subsection or scenario to add or update in
   `tests/e2e/README.md`.
2. Specify the user action, observable result, failure state, and screenshot or
   log evidence.
3. Add automated contract coverage where practical. Browser checks supplement
   focused automated tests; they do not replace them.
4. Update or remove obsolete checklist steps when UI behavior changes or is
   removed.

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
4. Confirm every durable new or changed UI interaction is represented in
   `tests/e2e/README.md`.
5. Run the declared focused commands and `uv run pytest`.
6. Run every declared browser scenario and record the run ID, assertions,
   evidence paths, console/network findings, and cleanup result.
7. Check the Testing Impact acceptance criterion and include concise evidence
   in `## Resolution`.

Keep the ticket open when required automated coverage, browser checklist
maintenance, execution evidence, or cleanup evidence is missing.
