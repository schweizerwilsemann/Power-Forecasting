# PV Power Forecasting Frontend

## Development

1. Install dependencies: `npm install`
2. Create `.env.development` (already provided) with `VITE_API_URL=http://localhost:8000`
3. Run dev server: `npm run dev`

The app hits the FastAPI backend for metrics and forecasts. Batch forecasts accept pasted CSV rows matching the Renewable dataset.
