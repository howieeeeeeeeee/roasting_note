"""
API tests for Review operations.

Tests cover:
- Add review to roast
- Edit existing review
- Delete review
- Review data validation
"""
import pytest
from datetime import datetime
from bson.objectid import ObjectId


class TestReviewCreate:
    """Tests for adding reviews to roasts."""

    def test_add_review_json(self, client, roasts_collection, started_test_roast):
        """Test adding a review via JSON API."""
        roast_id = started_test_roast['roast_id']

        review_data = {
            'overall_score': 4,
            'extraction_method': 'espresso',
            'notes': 'Great fruity notes, slight acidity'
        }

        response = client.post(
            f'/api/roast/add_review/{roast_id}',
            json=review_data,
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert 'review_id' in data

        # Verify review was added
        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert len(roast['reviews']) == 1
        assert roast['reviews'][0]['overall_score'] == 4
        assert roast['reviews'][0]['extraction_method'] == 'espresso'
        assert roast['reviews'][0]['notes'] == 'Great fruity notes, slight acidity'

    def test_add_review_form(self, client, roasts_collection, started_test_roast):
        """Test adding a review via form submission."""
        roast_id = started_test_roast['roast_id']

        form_data = {
            'overall_score': '5',
            'extraction_method': 'pourover',
            'notes': 'Perfect balance'
        }

        # Note: When using data= without content_type, Flask test client sends form data
        # which triggers request.form.to_dict() in the endpoint
        response = client.post(
            f'/api/roast/add_review/{roast_id}',
            data=form_data,
            follow_redirects=False
        )

        # Form submission redirects (non-JSON request)
        assert response.status_code == 302

        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert len(roast['reviews']) == 1
        assert roast['reviews'][0]['overall_score'] == 5
        assert roast['reviews'][0]['extraction_method'] == 'pourover'

    def test_add_review_default_score(self, client, roasts_collection, started_test_roast):
        """Test that review defaults to score 3 if not provided."""
        roast_id = started_test_roast['roast_id']

        review_data = {
            'extraction_method': 'cold_brew',
            'notes': 'Smooth'
        }

        client.post(
            f'/api/roast/add_review/{roast_id}',
            json=review_data,
            content_type='application/json'
        )

        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert roast['reviews'][0]['overall_score'] == 3

    def test_add_multiple_reviews(self, client, roasts_collection, started_test_roast):
        """Test adding multiple reviews to same roast."""
        roast_id = started_test_roast['roast_id']

        reviews = [
            {'overall_score': 4, 'extraction_method': 'espresso', 'notes': 'First review'},
            {'overall_score': 5, 'extraction_method': 'pourover', 'notes': 'Second review'},
            {'overall_score': 3, 'extraction_method': 'cold_brew', 'notes': 'Third review'},
        ]

        for review in reviews:
            client.post(
                f'/api/roast/add_review/{roast_id}',
                json=review,
                content_type='application/json'
            )

        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert len(roast['reviews']) == 3

    def test_add_review_has_timestamps(self, client, roasts_collection, started_test_roast):
        """Test that review has created_at and updated_at timestamps."""
        roast_id = started_test_roast['roast_id']

        before_create = datetime.now()

        client.post(
            f'/api/roast/add_review/{roast_id}',
            json={'overall_score': 4},
            content_type='application/json'
        )

        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        review = roast['reviews'][0]

        assert 'created_at' in review
        assert 'updated_at' in review
        assert 'review_date' in review


class TestReviewUpdate:
    """Tests for updating reviews."""

    def test_update_review_json(self, client, roasts_collection, started_test_roast):
        """Test updating a review via JSON API."""
        roast_id = started_test_roast['roast_id']

        # First create a review
        response = client.post(
            f'/api/roast/add_review/{roast_id}',
            json={'overall_score': 3, 'extraction_method': 'espresso', 'notes': 'Original'},
            content_type='application/json'
        )
        review_id = response.get_json()['review_id']

        # Update the review
        update_data = {
            'overall_score': 5,
            'extraction_method': 'pourover',
            'notes': 'Updated notes - much better!'
        }

        response = client.post(
            f'/api/roast/update_review/{roast_id}/{review_id}',
            json=update_data,
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True

        # Verify update
        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        review = roast['reviews'][0]
        assert review['overall_score'] == 5
        assert review['extraction_method'] == 'pourover'
        assert review['notes'] == 'Updated notes - much better!'

    def test_update_review_form(self, client, roasts_collection, started_test_roast):
        """Test updating a review via form submission."""
        roast_id = started_test_roast['roast_id']

        # Create a review
        response = client.post(
            f'/api/roast/add_review/{roast_id}',
            json={'overall_score': 3},
            content_type='application/json'
        )
        review_id = response.get_json()['review_id']

        # Update via form
        form_data = {
            'overall_score': '4',
            'extraction_method': 'ice_drop',
            'notes': 'Form updated'
        }

        response = client.post(
            f'/api/roast/update_review/{roast_id}/{review_id}',
            data=form_data,
            follow_redirects=False
        )

        assert response.status_code == 302

        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert roast['reviews'][0]['overall_score'] == 4
        assert roast['reviews'][0]['extraction_method'] == 'ice_drop'

    def test_update_review_updates_timestamp(self, client, roasts_collection, started_test_roast):
        """Test that updating a review updates the updated_at timestamp."""
        import time
        roast_id = started_test_roast['roast_id']

        # Create a review
        response = client.post(
            f'/api/roast/add_review/{roast_id}',
            json={'overall_score': 3},
            content_type='application/json'
        )
        review_id = response.get_json()['review_id']

        # Get original timestamp
        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        original_updated = roast['reviews'][0]['updated_at']

        time.sleep(0.1)  # Small delay to ensure different timestamp

        # Update the review
        client.post(
            f'/api/roast/update_review/{roast_id}/{review_id}',
            json={'overall_score': 5},
            content_type='application/json'
        )

        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        new_updated = roast['reviews'][0]['updated_at']

        assert new_updated > original_updated


class TestReviewDelete:
    """Tests for deleting reviews."""

    def test_delete_review_json(self, client, roasts_collection, started_test_roast):
        """Test deleting a review via JSON API."""
        roast_id = started_test_roast['roast_id']

        # Create a review
        response = client.post(
            f'/api/roast/add_review/{roast_id}',
            json={'overall_score': 4, 'notes': 'To be deleted'},
            content_type='application/json'
        )
        review_id = response.get_json()['review_id']

        # Verify review exists
        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert len(roast['reviews']) == 1

        # Delete the review
        response = client.post(
            f'/api/roast/delete_review/{roast_id}/{review_id}',
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True

        # Verify review was removed
        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert len(roast['reviews']) == 0

    def test_delete_one_of_multiple_reviews(self, client, roasts_collection, started_test_roast):
        """Test deleting one review when multiple exist."""
        roast_id = started_test_roast['roast_id']

        # Create three reviews
        review_ids = []
        for i in range(3):
            response = client.post(
                f'/api/roast/add_review/{roast_id}',
                json={'overall_score': i + 1, 'notes': f'Review {i + 1}'},
                content_type='application/json'
            )
            review_ids.append(response.get_json()['review_id'])

        # Delete the middle one
        client.post(
            f'/api/roast/delete_review/{roast_id}/{review_ids[1]}',
            content_type='application/json'
        )

        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert len(roast['reviews']) == 2
        notes = [r['notes'] for r in roast['reviews']]
        assert 'Review 1' in notes
        assert 'Review 2' not in notes
        assert 'Review 3' in notes

    def test_delete_review_form(self, client, roasts_collection, started_test_roast):
        """Test deleting a review via form submission (redirects)."""
        roast_id = started_test_roast['roast_id']

        # Create a review
        response = client.post(
            f'/api/roast/add_review/{roast_id}',
            json={'overall_score': 4},
            content_type='application/json'
        )
        review_id = response.get_json()['review_id']

        # Delete via form (no JSON content type)
        response = client.post(
            f'/api/roast/delete_review/{roast_id}/{review_id}',
            follow_redirects=False
        )

        assert response.status_code == 302

        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert len(roast['reviews']) == 0


class TestReviewExtractionMethods:
    """Tests for different extraction methods."""

    def test_all_extraction_methods(self, client, roasts_collection, started_test_roast):
        """Test that all extraction methods are accepted."""
        roast_id = started_test_roast['roast_id']

        methods = ['espresso', 'pourover', 'ice_drop', 'cold_brew', 'other']

        for method in methods:
            client.post(
                f'/api/roast/add_review/{roast_id}',
                json={'overall_score': 4, 'extraction_method': method},
                content_type='application/json'
            )

        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert len(roast['reviews']) == 5

        stored_methods = [r['extraction_method'] for r in roast['reviews']]
        for method in methods:
            assert method in stored_methods


class TestReviewScoreValidation:
    """Tests for review score handling."""

    def test_score_range(self, client, roasts_collection, started_test_roast):
        """Test scores 1-5 are stored correctly."""
        roast_id = started_test_roast['roast_id']

        for score in range(1, 6):
            client.post(
                f'/api/roast/add_review/{roast_id}',
                json={'overall_score': score},
                content_type='application/json'
            )

        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        scores = [r['overall_score'] for r in roast['reviews']]
        assert sorted(scores) == [1, 2, 3, 4, 5]

    def test_score_string_conversion(self, client, roasts_collection, started_test_roast):
        """Test that string scores are converted to integers."""
        roast_id = started_test_roast['roast_id']

        client.post(
            f'/api/roast/add_review/{roast_id}',
            data={'overall_score': '4'},  # Form data is string
            follow_redirects=False
        )

        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert roast['reviews'][0]['overall_score'] == 4
        assert isinstance(roast['reviews'][0]['overall_score'], int)
