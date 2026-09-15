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
from models.bean_purchases import bean_version
from werkzeug.datastructures import MultiDict
from tests.conftest import TEST_DATA_MARKER


def edit_data(beans, bean_id, **fields):
    bean = beans.find_one({'_id': ObjectId(bean_id)})
    values = {'bean_version': bean_version(bean), **fields}
    if any(key in fields for key in ('purchase_date', 'purchase_weight_grams', 'purchase_price_total')):
        values['purchase_history'] = '1'
        values['purchase_id'] = str(bean['_id'])
        values.setdefault('purchase_date', bean['purchase_date'].strftime('%Y-%m-%d') if bean.get('purchase_date') else '')
        values.setdefault('purchase_weight_grams', str(bean.get('purchase_weight_grams', '')))
        amount = bean.get('purchase_price_total')
        values.setdefault('purchase_price_total', str(amount.to_decimal()) if amount else '')
    return values


def history_data(bean, rows, **fields):
    data = MultiDict({'name': bean['name'], 'bean_version': bean_version(bean), 'purchase_history': '1', **fields})
    for row in rows:
        for key, value in zip(('purchase_id', 'purchase_date', 'purchase_weight_grams', 'purchase_price_total'), row):
            data.add(key, value)
    return data


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

        assert response.status_code == 400
        assert beans_collection.find_one({'name': 'Test Invalid Numbers Bean'}) is None


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

        response = client.post(f'/api/beans/edit/{bean_id}', data=edit_data(beans_collection, bean_id, **updated_data), follow_redirects=False)

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
                'bean_version': bean_version(beans_collection.find_one({'_id': ObjectId(bean_id)})),
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

        client.post(f'/api/beans/edit/{bean_id}', data=edit_data(beans_collection, bean_id, **updated_data), follow_redirects=False)

        bean = beans_collection.find_one({'_id': ObjectId(bean_id)})
        unit_price = float(bean['unit_price_per_kg'].to_decimal())
        assert unit_price == 50.0

    def test_edit_nonexistent_bean(self, client):
        """Test editing a bean that doesn't exist."""
        fake_id = str(ObjectId())
        response = client.post(f'/api/beans/edit/{fake_id}', data={'name': 'Test'}, follow_redirects=False)
        assert response.status_code == 404


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
            data=edit_data(beans_collection, bean_id, name='Restocked Bean', stock_grams='-40'),
        )
        second = client.post(f'/api/beans/{bean_id}/set-stock-zero')

        assert second.status_code == 200
        bean = beans_collection.find_one({'_id': bean_id})
        assert [
            entry['previous_stock_grams']
            for entry in bean['stock_change_log']
        ] == [1000, 0, -40]
        assert [entry['change_grams'] for entry in bean['stock_change_log']] == [
            -1000,
            -40,
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
            'purchase_weight_grams': '1000',
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


def test_purchase_history_deltas_summaries_replay_and_manual_correction(client, beans_collection, created_test_bean):
    bean_id = ObjectId(created_test_bean)
    bean = beans_collection.find_one({'_id': bean_id})
    rows = [(str(bean_id), '2024-01-15', '1000', '45'), ('', '2025-01-01', '500', '30')]
    data = history_data(bean, rows)
    url = f'/api/beans/edit/{bean_id}'
    assert client.post(url, data=data).status_code == 302
    updated = beans_collection.find_one({'_id': bean_id})
    assert updated['stock_grams'] == 1500
    assert updated['purchase_weight_grams'] == 1500
    assert updated['purchase_price_total'].to_decimal() == 75
    assert updated['unit_price_per_kg'].to_decimal() == 50
    assert client.post(url, data=data).status_code == 409
    rows[1] = (str(updated['purchases'][1]['id']), '2023-01-01', '600', '30')
    assert client.post(url, data=history_data(updated, rows)).status_code == 302
    updated = beans_collection.find_one({'_id': bean_id})
    assert updated['stock_grams'] == 1600
    assert updated['purchase_date'] == datetime(2024, 1, 15)
    assert client.post(url, data=history_data(updated, rows, stock_grams='-10')).status_code == 302
    corrected = beans_collection.find_one({'_id': bean_id})
    assert corrected['stock_change_log'][-1]['change_grams'] == -1610
    assert corrected['stock_change_log'][-1]['event_type'] == 'manual_correction'
    assert client.post(url, data=history_data(corrected, rows[:1])).status_code == 302
    assert beans_collection.find_one({'_id': bean_id})['stock_grams'] == -610
    html = client.get(f'/beans/detail/{bean_id}').get_data(as_text=True)
    assert 'Purchase History' in html and '2024-01-15' in html
    assert 'Average Price per kg' in html


@pytest.mark.parametrize('date,weight,amount', [
    ('2026-02-30', '100', '5'), ('2026-01-01', '0', '5'),
    ('2026-01-01', '-1', '5'), ('2026-01-01', '1.5', '5'),
    ('2026-01-01', 'true', '5'), ('2026-01-01', '10', 'NaN'),
    ('2026-01-01', '10', 'Infinity'), ('2026-01-01', '10', '-5'),
])
def test_invalid_purchase_never_partially_writes(client, beans_collection, created_test_bean, date, weight, amount):
    bean = beans_collection.find_one({'_id': ObjectId(created_test_bean)})
    data = history_data(bean, [('', date, weight, amount)], name='Must not save')
    response = client.post(f'/api/beans/edit/{created_test_bean}', data=data)
    assert response.status_code == 400
    assert beans_collection.find_one({'_id': bean['_id']}) == bean


def test_purchase_identifiers_unknown_cost_and_stale_roast(client, beans_collection, created_test_bean):
    bean = beans_collection.find_one({'_id': ObjectId(created_test_bean)})
    url = f'/api/beans/edit/{bean["_id"]}'
    for rows in [
        [('bad', '', '10', '1')], [(str(ObjectId()), '', '10', '1')],
        [(str(bean['_id']), '', '10', '1')] * 2,
    ]:
        assert client.post(url, data=history_data(bean, rows)).status_code == 400
    data = history_data(bean, [(str(bean['_id']), '', '1000', '')])
    assert client.post(url, data=data).status_code == 302
    bean = beans_collection.find_one({'_id': bean['_id']})
    assert bean['purchase_price_total'] is None and bean['unit_price_per_kg'] is None
    stale = history_data(bean, [('', '', '500', '')])
    beans_collection.update_one({'_id': bean['_id']}, {'$inc': {'stock_grams': -200}})
    assert client.post(url, data=stale).status_code == 409
    assert beans_collection.find_one({'_id': bean['_id']})['stock_grams'] == 800


def test_purchase_compare_and_swap_rejects_intervening_write(monkeypatch, client, beans_collection, created_test_bean):
    import models.bean_helpers as purchases
    bean = beans_collection.find_one({'_id': ObjectId(created_test_bean)})
    original = purchases.snapshot_query
    def racing_query(document):
        beans_collection.update_one({'_id': document['_id']}, {'$inc': {'stock_grams': -200}})
        return original(document)
    monkeypatch.setattr(purchases, 'snapshot_query', racing_query)
    data = history_data(bean, [(str(bean['_id']), '', '1500', '50')])
    assert client.post(f'/api/beans/edit/{bean["_id"]}', data=data).status_code == 409
    stored = beans_collection.find_one({'_id': bean['_id']})
    assert stored['stock_grams'] == 800 and 'purchases' not in stored


def test_full_purchase_and_roast_inventory_equation(client, beans_collection, roasts_collection, created_test_bean):
    bean_id = ObjectId(created_test_bean)
    roast_id = roasts_collection.insert_one({'bean_id': bean_id, 'original_weight_grams': 200,
                                             'lifecycle_status': 'draft', 'test_data': True}).inserted_id
    url = f'/api/beans/edit/{bean_id}'
    try:
        assert client.post(f'/api/roast/start/{roast_id}', json={}).status_code == 200
        bean = beans_collection.find_one({'_id': bean_id})
        rows = [(str(bean_id), '2024-01-15', '1000', '45'), ('', '2026-09-10', '500', '30')]
        assert client.post(url, data=history_data(bean, rows)).status_code == 302
        bean = beans_collection.find_one({'_id': bean_id})
        assert bean['stock_grams'] == 1300
        rows[1] = (str(bean['purchases'][1]['id']), '2023-01-01', '600', '30')
        assert client.post(url, data=history_data(bean, rows)).status_code == 302
        bean = beans_collection.find_one({'_id': bean_id})
        assert bean['stock_grams'] == 1400
        assert bean['inventory_opening_adjustment_grams'] == 0
        assert client.post(f'/api/beans/{bean_id}/set-stock-zero').status_code == 200
        bean = beans_collection.find_one({'_id': bean_id})
        rows.append(('', '2026-09-15', '500', '0'))
        assert client.post(url, data=history_data(bean, rows)).status_code == 302
        assert beans_collection.find_one({'_id': bean_id})['stock_grams'] == 500
        for _ in range(2):
            assert client.post(f'/api/roast/delete/{roast_id}').status_code == 302
            bean = beans_collection.find_one({'_id': bean_id})
            assert bean['stock_grams'] == 700
        assert bean['stock_grams'] == sum(row['weight_grams'] for row in bean['purchases']) + sum(row['change_grams'] for row in bean['stock_change_log'])
        assert client.post(url, data=history_data(bean, [])).status_code == 302
        empty = beans_collection.find_one({'_id': bean_id})
        assert empty['stock_grams'] == -1400 and empty['purchases'] == []
        assert empty['purchase_date'] is None and empty['unit_price_per_kg'] is None
    finally:
        roasts_collection.delete_one({'_id': roast_id})
