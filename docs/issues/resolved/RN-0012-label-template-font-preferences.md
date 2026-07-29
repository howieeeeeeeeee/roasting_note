---
id: RN-0012
title: Remember Last-Used Label Template, Font, and Aspect Ratio
type: improvement
status: resolved
priority: medium
created: 2026-04-25
resolved: 2026-04-25
area: label-creator
parent:
decisions: []
blocked_by: []
tags:
  - labels
  - ux
---

# Remember Last-Used Label Template, Font, and Aspect Ratio

## Description

When a user opens the label creator for a bean that has no saved label, the modal currently falls back to hardcoded defaults (`nova` / `modern` / `5:4`). After spending effort to pick a template and font preset they like, users have to re-pick the same combination for every new bean.

Use saved label data already in the database as the source of truth: when opening the modal for a bean with no label of its own, seed the template / font / aspect ratio from the **most recently updated bean** that does have a saved label. No per-browser state, survives across devices.

This change also fixes a latent bug: the existing `POST /api/beans/<bean_id>/label` handler silently dropped `fontPreset` and `aspectRatio` from the payload, so the per-bean save claimed in `docs/design/screens/label-creator.md` never actually round-tripped those two fields.

## Details

- **Backend bug fix.** Add `fontPreset` and `aspectRatio` to the persisted `label_data` in `app.py` so per-bean saves actually round-trip them. Default `templateId` aligned to `nova`. Default export size kept at 5 × 4 cm (the original DB schema; the redesign briefly drifted to 10 × 8 in client code).
- **New endpoint** `GET /api/label/preferences` — returns `{ templateId, fontPreset, aspectRatio }` derived from the most recently updated non-archived bean that has a saved `label.templateId`. Falls back to `nova` / `modern` / `5:4` when no bean has a saved label yet. No new collection / schema; reads existing `bean.label` data.
- **Frontend.** Drop the `localStorage` `roastlogger.labelPrefs` helpers. In `openLabelModal()`'s no-saved-label branch, render immediately with hardcoded fallbacks, then `fetch('/api/label/preferences')` and overwrite the dropdowns + re-render. Per-bean saved labels still win — that branch is unchanged.
- Only template, font, and aspect ratio are remembered globally. `imageSrc`, `accentColor`, label text, export size remain strictly per-bean.
- Affects `templates/beans_detail.html`, `app.py`, and label-related docs.

## Acceptance Criteria

- [x] Picking a template / font / aspect ratio in one bean's label modal becomes the default the next time the modal is opened for any bean **that has no saved label**.
- [x] Beans with an existing `beans.label.templateId` (etc.) still load their saved values, not the global preference.
- [x] Defaults survive a page reload, browser change, and device change (stored in DB, not browser state).
- [x] On a fresh database with no saved labels, the modal still opens with `nova` / `modern` / `5:4`.
- [x] `POST /api/beans/<bean_id>/label` persists `fontPreset` and `aspectRatio` (previously silently dropped).
- [x] `docs/features/bean-label-creator.md`, `docs/design/screens/label-creator.md`, and `docs/architecture/api-endpoints.md` mention the new endpoint and remembered preference.

## Resolution

Initially shipped with `localStorage`-backed prefs; reworked per user preference to keep all storage in the DB.

- **Backend.** `POST /api/beans/<bean_id>/label` now persists `fontPreset` and `aspectRatio` (these were previously silently dropped — latent bug). Defaults aligned to the redesigned UI. New `GET /api/label/preferences` endpoint returns the style triplet from the most recently updated non-archived bean that has a saved `label.templateId`, with `nova` / `modern` / `5:4` fallback.
- **Frontend.** Removed all `localStorage` helpers. `openLabelModal()`'s unsaved-bean branch now applies hardcoded fallbacks first (so the modal renders immediately) then fetches `/api/label/preferences` and overwrites the three dropdowns + redraws. Style dropdowns no longer write a per-change pref — the next save propagates them via the bean's own `label`.

## Related Files

- `app.py`
- `templates/beans_detail.html`
- `docs/architecture/api-endpoints.md`
- `docs/features/bean-label-creator.md`
- `docs/design/screens/label-creator.md`
