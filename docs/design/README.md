# Design

UI/UX design documentation for RoastLogger. This folder is the **single source of truth** for how the app looks and feels — colour, typography, spacing, components, screens, and patterns. Feature docs in [`../features/`](../features/) cover *what the app does*; design docs cover *what the app looks like and why*.

Read [principles.md](./principles.md) first if you are new to the project.

## Navigation

```text
design/
├── principles.md              Six design principles
├── foundations/               Design tokens
│   ├── color.md               Palette, CSS variables, semantic roles
│   ├── typography.md          Font stack, type scale, instrument numerics
│   ├── spacing-layout.md      Spacing, touch targets, breakpoints, grids
│   └── dark-mode.md           Dark-mode system (CSS variable overrides + chart colours)
├── components/                Reusable UI components
│   ├── buttons.md             .btn variants, sizes, states
│   ├── instrument-displays.md Top-bar tiles, steppers, event buttons
│   ├── cards-surfaces.md      Cards, panels, shadows, elevation
│   ├── forms.md               Inputs, selects, form rows
│   └── navigation.md          Stable header and route transitions
├── screens/                   Screen-specific design specs
│   ├── live-roasting.md       Top-bar layout for the live roast view
│   ├── label-creator.md       Modal canvas editor for bean labels
│   ├── sticker-sheet.md       Modal editor for US-4 sticker sheets
│   ├── settings.md            Settings modal and sync preflight states
│   ├── roast-detail.md        Read-only roast view
│   └── bean-inventory.md      Beans list + bean detail
└── patterns/                  Recurring design systems
    ├── label-templates.md     Four label templates as a design system
    └── sticker-templates.md   Physical sticker-sheet template specs
```

## Quick Index

**"What colour is X?"** → [foundations/color.md](./foundations/color.md)
**"What font should this use?"** → [foundations/typography.md](./foundations/typography.md)
**"How big should this touch target be?"** → [foundations/spacing-layout.md](./foundations/spacing-layout.md)
**"How do I make this dark-mode aware?"** → [foundations/dark-mode.md](./foundations/dark-mode.md)
**"How does the live roast screen work?"** → [screens/live-roasting.md](./screens/live-roasting.md)
**"How should Roasts and Beans transition?"** → [components/navigation.md](./components/navigation.md)
**"How does sync preflight appear in Settings?"** → [screens/settings.md](./screens/settings.md)
**"How do I add a new label template?"** → [../features/adding-label-templates.md](../features/adding-label-templates.md) (step-by-step) + [patterns/label-templates.md](./patterns/label-templates.md) (design system)
**"How is US-4 sticker stock laid out?"** → [patterns/sticker-templates.md](./patterns/sticker-templates.md)

## Design Philosophy

RoastLogger is a **tablet-first instrument panel** for home coffee roasters. The six governing principles are covered in full in [principles.md](./principles.md):

1. **Two density contexts** — compact 44px management controls and protected 54px live-roast controls.
2. **Chart dominance** — the roast curve is always the largest thing on screen.
3. **Glanceable readings** — instrument numerics legible from ~60 cm, monospaced so digits don't jitter.
4. **Minimal chrome during a roast** — collapse anything that isn't about the active roast.
5. **Dark mode is first-class** — roasteries are dim; the dark palette is a peer, not a theme.
6. **Stable workspace continuity** — native Roasts/Beans navigation uses restrained, optional motion without changing URLs.

## Conventions for Design Docs

When adding or editing a design doc:

- Every doc **must link to at least one concrete code path** (CSS variable, class name, file) so the design system stays tied to the implementation.
- New UI must consume `var(--*)` tokens and reference an existing component recipe under `components/`. If a new visual pattern does not fit an existing recipe, add the component doc in the same change.
- Do not add ad-hoc page CSS for reusable controls. Put shared controls in `static/css/components/` and screen-only layout in `static/css/screens/`.
- Foundations answer *"what value?"*. Components answer *"what recipe?"*. Screens answer *"where does each component go?"*. Patterns answer *"how does this family of things work as a system?"*.
- Design content should live here, not duplicated in feature docs. If you find yourself writing "the button is …" in a feature doc, move it to [components/buttons.md](./components/buttons.md) and link.
