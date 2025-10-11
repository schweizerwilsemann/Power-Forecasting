# PV Power Forecasting Backend

## Setup

1. Create virtual environment: `python -m venv .venv`
2. Activate environment:
   - PowerShell: `.\.venv\Scripts\Activate.ps1`
3. Install dependencies: `pip install -r requirements.txt`
4. Train the model: `python -m app.train_model --data ..\Renewable.csv`
5. Start API: `uvicorn app.main:app --reload --port 8000`

API will expose `/health`, `/metrics`, `/forecast/next`, `/forecast/batch`.
