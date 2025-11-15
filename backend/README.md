# Backend

## Quick Start

### Start the server:
```bash
python3 app.py
```

### Restart the server:
```bash
./restart.sh
```

Or from the project root:
```bash
cd backend && ./restart.sh
```

## Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Generate sample data:
```bash
python3 generate_datasets.py
python3 load_data.py
```

3. Run tests:
```bash
pytest
```

4. Start the server:
```bash
python3 app.py
```

The server will run on `http://localhost:8000`

