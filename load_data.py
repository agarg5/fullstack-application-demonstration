#!/usr/bin/env python3
"""
Load CSV datasets into the SQLite database.
"""

import csv
import sqlite3
import os

DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/database.db')

def get_db_connection():
    """Create a database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def load_merchants():
    """Load merchants from CSV."""
    conn = get_db_connection()
    count = 0

    with open('merchants.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                conn.execute(
                    'INSERT INTO merchants (id, name, email) VALUES (?, ?, ?)',
                    (row['id'], row['name'], row['email'])
                )
                count += 1
            except sqlite3.IntegrityError:
                print(f"  Skipping duplicate merchant: {row['name']}")

    conn.commit()
    conn.close()
    print(f"Loaded {count} merchants")
    return count

def load_drivers():
    """Load drivers from CSV."""
    conn = get_db_connection()
    count = 0

    with open('drivers.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                conn.execute(
                    'INSERT INTO drivers (id, name) VALUES (?, ?)',
                    (row['id'], row['name'])
                )
                count += 1
            except sqlite3.IntegrityError:
                print(f"  Skipping duplicate driver: {row['name']}")

    conn.commit()
    conn.close()
    print(f"Loaded {count} drivers")
    return count

def load_vehicles():
    """Load vehicles from CSV."""
    conn = get_db_connection()
    count = 0

    with open('vehicles.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                conn.execute(
                    'INSERT INTO vehicles (id, driver_id, max_orders, max_weight) VALUES (?, ?, ?, ?)',
                    (row['id'], row['driver_id'], row['max_orders'], row['max_weight'])
                )
                count += 1
            except sqlite3.IntegrityError:
                print(f"  Skipping duplicate vehicle: {row['id']}")

    conn.commit()
    conn.close()
    print(f"Loaded {count} vehicles")
    return count

def load_shifts():
    """Load shifts from CSV."""
    conn = get_db_connection()
    count = 0

    with open('shifts.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                conn.execute(
                    'INSERT INTO shifts (id, driver_id, shift_date, start_time, end_time) VALUES (?, ?, ?, ?, ?)',
                    (row['id'], row['driver_id'], row['shift_date'], row['start_time'], row['end_time'])
                )
                count += 1
            except sqlite3.IntegrityError:
                print(f"  Skipping duplicate shift: driver {row['driver_id']} on {row['shift_date']}")

    conn.commit()
    conn.close()
    print(f"Loaded {count} shifts")
    return count

def load_orders():
    """Load orders from CSV."""
    conn = get_db_connection()
    count = 0

    with open('orders.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                driver_id = row['driver_id'] if row['driver_id'] else None
                vehicle_id = row['vehicle_id'] if row['vehicle_id'] else None
                description = row.get('description', '')

                conn.execute(
                    'INSERT INTO orders (id, merchant_id, driver_id, vehicle_id, status, description, pickup_time, dropoff_time, weight) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (row['id'], row['merchant_id'], driver_id, vehicle_id, row['status'],
                     description, row['pickup_time'], row['dropoff_time'], row['weight'])
                )
                count += 1
            except sqlite3.IntegrityError as e:
                print(f"  Skipping duplicate order: {row['id']}")
            except Exception as e:
                print(f"  Error loading order {row['id']}: {e}")

    conn.commit()
    conn.close()
    print(f"Loaded {count} orders")
    return count

if __name__ == '__main__':
    print("Loading CSV data into database...")
    print("=" * 50)

    # Ensure database directory exists
    os.makedirs(os.path.dirname(DATABASE_PATH) if os.path.dirname(DATABASE_PATH) else '.', exist_ok=True)

    # Check if CSV files exist
    required_files = ['merchants.csv', 'drivers.csv', 'vehicles.csv', 'shifts.csv', 'orders.csv']
    missing_files = [f for f in required_files if not os.path.exists(f)]

    if missing_files:
        print(f"Error: Missing CSV files: {', '.join(missing_files)}")
        print("Please run generate_datasets.py first to create the CSV files.")
        exit(1)

    # Import app to initialize database schema
    from app import init_db
    init_db()
    print("Database schema initialized\n")

    # Load data
    merchants_count = load_merchants()
    drivers_count = load_drivers()
    vehicles_count = load_vehicles()
    shifts_count = load_shifts()
    orders_count = load_orders()

    print("=" * 50)
    print("Data loading complete!")
    print(f"\nSummary:")
    print(f"  - {merchants_count} merchants")
    print(f"  - {drivers_count} drivers")
    print(f"  - {vehicles_count} vehicles")
    print(f"  - {shifts_count} shifts")
    print(f"  - {orders_count} orders")

