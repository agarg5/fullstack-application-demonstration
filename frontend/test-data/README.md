# Test CSV Files

These CSV files are for manual testing of the CSV upload functionality.

## Files

- **test_merchants.csv** - Sample merchants data
- **test_drivers.csv** - Sample drivers data
- **test_vehicles.csv** - Sample vehicles data (requires drivers with IDs 201, 202, 203 to exist)
- **test_orders.csv** - Sample orders data (requires merchants with IDs 101, 102, 103 to exist)

## Usage

1. Go to the Upload CSV page in the frontend
2. Select the appropriate data type
3. Choose the corresponding test CSV file
4. Click "Upload CSV"
5. Verify the data appears in the respective pages

## Notes

- Make sure to upload merchants and drivers before vehicles and orders (due to foreign key constraints)
- The test files use high IDs (101+, 201+, etc.) to avoid conflicts with existing data
- Orders can be uploaded with empty driver_id and vehicle_id (they'll be assigned later)

