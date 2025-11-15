#!/usr/bin/env python3
"""
Comprehensive tests for the Order Management System API.
"""

import os
import json
import pytest
import tempfile
import sqlite3
import sys
from datetime import datetime, timedelta

# Import app
from app import app, init_db, get_db_connection


@pytest.fixture
def client(monkeypatch):
    """Create a test client with a temporary database."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')

    # Patch the DATABASE_PATH in the app module
    monkeypatch.setattr('app.DATABASE_PATH', db_path)

    # Initialize the database
    init_db()

    with app.test_client() as client:
        yield client

    # Cleanup
    os.close(db_fd)
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def sample_merchant(client):
    """Create a sample merchant for testing."""
    response = client.post('/merchants', json={
        'name': 'Test Merchant',
        'email': 'test@merchant.com'
    })
    return json.loads(response.data)


@pytest.fixture
def sample_driver(client):
    """Create a sample driver for testing."""
    response = client.post('/drivers', json={'name': 'John Driver'})
    return json.loads(response.data)


@pytest.fixture
def sample_vehicle(client, sample_driver):
    """Create a sample vehicle for testing."""
    response = client.post('/vehicles', json={
        'driver_id': sample_driver['id'],
        'max_orders': 5,
        'max_weight': 200
    })
    return json.loads(response.data)


@pytest.fixture
def sample_shift(client, sample_driver):
    """Create a sample shift for testing."""
    tomorrow = (datetime.now() + timedelta(days=1)).date()
    response = client.post('/shifts', json={
        'driver_id': sample_driver['id'],
        'shift_date': tomorrow.isoformat(),
        'start_time': '09:00:00',
        'end_time': '17:00:00'
    })
    return json.loads(response.data)


class TestOrderCreation:
    """Test order creation and auto-assignment."""

    def test_create_order_with_valid_data(self, client, sample_merchant):
        """Test creating an order with valid data."""
        tomorrow = datetime.now() + timedelta(days=1)
        pickup_time = tomorrow.replace(
            hour=10, minute=0, second=0, microsecond=0)
        dropoff_time = pickup_time + timedelta(hours=2)

        response = client.post('/orders', json={
            'merchant_id': sample_merchant['id'],
            'description': 'Test Order',
            'pickup_time': pickup_time.isoformat(),
            'dropoff_time': dropoff_time.isoformat(),
            'weight': 50.0
        })

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['order_id'] is not None
        assert data['merchant_id'] == sample_merchant['id']
        assert data['description'] == 'Test Order'
        assert data['weight'] == 50.0
        assert data['status'] in ['pending', 'assigned']

    def test_create_order_missing_required_fields(self, client):
        """Test creating an order with missing required fields."""
        response = client.post('/orders', json={
            'merchant_id': 1,
            'pickup_time': '2025-01-15T10:00:00'
            # Missing dropoff_time and weight
        })

        assert response.status_code == 400

    def test_create_order_invalid_time_validation(self, client, sample_merchant):
        """Test order creation with invalid time constraints."""
        tomorrow = datetime.now() + timedelta(days=1)
        pickup_time = tomorrow.replace(hour=10, minute=0)
        dropoff_time = pickup_time + \
            timedelta(minutes=10)  # Less than 15 minutes

        response = client.post('/orders', json={
            'merchant_id': sample_merchant['id'],
            'pickup_time': pickup_time.isoformat(),
            'dropoff_time': dropoff_time.isoformat(),
            'weight': 50.0
        })

        assert response.status_code == 400
        data = json.loads(response.data)
        assert '15 minutes' in data['error']

    def test_create_order_different_days(self, client, sample_merchant):
        """Test order creation with pickup and dropoff on different days."""
        tomorrow = datetime.now() + timedelta(days=1)
        pickup_time = tomorrow.replace(hour=10, minute=0)
        dropoff_time = pickup_time + timedelta(days=1, hours=2)

        response = client.post('/orders', json={
            'merchant_id': sample_merchant['id'],
            'pickup_time': pickup_time.isoformat(),
            'dropoff_time': dropoff_time.isoformat(),
            'weight': 50.0
        })

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'same day' in data['error']

    def test_create_order_auto_assign_driver(self, client, sample_merchant, sample_driver,
                                             sample_vehicle, sample_shift):
        """Test that order automatically assigns a driver when available."""
        tomorrow = datetime.now() + timedelta(days=1)
        pickup_time = tomorrow.replace(
            hour=10, minute=0, second=0, microsecond=0)
        dropoff_time = pickup_time + timedelta(hours=2)

        response = client.post('/orders', json={
            'merchant_id': sample_merchant['id'],
            'description': 'Test Order',
            'pickup_time': pickup_time.isoformat(),
            'dropoff_time': dropoff_time.isoformat(),
            'weight': 50.0
        })

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['status'] == 'assigned'
        assert 'driver' in data
        assert data['driver']['id'] == sample_driver['id']
        assert data['driver']['name'] == sample_driver['name']


class TestOrderUpdate:
    """Test order updates."""

    def test_update_order_merchant_authorization(self, client, sample_merchant):
        """Test that only the merchant who created the order can update it."""
        # Create order
        tomorrow = datetime.now() + timedelta(days=1)
        pickup_time = tomorrow.replace(hour=10, minute=0)
        dropoff_time = pickup_time + timedelta(hours=2)

        order_response = client.post('/orders', json={
            'merchant_id': sample_merchant['id'],
            'pickup_time': pickup_time.isoformat(),
            'dropoff_time': dropoff_time.isoformat(),
            'weight': 50.0
        })
        order_id = json.loads(order_response.data)['order_id']

        # Create another merchant
        other_merchant_response = client.post('/merchants', json={
            'name': 'Other Merchant',
            'email': 'other@merchant.com'
        })
        other_merchant_id = json.loads(other_merchant_response.data)['id']

        # Try to update with wrong merchant
        response = client.put(f'/orders/{order_id}', json={
            'merchant_id': other_merchant_id,
            'description': 'Updated Description'
        })

        assert response.status_code == 403

    def test_update_order_completed_status(self, client, sample_merchant):
        """Test that completed orders cannot be edited."""
        # Create order
        tomorrow = datetime.now() + timedelta(days=1)
        pickup_time = tomorrow.replace(hour=10, minute=0)
        dropoff_time = pickup_time + timedelta(hours=2)

        order_response = client.post('/orders', json={
            'merchant_id': sample_merchant['id'],
            'pickup_time': pickup_time.isoformat(),
            'dropoff_time': dropoff_time.isoformat(),
            'weight': 50.0
        })
        order_id = json.loads(order_response.data)['order_id']

        # Mark as completed (using direct DB update for testing)
        import sqlite3
        from app import DATABASE_PATH
        conn = sqlite3.connect(DATABASE_PATH)
        conn.execute('UPDATE orders SET status = ? WHERE id = ?',
                     ('completed', order_id))
        conn.commit()
        conn.close()

        # Try to update
        response = client.put(f'/orders/{order_id}', json={
            'merchant_id': sample_merchant['id'],
            'description': 'Updated Description'
        })

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'completed' in data['error'] or 'cancelled' in data['error']

    def test_update_order_reassignment(self, client, sample_merchant, sample_driver,
                                       sample_vehicle, sample_shift):
        """Test that updating order time/weight triggers re-assignment."""
        tomorrow = datetime.now() + timedelta(days=1)
        pickup_time = tomorrow.replace(hour=10, minute=0)
        dropoff_time = pickup_time + timedelta(hours=2)

        # Create order (should be assigned)
        order_response = client.post('/orders', json={
            'merchant_id': sample_merchant['id'],
            'pickup_time': pickup_time.isoformat(),
            'dropoff_time': dropoff_time.isoformat(),
            'weight': 50.0
        })
        order_id = json.loads(order_response.data)['order_id']

        # Update with new time (still within shift)
        new_pickup = tomorrow.replace(hour=11, minute=0)
        new_dropoff = new_pickup + timedelta(hours=2)

        response = client.put(f'/orders/{order_id}', json={
            'merchant_id': sample_merchant['id'],
            'pickup_time': new_pickup.isoformat(),
            'dropoff_time': new_dropoff.isoformat()
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        # Driver should still be assigned if they fit
        assert data['status'] in ['pending', 'assigned']


class TestOrderCancellation:
    """Test order cancellation."""

    def test_cancel_order(self, client, sample_merchant, sample_driver,
                          sample_vehicle, sample_shift):
        """Test cancelling an order."""
        tomorrow = datetime.now() + timedelta(days=1)
        pickup_time = tomorrow.replace(hour=10, minute=0)
        dropoff_time = pickup_time + timedelta(hours=2)

        # Create and assign order
        order_response = client.post('/orders', json={
            'merchant_id': sample_merchant['id'],
            'pickup_time': pickup_time.isoformat(),
            'dropoff_time': dropoff_time.isoformat(),
            'weight': 50.0
        })
        order_id = json.loads(order_response.data)['order_id']

        # Cancel order
        response = client.delete(f'/orders/{order_id}')

        assert response.status_code == 200

        # Verify order is cancelled (check via database since we don't have GET endpoint for single order)
        import sqlite3
        from app import DATABASE_PATH
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        order = conn.execute(
            'SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
        conn.close()
        assert order is not None
        assert order['status'] == 'cancelled'
        assert order['driver_id'] is None


class TestOrderRetrieval:
    """Test order retrieval endpoints."""

    def test_get_orders_with_pagination(self, client, sample_merchant):
        """Test getting orders with pagination."""
        # Create multiple orders
        tomorrow = datetime.now() + timedelta(days=1)
        for i in range(5):
            pickup_time = tomorrow.replace(hour=10 + i, minute=0)
            dropoff_time = pickup_time + timedelta(hours=2)

            client.post('/orders', json={
                'merchant_id': sample_merchant['id'],
                'pickup_time': pickup_time.isoformat(),
                'dropoff_time': dropoff_time.isoformat(),
                'weight': 50.0
            })

        # Get orders with pagination
        response = client.get(
            f'/orders?merchant_id={sample_merchant["id"]}&page=1&per_page=3')

        assert response.status_code == 200
        data = json.loads(response.data)

        # Ensure pagination metadata is present
        assert data['page'] == 1
        assert data['per_page'] == 3
        assert data['total'] == 5
        assert data['total_pages'] == 2

        # Orders array should be paginated and contain required fields
        orders = data['orders']
        assert len(orders) <= 3
        assert all('order_id' in order for order in orders)
        assert all('status' in order for order in orders)

    def test_get_orders_missing_merchant_id(self, client):
        """Test getting orders without merchant_id."""
        response = client.get('/orders')

        assert response.status_code == 400


class TestDriverEndpoints:
    """Test driver-related endpoints."""

    def test_get_drivers_with_shifts(self, client, sample_driver, sample_shift):
        """Test getting drivers with their shifts."""
        response = client.get('/drivers')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) > 0

        # Find our driver
        driver = next(
            (d for d in data if d['id'] == sample_driver['id']), None)
        assert driver is not None
        assert 'shifts' in driver
        assert len(driver['shifts']) > 0


class TestValidation:
    """Test validation logic."""

    def test_order_time_validation_4_hour_limit(self, client, sample_merchant):
        """Test that dropoff cannot be more than 4 hours after pickup."""
        tomorrow = datetime.now() + timedelta(days=1)
        pickup_time = tomorrow.replace(hour=10, minute=0)
        dropoff_time = pickup_time + timedelta(hours=5)  # More than 4 hours

        response = client.post('/orders', json={
            'merchant_id': sample_merchant['id'],
            'pickup_time': pickup_time.isoformat(),
            'dropoff_time': dropoff_time.isoformat(),
            'weight': 50.0
        })

        assert response.status_code == 400
        data = json.loads(response.data)
        assert '4 hours' in data['error']


class TestDriverAssignment:
    """Test driver assignment logic."""

    def test_no_driver_assignment_when_no_shift(self, client, sample_merchant,
                                                sample_driver, sample_vehicle):
        """Test that order stays pending when driver has no shift."""
        tomorrow = datetime.now() + timedelta(days=1)
        pickup_time = tomorrow.replace(hour=10, minute=0)
        dropoff_time = pickup_time + timedelta(hours=2)

        response = client.post('/orders', json={
            'merchant_id': sample_merchant['id'],
            'pickup_time': pickup_time.isoformat(),
            'dropoff_time': dropoff_time.isoformat(),
            'weight': 50.0
        })

        assert response.status_code == 201
        data = json.loads(response.data)
        # Should be pending since no shift exists
        assert data['status'] == 'pending'

    def test_no_driver_assignment_when_weight_exceeds_capacity(self, client, sample_merchant,
                                                               sample_driver, sample_vehicle,
                                                               sample_shift):
        """Test that order stays pending when weight exceeds vehicle capacity."""
        tomorrow = datetime.now() + timedelta(days=1)
        pickup_time = tomorrow.replace(hour=10, minute=0)
        dropoff_time = pickup_time + timedelta(hours=2)

        response = client.post('/orders', json={
            'merchant_id': sample_merchant['id'],
            'pickup_time': pickup_time.isoformat(),
            'dropoff_time': dropoff_time.isoformat(),
            'weight': 300.0  # Exceeds max_weight of 200
        })

        assert response.status_code == 201
        data = json.loads(response.data)
        # Should be pending since weight exceeds capacity
        assert data['status'] == 'pending'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
