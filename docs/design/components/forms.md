# Forms

Form inputs, selects, textareas, and the form containers that hold them. Defined in [static/css/style.css](../../../static/css/style.css) under `Forms`.

## Form Container (`.form`)

The outer wrapper on full-page forms (add/edit bean, roast edit):

```css
background: var(--card-bg);
padding: 2rem;
border-radius: 8px;
box-shadow: var(--shadow);
```

Internally subdivided into `.form-section` blocks (with an H2 heading in `--primary-color`) and `.form-group` rows.

## Form Group (`.form-group`)

Label-above-input pattern:

```
Label                       ← 0.5rem below input, weight 500, text-color
[ input                 ]   ← 100% width, 0.625rem 0.875rem padding
```

- `margin-bottom: 1.5rem` between groups.
- Label: `display: block; font-weight: 500;`.

## Inputs, Selects, Textareas

All three share the same visual treatment:

```css
width: 100%;
padding: 0.625rem 0.875rem;
border: 1px solid var(--border-color);
border-radius: 6px;
font-size: 0.9375rem;
background-color: var(--card-bg);
```

**States**

| State | Treatment |
|---|---|
| Hover | `border-color: var(--secondary-color)` |
| Focus | `border-color: var(--primary-color)` + `box-shadow: 0 0 0 3px rgba(107, 91, 77, 0.1)` — a soft halo ring, not a hard outline |
| Disabled / readonly | No explicit rule; lean on browser defaults |

## Form Rows (`.form-row`)

Multi-column input layouts:

```css
.form-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
}
```

Auto-fit keeps columns full-width on narrow screens and collapses to stacks below ~400px.

## Form Actions (`.form-actions`)

Button row at the bottom of a form:

```css
display: flex;
gap: 1rem;
margin-top: 2rem;
flex-wrap: wrap;
```

Primary action goes first (`.btn-primary`). Destructive actions go last (or are moved to the page-header dropdown menu).

## Live-Roast Settings Rows

The live-roast screen reuses `.form-group` but packs rows tighter:

- `.settings-row-temp` — single-column, 1 input (temperature hidden input, now auto-filled).
- `.settings-row-fp` — two-column grid for Fan and Power steppers. Each cell is a `.form-group` containing a label + `.stepper-control` ([see instrument-displays.md](./instrument-displays.md#stepper-control-stepper-control)).
- All inputs and stepper controls in these rows are locked to `44px` height.

## Dark Mode

Inputs/selects/textareas have an explicit dark-mode rule (`body.dark-mode .form-group input, ...`) that swaps `background-color` to `var(--bg-color)` — the input sits slightly *below* the card surface, matching the inset feel of instrument panels. Focus halo uses the same `rgba(107, 91, 77, 0.1)` — the warm-brown halo reads fine against both palettes.

## Accessory Components

- **`.calc-display`** — readonly computed value shown beside an input (e.g. loss % on roast edit). Light grey chip (`#f0f0f0`), `--primary-color` text, `0.75rem` padding, 4px radius.
- **`.info-text`** — blue-tinted note box for instructional copy inside a form. `#e3f2fd` background, `#2196F3` left border. Used sparingly — most forms don't need an info box.
