---
id: RN-0029-01
title: Establish Quiet Compact UI Foundations
type: improvement
status: in_progress
priority: high
created: 2026-08-20
resolved:
area: design-system
parent: RN-0029
decisions: []
blocked_by: []
testing_policy: v1
tags:
  - design
  - tokens
  - contrast
  - typography
  - spacing
  - dark-mode
---

# Establish Quiet Compact UI Foundations

## Description

Create the shared contrast, typography, density, surface, and motion tokens
needed by the Quiet Compact refresh. Preserve RoastLogger's warm identity while
removing duplicated font delivery and separating management density from
live-roast instrument sizing.

## Details

- Current behavior: Visible tertiary text uses `--txt3`, which measures about
  `2.26:1` on the light surface and `1.89:1` on the dark surface. Small table
  headings, inactive navigation text, placeholders, and related UI can become
  difficult to read.
- Current font delivery: `templates/base.html` requests all six families, and
  `static/css/tokens.css` imports nearly the same set again. Playfair Display,
  Barlow Condensed, and Roboto Slab are label-only faces but load on ordinary
  Roasts, Beans, Settings, and form pages.
- Contrast: Give every normal visible text role, placeholder, table heading,
  and inactive navigation state a WCAG AA color in both themes. Use border or
  decorative tokens for intentionally faint non-text marks instead of reusing
  an unreadable text token.
- Typography: Keep the established Inter UI, Raleway record-title, and DM Mono
  data roles for this preserve-style refresh. Remove duplicate requests and
  scope label-only faces to pages that can open the label creator without
  changing canvas font readiness or printable output.
- Density: Define explicit browse/manage spacing and panel recipes that use
  compact gaps and quieter surfaces while retaining `44px` minimum interactive
  targets. Do not apply those values to live-roast critical controls or its
  `54px+` target rules.
- Surfaces: Reduce reliance on a card around every content group. Static
  sections may use one containing surface, sparse dividers, or whitespace;
  elevation continues to communicate actual hierarchy such as dialogs and
  menus.
- Shape and color locks: Preserve the warm neutral palette, single primary
  accent, semantic success/danger/warning roles, and existing radius family.
  Do not add gradients, glows, glass effects, a new icon family, or another
  design system.
- Motion foundation: Add shared duration/easing tokens and a mandatory
  `prefers-reduced-motion` override for later children. This ticket does not
  itself animate route changes.
- In scope: `tokens.css`, base typography and surface rules, scoped font links,
  contrast-safe text roles, reusable density hooks, automated design
  contracts, and matching design documentation.
- Out of scope: page recomposition, navigation animation, Settings markup,
  form field rearrangement, live-roast sizing, printable label appearance, API
  behavior, and database behavior.

## Acceptance Criteria

- [ ] Every normal visible text token used for body copy, placeholders, table
  headings, and inactive navigation reaches WCAG AA contrast on its documented
  light and dark surfaces.
- [ ] Faint decorative borders and separators use non-text tokens rather than
  weakening readable secondary or tertiary text.
- [ ] The complete six-family Google Fonts request is not duplicated between
  `base.html` and `tokens.css`.
- [ ] Ordinary Roasts, Beans, Settings, and form pages request only the global
  UI, record-title, mono, and icon resources they use; label-capable pages load
  the remaining documented label faces before canvas drawing.
- [ ] Browse/manage density recipes preserve a minimum `44px` interactive
  target and do not change live-roast critical sizing or instrument typography.
- [ ] Static sections have a documented flat grouping option, and shadows are
  reserved for real overlay or clickable hierarchy.
- [ ] Light and dark modes retain one warm palette, one primary accent, and
  equivalent hierarchy without theme inversion between sections.
- [ ] Shared motion tokens include a complete reduced-motion override and are
  documented for the navigation child.
- [ ] Testing Impact reviewed against the implementation diff; declared automated and browser coverage is complete.
- [ ] Documentation Impact reviewed against the implementation diff; every affected document below is updated in this branch.

## Testing Impact

- Change classification: ui-visual
- Browser verification level: targeted
- Automated tests to add or update: Add `tests/test_design_contracts.py` for contrast calculations across documented text/surface pairs, one global font request, route-scoped label faces, `44px` management targets, protected live-roast target tokens, radius/palette locks, and reduced-motion token coverage; update `tests/test_api_contracts.py` for rendered font resources on ordinary and label-capable pages; retain `tests/test_file_size_policy.py`
- Browser E2E scenarios to add or update: Add `tests/e2e/README.md` -> `Quiet Compact UI` -> `Foundations` with a targeted visual matrix covering Roasts, Beans, Add Bean, Settings, and the live-roast shell at desktop and tablet widths in light and dark modes; verify readable small text, no unexpected font swap, consistent surfaces, and unchanged live-roast sizes
- Required commands: `uv run pytest tests/test_design_contracts.py tests/test_api_contracts.py tests/test_file_size_policy.py`; `uv run pytest`; `uv run python -m tests.e2e.manage start --run-id rn-0029-foundations-a`; `uv run python -m tests.e2e.manage cleanup --run-id rn-0029-foundations-a`; `git diff --check`
- Required browser evidence: Record run ID `rn-0029-foundations-a`; save light/dark screenshots of representative list, form, Settings, and live-roast surfaces at `1440x900` and `1024x768`; record computed font families, small-text readability, font-request findings, protected target measurements, console errors, failed network requests, and cleanup in `tests/e2e/artifacts/rn-0029-foundations-a/summary.md`
- Not applicable reason: None. The ticket changes shared visual tokens and font delivery, so a targeted representative-screen check supplements automated contracts.

## Documentation Impact

- Update `docs/design/foundations/color.md` with contrast-safe text roles and
  separate decorative tokens.
- Update `docs/design/foundations/typography.md` with deduplicated global and
  label-scoped font delivery.
- Update `docs/design/foundations/spacing-layout.md` with browse/manage density
  hooks and the protected live-roast exception.
- Update `docs/design/foundations/dark-mode.md` with hierarchy and contrast
  parity requirements.
- Update `docs/design/components/cards-surfaces.md` with the flat static-group
  recipe and elevation limits.
- Update `docs/design/principles.md` with the two density contexts.
- Update `tests/README.md` with `tests/test_design_contracts.py` coverage and
  `tests/e2e/README.md` with the targeted Foundations matrix.
- Conditional: update `docs/architecture/tech-stack.md` if font delivery or a
  dependency changes beyond moving the existing Google Fonts requests.

## Database Operations Impact

None. Focused reads confirm this ticket changes CSS tokens, font resources,
rendered presentation, tests, and documentation only. It performs no database
write, schema change, migration, synchronization, backup, or audit operation.

## Open Questions

- None. Preserve the existing app type roles and warm palette; improve their
  delivery, contrast, density, and documented usage.

## Related Files

- `templates/base.html`
- `templates/beans_detail.html`
- `static/css/tokens.css`
- `static/css/base.css`
- `static/css/components/cards.css`
- `static/css/components/forms.css`
- `static/css/screens/live-roasting.css`
- `tests/test_design_contracts.py`
- `tests/test_api_contracts.py`
