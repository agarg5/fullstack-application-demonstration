import os
import sqlite3
import threading
from datetime import datetime, timedelta, time as dt_time
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Database configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/database.db')

# Lock for order updates (to prevent race conditions)
order_locks = {}
lock_manager = threading.Lock()


def get_db_connection():
    """Create a database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database with all required tables."""
    conn = get_db_connection()

    # Merchants table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS merchants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Drivers table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Vehicles table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id INTEGER NOT NULL,
            max_orders INTEGER NOT NULL,
            max_weight REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (driver_id) REFERENCES drivers(id) ON DELETE CASCADE,
            UNIQUE(driver_id)
        )
    ''')

    # Shifts table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id INTEGER NOT NULL,
            shift_date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (driver_id) REFERENCES drivers(id) ON DELETE CASCADE,
            UNIQUE(driver_id, shift_date)
        )
    ''')

    # Orders table - add description field
    conn.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            merchant_id INTEGER NOT NULL,
            driver_id INTEGER,
            vehicle_id INTEGER,
            status TEXT NOT NULL DEFAULT 'pending',
            description TEXT,
            pickup_time TIMESTAMP NOT NULL,
            dropoff_time TIMESTAMP NOT NULL,
            weight REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (merchant_id) REFERENCES merchants(id) ON DELETE CASCADE,
            FOREIGN KEY (driver_id) REFERENCES drivers(id) ON DELETE SET NULL,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE SET NULL,
            CHECK(status IN ('pending', 'assigned', 'completed', 'cancelled'))
        )
    ''')

    # Add description column if it doesn't exist (for existing databases)
    try:
        conn.execute('ALTER TABLE orders ADD COLUMN description TEXT')
    except sqlite3.OperationalError:
        pass  # Column already exists

    conn.commit()
    conn.close()


def validate_order_times(pickup_time_str, dropoff_time_str):
    """Validate order pickup and dropoff times."""
    try:
        pickup_time = datetime.fromisoformat(
            pickup_time_str.replace('Z', '+00:00'))
        dropoff_time = datetime.fromisoformat(
            dropoff_time_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return False, "Invalid datetime format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"

    # Check if both are on the same day
    if pickup_time.date() != dropoff_time.date():
        return False, "Pickup and dropoff must be on the same day"

    # Check if pickup is at least 15 minutes before dropoff
    time_diff = dropoff_time - pickup_time
    if time_diff < timedelta(minutes=15):
        return False, "Pickup time must be at least 15 minutes before dropoff time"

    # Check if dropoff is at most 4 hours after pickup
    if time_diff > timedelta(hours=4):
        return False, "Dropoff time must be at most 4 hours after pickup time"

    return True, None


def find_available_driver(conn, pickup_time_str, dropoff_time_str, weight, exclude_driver_id=None):
    """
    Find an available driver for an order.
    Checks: shift availability, vehicle capacity (orders and weight).
    """
    try:
        pickup_time = datetime.fromisoformat(
            pickup_time_str.replace('Z', '+00:00'))
        dropoff_time = datetime.fromisoformat(
            dropoff_time_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None, None

    order_date = pickup_time.date()
    pickup_time_only = pickup_time.time()
    dropoff_time_only = dropoff_time.time()

    # Find drivers with shifts on the order date
    shifts = conn.execute('''
        SELECT s.*, d.id as driver_id, d.name as driver_name, v.id as vehicle_id,
               v.max_orders, v.max_weight
        FROM shifts s
        JOIN drivers d ON s.driver_id = d.id
        JOIN vehicles v ON v.driver_id = d.id
        WHERE s.shift_date = ?
        AND s.start_time <= ?
        AND s.end_time >= ?
    ''', (order_date.isoformat(), pickup_time_only.strftime('%H:%M:%S'),
          dropoff_time_only.strftime('%H:%M:%S'))).fetchall()

    for shift in shifts:
        driver_id = shift['driver_id']
        vehicle_id = shift['vehicle_id']
        max_orders = shift['max_orders']
        max_weight = shift['max_weight']

        # Skip if this is the excluded driver (for re-assignment checks)
        if exclude_driver_id and driver_id == exclude_driver_id:
            continue

        # Check vehicle weight capacity
        if weight > max_weight:
            continue

        # Count current assigned orders for this vehicle on the same day
        # that overlap with the order time window
        # Two orders overlap if: (start1 < end2) AND (end1 > start2)
        overlapping_orders = conn.execute('''
            SELECT COUNT(*) as count
            FROM orders
            WHERE vehicle_id = ?
            AND status IN ('assigned', 'completed')
            AND DATE(pickup_time) = ?
            AND pickup_time < ? AND dropoff_time > ?
        ''', (vehicle_id, order_date.isoformat(),
              dropoff_time_str, pickup_time_str)).fetchone()

        current_order_count = overlapping_orders['count'] if overlapping_orders else 0

        # Check if vehicle has capacity
        if current_order_count >= max_orders:
            continue

        # Driver and vehicle are available!
        return driver_id, vehicle_id

    return None, None


def assign_driver_to_order(conn, order_id, pickup_time, dropoff_time, weight, exclude_driver_id=None):
    """Assign a driver to an order if possible."""
    driver_id, vehicle_id = find_available_driver(
        conn, pickup_time, dropoff_time, weight, exclude_driver_id)

    if driver_id and vehicle_id:
        conn.execute('''
            UPDATE orders
            SET driver_id = ?, vehicle_id = ?, status = 'assigned'
            WHERE id = ?
        ''', (driver_id, vehicle_id, order_id))
        conn.commit()
        return driver_id, vehicle_id
    else:
        # No driver available, set to pending
        conn.execute('''
            UPDATE orders
            SET driver_id = NULL, vehicle_id = NULL, status = 'pending'
            WHERE id = ?
        ''', (order_id,))
        conn.commit()
        return None, None


# ==================== DRIVERS ====================


@app.route('/drivers', methods=['GET'])
def get_drivers():
    """Retrieve drivers and their shifts."""
    conn = get_db_connection()
    drivers = conn.execute('SELECT * FROM drivers ORDER BY id').fetchall()

    result = []
    for driver in drivers:
        driver_id = driver['id']
        # Get shifts for this driver
        shifts = conn.execute('''
            SELECT * FROM shifts
            WHERE driver_id = ?
            ORDER BY shift_date, start_time
        ''', (driver_id,)).fetchall()

        driver_data = dict(driver)
        driver_data['shifts'] = [dict(shift) for shift in shifts]
        result.append(driver_data)

    conn.close()
    return jsonify(result)


# ==================== ORDERS ====================


@app.route('/orders', methods=['GET'])
def get_orders():
    """Retrieve all orders for the merchant with pagination."""
    merchant_id = request.args.get('merchant_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    if not merchant_id:
        return jsonify({"error": "merchant_id query parameter is required"}), 400

    conn = get_db_connection()

    # Get total count
    total = conn.execute(
        'SELECT COUNT(*) as count FROM orders WHERE merchant_id = ?',
        (merchant_id,)).fetchone()['count']

    # Get paginated orders
    offset = (page - 1) * per_page
    orders = conn.execute('''
        SELECT id as order_id, status, driver_id
        FROM orders
        WHERE merchant_id = ?
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    ''', (merchant_id, per_page, offset)).fetchall()

    conn.close()

    return jsonify([dict(order) for order in orders])


@app.route('/orders', methods=['POST'])
def create_order():
    """Create a new order and assign it to a driver (if possible)."""
    data = request.get_json()
    merchant_id = data.get('merchant_id')
    description = data.get('description', '')
    pickup_time = data.get('pickup_time')
    dropoff_time = data.get('dropoff_time')
    weight = data.get('weight')

    if not all([merchant_id, pickup_time, dropoff_time, weight]):
        return jsonify({"error": "merchant_id, pickup_time, dropoff_time, and weight are required"}), 400

    # Validate times
    valid, error_msg = validate_order_times(pickup_time, dropoff_time)
    if not valid:
        return jsonify({"error": error_msg}), 400

    conn = get_db_connection()

    # Check if merchant exists
    merchant = conn.execute(
        'SELECT * FROM merchants WHERE id = ?', (merchant_id,)).fetchone()
    if not merchant:
        conn.close()
        return jsonify({"error": "Merchant not found"}), 404

    # Create order with pending status
    cursor = conn.execute(
        'INSERT INTO orders (merchant_id, description, status, pickup_time, dropoff_time, weight) VALUES (?, ?, ?, ?, ?, ?)',
        (merchant_id, description, 'pending', pickup_time, dropoff_time, weight)
    )
    order_id = cursor.lastrowid

    # Try to assign a driver
    driver_id, vehicle_id = assign_driver_to_order(
        conn, order_id, pickup_time, dropoff_time, weight)

    # Get the order with driver info
    order = conn.execute('''
        SELECT o.id as order_id, o.merchant_id, o.description, o.pickup_time,
               o.dropoff_time, o.weight, o.status, d.id as driver_id, d.name as driver_name
        FROM orders o
        LEFT JOIN drivers d ON o.driver_id = d.id
        WHERE o.id = ?
    ''', (order_id,)).fetchone()

    conn.close()

    # Format response
    response = {
        "order_id": order['order_id'],
        "merchant_id": order['merchant_id'],
        "description": order['description'],
        "pickup_time": order['pickup_time'],
        "dropoff_time": order['dropoff_time'],
        "weight": order['weight'],
        "status": order['status']
    }

    if order['driver_id']:
        response["driver"] = {
            "id": order['driver_id'],
            "name": order['driver_name']
        }

    return jsonify(response), 201


@app.route('/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    """
    Modify an existing order.
    - Only the same merchant who created the order can edit it
    - Only one order can be edited at a time (locking)
    - Completed or cancelled orders cannot be edited
    - Re-run assignment logic if time or weight changes
    """
    data = request.get_json()
    merchant_id = data.get('merchant_id')

    if not merchant_id:
        return jsonify({"error": "merchant_id is required"}), 400

    # Get lock for this order
    with lock_manager:
        if order_id not in order_locks:
            order_locks[order_id] = threading.Lock()
        order_lock = order_locks[order_id]

    with order_lock:
        conn = get_db_connection()

        # Get current order
        order = conn.execute(
            'SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
        if not order:
            conn.close()
            return jsonify({"error": "Order not found"}), 404

        # Check merchant ownership
        if order['merchant_id'] != merchant_id:
            conn.close()
            return jsonify({"error": "Only the merchant who created the order can edit it"}), 403

        # Check if order is completed or cancelled
        if order['status'] in ['completed', 'cancelled']:
            conn.close()
            return jsonify({"error": "Cannot edit completed or cancelled orders"}), 400

        # Get fields to update
        description = data.get('description', order['description'])
        pickup_time = data.get('pickup_time', order['pickup_time'])
        dropoff_time = data.get('dropoff_time', order['dropoff_time'])
        weight = data.get('weight', order['weight'])

        # Validate times if they changed
        if pickup_time != order['pickup_time'] or dropoff_time != order['dropoff_time']:
            valid, error_msg = validate_order_times(pickup_time, dropoff_time)
            if not valid:
                conn.close()
                return jsonify({"error": error_msg}), 400

        # Check if time or weight changed (need to re-assign)
        time_changed = (pickup_time != order['pickup_time'] or
                        dropoff_time != order['dropoff_time'])
        weight_changed = weight != order['weight']
        needs_reassignment = time_changed or weight_changed

        # Update order
        conn.execute('''
            UPDATE orders
            SET description = ?, pickup_time = ?, dropoff_time = ?, weight = ?
            WHERE id = ?
        ''', (description, pickup_time, dropoff_time, weight, order_id))

        # Re-run assignment logic if needed
        if needs_reassignment:
            old_driver_id = order['driver_id']
            driver_id = None
            vehicle_id = None

            # Check if old driver still fits
            if old_driver_id:
                # Get vehicle for old driver
                vehicle = conn.execute(
                    'SELECT id, max_orders, max_weight FROM vehicles WHERE driver_id = ?',
                    (old_driver_id,)).fetchone()

                if vehicle:
                    # Check if driver has a shift on the order date
                    order_date = datetime.fromisoformat(
                        pickup_time.replace('Z', '+00:00')).date()
                    pickup_time_only = datetime.fromisoformat(
                        pickup_time.replace('Z', '+00:00')).time()
                    dropoff_time_only = datetime.fromisoformat(
                        dropoff_time.replace('Z', '+00:00')).time()

                    shift = conn.execute('''
                        SELECT * FROM shifts
                        WHERE driver_id = ?
                        AND shift_date = ?
                        AND start_time <= ?
                        AND end_time >= ?
                    ''', (old_driver_id, order_date.isoformat(),
                          pickup_time_only.strftime('%H:%M:%S'),
                          dropoff_time_only.strftime('%H:%M:%S'))).fetchone()

                    if shift:
                        # Check vehicle weight capacity
                        if weight <= vehicle['max_weight']:
                            # Check current order count (excluding this order)
                            # Two orders overlap if: (start1 < end2) AND (end1 > start2)
                            overlapping = conn.execute('''
                                SELECT COUNT(*) as count
                                FROM orders
                                WHERE vehicle_id = ?
                                AND status IN ('assigned', 'completed')
                                AND DATE(pickup_time) = ?
                                AND id != ?
                                AND pickup_time < ? AND dropoff_time > ?
                            ''', (vehicle['id'], order_date.isoformat(), order_id,
                                  dropoff_time, pickup_time)).fetchone()

                            if overlapping['count'] < vehicle['max_orders']:
                                # Old driver still fits
                                driver_id = old_driver_id
                                vehicle_id = vehicle['id']

            # If old driver doesn't fit, find a new one
            if not driver_id:
                driver_id, vehicle_id = find_available_driver(
                    conn, pickup_time, dropoff_time, weight, exclude_driver_id=old_driver_id)

            # Assign driver
            if driver_id and vehicle_id:
                conn.execute('''
                    UPDATE orders
                    SET driver_id = ?, vehicle_id = ?, status = 'assigned'
                    WHERE id = ?
                ''', (driver_id, vehicle_id, order_id))
            else:
                # No driver available
                conn.execute('''
                    UPDATE orders
                    SET driver_id = NULL, vehicle_id = NULL, status = 'pending'
                    WHERE id = ?
                ''', (order_id,))

        conn.commit()

        # Get updated order
        updated_order = conn.execute('''
            SELECT o.id as order_id, o.merchant_id, o.description, o.pickup_time,
                   o.dropoff_time, o.weight, o.status, d.id as driver_id, d.name as driver_name
            FROM orders o
            LEFT JOIN drivers d ON o.driver_id = d.id
            WHERE o.id = ?
        ''', (order_id,)).fetchone()

        conn.close()

        # Format response
        response = {
            "order_id": updated_order['order_id'],
            "merchant_id": updated_order['merchant_id'],
            "description": updated_order['description'],
            "pickup_time": updated_order['pickup_time'],
            "dropoff_time": updated_order['dropoff_time'],
            "weight": updated_order['weight'],
            "status": updated_order['status']
        }

        if updated_order['driver_id']:
            response["driver"] = {
                "id": updated_order['driver_id'],
                "name": updated_order['driver_name']
            }

        return jsonify(response)


@app.route('/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    """Cancel an order and free up any driver/vehicle assignment immediately."""
    conn = get_db_connection()

    # Get order to check if it exists
    order = conn.execute(
        'SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    if not order:
        conn.close()
        return jsonify({"error": "Order not found"}), 404

    # Update status to cancelled and free up driver/vehicle
    conn.execute('''
        UPDATE orders
        SET status = 'cancelled', driver_id = NULL, vehicle_id = NULL
        WHERE id = ?
    ''', (order_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Order cancelled and driver/vehicle assignment freed"}), 200


# ==================== OTHER ENDPOINTS (for admin/internal use) ====================


@app.route('/')
def home():
    """Health check endpoint."""
    return jsonify({"message": "Order Management System is running!", "status": "healthy"})


@app.route('/merchants', methods=['GET'])
def get_merchants():
    """Get all merchants."""
    conn = get_db_connection()
    merchants = conn.execute('SELECT * FROM merchants ORDER BY id').fetchall()
    conn.close()
    return jsonify([dict(merchant) for merchant in merchants])


@app.route('/merchants', methods=['POST'])
def create_merchant():
    """Create a new merchant."""
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')

    if not name or not email:
        return jsonify({"error": "Name and email are required"}), 400

    conn = get_db_connection()
    try:
        cursor = conn.execute(
            'INSERT INTO merchants (name, email) VALUES (?, ?)',
            (name, email)
        )
        conn.commit()
        merchant_id = cursor.lastrowid
        merchant = conn.execute(
            'SELECT * FROM merchants WHERE id = ?', (merchant_id,)).fetchone()
        conn.close()
        return jsonify(dict(merchant)), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Merchant with this name or email already exists"}), 400


if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    print(f"Database initialized at: {DATABASE_PATH}")

    # Run the Flask app
    app.run(host='0.0.0.0', port=8000, debug=True)
