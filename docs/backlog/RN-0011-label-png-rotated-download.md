---
id: RN-0011
title: Rotated (90°) PNG Download and Multi-Line Flavor Notes for Bean Labels
type: feature
status: resolved
priority: medium
created: 2026-04-25
resolved: 2026-04-25
area: label-creator
tags:
  - labels
  - export
---

# Rotated (90°) PNG Download and Multi-Line Flavor Notes for Bean Labels

## Description

Two improvements to the bean label creator:

1. **Rotated PNG export.** When exporting a bean label as PNG, also offer a 90°-rotated version of the same render. Some printers and label sheets feed media sideways, so users currently have to rotate the file in another tool before printing.
2. **Multi-line flavor notes.** The Flavor Notes field is a single-line input, which forces users to cram everything onto one line. Allow line breaks in the input and render each line stacked on the label.

## Details

- The current export path is `downloadLabelPNG()` in [templates/beans_detail.html:490](../../templates/beans_detail.html#L490), which calls `canvas.toDataURL('image/png')` on the canvas rendered by [static/js/label-creator.js](../../static/js/label-creator.js).
- Add a way to download the same label rotated 90° clockwise (and ideally also -90° / counter-clockwise) without changing the on-screen preview or the underlying template aspect ratio.
- Implementation sketch: render to the existing canvas, then draw onto an offscreen canvas of swapped dimensions (`width = src.height`, `height = src.width`) with a `translate` + `rotate(±π/2)` transform, and export that offscreen canvas via `toDataURL('image/png')`.
- Preserve the current export resolution (`RENDER_SCALE = 4`) so print quality matches the non-rotated download.
- Filename should make the orientation obvious, e.g. `<bean>_label_rotated.png` (or `_rot90` / `_rot-90` if both directions are offered).
- UI: extend the existing "Download PNG" control in `templates/beans_detail.html` — either a second button ("Download PNG (rotated)") or a small dropdown next to the existing one. Match existing button styling; do not introduce a new component pattern.

### Multi-line flavor notes

- Replace the `<input type="text" id="labelFlavorNotes">` in `templates/beans_detail.html` with a `<textarea>` (rows ≈ 3) so users can enter each note on its own line.
- Update the canvas renderer in [static/js/label-creator.js](../../static/js/label-creator.js) so each non-blank line of `flavorNotes` is drawn on its own line for `nova`, `ink`, `washi`. For `strip`, prefer newline-split if present, otherwise keep the existing comma-split fallback so legacy single-line entries still stack correctly.
- Persisted value in `beans.label.flavorNotes` keeps `\n` characters — no schema change required.

## Acceptance Criteria

- [x] User can trigger a rotated PNG download from the label creator modal.
- [x] Downloaded PNG is the label rotated 90° with no clipping, scaling artefacts, or quality loss vs. the standard export.
- [x] On-screen preview and the standard "Download PNG" output are unchanged.
- [x] Filename clearly indicates the rotated variant.
- [x] Works across all four templates (`nova`, `ink`, `strip`, `washi`) and all supported aspect ratios.
- [x] `docs/features/` and/or `docs/design/` entry for the label creator updated to mention the rotated export option.
- [x] Flavor Notes input accepts and preserves line breaks.
- [x] Each non-blank line renders on its own line on all four templates (`strip` keeps comma-split fallback for legacy entries).
- [x] Persisted `beans.label.flavorNotes` round-trips line breaks across save/reopen.

## Resolution

**Rotated PNG export.** Added a second action button "Download PNG (Rotated 90°)" alongside the existing "Download PNG" in the label creator modal. `downloadLabelPNG(rotateDeg)` now optionally takes a rotation in degrees: when set, it draws the source canvas onto an offscreen canvas with swapped dimensions and a `translate` + `rotate` transform, then exports that via `toDataURL('image/png')`. Render scale is preserved (no resampling), so output quality matches the standard export. Filename suffix is `_rot90.png` for the rotated variant.

**Multi-line flavor notes.** Replaced the single-line `<input>` with a `<textarea rows="3">`. Added `splitLines` and `txtMulti` helpers in `label-creator.js`; the Nova, Ink, and Washi templates now stack each non-blank line. Strip prefers newline-split and falls back to comma-split for legacy entries, so existing labels render unchanged.

## Related Files

- `static/js/label-creator.js`
- `templates/beans_detail.html`
