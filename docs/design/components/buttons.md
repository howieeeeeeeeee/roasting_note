# Buttons

Defined in [static/css/style.css](../../../static/css/style.css) under the `Buttons` section (`.btn` and variants).

## Anatomy

```css
.btn {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.625rem 1.25rem;
    border: 1px solid var(--border-color);
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 500;
    background-color: var(--card-bg);
    color: var(--text-color);
}
```

All buttons use `inline-flex` so a Material icon and a label can sit on the same line with a consistent `0.375rem` gap.

## Variants

| Class | Fill | When to use |
|---|---|---|
| `.btn` (default) | `var(--card-bg)` | Neutral action (Back, Cancel). Border turns primary on hover |
| `.btn-primary` | `var(--primary-color)` | Default positive action (Save, Create, Edit) |
| `.btn-secondary` | `var(--secondary-color)` | Back / neutral navigation actions |
| `.btn-success` | `var(--success-color)` | Confirm-style actions (rarely used — `.live-ev-btn.fired` covers event confirmation) |
| `.btn-danger` | `var(--danger-color)` | Destructive or irreversible (End Roast, Archive Bean, Delete) |

## Sizes

| Class | Padding | Font |
|---|---|---|
| `.btn-sm` | `0.4rem 0.875rem` | `0.8125rem` |
| `.btn` (default) | `0.625rem 1.25rem` | `0.875rem` |
| `.btn-lg` | `0.875rem 1.75rem` | `1rem` |

`.btn-lg` is used for primary actions on the live roasting top bar (`End Roast`).

## Icon Buttons

`.btn-icon` is a borderless square tap target used for inline actions in tables, card footers, and dropdown triggers.

```css
.btn-icon {
    padding: 0.25rem;
    border-radius: 4px;
    color: var(--text-light);
}
.btn-icon:hover { color: var(--primary-color); }
```

Material icons inside sit at `1.125rem`. Danger variant (`.btn-icon-danger:hover`) uses a light red background.

### Settings Controls

The Settings gear declares `aria-haspopup="dialog"`, names the sheet with
`aria-controls`, and reflects open state with `aria-expanded`. The
`.settings-close` control is a real button with a visible Material close icon,
an accessible **Close Settings** name, and a fixed `44px` target.

The Sensor, Data, and Advanced controls use `.settings-tab`, not pill buttons.
They form a single-select tablist with one selected tab and one keyboard tab
stop. The selected state uses a two-pixel primary underline. Arrow keys, Home,
and End change the selected section. All Settings actions retain at least a
`44px` target, a non-wrapping label, and a visible `:focus-visible` outline.

See [Settings sheet](../screens/settings.md) for the complete focus and section
behavior.

## States

- **Hover**: default `.btn` shifts its border to `--primary-color` and its background to `--bg-color`. Variant buttons darken their fill (see `.btn-primary:hover`, `.btn-success:hover`). `.btn-success:hover` uses `!important`-free hardcoded darker value `#5d7d61` with a comment explaining why it must beat the base `.btn:hover` border.
- **Disabled**: `opacity: 0.5; cursor: not-allowed;` — used on event buttons before the roast starts.
- **Active / fired**: `.live-ev-btn.fired` receives a green tint and stays in that state (see [instrument-displays.md](./instrument-displays.md#event-buttons)).

## Dark Mode

Palette variants adapt automatically because they consume palette tokens. The default `.btn` (uses `--card-bg`) is explicitly mapped via the dark-mode section — its border and background both follow `var(--border-color)` and `var(--card-bg)`.
