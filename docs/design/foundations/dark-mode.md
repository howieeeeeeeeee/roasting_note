# Dark Mode

**Affects:** All pages
**Toggle:** Navbar icon (top-right, next to Settings)
**Persistence:** `localStorage` key `roast-dark`

## Approach: CSS Variable Override

The stylesheet uses CSS custom properties throughout ([color.md](./color.md) has the full token table). Dark mode works by redefining those variables on `body.dark-mode` — no component-level overrides needed for most elements.

```css
/* Light (default) — defined in :root */
--primary-color:  #6B5B4D;
--bg-color:       #FAFAF9;
--card-bg:        #FFFFFF;
--border-color:   #E8E6E3;
--text-color:     #2C2C2C;

/* Dark — overrides on body.dark-mode */
--primary-color:  #C9A87A;
--bg-color:       #0E0D0B;
--card-bg:        #171512;
--border-color:   #2A2620;
--text-color:     #EDE9E3;
--txt2:           #B8B1A8;
--txt3:           #9A948C;
```

Any component that uses these variables automatically adapts. Explicit `body.dark-mode` rules are only needed for elements with **hardcoded colours** or that need special treatment (e.g. chart colours, which are set in JavaScript).

## Hierarchy and contrast parity

Light and dark modes use the same semantic hierarchy. Body copy uses `--txt`,
supporting copy uses `--txt2`, and tertiary visible text uses `--txt3`. Both
secondary roles meet WCAG AA on `--bg`, `--surf`, and `--surf2`. Borders use
`--bd` or `--bd2` and may be intentionally quieter because they do not carry
text.

Navigation, Settings, and management surfaces keep the same accent and
elevation meaning across themes. A section never switches to an inverted local
theme. Reduced-motion behavior is also identical in both modes.

## Toggle Implementation

Defined in [templates/base.html](../../../templates/base.html):

```javascript
function toggleDarkMode() {
    const isDark = document.body.classList.toggle('dark-mode');
    const icon   = document.getElementById('darkModeIcon');
    const btn    = document.getElementById('darkModeToggle');

    if (icon) icon.textContent = isDark ? 'light_mode' : 'dark_mode';
    if (btn)  btn.classList.toggle('active', isDark);

    localStorage.setItem('roast-dark', isDark ? '1' : '0');
    window.dispatchEvent(new CustomEvent('darkmodechange', { detail: isDark }));
}

// Restore on page load
if (localStorage.getItem('roast-dark') === '1') {
    document.body.classList.add('dark-mode');
}
```

The custom `darkmodechange` event lets page-specific scripts react without coupling to `base.html`. Currently only `roast_live.html` listens for it (to reinit the Chart.js chart with dark-aware colours).

## Chart Colours

Chart.js datasets use hardcoded colour strings, so they need special handling. `getChartColors()` in [templates/roast_live.html](../../../templates/roast_live.html) is called each time the chart is initialised:

```javascript
function getChartColors() {
    const dark = document.body.classList.contains('dark-mode');
    return {
        temp:    dark ? '#D4895A' : '#6B5B4D',
        tempBg:  dark ? 'rgba(212,137,90,0.15)'  : 'rgba(107, 91, 77, 0.1)',
        ror:     dark ? '#7FB385' : '#6B8E6F',
        rorBg:   dark ? 'rgba(127,179,133,0.1)'  : 'rgba(107, 142, 111, 0.1)',
        power:   dark ? 'rgba(201,168,122,0.35)' : 'rgba(139, 115, 85, 0.4)',
        fan:     dark ? 'rgba(127,179,133,0.35)' : 'rgba(90, 122, 94, 0.4)',
        grid:    dark ? 'rgba(255,255,255,0.06)' : 'rgba(0, 0, 0, 0.05)',
        axis:    dark ? '#6A6560' : '#666',
    };
}
```

On toggle, the page destroys the existing chart instance and calls `initChart()` again to rebuild with the new palette.

## Adding a New Component

To make a new UI component automatically support dark mode:

1. **Use CSS variables.** Reference `var(--card-bg)`, `var(--border-color)`, `var(--text-color)` etc. instead of hardcoded hex values. It just works.

2. **If you must hardcode** (e.g. a chart or canvas element), add a `darkmodechange` listener:
   ```javascript
   window.addEventListener('darkmodechange', (e) => {
       const isDark = e.detail;
       // update your hardcoded colours here
   });
   ```

3. **For edge cases** (e.g. an element that needs a completely different treatment in dark mode), add an explicit override in the `/* Dark Mode */` section of [static/css/style.css](../../../static/css/style.css):
   ```css
   body.dark-mode .your-component {
       background: var(--card-bg);
       border-color: var(--border-color);
   }
   ```

## Palette Rationale

The dark palette is **warm**, not cold. Pure `#000000` backgrounds feel sterile; `#0E0D0B` has a faint warm undertone that matches the coffee/roastery aesthetic. Primary accents shift from muted brown (`#6B5B4D`) to warm tan (`#C9A87A`) — still earthy, but readable against dark surfaces without being garish.

Shadows are also stronger in dark mode (`rgba(0,0,0,0.4)` vs `0.08`) — subtle shadows disappear on dark backgrounds.
