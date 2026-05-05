# Sticker Sheet Screen - Design

**Opens as:** Modal on the beans list page ([templates/beans_list.html](../../../templates/beans_list.html))
**Behaviour:** [docs/features/sticker-sheet.md](../../features/sticker-sheet.md)
**Template system:** [../patterns/sticker-templates.md](../patterns/sticker-templates.md)

A compact print-prep modal for building a US Letter sheet with four fixed 4 in x 5 in sticker slots.

## Access

Beans list page -> **Create Stickers** button next to the out-of-stock filter -> opens modal.

## Layout Regions

Desktop keeps controls left and preview right:

```text
┌─────────────────────────────────────────────────────────────┐
│  Create Stickers                                      [x]   │
├───────────────────────┬─────────────────────────────────────┤
│ Template              │                                     │
│ [US-4 disabled]       │         US Letter preview            │
│ [Select Images] 0/4   │                                     │
│                       │   ┌────────────┬────────────┐       │
│ image row  qty remove │   │ slot 1     │ slot 2     │       │
│ image row  qty remove │   ├────────────┼────────────┤       │
│                       │   │ slot 3     │ slot 4     │       │
│                       │   └────────────┴────────────┘       │
├───────────────────────┴─────────────────────────────────────┤
│ Warning shown when total is not 4.           [Download PDF] │
└─────────────────────────────────────────────────────────────┘
```

At narrow widths the preview moves above the image list so the sheet remains visible while adjusting quantities.

The desktop modal is height-bounded to the viewport. The US Letter preview width is capped with `min(100%, 460px, 44vh)` so the full sheet remains visible without scrolling the whole modal. The image list grows with its rows up to a viewport-aware max height; a vertical scrollbar appears only when rows cannot fit (not for a full US-4 set on a typical desktop).

## Components

| Region | Class / implementation |
| --- | --- |
| Modal shell | `.sticker-sheet-modal-content` under the shared `.modal` system |
| Controls | `.sticker-sheet-controls` with disabled template selector, standard `.btn`, and `.btn-icon` controls |
| Image rows | `.sticker-image-item`, thumbnail, filename, quantity input, remove icon |
| Preview | `.sticker-sheet-preview` with absolutely positioned `.sticker-slot` children |
| Footer | `.sticker-sheet-footer`, validation text, and primary PDF action |

## Preview Interaction

The preview is intentionally close to the printed result but still exposes editing aids:

- The sheet uses `aspect-ratio: 8.5 / 11`.
- Slots are positioned as percentages derived from the US-4 inch template.
- Filled slots use center-cover images, clipped to the sticker rectangle.
- Faint dashed slot borders and slot numbers appear in the modal only.

There is no manual crop or scale control in this phase. The selected images are auto-rotated to portrait when needed and center-cover fitted into the slots.

## Export Appearance

The exported PDF is clean. It contains only the sticker images at their physical coordinates. Preview borders, slot numbers, and other editing affordances are never rendered into the PDF.

## Dark Mode

The modal chrome inherits app CSS variables. The sheet preview itself remains white because it represents a printed US Letter page, not an app surface.
