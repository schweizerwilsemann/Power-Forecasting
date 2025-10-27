# Tests Directory

This directory contains test files for the PV Power Forecasting system.

## Files

- `test_enhanced_features.py` - Comprehensive test suite for all enhanced features

## Running Tests

### Prerequisites
1. Make sure the backend server is running:
   ```bash
   cd backend
   python run.py --reload
   ```

2. Install required dependencies:
   ```bash
   pip install requests
   ```

### Running the Test Suite

From the project root directory:
```bash
python tests/test_enhanced_features.py
```

Or from the tests directory:
```bash
cd tests
python test_enhanced_features.py
```

## Test Coverage

The test suite covers:

- ✅ Basic API endpoints (health, metrics, forecast)
- ✅ Monitoring endpoints (health, performance)
- ✅ Advanced forecasting (confidence intervals, scenarios)
- ✅ Data quality management
- ✅ Model management
- ✅ Historical analysis
- ✅ System status monitoring

## Expected Output

When all tests pass, you should see:
```
🎉 All tests passed! The enhanced features are working correctly.
```

If some tests fail, check:
1. Backend server is running on port 8000
2. All dependencies are installed
3. Model artifacts are present in `backend/artifacts/`
4. Data file `Renewable.csv` is available

## Troubleshooting

### Connection Error
```
❌ Cannot connect to server. Please make sure the backend is running:
   cd backend && python run.py --reload
   or from project root: python backend/run.py --reload
```

**Solution**: Start the backend server first.

### Import Error
```
❌ Error: No module named 'requests'
```

**Solution**: Install requests: `pip install requests`

### Model Not Ready
```
❌ Model not loaded
```

**Solution**: Train the model first:
```bash
cd backend
python -m app.train_model --data ../Renewable.csv
```
