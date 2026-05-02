---
id: RN-0018
title: Refactor Flask App into Smaller Modules
type: refactor
status: pending
priority: high
created: 2026-05-02
resolved:
area: app-architecture
tags:
  - maintainability
  - agent-readability
---

<!-- markdownlint-disable MD025 -->

# Refactor Flask App into Smaller Modules

## Description

`app.py` has grown into a large, mixed-responsibility Flask module, making it harder for future agents and maintainers to reason about changes safely. Split the backend into smaller modules while preserving the existing user-facing behaviour, API contracts, database schema, visual design, and dependency set.

## Details

- Keep `app.py` as the Flask entry point unless there is a compelling reason to change the deployment contract.
- Split page routes and API routes into feature-focused modules or Flask blueprints.
- Move database connection setup, database mode selection, and collection helpers out of the main application module.
- Move roast lifecycle, live roast, temperature, and rate-of-rise helper logic into focused backend modules.
- Move API serialization, request parsing, validation, and response helper logic out of route handlers where doing so makes the route behaviour easier to audit.
- Preserve all existing endpoint URLs, HTTP methods, response shapes, template names, session semantics, and database reads/writes.
- Do not introduce new dependencies, migrations, UI redesign, CSS changes, or user-facing behaviour changes as part of this refactor.
- Prefer small, reviewable extraction steps with tests after each meaningful module boundary.

## Acceptance Criteria

- [ ] `app.py` is substantially shorter and primarily responsible for app creation, configuration, extension setup, and route/module registration.
- [ ] Existing page routes and API endpoints continue to use the same URLs, HTTP methods, redirects, templates, status codes, and JSON response shapes.
- [ ] Database selection, collection access, sync helpers, roast lifecycle helpers, temperature sensor helpers, and route handlers live in clearly named modules with minimal circular imports.
- [ ] Existing API tests pass, with additional focused regression coverage added where extraction risk is high.
- [ ] No database schema changes, new dependencies, visual changes, or user-facing behaviour changes are included.
- [ ] Relevant docs updated when implemented: `docs/README.md`, `docs/architecture/README.md`, `docs/architecture/tech-stack.md`, and any feature docs that reference moved constants or helper locations such as `docs/features/live-roasting.md`.

## Open Questions

- What target module layout should the implementer use: feature blueprints, service modules grouped by domain, or a minimal first pass that only extracts database and helper code?
- Should this be completed in one refactor ticket, or split into follow-up tickets after the first safe extraction proves the pattern?
- Is there a desired maximum size for `app.py` after the refactor, or is "small enough to navigate safely" sufficient?

## Related Files

- `app.py`
- `tests/test_beans_api.py`
- `tests/test_roasts_api.py`
- `tests/test_temperature_api.py`
- `tests/test_sync_api.py`
- `tests/test_reviews_api.py`
- `docs/README.md`
- `docs/architecture/README.md`
- `docs/architecture/tech-stack.md`
- `docs/features/live-roasting.md`
