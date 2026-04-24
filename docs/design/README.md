# Design Documentation

This folder captures UI/UX design decisions for Howie's Roast Log — rationale, component patterns, and implementation notes. It lives alongside the code so decisions stay traceable.

## Contents

| File | What it covers |
|---|---|
| [`live-roasting-screen.md`](./live-roasting-screen.md) | Top Bar layout redesign, component breakdown, interaction notes |
| [`dark-mode.md`](./dark-mode.md) | How dark mode works, CSS variable approach, adding new components |

## Design Principles

1. **Tablet-first for live roasting.** The live screen is used propped next to a roaster. Touch targets ≥ 54px, controls reachable without repositioning hands.
2. **Chart dominance.** The roast curve is the most information-dense element — it should always be the largest thing on screen.
3. **Glanceable readings.** Timer, Temp, and RoR must be readable from ~60cm away without squinting.
4. **Minimal chrome during a roast.** Setup info collapses once roasting starts. No unnecessary labels or decorations while heat is on.
5. **Dark mode is a first-class feature.** Roasteries are often dimly lit. The dark palette is not an afterthought — it uses the same component system as light mode via CSS variable overrides.
