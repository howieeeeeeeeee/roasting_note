---
id: RN-0014
title: Add Short Flavor Note to Beans
type: feature
status: resolved
priority: high
created: 2026-05-01
resolved: 2026-05-01
area: bean-inventory
tags:
  - beans
  - label-creator
  - data-model
---

# Add Short Flavor Note to Beans

## Description

Add a dedicated short flavor note field to bean records so compact tasting copy can be shown in the bean inventory and reused by the label creator without replacing the longer bean notes/description field.

## Details

- Add a new bean data field for the short flavor note, separate from the existing longer `notes` field.
- The add-bean and edit-bean forms must let users create and update the short flavor note.
- The Beans tab should show the short flavor note as secondary text under or near the bean name in each row.
- The existing longer bean `notes` field should remain available for detailed descriptions and should not be overwritten by this change.
- The bean label creator's Auto-fill from Bean action should populate label `flavorNotes` from the new short flavor note field.
- If a bean has no short flavor note, Auto-fill from Bean should leave label `flavorNotes` blank instead of falling back to the longer notes/description.
- Existing saved per-bean label data should continue to take precedence when opening a label that has already been saved.

## Acceptance Criteria

- [x] New beans can be created with a short flavor note, and the value is persisted on the bean document.
- [x] Existing beans can be edited to add, change, or clear the short flavor note.
- [x] Short flavor notes can be edited interactively as removable tags in the add/edit bean form.
- [x] The Beans tab displays the short flavor note as compact secondary text in the bean-name row when present.
- [x] The Beans tab does not show the longer `notes` field as the preview once the short flavor note field exists.
- [x] Label Auto-fill from Bean copies the bean short flavor note into label `flavorNotes`.
- [x] Label Auto-fill leaves label `flavorNotes` blank when the bean short flavor note is empty.
- [x] API/model tests cover create and edit persistence for the new field, including clearing it.
- [x] Relevant docs updated when implemented: `docs/architecture/data-models.md`, `docs/architecture/api-endpoints.md`, `docs/features/bean-label-creator.md`, `docs/design/screens/bean-inventory.md`, `docs/design/screens/label-creator.md`.

## Open Questions

- Answered: stored field is `short_flavor_notes`, an array of strings.
- Answered: no hard UI max length in this version.
- Answered: bean detail shows short flavor notes as chips in addition to the Beans tab row preview.

## Resolution

Implemented `short_flavor_notes` as a bean-level array, exposed it in add/edit forms with an interactive removable-tag editor, displayed it as compact chips on bean list/detail screens, and used it for label auto-fill.

## Related Files

- `models/bean_helpers.py`
- `templates/beans_form.html`
- `templates/beans_list.html`
- `templates/beans_detail.html`
- `app.py`
- `tests/test_beans_api.py`
- `docs/architecture/data-models.md`
- `docs/architecture/api-endpoints.md`
- `docs/features/bean-label-creator.md`
- `docs/design/screens/bean-inventory.md`
- `docs/design/screens/label-creator.md`
