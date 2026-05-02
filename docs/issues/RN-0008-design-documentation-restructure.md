---
id: RN-0008
title: Design Documentation Restructure
type: todo
status: resolved
priority: medium
created: 2026-04-20
resolved: 2026-04-24
area: docs
tags:
  - design-system
  - documentation
---

# Design Documentation Restructure

## Description

The `docs/design/` folder contained only ad-hoc docs (`README.md`, `dark-mode.md`, `live-roasting-screen.md`). Significant design content was scattered across feature docs (notably `bean-label-creator.md` and `live-roasting.md`). Request: come up with a better doc structure within `docs/design/` and write the full set of design docs.

## Resolution

Restructured `docs/design/` into four subfolders and wrote the full documentation set:

```text
docs/design/
├── README.md                       Navigation + philosophy
├── principles.md                   Five design principles
├── foundations/                    Design tokens
│   ├── color.md
│   ├── typography.md
│   ├── spacing-layout.md
│   └── dark-mode.md                (moved from docs/design/dark-mode.md)
├── components/                     Reusable UI components
│   ├── buttons.md
│   ├── instrument-displays.md
│   ├── cards-surfaces.md
│   └── forms.md
├── screens/                        Screen-specific specs
│   ├── live-roasting.md            (moved from docs/design/live-roasting-screen.md)
│   ├── label-creator.md
│   ├── roast-detail.md
│   └── bean-inventory.md
└── patterns/
    └── label-templates.md          (4 templates × 5 font presets × 5 ratios)
```

Trimmed design content from `docs/features/bean-label-creator.md` and `docs/features/live-roasting.md` and linked back to the canonical design docs — feature docs now cover behaviour / API / data model only.

Updated top-level navigation in `docs/README.md` to include the `design/` section.

## Related Files

- `docs/design/**` (14 new docs + rewritten README)
- `docs/features/bean-label-creator.md`
- `docs/features/live-roasting.md`
- `docs/README.md`
- `docs/issues/README.md`
