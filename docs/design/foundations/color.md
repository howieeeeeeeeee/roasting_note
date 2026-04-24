# Color

RoastLogger uses a warm, earth-toned palette. Colours are defined as CSS custom properties in [static/css/style.css](../../../static/css/style.css) and consumed everywhere via `var(--*)`. Dark mode is a second set of values applied on `body.dark-mode` — see [dark-mode.md](./dark-mode.md).

## Token Reference

| Token | Light | Dark | Role |
|---|---|---|---|
| `--primary-color` | `#6B5B4D` | `#C9A87A` | Headings, active states, numeric readouts, primary buttons |
| `--primary-hover` | `#5A4A3D` | `#D9B88A` | Primary button hover |
| `--secondary-color` | `#8B7D6B` | `#9A8A78` | Secondary buttons, input hover borders |
| `--accent-color` | `#A89884` | `#7A6A58` | Supporting accents |
| `--success-color` | `#6B8E6F` | `#7FB385` | Fired event buttons, RoR line, success toasts |
| `--danger-color` | `#B85C5C` | `#D07070` | End Roast button, FC badge, destructive actions |
| `--text-color` | `#2C2C2C` | `#EDE9E3` | Body text |
| `--text-light` | `#666` | `#8A8680` | Labels, meta, secondary text |
| `--bg-color` | `#FAFAF9` | `#0E0D0B` | Page background |
| `--card-bg` | `#FFFFFF` | `#171512` | Cards, panels, navbar, modals |
| `--border-color` | `#E8E6E3` | `#2A2620` | Borders, dividers |
| `--shadow` | `0 1px 3px rgba(0,0,0,0.08)` | `0 1px 4px rgba(0,0,0,0.4)` | Default card shadow |
| `--shadow-hover` | `0 2px 6px rgba(0,0,0,0.12)` | `0 2px 8px rgba(0,0,0,0.5)` | Card hover shadow |

## Semantic Roles

**`--primary-color`** is the dominant accent. It colours all numeric instrument readouts (timer, temperature, RoR), primary CTAs, active tab underlines, and card headings. In dark mode it is intentionally lighter and warmer (`#C9A87A` tan) rather than a darker version of the light primary — muted browns disappear on dark backgrounds.

**`--success-color`** is reserved for **positive confirmation of user action** (a fired event button) and the **RoR line** on the chart. It is not used for generic "success" toasts without prior user action.

**`--danger-color`** is reserved for **destructive or irreversible** actions (End Roast, Archive Bean, Delete) and for the **First Crack badge** on the live screen. Using it anywhere else dilutes the signal.

**Bean accent colours** are user-defined per bean (stored in `bean.color`) and flow through to the bean color indicator dot, the left accent band on Strip labels, corner dots on Washi labels, etc. They are independent of the palette above.

## Warm-Earth Rationale

Both palettes share a brown/tan undertone rather than a neutral grey. The light background `#FAFAF9` is not pure white; the dark background `#0E0D0B` is not pure black. This matches the coffee/roastery aesthetic and avoids the sterile feel of a pure-neutral UI.

## Usage Rules

1. **Never hardcode a palette colour in new CSS.** Use `var(--primary-color)` etc. Dark mode will then adapt automatically.
2. **Canvas and chart colours** (which cannot consume CSS variables) must listen for the `darkmodechange` event and swap their own palette. See [dark-mode.md](./dark-mode.md#chart-colours).
3. **Bean accent colours are user-provided** — treat them as arbitrary hex values. Do not assume sufficient contrast; the label renderer pairs them with light or dark template backgrounds that already provide contrast.
