---
id: RN-0021
title: Label PNG Export Prints With Incorrect Colors
type: bug
status: wont_fix
priority: medium
created: 2026-05-05
resolved: 2026-05-05
area: label-creator
parent:
decisions: []
blocked_by: []
tags:
  - label-export
  - png
  - print-color
---

# Label PNG Export Prints With Incorrect Colors

## Description

The bean label creator preview appears to show the expected colors on screen, but the downloaded PNG can print with noticeably different colors. This makes the printable label output unreliable even when the in-browser design looks correct.

## Details

- Trigger: open a bean detail page, use **Create Label**, download the PNG export, then print the downloaded label.
- Reported current behavior: the modal preview colors look right, but printed output colors are "way off."
- The downloaded PNG looks correct when opened before printing, so the first confirmed failure point is the print path rather than the canvas preview or saved PNG appearance.
- Confirmed print path: macOS Preview print.
- Observed print failure: output is too light, and black/dark areas do not print as true black.
- Printer and paper variability is unknown because this has not been tested on another printer or paper stock yet.
- Desired behavior: the downloaded PNG should print materially closer to the on-screen preview for the same template, accent color, image, and export size.
- Initial code read: `static/js/label-creator.js` paints directly to canvas with CSS hex and `rgba(...)` values; no obvious template-level color conversion is happening before export.
- Initial code read: `templates/beans_detail.html` exports via `canvas.toBlob(..., 'image/png')`, then injects a `pHYs` chunk to preserve the selected physical print size.
- Investigation should check whether the exported PNG lacks explicit color-profile metadata, such as `sRGB`, `gAMA`, `cHRM`, or ICC profile data, causing print apps or printer drivers to interpret colors differently.
- Investigation should also check whether browser-generated PNG metadata already contains a `pHYs` chunk before injection. If so, the current injection path may create duplicate physical-size metadata.
- Preserve the exact physical-size behavior of the PNG export. The fix should not regress the current ability to insert a 12.7 x 10.16 cm label at the intended size.
- Include both standard and rotated 90 degree PNG exports in the investigation, since both use the same canvas export path.
- Recommended plan:
  1. Export a failing label PNG and inspect its chunks with a metadata tool to confirm `pHYs`, `sRGB`, `gAMA`, `cHRM`, and ICC/profile state.
  2. Create a controlled test label with black, near-black, white, mid-gray, and the selected accent color so print output can be compared without photo/image noise.
  3. Print the same PNG through macOS Preview and one alternate path, such as browser print, Pages, or PDF conversion, to isolate Preview-specific color handling.
  4. If metadata is ambiguous, update PNG export to write a predictable profile/signaling strategy while preserving the existing `pHYs` physical-size chunk.
  5. If metadata is correct but macOS Preview still prints too light, document a recommended print workflow or add an app-side "print test / export for print" path with stronger dark values.

## Acceptance Criteria

- [ ] Reproduce and document at least one concrete color-shift case, including template, accent color, optional image, print app, printer, and paper type when available.
- [ ] Confirm whether the issue is specific to macOS Preview print by testing one alternate print path.
- [ ] Add or manually use a controlled test label containing black, near-black, white, mid-gray, and the selected accent color.
- [ ] Inspect the exported PNG metadata and document whether it contains duplicate `pHYs` chunks or missing / ambiguous color-profile chunks.
- [ ] Identify whether the color shift happens in print preview, only on physical print, or both.
- [ ] Implement a fix or explicit product guidance that makes label PNG print color predictable enough for normal use.
- [ ] Verify standard PNG and rotated PNG exports after the change.
- [ ] Verify the exported PNG still opens or inserts at the selected physical size.
- [ ] Relevant docs updated when implemented: `docs/features/bean-label-creator.md`, `docs/design/patterns/label-templates.md`, `docs/design/screens/label-creator.md`.

## Open Questions

- Which template, accent color, image, and font preset produced the bad print?
- Does macOS Preview's print preview already look too light, or does it only become too light on physical paper?
- Does the same PNG print closer to expected colors from browser print, Pages, Word, or PDF conversion?

## Related Files

- `static/js/label-creator.js`
- `templates/beans_detail.html`
- `docs/features/bean-label-creator.md`
- `docs/design/patterns/label-templates.md`
- `docs/design/screens/label-creator.md`

## Resolution

Closed without product changes. The print color issue was caused by the printer running low on ink, not by the label canvas renderer, PNG export path, or macOS Preview print handling.
