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

Each section uses a neutral token border in both light and dark modes, with no
decorative color strip or other accent along its edge. The uppercase H2 divider
provides hierarchy; section headings are labels for scanability, not marketing
copy.

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

## Compact Management Forms

Bean add/edit and Roast edit add `.management-form` to the existing `.form`
contract. Sections retain their semantic headings, field names, labels,
validation, and DOM order while the layout uses available width.

- Bean Profile and Flavor Notes sit side by side from `1024px`; Inventory then
  spans the full form and exposes its four fields as a source-ordered grid.
- Roast Basic Information spans the form and uses three columns; Weights and
  Notes share the next row. Historical Roast Data remains full width so its
  chart and tables do not shrink.
- `.management-form-section` applies compact padding and removes unnecessary
  elevation. Labels stay above controls and all interactive targets remain at
  least `var(--control-min)`.
- `.management-form-actions` is sticky at the viewport bottom on screen. It
  includes `env(safe-area-inset-bottom)`, stays after the final field in the
  DOM, and returns to `position: static` for print.
- Inputs receive a scroll margin larger than the action row so browser focus
  and validation navigation can reveal the complete field.
- Below `768px`, the form and every nested grid collapse to one logical column;
  Save/Add remains before Cancel.

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
