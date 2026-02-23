
### Requirement: Add Tasting Review
A user can record a post-roast tasting note with a score and extraction method.

#### Scenario: Add review
- **WHEN** POST `/api/roast/add_review/<roast_id>` is called with `overall_score`, `extraction_method`, and `notes`
- **THEN** a review document is embedded in the roast's `reviews` array
- **AND** the review includes `review_date`, `created_at`, and `updated_at` timestamps
- **AND** the review is assigned a unique `_id`

#### Scenario: Valid extraction methods
- **WHEN** `extraction_method` is one of `espresso`, `pourover`, `ice_drop`, `cold_brew`, `other`
- **THEN** the review is accepted

#### Scenario: Overall score is integer
- **WHEN** `overall_score` is provided
- **THEN** it is stored as an integer

---

### Requirement: Edit Review
A user can update any field of an existing review.

#### Scenario: Edit review
- **WHEN** POST `/api/roast/update_review/<roast_id>/<review_id>` is called with updated fields
- **THEN** the matching review's `extraction_method`, `overall_score`, and `notes` are updated
- **AND** `updated_at` is refreshed

#### Scenario: Edit non-existent review
- **WHEN** a review_id does not exist in the roast's reviews array
- **THEN** a 404 response is returned

---

### Requirement: Delete Review
A user can remove a review from a roast.

#### Scenario: Delete review
- **WHEN** POST `/api/roast/delete_review/<roast_id>/<review_id>` is called
- **THEN** the review is removed from the roast's `reviews` array

#### Scenario: Delete non-existent review
- **WHEN** the review_id does not match any review
- **THEN** a 404 response is returned

---

### Requirement: View Reviews
Reviews are displayed alongside the roast they belong to.

#### Scenario: Reviews shown on roast detail
- **WHEN** a roast detail page is loaded
- **THEN** all embedded reviews are displayed with score, extraction method, and notes
