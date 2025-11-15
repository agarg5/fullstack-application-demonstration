# Order Management System

A Python Flask backend with SQLite database for managing orders, merchants, drivers, vehicles, and shifts.

## Project Structure

```
.
├── Dockerfile
├── requirements.txt
├── app.py                 # Main Flask application
├── generate_datasets.py   # Script to generate CSV datasets
├── load_data.py          # Script to load CSV data into database
├── .dockerignore
└── data/                 # SQLite database storage (created automatically)
```

## Database Schema

### Merchants
- `id`: Primary key
- `name`: Unique merchant name
- `email`: Unique email address
- `created_at`: Timestamp

### Drivers
- `id`: Primary key
- `name`: Unique driver name
- `created_at`: Timestamp

### Vehicles
- `id`: Primary key
- `driver_id`: Foreign key to drivers (one vehicle per driver)
- `max_orders`: Maximum number of orders (5-10)
- `max_weight`: Maximum weight capacity (100-500)
- `created_at`: Timestamp

### Shifts
- `id`: Primary key
- `driver_id`: Foreign key to drivers
- `shift_date`: Date of the shift
- `start_time`: Shift start time (e.g., 09:00:00)
- `end_time`: Shift end time (e.g., 17:00:00)
- `created_at`: Timestamp
- Unique constraint: one shift per driver per day

### Orders
- `id`: Primary key
- `merchant_id`: Foreign key to merchants
- `driver_id`: Foreign key to drivers (nullable, assigned when status changes to 'assigned')
- `vehicle_id`: Foreign key to vehicles (nullable, assigned when status changes to 'assigned')
- `status`: Order status - `pending`, `assigned`, `completed`, or `cancelled`
- `pickup_time`: Timestamp for pickup
- `dropoff_time`: Timestamp for dropoff
- `weight`: Order weight (10-200)
- `created_at`: Timestamp

## Order Statuses

- **pending**: Order created but no driver allocated yet
- **assigned**: A driver and vehicle have been allocated to the order
- **completed**: Order marked as complete by the driver
- **cancelled**: Order cancelled by merchant or driver

## Order Validation Rules

1. **Pickup time** must be at least **15 minutes** before dropoff time
2. **Dropoff time** must be at most **4 hours** after pickup time
3. Both pickup and dropoff must be on the **same day**

## Getting Started

### Build the Docker image:
```bash
docker build -t python-sqlite-backend .
```

### Run the container:
```bash
docker run -p 8000:8000 -v $(pwd)/data:/app/data python-sqlite-backend
```

The `-v $(pwd)/data:/app/data` flag mounts a local directory to persist the database.

### Generate Sample Data

1. Generate CSV datasets:
```bash
python3 generate_datasets.py
```

This creates:
- `merchants.csv` - 10 merchants
- `drivers.csv` - 50 drivers
- `shifts.csv` - 500 shifts (50 drivers × 10 days)
- `vehicles.csv` - 50 vehicles (one per driver)
- `orders.csv` - 1,000 orders

2. Load data into database:
```bash
python3 load_data.py
```

## API Endpoints

### Health Check
- `GET /` - Health check endpoint

### Merchants
- `GET /merchants` - Get all merchants
- `POST /merchants` - Create a new merchant
  ```json
  {
    "name": "Acme Corp",
    "email": "contact@acme.com"
  }
  ```
- `GET /merchants/<id>` - Get merchant by ID

### Drivers
- `GET /drivers` - Get all drivers
- `POST /drivers` - Create a new driver
  ```json
  {
    "name": "John Doe"
  }
  ```
- `GET /drivers/<id>` - Get driver by ID

### Vehicles
- `GET /vehicles` - Get all vehicles (includes driver name)
- `POST /vehicles` - Create a new vehicle
  ```json
  {
    "driver_id": 1,
    "max_orders": 8,
    "max_weight": 300
  }
  ```
- `GET /vehicles/<id>` - Get vehicle by ID

### Shifts
- `GET /shifts` - Get all shifts (includes driver name)
- `POST /shifts` - Create a new shift
  ```json
  {
    "driver_id": 1,
    "shift_date": "2025-01-15",
    "start_time": "09:00:00",
    "end_time": "17:00:00"
  }
  ```
- `GET /shifts/<id>` - Get shift by ID

### Orders
- `GET /orders` - Get all orders (includes merchant, driver, vehicle info)
  - Query parameter: `?status=pending` - Filter by status
- `POST /orders` - Create a new order
  ```json
  {
    "merchant_id": 1,
    "pickup_time": "2025-01-15T10:00:00",
    "dropoff_time": "2025-01-15T12:00:00",
    "weight": 150.5
  }
  ```
- `GET /orders/<id>` - Get order by ID
- `PATCH /orders/<id>` - Update an order
  ```json
  {
    "status": "assigned",
    "driver_id": 1,
    "vehicle_id": 1
  }
  ```
- `DELETE /orders/<id>` - Delete an order

## Local Development (without Docker)

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

## Testing the API

```bash
# Health check
curl http://localhost:8000/

# Create a merchant
curl -X POST http://localhost:8000/merchants \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme Corp", "email": "contact@acme.com"}'

# Create a driver
curl -X POST http://localhost:8000/drivers \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe"}'

# Create a vehicle
curl -X POST http://localhost:8000/vehicles \
  -H "Content-Type: application/json" \
  -d '{"driver_id": 1, "max_orders": 8, "max_weight": 300}'

# Create a shift
curl -X POST http://localhost:8000/shifts \
  -H "Content-Type: application/json" \
  -d '{"driver_id": 1, "shift_date": "2025-01-15", "start_time": "09:00:00", "end_time": "17:00:00"}'

# Create an order
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "merchant_id": 1,
    "pickup_time": "2025-01-15T10:00:00",
    "dropoff_time": "2025-01-15T12:00:00",
    "weight": 150.5
  }'

# Get all orders
curl http://localhost:8000/orders

# Get pending orders
curl http://localhost:8000/orders?status=pending

# Assign driver to order
curl -X PATCH http://localhost:8000/orders/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "assigned", "driver_id": 1, "vehicle_id": 1}'

# Update order status
curl -X PATCH http://localhost:8000/orders/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'
```

## Testing

### Install Test Dependencies

```bash
pip install -r requirements.txt
```

### Run Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest test_app.py

# Run specific test class
pytest test_app.py::TestOrderCreation

# Run specific test
pytest test_app.py::TestOrderCreation::test_create_order_with_valid_data
```

### Test Coverage

The test suite includes:

- **Order Creation**: Valid data, missing fields, time validation, auto-assignment
- **Order Updates**: Merchant authorization, status checks, re-assignment logic
- **Order Cancellation**: Cancellation and driver/vehicle freeing
- **Order Retrieval**: Pagination, merchant filtering
- **Driver Endpoints**: Driver listing with shifts
- **Validation**: Time constraints, weight limits
- **Driver Assignment**: Shift availability, capacity checks
