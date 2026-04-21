# Dark Mode — Design & Implementation

**Affects:** All pages  
**Toggle:** Navbar icon (top-right, next to Settings)  
**Persistence:** `localStorage` key `roast-dark`

---

## Approach: CSS Variable Override

The existing stylesheet already uses CSS custom properties throughout. Dark mode works by redefining those variables on `body.dark-mode` — no component-level overrides needed for most elements.

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
```

Any component that uses these variables automatically adapts. You only need explicit dark-mode rules for elements that use **hardcoded colours** or need special treatment (e.g. chart colours, which are set in JavaScript).

---

## Full Variable Map

| Variable | Light | Dark | Usage |
|---|---|---|---|
| `--primary-color` | `#6B5B4D` | `#C9A87A` | Headings, active states, key values |
| `--primary-hover` | `#5A4A3D` | `#D9B88A` | Button hover |
| `--secondary-color` | `#8B7D6B` | `#9A8A78` | Secondary buttons |
| `--success-color` | `#6B8E6F` | `#7FB385` | Success states, RoR line |
| `--danger-color` | `#B85C5C` | `#D07070` | End Roast button, FC badge |
| `--text-color` | `#2C2C2C` | `#EDE9E3` | Body text |
| `--text-light` | `#666` | `#8A8680` | Labels, secondary text |
| `--bg-color` | `#FAFAF9` | `#0E0D0B` | Page background |
| `--card-bg` | `#FFFFFF` | `#171512` | Cards, panels, nav |
| `--border-color` | `#E8E6E3` | `#2A2620` | Borders, dividers |

---

## Toggle Implementation (`base.html`)

```javascript
function toggleDarkMode() {
    const isDark = document.body.classList.toggle('dark-mode');
    const icon   = document.getElementById('darkModeIcon');
    const btn    = document.getElementById('darkModeToggle');

    // Swap icon
    if (icon) icon.textContent = isDark ? 'light_mode' : 'dark_mode';
    if (btn)  btn.classList.toggle('active', isDark);

    // Persist
    localStorage.setItem('roast-dark', isDark ? '1' : '0');

    // Notify other scripts (e.g. chart reinit on live roast page)
    window.dispatchEvent(new CustomEvent('darkmodechange', { detail: isDark }));
}

// Restore on page load
if (localStorage.getItem('roast-dark') === '1') {
    document.body.classList.add('dark-mode');
    // ... update icon/button
}
```

The `darkmodechange` custom event lets page-specific scripts react without coupling to `base.html`. Currently only `roast_live.html` listens for it (to reinit the Chart.js chart with dark-aware colours).

---

## Chart Colours (`roast_live.html`)

Chart.js datasets use hardcoded colour strings, so they need special handling. The `getChartColors()` helper is called each time the chart is initialised:

```javascript
function getChartColors() {
    const dark = document.body.classList.contains('dark-mode');
    return {
        temp:     dark ? '#D4895A' : '#6B5B4D',
        tempBg:   dark ? 'rgba(212,137,90,0.15)'  : 'rgba(107, 91, 77, 0.1)',
        ror:      dark ? '#7FB385' : '#6B8E6F',
        rorBg:    dark ? 'rgba(127,179,133,0.1)'  : 'rgba(107, 142, 111, 0.1)',
        power:    dark ? 'rgba(201,168,122,0.35)' : 'rgba(139, 115, 85, 0.4)',
        powerBg:  dark ? 'rgba(201,168,122,0.1)'  : 'rgba(139, 115, 85, 0.2)',
        fan:      dark ? 'rgba(127,179,133,0.35)' : 'rgba(90, 122, 94, 0.4)',
        fanBg:    dark ? 'rgba(127,179,133,0.08)' : 'rgba(90, 122, 94, 0.2)',
        grid:     dark ? 'rgba(255,255,255,0.06)' : 'rgba(0, 0, 0, 0.05)',
        axis:     dark ? '#6A6560' : '#666',
    };
}
```

When the user toggles dark mode, `roast_live.html` listens for `darkmodechange`, destroys the existing chart instance, and calls `initChart()` again to rebuild with the new palette.

---

## Adding a New Component

If you add a new UI component and want it to automatically support dark mode:

1. **Use CSS variables** — reference `var(--card-bg)`, `var(--border-color)`, `var(--text-color)` etc. instead of hardcoded hex values. It will just work.

2. **If you must hardcode** (e.g. a chart or canvas element), add a `darkmodechange` listener:
   ```javascript
   window.addEventListener('darkmodechange', (e) => {
       const isDark = e.detail;
       // update your hardcoded colours here
   });
   ```

3. **For edge cases** (e.g. an element that needs a completely different treatment in dark mode), add an explicit override in `style.css` under the `/* Dark Mode */` section:
   ```css
   body.dark-mode .your-component {
       background: var(--card-bg);
       border-color: var(--border-color);
   }
   ```

---

## Colour Palette Rationale

The dark palette is **warm**, not cold. Pure `#000000` backgrounds feel sterile; the `#0E0D0B` base has a faint warm undertone that matches the coffee/roastery aesthetic. Primary accents shift from the muted brown (`#6B5B4D`) to a warm tan (`#C9A87A`) — still earthy, but readable against dark surfaces without being garish.
