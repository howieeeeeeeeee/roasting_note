# Navigation

RoastLogger uses one stable 56px workspace header for Roasts and Beans. The
component lives in [templates/base.html](../../../templates/base.html) and
[static/css/components/nav.css](../../../static/css/components/nav.css).

## Anatomy

The desktop header remains on one line at 1024px:

1. Howie's Roast Log brand link
2. Roasts and Beans native links with server-rendered counts
3. Page-specific actions
4. Dark-mode and Settings controls

The active link carries `aria-current="page"`. Mobile keeps the same
information architecture behind a 44px menu button with synchronized
`aria-expanded` state.

## Workspace continuity

Same-origin documents progressively opt into native cross-document View
Transitions with `@view-transition { navigation: auto; }`. Ordinary anchors,
URLs, direct loads, browser history, and failure behavior remain the complete
fallback. No fetch interception, partial HTML replacement, or client-side
router is involved.

Named transition roles are:

| Role | CSS name | Behavior |
| --- | --- | --- |
| Stable header | `app-navbar` | No entrance or exit animation |
| Main content | `app-content` | 180ms opacity plus at most 4px translation |
| Active rule | `active-nav-indicator` | Shared position change between tabs |

The blanket `.container` page-load animation is removed so it cannot compete
with the named transition. Unsupported browsers render the next document
immediately.

## Reduced motion and live roasting

Under `prefers-reduced-motion: reduce`, named roles are disabled and every View
Transition pseudo-element has no animation. The document update remains
immediate and complete.

The live-roast template adds `.no-route-transition` through the base
`main_class` block. Its chart, readings, setup, and event controls never use the
management content transition. The navbar may still render in its stable role.

## Interaction states

- Inactive, hover, active, pressed, and focus-visible states use semantic color
  tokens and remain readable in both themes.
- The active rule is the only shared moving element. Counts and labels do not
  morph.
- Motion changes only `transform` and `opacity`; it never animates layout,
  scroll position, width, or height.
- The desktop navbar remains 56px high, and the mobile menu must not create
  horizontal page overflow.
