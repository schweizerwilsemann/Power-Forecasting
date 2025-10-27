# PV Power Forecasting Backend

## Setup

1. Create virtual environment: `python -m venv .venv`
2. Activate environment:
   - PowerShell: `.\.venv\Scripts\Activate.ps1`
3. Install dependencies: `pip install -r requirements.txt`
4. Train the model: `python -m app.train_model --data ..\Renewable.csv`
5. Start API: `python run.py --reload`

## API Endpoints

### Basic Endpoints
- `GET /health` - Health check
- `GET /metrics` - Model metrics
- `POST /forecast/next` - Single forecast
- `POST /forecast/batch` - Batch forecast

### Enhanced Endpoints
- `GET /monitoring/health` - System health status
- `GET /monitoring/performance` - Performance metrics
- `POST /forecast/advanced` - Advanced forecasting with confidence
- `POST /forecast/scenarios` - Multiple weather scenarios
- `GET /data/quality` - Data quality assessment
- `POST /data/import` - Data import and validation
- `GET /models/status` - Model status and metrics
- `POST /models/retrain` - Retrain models
- `POST /analysis/historical` - Historical analysis

## Running from Project Root

You can also run the backend from the project root:
```bash
python backend/run.py --reload
```

## Testing

Run the test suite:
```bash
python tests/test_enhanced_features.py
```
