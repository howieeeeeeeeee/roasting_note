# Offline Dashboard Maintenance

Read this file before changing the issue workbench.

## Sources And Output

- Edit `html/overview.template.html` for layout, appearance, and browser
  behavior.
- Edit `scripts/render_dashboard.py` for record-derived data.
- Edit `scripts/generate_issues_index.py` for schema, validation, filing, or
  generated Markdown.
- Never edit `docs/issues/overview.html`; regenerate it.

The generated dashboard must remain one self-contained offline HTML file. Do
not add CDN scripts, remote fonts, analytics, network requests, forms that
mutate records, or links that transmit ticket content.

## Required Views

Preserve:

- Next: ready decisions, ready work, in-progress work, epics, and blockers;
- Board: active child and standalone tickets by state;
- Directory: decisions, epics with children, and standalone tickets;
- Dependencies: blockers and direct downstream records;
- record details, source links, search, area/status/priority filters, theme
  switching, keyboard focus, Escape-to-close, and reduced-motion behavior.

Keep wide-screen details docked so the workbench remains interactive. Use a
full-screen detail panel at compact widths. Keep standalone records to at most
two columns.

## Safety And Verification

Escape embedded JSON so record text cannot break out of the script element.
Render record bodies as escaped text unless a reviewed sanitizer is bundled
locally with its license.

After changes:

```bash
uv run python scripts/generate_issues_index.py
uv run python scripts/generate_issues_index.py --check
uv run --extra test pytest tests/test_ticket_system.py
```

Also open `docs/issues/overview.html` directly and verify all views, filters,
details, links, light/dark themes, desktop split view, and compact layout.
