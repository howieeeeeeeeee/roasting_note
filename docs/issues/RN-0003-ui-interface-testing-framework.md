---
id: RN-0003
title: UI/Interface Testing Framework
type: todo
status: pending
priority: medium
created: 2026-01-11
area: testing
tags:
  - ui
  - e2e
---

# UI/Interface Testing Framework

## Description

Add end-to-end browser tests for critical user workflows to ensure the interface works correctly.

## What This Tests

- Full user workflows (clicking, typing, navigation)
- Frontend JavaScript behavior
- Chart rendering and interactions
- Real user experience across pages
- Integration between frontend and backend

## Why This is Separate

- More complex to set up (requires browser automation)
- Slower to run than API tests
- Should focus on critical user flows, not everything
- Builds on top of API testing foundation

## Critical Workflows to Test

### 1. Live Roasting Session (Priority 1)

**Most important workflow - test this first:**

- Create new roast
- Select bean and enter weight
- Start roast (verify timer starts)
- Monitor temperature display updates
- Log key events (FC, SC) using quick buttons
- Adjust fan/power settings
- Verify chart updates in real-time
- End roast
- Verify redirect to edit page

**Why this matters:**
- This is the core feature of the app
- Real-time updates must work reliably
- Can't afford failures during actual roasting

### 2. Bean Management

- Add new bean
- Edit bean details
- Verify bean shows in bean list
- Delete bean
- Verify stock updates after roast

### 3. Roast Review

- View completed roast
- Add review with score and notes
- Edit review
- Delete review
- Verify chart displays correctly

### 4. Chart Visualization

- Temperature line renders correctly
- RoR line displays
- Event markers appear at right times
- Power/Fan timeline bars show segments
- Chart scales adjust properly

## What We Need to Decide

**Before implementing, clarify:**

- Which tool to use? (Selenium, Playwright, Cypress)
- How much coverage vs speed trade-off?
- Run in CI/CD or manual only?
- Test on multiple browsers or just one?

## Manual Testing (For Now)

Until automated UI tests are ready, manually verify:

- User interface layout and appearance
- Chart visualization accuracy
- Mobile responsiveness
- Touch interactions on tablet
- Edge cases in live roasting flow

## Success Criteria

- [ ] Live roasting workflow tested end-to-end
- [ ] Critical user interactions verified (buttons, forms, navigation)
- [ ] Chart rendering validated
- [ ] Real-time updates confirmed working
- [ ] Tests can run without manual intervention
- [ ] Clear documentation for running UI tests
- [ ] Failures are easy to diagnose (screenshots, logs)

## Dependencies

- **Requires:** API testing completed first
- **Requires:** Decision on browser testing tool
- **Requires:** Test data setup mechanism (from API tests)

## Related Files

- `templates/roast_live.html` - Live roasting interface
- `templates/beans_list.html` - Bean management
- `templates/roast_detail.html` - Roast viewing
- `static/js/roast-chart.js` - Chart rendering
