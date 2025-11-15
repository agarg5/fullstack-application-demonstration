#!/usr/bin/env python3
"""
Generate CSV datasets for merchants, drivers, vehicles, shifts, and orders.
"""

import csv
import random
from datetime import datetime, timedelta, time
from faker import Faker

# Set seed for reproducibility
random.seed(42)
fake = Faker()
Faker.seed(42)


def generate_merchants(num_merchants=10):
    """Generate merchants CSV with unique names."""
    merchants = []
    used_names = set()
    used_emails = set()

    for i in range(num_merchants):
        name = fake.company()
        counter = 1
        while name in used_names:
            name = f"{fake.company()} {counter}"
            counter += 1
        used_names.add(name)

        email = fake.company_email()
        counter = 1
        while email in used_emails:
            email = fake.company_email()
            counter += 1
        used_emails.add(email)

        merchants.append({
            'id': i + 1,
            'name': name,
            'email': email
        })

    with open('merchants.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'name', 'email'])
        writer.writeheader()
        writer.writerows(merchants)

    print(f"Generated {num_merchants} merchants in merchants.csv")
    return merchants


def generate_drivers(num_drivers=50):
    """Generate drivers CSV with unique names."""
    drivers = []
    used_names = set()

    for i in range(num_drivers):
        name = fake.name()
        counter = 1
        while name in used_names:
            name = f"{fake.name()} {counter}"
            counter += 1
        used_names.add(name)

        drivers.append({
            'id': i + 1,
            'name': name
        })

    with open('drivers.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'name'])
        writer.writeheader()
        writer.writerows(drivers)

    print(f"Generated {num_drivers} drivers in drivers.csv")
    return drivers


def generate_shifts(drivers, num_days=10):
    """Generate shifts CSV for drivers over the next num_days days."""
    shifts = []
    shift_templates = [
        (8, 12),   # 8am-12pm
        (9, 13),   # 9am-1pm
        (10, 14),  # 10am-2pm
        (11, 15),  # 11am-3pm
        (12, 16),  # 12pm-4pm
        (13, 17),  # 1pm-5pm
        (14, 18),  # 2pm-6pm
        (8, 16),   # 8am-4pm
        (9, 17),   # 9am-5pm
        (10, 18),  # 10am-6pm
    ]

    start_date = datetime.now().date()

    for driver in drivers:
        for day_offset in range(num_days):
            shift_date = start_date + timedelta(days=day_offset)
            start_hour, end_hour = random.choice(shift_templates)
            start_time = time(start_hour, 0)
            end_time = time(end_hour, 0)

            shifts.append({
                'id': len(shifts) + 1,
                'driver_id': driver['id'],
                'shift_date': shift_date.isoformat(),
                'start_time': start_time.strftime('%H:%M:%S'),
                'end_time': end_time.strftime('%H:%M:%S')
            })

    with open('shifts.csv', 'w', newline='') as f:
        writer = csv.DictWriter(
            f, fieldnames=['id', 'driver_id', 'shift_date', 'start_time', 'end_time'])
        writer.writeheader()
        writer.writerows(shifts)

    print(f"Generated {len(shifts)} shifts in shifts.csv")
    return shifts


def generate_vehicles(drivers):
    """Generate vehicles CSV, one per driver."""
    vehicles = []

    for driver in drivers:
        max_orders = random.randint(5, 10)
        max_weight = random.randint(100, 500)

        vehicles.append({
            'id': len(vehicles) + 1,
            'driver_id': driver['id'],
            'max_orders': max_orders,
            'max_weight': max_weight
        })

    with open('vehicles.csv', 'w', newline='') as f:
        writer = csv.DictWriter(
            f, fieldnames=['id', 'driver_id', 'max_orders', 'max_weight'])
        writer.writeheader()
        writer.writerows(vehicles)

    print(f"Generated {len(vehicles)} vehicles in vehicles.csv")
    return vehicles


def generate_orders(merchants, num_orders=1000, num_days=10):
    """Generate orders CSV with random merchant assignments and times."""
    orders = []
    start_date = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=num_days)

    for i in range(num_orders):
        merchant = random.choice(merchants)

        # Generate random pickup time within the next num_days
        days_offset = random.randint(0, num_days - 1)
        hours_offset = random.randint(0, 12)  # 8am to 8pm
        minutes_offset = random.randint(0, 59)

        pickup_datetime = start_date + timedelta(
            days=days_offset,
            hours=hours_offset,
            minutes=minutes_offset
        )

        # Ensure pickup is at least at 8am and before 8pm
        if pickup_datetime.hour < 8:
            pickup_datetime = pickup_datetime.replace(hour=8, minute=0)
        if pickup_datetime.hour >= 20:
            pickup_datetime = pickup_datetime.replace(hour=19, minute=0)

        # Generate dropoff time: 15 minutes to 4 hours after pickup, same day
        # Calculate maximum minutes available until end of day (11:59 PM)
        pickup_minutes = pickup_datetime.hour * 60 + pickup_datetime.minute
        end_of_day_minutes = 23 * 60 + 59
        available_minutes = end_of_day_minutes - pickup_minutes

        # Dropoff must be at least 15 minutes and at most 4 hours (240 minutes) after pickup
        min_offset = 15
        max_offset = min(240, available_minutes)

        # If we can't fit 4 hours, ensure we can at least fit 15 minutes
        if max_offset < min_offset:
            # Adjust pickup time earlier if needed
            if pickup_minutes > min_offset:
                pickup_datetime = pickup_datetime - \
                    timedelta(minutes=(min_offset + 10))
                pickup_minutes = pickup_datetime.hour * 60 + pickup_datetime.minute
                available_minutes = end_of_day_minutes - pickup_minutes
                max_offset = min(240, available_minutes)

        dropoff_offset_minutes = random.randint(min_offset, max_offset)
        dropoff_datetime = pickup_datetime + \
            timedelta(minutes=dropoff_offset_minutes)

        # Final check: ensure both are on the same day
        if dropoff_datetime.date() != pickup_datetime.date():
            # If somehow they're different days, cap dropoff at end of pickup day
            dropoff_datetime = pickup_datetime.replace(hour=23, minute=59)

        weight = round(random.uniform(10, 200), 2)

        # Generate random descriptions using Faker
        description = fake.catch_phrase()

        orders.append({
            'id': len(orders) + 1,
            'merchant_id': merchant['id'],
            'driver_id': '',  # Will be assigned later
            'vehicle_id': '',  # Will be assigned later
            'status': 'pending',
            'description': description,
            'pickup_time': pickup_datetime.isoformat(),
            'dropoff_time': dropoff_datetime.isoformat(),
            'weight': weight
        })

    with open('orders.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'id', 'merchant_id', 'driver_id', 'vehicle_id', 'status',
            'description', 'pickup_time', 'dropoff_time', 'weight'
        ])
        writer.writeheader()
        writer.writerows(orders)

    print(f"Generated {len(orders)} orders in orders.csv")
    return orders


if __name__ == '__main__':
    print("Generating datasets...")
    print("=" * 50)

    merchants = generate_merchants(10)
    drivers = generate_drivers(50)
    shifts = generate_shifts(drivers, num_days=10)
    vehicles = generate_vehicles(drivers)
    orders = generate_orders(merchants, num_orders=1000, num_days=10)

    print("=" * 50)
    print("All datasets generated successfully!")
    print("\nGenerated files:")
    print("  - merchants.csv (10 merchants)")
    print("  - drivers.csv (50 drivers)")
    print("  - shifts.csv (500 shifts for 10 days)")
    print("  - vehicles.csv (50 vehicles)")
    print("  - orders.csv (1,000 orders)")
