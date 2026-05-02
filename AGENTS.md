# Codex Instructions for RoastLogger

> **Core responsibility:** whenever a change affects the **scope, behaviour, or appearance** of the project, update the relevant docs in the same change. Out-of-date docs are worse than no docs.

## Documentation Map

```text
docs/
├── README.md         # Start here — overview + navigation
├── architecture/     # Data models, API routes, tech stack
├── design/           # Principles, tokens, components, screens, patterns
├── features/         # Feature specifications (behaviour, API, data model)
├── hardware/         # ESP32 temperature sensor
├── backlog/          # Bugs, features, improvements, todos (YAML-frontmatter tickets)
└── deployment/       # Render deployment guide

tests/README.md       # How to run tests, fixtures, when to run them
```

## Keep Docs in Sync — Required

When your change touches the project, update the docs listed below **in the same branch**. If you're not sure whether a doc applies, err on updating it.

| Change | Update |
| --- | --- |
| New or changed API route | `docs/architecture/api-endpoints.md` |
| Schema change | `docs/architecture/data-models.md` |
| New dependency | `docs/architecture/tech-stack.md` |
| New or changed feature behaviour | `docs/features/<feature>.md` |
| **UI / CSS / visual change** (colour, font, spacing, layout, component, screen redesign, new design pattern) | **Relevant file under `docs/design/`** — foundations for token changes, components for reusable UI, screens for page-level layout, patterns for design systems |
| New screen or major layout change | `docs/design/screens/<screen>.md` + `docs/README.md` navigation |
| Bug fix or any ticketed work | Update the ticket in `docs/backlog/` (see workflow below) |

These index files must also stay current when structure changes:

- `docs/README.md` — top-level navigation
- `docs/design/README.md` — design folder navigation
- `docs/backlog/README.md` — generated index, do not hand-edit

If a feature change has visual implications, update **both** the feature doc (behaviour) and the design doc (look and feel). Do not duplicate content — link between them.

## Branch Strategy

```bash
git checkout -b feat/<feature-name>      # new features
git checkout -b fix/<bug-name>           # bug fixes
git checkout -b improve/<improvement>    # improvements
git checkout -b docs/<topic>             # doc-only changes
```

## Before Making Changes

1. Create a new branch from `main`.
2. Read `docs/README.md` for project overview.
3. Check `docs/backlog/README.md` for related tickets.
4. Read the relevant docs — features, design, architecture — that overlap with your change.

## Testing

Run and write tests per `tests/README.md`. At minimum, run the API suite after any change to endpoints, database operations, or business logic, and before committing.

```bash
uv run pytest           # full suite
uv run pytest -v        # verbose
```

Full details, fixtures, when-to-run rules, and how to add tests live in [tests/README.md](./tests/README.md).

## Backlog

Tickets live in `docs/backlog/` as Markdown files with YAML frontmatter. Each ticket has a stable `RN-XXXX` id — filenames never change when status changes; update the `status` field instead.

Use `docs/backlog/TEMPLATE.md` for new tickets. After creating or changing any ticket metadata, regenerate the index:

```bash
uv run python scripts/generate_backlog_index.py
```

Do not hand-edit `docs/backlog/README.md` — it is generated from ticket frontmatter. Field definitions, allowed values, and the full workflow live in [docs/backlog/README.md](./docs/backlog/README.md).

## Quick Reference

| Need to… | Go to |
| --- | --- |
| Understand the project | `docs/README.md` |
| See API routes | `docs/architecture/api-endpoints.md` |
| See DB schema | `docs/architecture/data-models.md` |
| Understand a feature's behaviour | `docs/features/` |
| Look up a design token / component / screen | `docs/design/` |
| Check pending work | `docs/backlog/README.md` |
| Run tests | `tests/README.md` |
