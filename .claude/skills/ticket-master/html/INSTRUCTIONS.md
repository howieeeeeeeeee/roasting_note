# Offline Dashboard Maintenance

Read this file before changing the issue workbench.

## Canonical Design

`html/overview.template.html` directly follows the neutral workbench design in
the Kantian ticket-system reference. Preserve that design as the shared ticket
interface: typewriter typography, paper-and-ink palette, generous spacing,
simple status accents, board columns, and docked record details.

Do not restyle the workbench to match the host application's branding or
design system. Project-specific content belongs in `docs/issues/tracker.toml`
and record metadata, not in dashboard colors, type, component shapes, or
storage keys.

The only intended repository-specific inputs are:

- project name, description, and id prefixes;
- configured ticket types and priorities; and
- generated ticket and human-decision data.

## Sources And Output

- Edit `html/overview.template.html` for layout, appearance, and browser
  behavior.
- Edit `scripts/render_dashboard.py` for record-derived data and bundled
  assets.
- Edit `scripts/generate_issues_index.py` for schema, validation, filing, or
  generated Markdown.
- Never edit `docs/issues/overview.html`; regenerate it.

The generated dashboard must remain one self-contained offline HTML file. Do
not add CDN scripts, remote fonts, analytics, network requests, forms that
mutate records, or links that transmit ticket content.

## Required Views

Preserve:

- Next: ready decisions, waiting decisions, ready work, in-progress work, and
  epics;
- Board: active child and standalone tickets by state and epic;
- Directory: decisions, epics with children, and standalone tickets;
- Dependencies: blockers, direct effects, and further downstream records;
- record details, internal Markdown links, source links, search,
  area/status/priority filters, theme switching, keyboard focus,
  Escape-to-close, and reduced-motion behavior.

Keep wide-screen details docked so the workbench remains interactive. Use a
full-screen detail panel at compact widths. Keep standalone records to at most
two columns.

## Bundled Assets

The output embeds local copies of:

- Courier Prime Regular and Bold for the reference typewriter typography;
- Marked for GitHub-flavored Markdown rendering; and
- DOMPurify for browser-side sanitization.

Keep their license files under `html/licenses/`. Do not replace these assets
with CDN URLs. Font binaries are stored as Base64 text under `html/fonts/` so
the complete source bundle can be maintained with ordinary text patches.

## Safety And Verification

Escape embedded JSON so record text cannot break out of the script element.
Sanitize rendered Markdown with the bundled DOMPurify build.

After changes:

```bash
uv run python scripts/generate_issues_index.py
uv run python scripts/generate_issues_index.py --check
uv run --extra test pytest tests/test_ticket_system.py
```

Also open `docs/issues/overview.html` directly and verify all views, filters,
details, links, light/dark themes, desktop split view, and compact layout.
