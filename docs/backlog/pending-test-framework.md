# [TODO] Add Test Framework

**Status:** PENDING
**Created:** 2025-01-10

## Description

Add comprehensive test functions for all major features to ensure data integrity and frontend behavior.

## Requirements

### Test Coverage

1. **Bean Operations**
   - Create bean
   - Edit bean
   - Delete bean (soft delete)
   - Stock management

2. **Roast Operations**
   - Create draft roast
   - Start roast
   - Add key timing events
   - Add temperature events
   - End roast
   - Edit roast
   - Delete roast (soft delete + stock restore)

3. **Review Operations**
   - Add review
   - Edit review
   - Delete review

4. **Live Roast Data**
   - Temperature polling
   - Event logging
   - RoR calculation
   - Chart updates

### Test Data Labeling

- All test data should include `test_data: true` field
- Add "Delete Test Data" button in Settings modal
- Only run tests against local database

### Implementation Notes

- Create test functions that verify:
  - Data is correctly saved to database
  - Stock is properly adjusted
  - Calculated fields are correct
  - Frontend displays expected values

## Acceptance Criteria

- [ ] Test suite covers all CRUD operations
- [ ] Test data is clearly labeled
- [ ] One-click cleanup of test data
- [ ] Tests only run on local DB
- [ ] Instructions added to CLAUDE.md

## Related Files

- `app.py` - Add test endpoints
- `templates/base.html` - Add delete test data button
- `CLAUDE.md` - Add testing instructions
