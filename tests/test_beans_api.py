"""
API tests for Bean operations.

Tests cover:
- Create bean with valid/invalid data
- Edit bean details
- Delete bean (verify soft delete)
- Stock management
- Unit price calculation
"""
from datetime import datetime
from types import SimpleNamespace

import pytest
from bson.objectid import ObjectId
from bson.decimal128 import Decimal128

from models.bean_helpers import set_bean_stock_to_zero
from tests.conftest import TEST_DATA_MARKER


class TestBeanCreate:
    """Tests for bean creation endpoint."""

    def test_create_bean_valid_data(self, client, beans_collection, test_bean_data):
        """Test creating a bean with all valid fields."""
        # Add test marker to form data
        form_data = {**test_bean_data}

        response = client.post('/api/beans/add', data=form_data, follow_redirects=False)

        # Should redirect to beans list
        assert response.status_code == 302
        assert '/beans' in response.location

        # Verify bean was created
        bean = beans_collection.find_one({'name': test_bean_data['name']})
        assert bean is not None
        assert bean['origin'] == test_bean_data['origin']
        assert bean['process'] == test_bean_data['process']
        assert bean['supplier'] == test_bean_data['supplier']
        assert bean['short_flavor_notes'] == [
            'Blueberry',
            'Jasmine',
            'Dark Chocolate',
        ]
        assert int(bean['stock_grams']) == int(test_bean_data['stock_grams'])
        assert bean['stock_change_log'] == []
        assert bean['archived'] == False

        # Cleanup - mark and delete
        beans_collection.delete_one({'_id': bean['_id']})

    def test_create_bean_minimal_data(self, client, beans_collection):
        """Test creating a bean with only required fields."""
        form_data = {
            'name': 'Test Minimal Bean',
            'origin': '',
            'process': '',
        }

        response = client.post('/api/beans/add', data=form_data, follow_redirects=False)

        assert response.status_code == 302

        # Verify bean was created
        bean = beans_collection.find_one({'name': 'Test Minimal Bean'})
        assert bean is not None
        assert bean['name'] == 'Test Minimal Bean'
        assert bean['short_flavor_notes'] == []

        # Cleanup
        beans_collection.delete_one({'_id': bean['_id']})

    def test_create_bean_calculates_unit_price(self, client, beans_collection):
        """Test that unit_price_per_kg is calculated correctly."""
        form_data = {
            'name': 'Test Price Bean',
            'purchase_price_total': '50.00',
            'purchase_weight_grams': '500',  # 0.5 kg
            'stock_grams': '500',
        }

        client.post('/api/beans/add', data=form_data, follow_redirects=False)

        bean = beans_collection.find_one({'name': 'Test Price Bean'})
        assert bean is not None

        # Unit price should be 50 / 0.5 = 100 per kg
        unit_price = float(bean['unit_price_per_kg'].to_decimal())
        assert unit_price == 100.0

        # Cleanup
        beans_collection.delete_one({'_id': bean['_id']})

    def test_create_bean_handles_invalid_numbers(self, client, beans_collection):
        """Test that invalid numeric fields are handled gracefully."""
        form_data = {
            'name': 'Test Invalid Numbers Bean',
            'purchase_price_total': 'not-a-number',
            'purchase_weight_grams': 'also-not-a-number',
            'stock_grams': 'still-not-a-number',
        }

        response = client.post('/api/beans/add', data=form_data, follow_redirects=False)

        # Should still succeed (with default/zero values)
        assert response.status_code == 302

        bean = beans_collection.find_one({'name': 'Test Invalid Numbers Bean'})
        assert bean is not None

        # Cleanup
        beans_collection.delete_one({'_id': bean['_id']})


class TestBeanEdit:
    """Tests for bean edit endpoint."""

    def test_edit_bean_updates_fields(self, client, beans_collection, created_test_bean):
        """Test editing a bean updates all provided fields."""
        bean_id = created_test_bean

        updated_data = {
            'name': 'Updated Bean Name',
            'origin': 'Colombia',
            'process': 'Natural',
            'supplier': 'New Supplier',
            'purchase_price_total': '60.00',
            'purchase_weight_grams': '1200',
            'stock_grams': '800',
            'color': '#FF5733',
            'short_flavor_notes': 'Cherry\nCocoa',
            'notes': 'Updated notes',
        }

        response = client.post(f'/api/beans/edit/{bean_id}', data=updated_data, follow_redirects=False)

        assert response.status_code == 302

        # Verify updates
        bean = beans_collection.find_one({'_id': ObjectId(bean_id)})
        assert bean['name'] == 'Updated Bean Name'
        assert bean['origin'] == 'Colombia'
        assert bean['process'] == 'Natural'
        assert bean['short_flavor_notes'] == ['Cherry', 'Cocoa']
        assert int(bean['stock_grams']) == 800

    def test_edit_bean_clears_short_flavor_notes(self, client, beans_collection, created_test_bean):
        """Test editing can clear short flavor notes."""
        bean_id = created_test_bean

        response = client.post(
            f'/api/beans/edit/{bean_id}',
            data={
                'name': 'Cleared Notes Bean',
                'short_flavor_notes': '',
            },
            follow_redirects=False,
        )

        assert response.status_code == 302
        bean = beans_collection.find_one({'_id': ObjectId(bean_id)})
        assert bean['short_flavor_notes'] == []

    def test_edit_bean_recalculates_unit_price(self, client, beans_collection, created_test_bean):
        """Test that editing price/weight recalculates unit price."""
        bean_id = created_test_bean

        updated_data = {
            'name': 'Price Update Bean',
            'purchase_price_total': '100.00',
            'purchase_weight_grams': '2000',  # 2 kg, so price should be 50/kg
            'stock_grams': '2000',
        }

        client.post(f'/api/beans/edit/{bean_id}', data=updated_data, follow_redirects=False)

        bean = beans_collection.find_one({'_id': ObjectId(bean_id)})
        unit_price = float(bean['unit_price_per_kg'].to_decimal())
        assert unit_price == 50.0

    def test_edit_nonexistent_bean(self, client):
        """Test editing a bean that doesn't exist."""
        fake_id = str(ObjectId())
        response = client.post(f'/api/beans/edit/{fake_id}', data={'name': 'Test'}, follow_redirects=False)
        # The helper function will try to update but find nothing
        # This should still redirect (no error handling in current implementation)
        assert response.status_code == 302


class TestBeanDelete:
    """Tests for bean deletion (soft delete)."""

    def test_delete_bean_soft_deletes(self, client, beans_collection, created_test_bean):
        """Test that deleting a bean sets archived=True."""
        bean_id = created_test_bean

        response = client.post(f'/api/beans/delete/{bean_id}', follow_redirects=False)

        assert response.status_code == 302

        # Verify soft delete
        bean = beans_collection.find_one({'_id': ObjectId(bean_id)})
        assert bean is not None  # Bean still exists
        assert bean['archived'] == True

    def test_deleted_bean_not_in_active_list(self, client, beans_collection, created_test_bean):
        """Test that archived beans don't appear in active queries."""
        bean_id = created_test_bean

        # Delete the bean
        client.post(f'/api/beans/delete/{bean_id}', follow_redirects=False)

        # Query for non-archived beans
        active_beans = list(beans_collection.find({
            'archived': {'$ne': True},
            '_id': ObjectId(bean_id)
        }))

        assert len(active_beans) == 0


class TestBeanStock:
    """Tests for bean stock management."""

    def test_bean_stock_decrements_on_roast_start(self, client, beans_collection, created_test_bean):
        """Test that starting a roast decrements bean stock."""
        bean_id = created_test_bean

        # Get initial stock
        bean = beans_collection.find_one({'_id': ObjectId(bean_id)})
        initial_stock = bean['stock_grams']

        # Create a roast and start it with this bean
        response = client.post('/api/roast/create')
        roast_data = response.get_json()
        roast_id = roast_data['new_roast_id']

        # Start the roast
        start_data = {
            'bean_id': bean_id,
            'original_weight_grams': 150
        }
        client.post(
            f'/api/roast/start/{roast_id}',
            json=start_data,
            content_type='application/json'
        )

        # Verify stock decreased
        bean = beans_collection.find_one({'_id': ObjectId(bean_id)})
        assert bean['stock_grams'] == initial_stock - 150
        assert bean.get('stock_change_log', []) == []

        # Cleanup roast
        from app import db_local
        db_local.roasts.delete_one({'_id': ObjectId(roast_id)})

    def test_bean_stock_restored_on_roast_delete(
        self, client, beans_collection, roasts_collection, created_test_roast
    ):
        """Test that deleting a roast restores bean stock."""
        roast_id = created_test_roast['roast_id']
        bean_id = created_test_roast['bean_id']

        # First start the roast to decrement stock
        start_data = {
            'bean_id': bean_id,
            'original_weight_grams': 150
        }
        client.post(
            f'/api/roast/start/{roast_id}',
            json=start_data,
            content_type='application/json'
        )

        # Get stock after start
        bean_after_start = beans_collection.find_one({'_id': ObjectId(bean_id)})
        stock_after_start = bean_after_start['stock_grams']

        # Update roast to have original_weight_grams (needed for restore)
        roasts_collection.update_one(
            {'_id': ObjectId(roast_id)},
            {'$set': {'original_weight_grams': 150}}
        )

        # Delete the roast
        client.post(f'/api/roast/delete/{roast_id}', follow_redirects=False)

        # Verify stock restored
        bean_after_delete = beans_collection.find_one({'_id': ObjectId(bean_id)})
        assert bean_after_delete['stock_grams'] == stock_after_start + 150
        assert bean_after_delete.get('stock_change_log', []) == []

    @pytest.mark.parametrize(
        ('initial_stock', 'expected_change'),
        [(275, -275), (-25, 25)],
    )
    def test_set_non_zero_stock_to_zero_records_exact_change(
        self,
        client,
        beans_collection,
        created_test_bean,
        initial_stock,
        expected_change,
    ):
        bean_id = ObjectId(created_test_bean)
        beans_collection.update_one(
            {'_id': bean_id},
            {
                '$set': {'stock_grams': initial_stock},
                '$unset': {'stock_change_log': ''},
            },
        )

        response = client.post(
            f'/api/beans/{bean_id}/set-stock-zero'
        )

        assert response.status_code == 200
        assert response.json['success'] is True
        assert response.json['previous_stock_grams'] == initial_stock
        assert response.json['change_grams'] == expected_change
        assert response.json['stock_grams'] == 0
        assert response.json['stock_change'] == {
            'event_type': 'set_to_zero',
            'previous_stock_grams': initial_stock,
            'change_grams': expected_change,
            'resulting_stock_grams': 0,
            'recorded_at': response.json['stock_change']['recorded_at'],
        }
        assert datetime.fromisoformat(
            response.json['stock_change']['recorded_at']
        ).utcoffset() is not None

        bean = beans_collection.find_one({'_id': bean_id})
        assert bean['stock_grams'] == 0
        assert bean['archived'] is False
        assert bean['test_data'] is True
        assert len(bean['stock_change_log']) == 1
        assert bean['stock_change_log'][0]['previous_stock_grams'] == initial_stock
        assert bean['stock_change_log'][0]['change_grams'] == expected_change
        assert bean['updated_at'] == bean['stock_change_log'][0]['recorded_at']

    def test_set_zero_stock_rejects_repeated_requests_without_duplicate_history(
        self,
        client,
        beans_collection,
        created_test_bean,
    ):
        bean_id = ObjectId(created_test_bean)

        first = client.post(f'/api/beans/{bean_id}/set-stock-zero')
        repeated = client.post(f'/api/beans/{bean_id}/set-stock-zero')

        assert first.status_code == 200
        assert repeated.status_code == 409
        assert repeated.json == {
            'success': False,
            'error': 'Bean stock is already zero',
        }
        bean = beans_collection.find_one({'_id': bean_id})
        assert len(bean['stock_change_log']) == 1

    def test_set_stock_zero_rejects_missing_and_archived_beans(
        self,
        client,
        beans_collection,
        created_test_bean,
    ):
        missing = client.post(
            f'/api/beans/{ObjectId()}/set-stock-zero'
        )
        assert missing.status_code == 404
        assert missing.json == {'success': False, 'error': 'Bean not found'}

        bean_id = ObjectId(created_test_bean)
        beans_collection.update_one(
            {'_id': bean_id},
            {'$set': {'archived': True}},
        )
        archived = client.post(f'/api/beans/{bean_id}/set-stock-zero')
        assert archived.status_code == 404
        assert archived.json == {'success': False, 'error': 'Bean not found'}
        assert beans_collection.find_one({'_id': bean_id})['stock_grams'] != 0

    def test_manual_restock_preserves_history_and_allows_another_zero_event(
        self,
        client,
        beans_collection,
        created_test_bean,
    ):
        bean_id = ObjectId(created_test_bean)
        first = client.post(f'/api/beans/{bean_id}/set-stock-zero')
        assert first.status_code == 200

        client.post(
            f'/api/beans/edit/{bean_id}',
            data={'name': 'Restocked Bean', 'stock_grams': '-40'},
        )
        second = client.post(f'/api/beans/{bean_id}/set-stock-zero')

        assert second.status_code == 200
        bean = beans_collection.find_one({'_id': bean_id})
        assert [
            entry['previous_stock_grams']
            for entry in bean['stock_change_log']
        ] == [1000, -40]
        assert [entry['change_grams'] for entry in bean['stock_change_log']] == [
            -1000,
            40,
        ]

    def test_concurrent_stock_change_returns_conflict_without_append(self):
        bean_id = ObjectId()
        update_calls = []

        class ConcurrentCollection:
            def __init__(self):
                self.read_count = 0

            def find_one(self, query):
                self.read_count += 1
                stock = 200 if self.read_count == 1 else 150
                return {'_id': bean_id, 'archived': False, 'stock_grams': stock}

            def update_one(self, query, update):
                update_calls.append((query, update))
                return SimpleNamespace(modified_count=0)

        result = set_bean_stock_to_zero(
            ConcurrentCollection(),
            str(bean_id),
        )

        assert result == {'status': 'conflict'}
        assert update_calls[0][0]['stock_grams'] == 200
        assert update_calls[0][1]['$push']['stock_change_log'][
            'previous_stock_grams'
        ] == 200


class TestBeanLabel:
    """Tests for bean label API endpoint."""

    def test_save_label_data(self, client, beans_collection, created_test_bean):
        """Test saving label data to a bean."""
        bean_id = created_test_bean

        label_data = {
            'name': 'Ethiopia Yirgacheffe',
            'origin': 'Ethiopia',
            'process': 'Washed',
            'roastLevel': 'Medium',
            'templateId': 'minimal',
            'customFields': {}
        }

        response = client.post(
            f'/api/beans/{bean_id}/label',
            json=label_data,
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

        bean = beans_collection.find_one({'_id': ObjectId(bean_id)})
        assert bean['label']['name'] == 'Ethiopia Yirgacheffe'
        assert bean['label']['templateId'] == 'minimal'
        assert bean['label']['roastLevel'] == 'Medium'

    def test_save_label_invalid_bean(self, client):
        """Test saving label data for a non-existent bean returns 404."""
        fake_id = str(ObjectId())

        response = client.post(
            f'/api/beans/{fake_id}/label',
            json={'name': 'Test', 'templateId': 'minimal', 'customFields': {}},
            content_type='application/json'
        )

        assert response.status_code == 404

    def test_save_label_with_image(self, client, beans_collection, created_test_bean):
        """Test saving label data with image selection."""
        bean_id = created_test_bean

        label_data = {
            'name': 'Test Bean',
            'origin': 'Colombia',
            'process': 'Natural',
            'roastLevel': 'Dark',
            'templateId': 'minimal',
            'imageSrc': '/static/img/nova.png'
        }

        response = client.post(
            f'/api/beans/{bean_id}/label',
            json=label_data,
            content_type='application/json'
        )

        assert response.status_code == 200

        bean = beans_collection.find_one({'_id': ObjectId(bean_id)})
        assert bean['label']['imageSrc'] == '/static/img/nova.png'
        assert bean['label']['templateId'] == 'minimal'


class TestBeanFormValidation:
    """Tests for bean form validation and data handling."""

    def test_bean_purchase_date_parsing(self, client, beans_collection):
        """Test that purchase date is correctly parsed."""
        form_data = {
            'name': 'Date Test Bean',
            'purchase_date': '2024-06-15',
        }

        client.post('/api/beans/add', data=form_data, follow_redirects=False)

        bean = beans_collection.find_one({'name': 'Date Test Bean'})
        assert bean is not None
        assert bean['purchase_date'].year == 2024
        assert bean['purchase_date'].month == 6
        assert bean['purchase_date'].day == 15

        # Cleanup
        beans_collection.delete_one({'_id': bean['_id']})

    def test_bean_color_default(self, client, beans_collection):
        """Test that color has a default value if not provided."""
        form_data = {
            'name': 'Color Default Bean',
        }

        client.post('/api/beans/add', data=form_data, follow_redirects=False)

        bean = beans_collection.find_one({'name': 'Color Default Bean'})
        assert bean is not None
        assert bean['color'] == '#6B8E6F'  # Default color

        # Cleanup
        beans_collection.delete_one({'_id': bean['_id']})

    def test_bean_timestamps_created(self, client, beans_collection):
        """Test that created_at and updated_at timestamps are set."""
        form_data = {
            'name': 'Timestamp Test Bean',
        }

        before_create = datetime.now()
        client.post('/api/beans/add', data=form_data, follow_redirects=False)

        bean = beans_collection.find_one({'name': 'Timestamp Test Bean'})
        assert bean is not None
        assert 'created_at' in bean
        assert 'updated_at' in bean
        assert bean['created_at'] >= before_create.replace(microsecond=0)

        # Cleanup
        beans_collection.delete_one({'_id': bean['_id']})
