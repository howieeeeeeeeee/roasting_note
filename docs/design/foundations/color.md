# Color

RoastLogger uses a warm, earth-toned palette. Colours are defined as CSS custom properties in [static/css/style.css](../../../static/css/style.css) and consumed everywhere via `var(--*)`. Dark mode is a second set of values applied on `body.dark-mode` — see [dark-mode.md](./dark-mode.md).

## Token Reference

| Token | Light | Dark | Role |
| --- | --- | --- | --- |
| `--primary-color` | `#6B5B4D` | `#C9A87A` | Headings, active states, numeric readouts, primary buttons |
| `--primary-hover` | `#5A4A3D` | `#D9B88A` | Primary button hover |
| `--secondary-color` | `#8B7D6B` | `#9A8A78` | Secondary buttons, input hover borders |
| `--accent-color` | `#A89884` | `#7A6A58` | Supporting accents |
| `--ok` / `--ok-text` | `#6B8E6F` / `#486A4D` | `#7FB385` | Positive graphics and text-safe status copy |
| `--err` / `--err-text` | `#B85C5C` / `#974646` | `#D07070` / `#DC8080` | Danger graphics and text-safe status copy |
| `--warn` / `--warn-text` | `#C4893A` / `#8A5C1F` | `#D4A060` | Warning graphics and text-safe status copy |
| `--text-color` | `#2C2C2C` | `#EDE9E3` | Body text |
| `--txt2` / `--text-light` | `#666666` | `#B8B1A8` | Secondary labels, helper text, and metadata |
| `--txt3` | `#726D69` | `#9A948C` | Tertiary text, placeholders, and inactive navigation |
| `--bg-color` | `#FAFAF9` | `#0E0D0B` | Page background |
| `--card-bg` | `#FFFFFF` | `#171512` | Cards, panels, navbar, modals |
| `--border-color` | `#E8E6E3` | `#2A2620` | Borders, dividers |
| `--shadow` | `0 1px 3px rgba(0,0,0,0.08)` | `0 1px 4px rgba(0,0,0,0.4)` | Default card shadow |
| `--shadow-hover` | `0 2px 6px rgba(0,0,0,0.12)` | `0 2px 8px rgba(0,0,0,0.5)` | Card hover shadow |

## Semantic Roles

**`--primary-color`** is the dominant accent. It colours all numeric instrument readouts (timer, temperature, RoR), primary CTAs, active tab underlines, and card headings. In dark mode it is intentionally lighter and warmer (`#C9A87A` tan) rather than a darker version of the light primary — muted browns disappear on dark backgrounds.

The browser favicon (`static/img/favicon.svg`) uses the Material `local_cafe` glyph filled with the light primary brown (`#6B5B4D`). It is hardcoded in the SVG because browser favicon rendering cannot reliably consume CSS variables or respond to app dark mode.

**`--success-color`** aliases the text-safe success role and is reserved for
**positive confirmation of user action** (a fired event button) and the **RoR
line** on the chart. `--ok` remains available for non-text fills and borders.
It is not used for generic "success" toasts without prior user action.

**`--danger-color`** aliases `--err-text` and is reserved for **destructive or
irreversible** actions (End Roast, Archive Bean, Delete) and for the **First
Crack badge** on the live screen. `--err` remains the decorative fill and
border role. Using danger anywhere else dilutes the signal.

**Bean accent colours** are user-defined per bean (stored in `bean.color`) and flow through to the bean color indicator dot, the left accent band on Strip labels, corner dots on Washi labels, etc. They are independent of the palette above.

### Text and decorative contrast

`--txt2`, `--txt3`, and the `--*-text` semantic roles are readable text
colors. Each reaches WCAG AA on
the documented page, primary surface, and secondary surface backgrounds in
light and dark modes, including semantic tinted backgrounds. Filled buttons
pair the stronger text-safe semantic fill with `--on-*` foreground tokens so
their labels remain readable in either theme. Use `--bd`, `--bd2`, and the
base semantic tokens for intentionally faint borders, rules, and other
non-text decoration. Do not lower visible text contrast to make a separator
quieter.

Global toasts use one neutral border around the whole surface. They do not use
a colored left rail. Error and warning copy may use the text-safe semantic
roles; success keeps the ordinary text color so status does not become a
decorative card treatment.

## Warm-Earth Rationale

Both palettes share a brown/tan undertone rather than a neutral grey. The light background `#FAFAF9` is not pure white; the dark background `#0E0D0B` is not pure black. This matches the coffee/roastery aesthetic and avoids the sterile feel of a pure-neutral UI.

## Usage Rules

1. **Never hardcode a palette colour in new CSS.** Use `var(--primary-color)` etc. Dark mode will then adapt automatically.
2. **Canvas and chart colours** (which cannot consume CSS variables) must listen for the `darkmodechange` event and swap their own palette. See [dark-mode.md](./dark-mode.md#chart-colours).
3. **Bean accent colours are user-provided** — treat them as arbitrary hex values. Do not assume sufficient contrast; the label renderer pairs them with light or dark template backgrounds that already provide contrast.
4. **Text tokens remain text-safe.** Placeholders, small headings, inactive navigation, and helper text use `--txt2` or `--txt3`; decorative marks use border tokens.
