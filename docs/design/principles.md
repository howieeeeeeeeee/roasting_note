# Design Principles

The five principles below govern every visual and interaction decision in RoastLogger. When a new screen or component is designed, it should be checkable against each of them.

## 1. Tablet-first for live roasting

The live roasting screen is used with a tablet propped next to a hot roaster. Interaction is thumb-based, one-handed, and glanced at — not scrolled through.

- Primary touch targets are **≥ 54px** on a side.
- Controls live within thumb reach from either edge of the tablet.
- Layout does not depend on hover or right-click.

## 2. Chart dominance

The roast curve is the most information-dense element on any screen it appears on and is always the largest. Other readings (timer, temperature, RoR) support the chart, they do not compete with it.

- Chart uses `flex: 1` inside the live screen layout ([static/css/style.css](../../static/css/style.css) — `.live-chart-area`).
- Secondary panels (event log, notes) do not occupy horizontal space alongside the chart during a roast.

## 3. Glanceable readings

Timer, Temperature, and Rate of Rise must be legible from **~60 cm away**. Roasters are often moving, so numeric values use a monospaced face so digit widths do not jitter as values change.

- Large numerics use **DM Mono** (see [foundations/typography.md](./foundations/typography.md)).
- Top-bar tile value font size: `2.5rem` (40px) at 1x.
- Colour contrast is always evaluated on the dark palette too — dark mode is where most roasting happens.

## 4. Minimal chrome during a roast

Once roasting starts, every pixel that is not about *what is happening right now* is a distraction.

- The setup section collapses to a thin bar once the roast begins.
- Decorative labels, section headers, and icons are removed from the live view.
- Event log and notes are accessed on demand, not always visible.

## 5. Dark mode is first-class

Roasteries and garages are dimly lit. Dark mode is not a tacked-on theme — it uses the same CSS variable system as light mode, so every component adapts automatically.

- Palette uses **warm** undertones (`#0E0D0B` base, `#C9A87A` accent) — never cold pure-black.
- All new components must consume `var(--*)` tokens rather than hardcoded hex.
- See [foundations/dark-mode.md](./foundations/dark-mode.md) for the full system.
