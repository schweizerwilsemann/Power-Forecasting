import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export function useForecastApi() {
  const fetchNext = async (payload) => {
    const { data } = await api.post('/forecast/next', payload);
    return data;
  };

  const fetchBatch = async (payload) => {
    const { data } = await api.post('/forecast/batch', payload);
    return data;
  };

  const fetchMetrics = async () => {
    const { data } = await api.get('/metrics');
    return data;
  };

  return { fetchNext, fetchBatch, fetchMetrics };
}
