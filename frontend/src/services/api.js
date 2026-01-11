import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Stock endpoints
export const getStocks = async (category = null, sector = null) => {
  const params = new URLSearchParams();
  if (category) params.append('category', category);
  if (sector) params.append('sector', sector);
  const response = await api.get(`/stocks?${params}`);
  return response.data;
};

export const getStock = async (symbol) => {
  const response = await api.get(`/stocks/${symbol}`);
  return response.data;
};

export const getStockMetrics = async (symbol) => {
  const response = await api.get(`/stocks/${symbol}/metrics`);
  return response.data;
};

export const getStockHistory = async (symbol, period = '1y') => {
  const response = await api.get(`/stocks/${symbol}/history?period=${period}`);
  return response.data;
};

export const getSectors = async () => {
  const response = await api.get('/stocks/sectors');
  return response.data;
};

// Portfolio endpoints
export const optimizePortfolio = async (stocks, target = 'max_sharpe', options = {}) => {
  const response = await api.post('/portfolio/optimize', {
    stocks,
    target,
    target_return: options.targetReturn,
    max_weight: options.maxWeight || 1.0,
    min_weight: options.minWeight || 0.0,
  });
  return response.data;
};

export const getEqualWeightPortfolio = async (stocks) => {
  const response = await api.post('/portfolio/equal-weight', { stocks });
  return response.data;
};

// Risk endpoints
export const analyzeRisk = async (weights) => {
  const response = await api.post('/risk/analyze', { weights });
  return response.data;
};

export const getCorrelation = async (symbols) => {
  const response = await api.get(`/risk/correlation?symbols=${symbols.join(',')}`);
  return response.data;
};

export const getVarBreakdown = async (symbols, weights = null) => {
  let url = `/risk/var-breakdown?symbols=${symbols.join(',')}`;
  if (weights) {
    url += `&weights=${Object.values(weights).join(',')}`;
  }
  const response = await api.get(url);
  return response.data;
};

// Health check
export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;
