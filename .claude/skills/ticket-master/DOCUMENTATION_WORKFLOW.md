# RoastLogger Documentation Workflow

Read this file whenever creating, refining, or resolving a ticket. Use it to
record the documentation impact before implementation and to verify the actual
documentation changes before resolution. Read `TESTING_WORKFLOW.md` alongside
it so verification and durable UI regression coverage are recorded separately
instead of being hidden inside documentation notes.

## Start Here

Read `docs/README.md` for project context and navigation. Then read only the
documentation areas touched by the proposed change.

```text
docs/
├── README.md
├── architecture/
│   ├── api-endpoints.md
│   ├── data-models.md
│   └── tech-stack.md
├── design/
│   ├── README.md
│   ├── principles.md
│   ├── foundations/
│   ├── components/
│   ├── screens/
│   └── patterns/
├── features/
├── hardware/
├── deployment/
└── issues/

tests/README.md
```

## Route Changes To Documents

| Change | Required documentation |
| --- | --- |
| API route added, changed, or removed | `docs/architecture/api-endpoints.md` |
| MongoDB schema or document shape | `docs/architecture/data-models.md` |
| Dependency, runtime, or major tool change | `docs/architecture/tech-stack.md` |
| Feature behavior, lifecycle, validation, or API usage | Matching file under `docs/features/` |
| Color, typography, spacing, or dark-mode tokens | Matching file under `docs/design/foundations/` |
| Reusable UI component | Matching file under `docs/design/components/` |
| Page or modal layout and interaction | Matching file under `docs/design/screens/` |
| Repeated design system or printable pattern | Matching file under `docs/design/patterns/` |
| Design principle or interaction constraint | `docs/design/principles.md` |
| ESP32, thermocouple, or sensor behavior | Matching file under `docs/hardware/` |
| Hosting, environment, or release procedure | Matching file under `docs/deployment/` |
| Test command, fixture, or testing policy | `tests/README.md` |
| Documentation structure or navigation | `docs/README.md` and the affected local `README.md` |
| Ticketed implementation | Governing record under `docs/issues/` |

If a change affects both behavior and appearance, update both the feature and
design docs. Link between them instead of duplicating content.

## Database Operations Impact

Treat a ticket as database-impacting when it changes a MongoDB document shape,
persistence behavior, database route or service, migration/backfill, database
configuration, or synchronization behavior. Add
`## Database Operations Impact` with:

- affected collections and local/online effects;
- migration or backfill needs;
- expected sync direction;
- whether an applied mirror is part of delivery; and
- required backup and audit evidence for resolution.

Use `None` only after focused repository and documentation reads establish that
no live database operation is required. Before implementation, require
`docs/features/database-sync.md` to be read and a configured guarded CLI
`--dry-run` to be attempted. An unavailable endpoint is an environment
limitation unless the ticket requires live-data evidence.

Automated verification uses mocks, fixtures, or an isolated local database.
An applied mirror is a separate user-authorized operation after a visible
preflight and requires both exact run-specific tokens; a ticketing turn must
not perform it. Resolution must record dry-run evidence or the applied run ID
and audit path and verify `git ls-files db_backup 'db_backup/**'` returns no
tracked files.

## Write The Ticket

Add a `## Documentation Impact` section containing:

- exact known doc paths;
- conditional doc paths and the condition that activates them;
- navigation/index files that must change when structure changes; and
- `None` only when focused repository reads show that no durable behavior,
  architecture, design, hardware, deployment, or testing guidance changes.

Add this acceptance criterion:

```markdown
- [ ] Documentation Impact reviewed against the implementation diff; every affected document above is updated in this branch.
```

Do not use a generic "docs updated" checkbox when exact paths can be known.

## Resolve The Ticket

Before resolution:

1. Compare the implementation diff with this routing table.
2. Update the ticket's Documentation Impact if scope changed.
3. Confirm every required doc changed in the same branch.
4. For database-impacting work, verify the recorded dry-run or applied audit
   evidence and confirm no backup payload is tracked.
5. Add the updated paths and verification to `## Resolution`.
6. Keep the ticket open if required documentation is missing.
