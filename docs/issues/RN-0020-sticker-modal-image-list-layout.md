---
id: RN-0020
title: Sticker modal image list — remove unused scrollbar and dead space
type: bug
status: resolved
priority: low
created: 2026-05-04
resolved: 2026-05-04
area: label-creator
tags:
  - stickers
  - ui
  - beans-list
---

# Sticker modal image list — remove unused scrollbar and dead space

## Description

In the **Create Stickers** modal on the beans list, the left column’s image list shows a vertical scrollbar and leaves noticeable empty space below the rows even when all four US-4 sticker rows are visible and nothing overflows. The layout should grow only as tall as the content when it fits, and show scrolling only when the list actually exceeds the available space.

## Details

- **Where:** Beans list → **Create Stickers** → modal; left column under **Select Images**, when four images are listed (e.g. US-4, 4 / 4 images).
- **Current behaviour:** A scrollbar appears on the image list while extra whitespace sits below the last row — the list region reads as shorter than it needs to be for the content, or the scroll container is taller than the content without needing to scroll.
- **Desired behaviour:** When every row fits without overflow, there is no scrollbar track and no large unused gap under the last row. When the user adds enough rows or uses a shorter viewport so content cannot fit, scrolling appears as needed (keyboard / touch still work).
- **Out of scope:** Changing sticker PDF layout, template math, or preview panel behaviour; this ticket is only the left-column list chrome and spacing.

## Acceptance Criteria

- [x] With US-4 and four image rows on a typical desktop viewport, the image list does not show an unnecessary vertical scrollbar.
- [x] Dead space below the last image row is reduced so the list area does not look like a tall empty box when content fits.
- [x] If future templates allow more rows or the viewport is short, overflow still scrolls correctly and remains accessible.
- [x] Relevant docs updated when implemented: `docs/design/screens/sticker-sheet.md`, and `docs/features/sticker-sheet.md` only if layout/behaviour notes need to mention the list region.

## Open Questions

- Should the list use a **minimum** height when there are zero or one rows so the column does not jump wildly, or is strictly content-sized height preferred for all counts?

## Resolution

Raised the image list `max-height` clamp (was capped at 240px, which was shorter than four sticker rows plus gaps, causing an unnecessary scrollbar). Set `.sticker-sheet-controls { height: fit-content }` so the left column does not inherit excess vertical space. Updated `docs/design/screens/sticker-sheet.md`.

## Related Files

- `templates/beans_list.html`
- `static/css/screens/sticker-sheet.css`
- `static/js/sticker-sheet.js`
