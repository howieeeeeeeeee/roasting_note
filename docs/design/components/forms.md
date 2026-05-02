# Forms

Form inputs, selects, textareas, and the form sections that hold them. Defined in [static/css/components/forms.css](../../../static/css/components/forms.css).

## Form Container (`.form`)

The outer wrapper on full-page forms (add/edit bean, roast edit) is intentionally unframed. It only constrains width:

```css
width: min(100%, 1280px);
margin: 0;
```

The visible surfaces are `.form-section` panels. Forms are left-aligned inside the page container so desktop edit screens do not leave a large unused column on the right.

## Form Section (`.form-section`)

Used for logical groups such as Bean Profile, Flavor Notes, Inventory, Basic Information, Weights, and Notes.

```css
background: var(--surf);
border: 1px solid var(--bd);
border-radius: var(--radius-xl);
padding: var(--space-7);
box-shadow: var(--shadow-sm);
```

Each section has a subtle primary accent rule on the left edge and an uppercase H2 divider. Section headings are labels for scanability, not marketing copy.

## Form Group (`.form-group`)

Label-above-input pattern:

```
Label                       ← 0.5rem above input, weight 600, muted text
[ input                 ]   ← 100% width, 46px minimum height
```

- `margin-bottom: var(--space-4)` between groups.
- Label: `display: block; font-weight: 600;`.
- `.form-group-title` is reserved for bean names and roast titles. Its text input uses `--font-display`, `var(--text-lg)`, and 700 weight so record names feel intentional without affecting data-entry fields.

## Inputs, Selects, Textareas

All three share the same inset treatment:

```css
width: 100%;
min-height: 46px;
padding: 0.65rem 0.875rem;
border: 1px solid var(--bd);
border-radius: var(--radius-md);
background: var(--surf2);
```

**States**

| State | Treatment |
|---|---|
| Hover | Inherits the base border; avoid noisy hover chrome on dense forms |
| Focus | `border-color: var(--pr)` + `box-shadow: 0 0 0 3px var(--pr-l)` and `background: var(--surf)` |
| Disabled / readonly | No explicit rule; lean on browser defaults |

## Form Rows (`.form-row`)

Multi-column input layouts:

```css
.form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-4);
}
```

Rows collapse to one column below 768px.

## Form Actions (`.form-actions`)

Button row at the bottom of a form:

```css
display: flex;
gap: var(--space-3);
flex-wrap: wrap;
justify-content: flex-end;
```

Primary action goes first (`.btn-primary`). Destructive actions go last (or are moved to the page-header dropdown menu).

## Live-Roast Settings Rows

The live-roast screen reuses `.form-group` but packs rows tighter:

- `.settings-row-temp` — single-column, 1 input (temperature hidden input, now auto-filled).
- `.settings-row-fp` — two-column grid for Fan and Power steppers. Each cell is a `.form-group` containing a label + `.stepper-control` ([see instrument-displays.md](./instrument-displays.md#stepper-control-stepper-control)).
- All inputs and stepper controls in these rows are locked to `44px` height.

## Dark Mode

Inputs, sections, helpers, and focus rings inherit from semantic tokens. Dark mode is handled by token overrides on `body.dark-mode`; form CSS does not need component-specific dark overrides.

## Accessory Components

- **`.calc-display`** — readonly computed value shown beside an input (e.g. loss % on roast edit). Uses `--font-mono`, `--surf2`, dashed `--bd`, and `--pr` text.
- **`.short-flavor-editor`** — tokenized chip-input surface used by add/edit bean. It matches field height, uses `--surf2` when idle, and switches to `--surf` on focus.
- **`.color-picker-wrapper`** — compact input group for bean label colour. The swatch and mono hex preview sit inside one tokenized field shell.
- **`.info-text`** — small helper text block for form caveats. Use sparingly; most forms should rely on field labels.
