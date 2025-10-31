import { apiClient } from './apiClient';

export function useForecastApi() {
  const fetchNext = async (payload) => {
    const { data } = await apiClient.post('/forecast/next', payload);
    return data;
  };

  const fetchBatch = async (payload) => {
    const { data } = await apiClient.post('/forecast/batch', payload);
    return data;
  };

  const fetchMetrics = async () => {
    const { data } = await apiClient.get('/metrics');
    return data;
  };

  return { fetchNext, fetchBatch, fetchMetrics };
}
