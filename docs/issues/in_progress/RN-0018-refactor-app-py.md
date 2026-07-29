---
id: RN-0018
title: Refactor Oversized Source Files into Focused Modules
type: refactor
status: in_progress
priority: high
created: 2026-05-02
resolved:
area: app-architecture
parent:
decisions: []
blocked_by: []
tags:
  - maintainability
  - agent-readability
  - modularity
  - line-limit
---

<!-- markdownlint-disable MD025 -->

# Refactor Oversized Source Files into Focused Modules

## Description

Split every existing human-authored source file above 1,000 physical lines
into focused modules, and add an automated repository guard against future
oversized code or documentation. Preserve the application's behavior,
interfaces, deployment contract, visual design, data model, and dependency
set.

## Details

### Current Oversized Source Files

The implementation must address all three human-authored files currently above
the limit:

| File | Baseline | Required boundary |
| --- | ---: | --- |
| `app.py` | 1,860 lines | Thin compatibility entry point plus imported application modules |
| `templates/roast_live.html` | 1,660 lines | Focused template markup plus imported live-roast JavaScript modules |
| `.claude/skills/ticket-master/scripts/generate_issues_index.py` | 1,017 lines | Thin CLI/orchestrator plus imported tracker modules |

Line counts are the planning baseline and may change before implementation.
Recount tracked files before starting and include any additional
human-authored file that has crossed the limit.

### Flask Application Boundary

- Keep `app.py` as the stable development and Gunicorn entry point. It must
  continue to export `app`, support direct execution, and preserve
  `gunicorn app:app`.
- Add a `roastlogger` package with
  `create_app(config_overrides=None)`. `app.py` creates the default instance
  from that factory.
- Put configuration and database connection/selection in focused modules.
  Make the local database name and sensor URL app configuration so tests can
  override them without changing production defaults.
- Register page, bean, roast, temperature, settings, and synchronization
  routes through feature-focused Flask blueprints.
- Put roast lifecycle/live-sync behavior, temperature sensor access and RoR,
  and database synchronization in service modules. Route modules may depend on
  services; services must not import the global `app` instance or blueprints.
- Keep API request parsing, validation, serialization, status codes, and error
  behavior auditable at the route/service boundary.

### Live-Roast Template Boundary

- Keep server-rendered live-roast markup in
  `templates/roast_live.html`, but remove the large inline implementation
  script.
- Serialize all Jinja-derived runtime values through one safely encoded
  `<script type="application/json" id="live-roast-config">` bootstrap object.
- Load a stable JavaScript entry point from `static/js/live-roast/`. Split
  chart setup, polling/session state, setup and event controls, and fullscreen
  behavior into focused modules.
- Preserve existing DOM identifiers, timing cadence, chart datasets and
  annotations, sensor-state presentation, touch/fullscreen interactions, and
  visible layout.

### Ticket-Generator Boundary

- Keep `.claude/skills/ticket-master/scripts/generate_issues_index.py` as the
  supported CLI and import compatibility module.
- Extract record/config models and parsing, metadata/dependency validation,
  status filing, and Markdown generation into a small internal tracker
  package. Keep dashboard rendering in its existing focused module.
- Preserve both generator commands, deterministic output, canonical filing,
  validation messages, and callable names imported by the existing tests and
  compatibility wrapper.

### Repository Line-Limit Guard

- Add a test that counts physical lines in tracked, human-authored
  `*.py`, `*.js`, `*.html`, `*.css`, `*.cpp`, `*.h`, and `*.md` files.
- Fail with the path and observed line count when any included file exceeds
  1,000 lines.
- Exclude generated files such as `docs/issues/overview.html`, files carrying
  the tracker generated notice, vendored/minified assets, binaries, fonts,
  licenses, and lock files.
- The repository guidance must explain that oversized code is split by
  responsibility and imported, included, or registered from a stable entry
  point. Oversized documentation is grouped into aspect-specific files under
  a named directory with a concise `README.md` index and updated navigation.
- Do not satisfy the check with arbitrary numbered chunks or by adding a file
  to the exclusion list.

### Compatibility And Delivery

- Preserve every page/API URL, HTTP method, redirect, template, status code,
  JSON shape, session behavior, database read/write, timestamp rule, and
  application configuration default.
- Do not add dependencies, migrations, UI/CSS changes, or user-facing
  behavior.
- Extract one boundary at a time and run focused regression tests after each
  extraction. Run the full suite before resolution.

## Acceptance Criteria

- [ ] `app.py`, `templates/roast_live.html`, and the ticket generator are each at or below 1,000 physical lines, and every extracted human-authored file also satisfies the limit.
- [ ] `app.py` remains the direct-run and `gunicorn app:app` compatibility entry point and creates the application through `create_app(config_overrides=None)`.
- [ ] Existing page routes and API endpoints continue to use the same URLs, HTTP methods, redirects, templates, status codes, and JSON response shapes.
- [ ] Configuration/database access, route blueprints, roast services, sensor/RoR services, and synchronization services follow the dependency direction described above without circular imports or global-app imports from services.
- [ ] The live-roast page uses one safely encoded bootstrap object and focused JavaScript modules while preserving charting, polling, controls, sensor states, responsive behavior, and fullscreen behavior.
- [ ] The ticket generator keeps its CLI/import compatibility, validation, filing, and deterministic generated output after its internal modules are extracted.
- [ ] An automated repository check rejects oversized human-authored code and documentation and applies only the documented exemptions.
- [ ] Focused route, service, live-page, and tracker regression coverage protects each extraction boundary, and `uv run pytest` passes.
- [ ] No database schema changes, new dependencies, visual changes, or user-facing behaviour changes are included.
- [ ] Documentation Impact reviewed against the implementation diff; every affected document below is updated in this branch.

## Documentation Impact

- `AGENTS.md`
- `CLAUDE.md`
- `docs/README.md`
- `docs/architecture/README.md`
- `docs/architecture/tech-stack.md`
- `docs/features/live-roasting.md`
- `tests/README.md`
- Conditional: `.claude/skills/ticket-master/SKILL.md` if the supported
  generator command, import surface, or file references change.
- Conditional: `docs/design/screens/live-roasting.md` if preserving the
  existing interaction requires any selector, layout, or interaction change.

## Open Questions

- None. The 1,000-line limit, current scope, module boundaries, compatibility
  constraints, and exemptions are decided.

## Related Files

- `app.py`
- `templates/roast_live.html`
- `static/js/roast-chart.js`
- `.claude/skills/ticket-master/scripts/generate_issues_index.py`
- `.claude/skills/ticket-master/scripts/render_dashboard.py`
- `scripts/generate_issues_index.py`
- `tests/test_ticket_system.py`
- `tests/test_beans_api.py`
- `tests/test_roasts_api.py`
- `tests/test_temperature_api.py`
- `tests/test_sync_api.py`
- `tests/test_reviews_api.py`
- `AGENTS.md`
- `CLAUDE.md`
- `docs/README.md`
- `docs/architecture/README.md`
- `docs/architecture/tech-stack.md`
- `docs/features/live-roasting.md`
