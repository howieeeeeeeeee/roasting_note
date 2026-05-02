---
id: RN-0016
title: New Design System Rollout & Full UI Redesign
type: feature
status: pending
priority: high
created: 2026-05-01
resolved:
area: design-system
tags:
  - design
  - design-system
  - redesign
  - tokens
  - dark-mode
---

# New Design System Rollout & Full UI Redesign

## Description

Adopt a new design system delivered as an Anthropic design bundle and apply it across every screen of RoastLogger in a single coordinated change. This ticket installs the design tokens, base components, and updated design docs that future work will follow, and restyles every existing template against the new system. After this lands, "adding a new thing" should mean composing tokens and component recipes from `docs/design/` rather than authoring ad-hoc CSS.

## Details

- **Source of truth — design bundle**: <https://api.anthropic.com/v1/design/h/AwN20px-BxgCZwbgYpD2ZA>. The endpoint returns a gzipped tar (~894 KB) containing a README and design assets. Implementer must fetch, unpack, and read the README before any styling work.
- **Scope**: full app redesign. All eight templates and the entirety of `static/css/style.css` (4,268 lines) are in scope. Rip-and-replace, not progressive.
- **Anchor screens** (land + review against the system first, before the rest of the app):
  1. Beans inventory — `templates/beans_list.html`, `templates/beans_detail.html`, `templates/beans_form.html`.
  2. Roast detail / history — `templates/roast_detail.html`, `templates/index.html` (history table).
- **Remaining screens** restyled in the same ticket once anchors are validated: `templates/base.html`, `templates/roast_live.html`, `templates/roast_edit.html`, plus the label-creator and sticker-sheet modals embedded in the bean templates.
- **Design system installation** updates the existing `docs/design/` structure (do not create a parallel folder). Refresh:
  - `docs/design/principles.md` if any of the five principles (tablet-first, chart dominance, glanceable readings, minimal chrome, dark-mode first-class) is changed or replaced.
  - `docs/design/foundations/{color,typography,spacing-layout,dark-mode}.md` with new token values.
  - `docs/design/components/{buttons,cards-surfaces,forms,instrument-displays}.md` with updated recipes.
  - `docs/design/screens/*.md` with new layouts.
  - `docs/design/patterns/*.md` if label/sticker patterns are touched.
  - `docs/design/README.md` navigation if file structure changes.
- **CSS approach**: rip and replace `static/css/style.css`. New component styles must consume `var(--*)` tokens — no hardcoded hex anywhere. No orphan rules referring to deleted classes.
- **Dark mode parity**: every new token has paired light + dark values. Dark mode remains first-class, not a tacked-on theme.
- **Live roasting constraints survive the redesign**: ≥54px touch targets on roasting-critical controls, chart dominance preserved, monospaced numerics for timer/temperature/RoR. If the new system clashes with any of these, raise it in Open Questions before merging — do not silently relax the principle.
- **Forward-looking convention**: capture in `docs/design/README.md` that all new UI must (a) consume `var(--*)` tokens and (b) link to a component recipe under `docs/design/components/`. Ad-hoc styling is not allowed post-rollout.
- **Out of scope**: backend behaviour, API contracts, data model, hardware integration, label / sticker template *content* (visual styling of those templates is in scope; the printable layouts they generate are not).
- please note that i want to keep th ecurrent roast live interaction untouched, this is the key.

## Implementation Notes

- 2026-05-02 refinement pass: edit bean now uses the same `.form-section` design-system panels as edit roast, grouped by Bean Profile, Flavor Notes, and Inventory.
- Shared form controls now use tokenized inset fields, a section accent rule, and `.form-group-title` for bean/roast names.
- Beans table now uses a fixed `colgroup`, centered sortable metric columns, and horizontal overflow so Stock, Purchase Date, and Price/kg headers align with their values.
- Bean and roast record names now use the `--font-display` title role (`Raleway`) in list rows, detail headers, and title inputs.
- Follow-up: roast list/history tables no longer expose an Actions header/column. Row actions render only as a right-edge hover/focus overlay on a neutral row highlight, edit forms are left-aligned at a wider max width, and empty review panels use a compact Add Review button.
- Follow-up: sticker sheet modal now uses reduced chrome and viewport-bounded preview sizing so the full sheet stays visible; the selected-image list handles overflow internally.
- Follow-up: review card hover now uses a neutral grey contour instead of the dark primary outline.
- Follow-up: review cards no longer use a left color strip; they use a plain neutral border at rest.

## Acceptance Criteria

- [ ] Design bundle fetched, unpacked, and its README summarized in the implementing branch's PR description.
- [ ] New design tokens (color, typography, spacing, radii, shadows) live as CSS variables in `static/css/style.css` (or a dedicated tokens file imported from it), with full light + dark coverage.
- [ ] `static/css/style.css` rewritten end-to-end with no orphan rules referring to deleted classes.
- [ ] All eight templates restyled against the new system: `base.html`, `index.html`, `beans_list.html`, `beans_detail.html`, `beans_form.html`, `roast_detail.html`, `roast_edit.html`, `roast_live.html`.
- [ ] Beans inventory and roast detail/history screens explicitly called out as the anchor reference for the new system in `docs/design/screens/`.
- [ ] Live roasting screen re-verified against principles 1–4 (touch targets ≥54px, chart dominance, glanceable monospaced numerics, minimal chrome) under the new tokens.
- [ ] Dark mode verified on every restyled screen.
- [ ] All design docs updated: `docs/design/README.md`, `docs/design/principles.md`, every file under `foundations/`, `components/`, `screens/`, and any touched files under `patterns/`.
- [ ] `docs/design/README.md` documents the post-rollout convention: new UI consumes `var(--*)` tokens and links to a component recipe — no ad-hoc styles.
- [ ] `uv run pytest` passes.
- [ ] Manually verified in a browser at tablet width (1024px) and desktop width (1440px), in both light and dark mode.
- [ ] Relevant docs updated when implemented: `docs/design/README.md`, `docs/design/principles.md`, `docs/design/foundations/*.md`, `docs/design/components/*.md`, `docs/design/screens/*.md`, `docs/design/patterns/*.md` (if touched), and `docs/architecture/tech-stack.md` (only if a new CSS framework, font, or icon dependency is added).

## Open Questions

- What is the design system named in the bundle's README, and what palette / type scale / icon set does it ship? — answer:
- Does the new system change any of the five existing design principles (especially "tablet-first" and "dark-mode first-class")? If a principle is replaced, `principles.md` must be rewritten, not appended to. — answer:
- Should the existing warm-roastery palette (`#0E0D0B` base, `#C9A87A` accent) be preserved, replaced, or layered with a brand accent from the new system? — answer:
- Are there new components in the bundle that don't map to existing recipes (`buttons`, `cards-surfaces`, `forms`, `instrument-displays`)? If yes, add new files under `docs/design/components/` rather than expanding existing ones. — answer:
- Does the bundle ship icons or illustrations? If yes, where should they live under `static/img/` and how should templates reference them? — answer:
- Does the new system specify a CSS framework, utility library, or font CDN that introduces a new dependency? If yes, this ticket also updates `docs/architecture/tech-stack.md`. — answer:
- Land as one large PR or split into foundations PR + per-screen PRs? Current direction is one merge per the user's "rip and replace" choice — confirm before opening the first PR. — answer:
- Any rollout date or event tied to this work? — answer:

## Related Files

- `static/css/style.css`
- `static/img/`
- `templates/base.html`
- `templates/index.html`
- `templates/beans_list.html`
- `templates/beans_detail.html`
- `templates/beans_form.html`
- `templates/roast_detail.html`
- `templates/roast_edit.html`
- `templates/roast_live.html`
- `docs/design/README.md`
- `docs/design/principles.md`
- `docs/design/foundations/color.md`
- `docs/design/foundations/typography.md`
- `docs/design/foundations/spacing-layout.md`
- `docs/design/foundations/dark-mode.md`
- `docs/design/components/buttons.md`
- `docs/design/components/cards-surfaces.md`
- `docs/design/components/forms.md`
- `docs/design/components/instrument-displays.md`
- `docs/design/screens/bean-inventory.md`
- `docs/design/screens/roast-detail.md`
- `docs/design/screens/live-roasting.md`
- `docs/design/screens/label-creator.md`
- `docs/design/screens/sticker-sheet.md`
- `docs/design/patterns/label-templates.md`
- `docs/design/patterns/sticker-templates.md`
