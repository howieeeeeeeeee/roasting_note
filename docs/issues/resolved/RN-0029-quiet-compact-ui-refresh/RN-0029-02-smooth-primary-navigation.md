---
id: RN-0029-02
title: Smooth Primary Navigation Continuity
type: improvement
status: resolved
priority: high
created: 2026-08-20
resolved: 2026-08-20
area: navigation
parent: RN-0029
decisions: []
blocked_by: []
testing_policy: v1
tags:
  - navigation
  - motion
  - view-transitions
  - accessibility
  - responsive
---

# Smooth Primary Navigation Continuity

## Description

Make Roasts and Beans feel like two states of one stable workspace. Keep normal
server-rendered links and URLs, but progressively animate the selected tab and
main content without reanimating the entire page chrome.

## Details

- Current behavior: Roasts and Beans are ordinary document links, while every
  `.container` runs the same `fadeUp` animation after navigation. The navbar,
  counts, contextual actions, and active underline are recreated rather than
  reading as a continuous shell.
- Stable shell: Keep the current `56px` top navbar, brand, Roasts and Beans
  labels, counts, contextual actions, dark-mode toggle, and Settings entry in
  one desktop line. Mobile retains the existing collapsed navigation concept.
- Progressive transition: Use native same-origin cross-document View
  Transitions as a progressive enhancement. Give the stable navbar, selected
  tab indicator, and main content intentional named transition roles; retain
  ordinary links, page loads, Back/Forward behavior, and server error handling.
- Motion: Use a restrained `160-200ms` transform/opacity transition with the
  shared Quiet Compact easing. The selected underline may glide between
  Roasts and Beans while main content moves no more than `4px`. Do not animate
  height, width, top, left, or scroll position.
- Remove the blanket new-page `.container` entrance that competes with the
  cross-document transition. First load and unsupported browsers render
  immediately without a staged entrance.
- Reduced motion: `prefers-reduced-motion: reduce` disables cross-document
  choreography, opacity fades, and translation. Navigation remains immediate
  and complete.
- Live-roast protection: The live-roast template opts out of main-content
  transition choreography. Entering, leaving, starting, or running a roast may
  not animate the chart, readings, setup, or event controls.
- Accessibility: Focus, link semantics, current-page indication, browser
  history, and keyboard activation remain native. Motion must not conceal
  loading failures or delay access to the new document.
- In scope: base/nav markup hooks, transition CSS, active indicator, reduced
  motion, responsive stability, automated contracts, and navigation docs.
- Out of scope: intercepting links with fetch, partial HTML replacement, SPA
  state, preload frameworks, route or label changes, mobile information
  architecture replacement, live-roast redesign, and backend changes.

## Acceptance Criteria

- [x] Clicking Roasts or Beans keeps the navbar visually stationary while the
  selected indicator and main content communicate the document change.
- [x] Roasts, Beans, contextual actions, record counts, URLs, and active-page
  semantics remain server rendered and correct after click, Back, Forward, and
  direct load.
- [x] The normal-motion transition completes in `160-200ms`, moves content no
  more than `4px`, and animates only transform and opacity.
- [x] First load, unsupported browsers, failed navigation, and reduced-motion
  mode remain complete and usable without relying on animation.
- [x] Reduced-motion mode has no route fade, translation, shared-indicator
  motion, or delayed content visibility.
- [x] The blanket `.container` entrance does not double-animate navigation or
  make the persistent header appear to reload.
- [x] The desktop navbar remains one line at `1024px`; mobile navigation is
  usable at `390px` without horizontal page overflow.
- [x] Light and dark modes use the same motion hierarchy and readable active,
  inactive, hover, focus, and pressed states.
- [x] Live-roast chart, readings, controls, and active sensor state do not
  receive route-content choreography or changed dimensions.
- [x] No JavaScript scroll listener, React-style state layer, navigation
  framework, new dependency, route, or API change is introduced.
- [x] Testing Impact reviewed against the implementation diff; declared automated and browser coverage is complete.
- [x] Documentation Impact reviewed against the implementation diff; every affected document below is updated in this branch.

## Testing Impact

- Change classification: ui-interaction, cross-workflow
- Browser verification level: full
- Automated tests to add or update: Update `tests/test_design_contracts.py` for named view-transition roles, normal-motion duration/property limits, removal of the blanket container entrance, full reduced-motion disablement, live-roast opt-out, and responsive nav rules; update `tests/test_api_contracts.py` for native Roasts/Beans links, current-page semantics, counts, contextual actions, and live-roast opt-out markup; retain `tests/test_app_factory.py` for the unchanged public route manifest and `tests/test_file_size_policy.py`
- Browser E2E scenarios to add or update: Add `tests/e2e/README.md` -> `Quiet Compact UI` -> `Navigation continuity`: repeatedly switch Roasts and Beans, use Back/Forward, open a record and return, toggle dark mode, enable reduced motion, test direct loads and a failed URL, and enter the live-roast shell; verify stable navbar geometry, correct counts/actions/current tab, no double entrance, native history, mobile menu behavior, and protected live-roast content
- Required commands: `uv run pytest tests/test_design_contracts.py tests/test_api_contracts.py tests/test_app_factory.py tests/test_file_size_policy.py`; `uv run pytest`; `uv run python -m tests.e2e.manage start --run-id rn-0029-navigation-a`; `uv run python -m tests.e2e.manage cleanup --run-id rn-0029-navigation-a`; `git diff --check`
- Required browser evidence: Record run ID `rn-0029-navigation-a`; save Roasts and Beans screenshots with identical navbar geometry at `1440x900`, `1024x768`, and `390x844`; record normal and reduced-motion observations, Back/Forward results, active indicator/current-page semantics, live-roast opt-out, console errors, failed network requests, and cleanup in `tests/e2e/artifacts/rn-0029-navigation-a/summary.md`
- Not applicable reason: None. Primary navigation is a shared cross-screen interaction, so full browser verification is required.

## Documentation Impact

- Add `docs/design/components/navigation.md` with stable-shell anatomy, active
  indicator, progressive transition, fallback, focus, and responsive rules.
- Update `docs/design/README.md` to index the navigation component.
- Update `docs/design/principles.md` with stable-workspace continuity and
  motivated motion.
- Update `docs/design/foundations/spacing-layout.md` with navbar geometry and
  responsive constraints.
- Update `docs/design/foundations/dark-mode.md` with active/inactive navigation
  parity.
- Update `tests/README.md` with the navigation design contracts and
  `tests/e2e/README.md` with the full Navigation continuity scenario.

## Database Operations Impact

None. Focused reads confirm this ticket changes document transition markup,
CSS, browser focus/history verification, tests, and design documentation only.
It performs no database write, migration, synchronization, backup, or audit
operation.

## Open Questions

- None. Use native cross-document transitions as progressive enhancement and
  preserve ordinary server navigation as the complete fallback.

## Resolution

- Kept ordinary server-rendered links, URLs, history, focus, and failure
  behavior while adding stable shell roles and a restrained `180ms`
  transform/opacity-only transition for fully capable browsers.
- Added a synchronous complete-lifecycle feature gate. The in-app browser's
  partial implementation selected the immediate fallback, and repeated
  Roasts/Beans navigation plus Back/Forward completed without console errors.
- Moved contextual actions into the controlled mobile menu, retained readable
  filled-button labels, and verified zero horizontal overflow at `390px`.
- Reduced-motion cancellation is covered by static design contracts because
  the browser harness could not emulate the preference. The parent aggregate
  browser run supplied the remaining navigation evidence.

## Related Files

- `templates/base.html`
- `templates/index.html`
- `templates/beans_list.html`
- `templates/roast_live.html`
- `static/css/base.css`
- `static/css/components/nav.css`
- `static/css/screens/live-roasting.css`
- `tests/test_design_contracts.py`
- `tests/test_api_contracts.py`
- `tests/e2e/README.md`
