# Typography

Three shared typefaces are loaded globally from Google Fonts in [templates/base.html](../../../templates/base.html). Three label-only faces are requested by [templates/beans_detail.html](../../../templates/beans_detail.html), the only page that can open the label creator. Each has a specific role.

## Font Stack

| Family | Weights loaded | Used for |
|---|---|---|
| **Inter** | 300, 400, 500, 600, 700 | Body text, default UI font, label-creator body text |
| **DM Mono** | 400, 500 | All instrument-panel numerics (timer, temperature, RoR, steppers); Technical label preset |
| **Raleway** | 400, 600, 800, 900 | Record titles (bean/roast names) and Modern label preset |
| **Playfair Display** | 400, 700, 900 | Editorial label preset (bean name) |
| **Barlow Condensed** | 400, 600, 700, 800 | Bold label preset (bean name) |
| **Roboto Slab** | 300, 400, 500, 700 | Craft label preset (bean name + body) |

The body font stack in [static/css/style.css](../../../static/css/style.css) is:

```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
```

## Type Roles

### Instrument numerics — `DM Mono`

Any number that updates in real time and must be read at a glance uses DM Mono. Fixed-width digits prevent horizontal jitter when values change.

- Top-bar tile value (`.tb-value`): `2.5rem / 40px`, weight 500.
- FC elapsed tile (`.tb-value-fc`): `2rem / 32px`, weight 500.
- Top-bar unit (`.tb-unit`): `0.9375rem / 15px`.
- Stepper value (`.stepper-value`): `1.5rem / 24px`, weight 700.

Legacy screens still use `'Courier New', monospace` as a fallback — new code should use `'DM Mono', 'Courier New', monospace`.

### Headings — `Inter`, 600 weight

Page headers, card headers, section titles. Letter spacing stays at `0`; avoid negative tracking because it makes operational screens look brittle at smaller sizes.

### Record titles — `Raleway`, 700-800 weight

Bean names and roast names use the display stack through `--font-display`. This applies to:

- List links: `.bean-record-title`, `.roast-record-title`
- Detail page titles: `.record-title-heading`
- Edit form title fields: `.form-group-title input`

The goal is a small amount of roastery character in the records themselves, while labels, dates, prices, and controls remain in the neutral UI font.

### Body — `Inter`, 400 weight

Default UI text. Line height `1.6`. Labels use `0.875rem / 14px` with uppercase transform and `0.5px` letter-spacing (see `.panel-label`, `.tb-label`).

### Buttons — `Inter`, 500 weight

Button text is one step smaller than body (`0.875rem`). Small buttons drop to `0.8125rem`; large buttons use `1rem`.

### Label display faces

The bean label creator uses the four display faces (Raleway, Playfair, Barlow Condensed, Roboto Slab) plus DM Mono across five font presets. Playfair, Barlow Condensed, and Roboto Slab remain label-only. Raleway is also the UI record-title face. See [../patterns/label-templates.md](../patterns/label-templates.md) for the preset → face mapping.

## Type Scale

Sizes used across the UI, from largest to smallest:

| Size | Usage |
|---|---|
| `3rem / 48px` | Legacy timer / temp panels (`.panel-value`) |
| `2.5rem / 40px` | Live top-bar tile values |
| `2rem / 32px` | Page-header H1, FC elapsed tile |
| `1.5rem / 24px` | Stepper value, section H2 |
| `1.25rem / 20px` | Navbar brand, review rating |
| `1rem / 16px` | Default body |
| `0.9375rem / 15px` | Form inputs, top-bar unit |
| `0.875rem / 14px` | Button default, secondary meta |
| `0.8125rem / 13px` | Small buttons |
| `0.5625rem / 9px` | Top-bar tile label (`.tb-label`, with `0.12em` tracking) |

## Loading

`templates/base.html` requests Inter, Raleway, and DM Mono once. The token
stylesheet contains no remote font import, so ordinary Roasts, Beans, forms,
Settings, and live-roast pages do not duplicate the request. Bean detail adds
Playfair Display, Barlow Condensed, and Roboto Slab through its `extra_head`
block. The label creator still waits for `document.fonts.ready` in
[static/js/label-creator.js](../../../static/js/label-creator.js) before canvas
drawing, preserving every printable preset without loading label-only faces on
unrelated pages.
