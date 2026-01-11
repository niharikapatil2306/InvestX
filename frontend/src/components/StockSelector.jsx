import { useState, useEffect } from 'react';
import { Search, Plus, X, TrendingUp, TrendingDown } from 'lucide-react';
import { getStocks } from '../services/api';

export default function StockSelector({ selectedStocks, onStockSelect, onStockRemove }) {
  const [stocks, setStocks] = useState([]);
  const [filteredStocks, setFilteredStocks] = useState([]);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStocks();
  }, []);

  useEffect(() => {
    filterStocks();
  }, [stocks, search, categoryFilter]);

  const loadStocks = async () => {
    try {
      const data = await getStocks();
      setStocks(data);
      setLoading(false);
    } catch (err) {
      console.error('Failed to load stocks:', err);
      setLoading(false);
    }
  };

  const filterStocks = () => {
    let result = stocks;

    if (categoryFilter !== 'all') {
      result = result.filter(s => s.market_cap_category === categoryFilter);
    }

    if (search) {
      const searchLower = search.toLowerCase();
      result = result.filter(
        s =>
          s.symbol.toLowerCase().includes(searchLower) ||
          s.name.toLowerCase().includes(searchLower) ||
          s.sector?.toLowerCase().includes(searchLower)
      );
    }

    setFilteredStocks(result);
  };

  const isSelected = (symbol) => selectedStocks.includes(symbol);

  const handleToggle = (symbol) => {
    if (isSelected(symbol)) {
      onStockRemove(symbol);
    } else {
      onStockSelect(symbol);
    }
  };

  if (loading) {
    return (
      <div className="bg-slate-800 rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-slate-700 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map(i => (
              <div key={i} className="h-16 bg-slate-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-4">Select Stocks</h2>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-3 mb-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search stocks..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All Caps</option>
          <option value="large">Large Cap</option>
          <option value="mid">Mid Cap</option>
          <option value="small">Small Cap</option>
        </select>
      </div>

      {/* Selected Count */}
      <div className="mb-4 text-sm text-slate-400">
        {selectedStocks.length} stocks selected
        {selectedStocks.length >= 2 && (
          <span className="text-green-400 ml-2">Ready to optimize</span>
        )}
      </div>

      {/* Stock List */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {filteredStocks.map((stock) => (
          <div
            key={stock.symbol}
            onClick={() => handleToggle(stock.symbol)}
            className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors ${
              isSelected(stock.symbol)
                ? 'bg-blue-600/20 border border-blue-500'
                : 'bg-slate-700 hover:bg-slate-600 border border-transparent'
            }`}
          >
            <div className="flex items-center gap-3">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                  stock.market_cap_category === 'large'
                    ? 'bg-purple-600'
                    : stock.market_cap_category === 'mid'
                    ? 'bg-blue-600'
                    : 'bg-green-600'
                }`}
              >
                {stock.symbol.slice(0, 2)}
              </div>
              <div>
                <div className="font-medium">{stock.symbol}</div>
                <div className="text-sm text-slate-400 truncate max-w-[200px]">
                  {stock.name}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-sm text-slate-400">{stock.sector}</div>
                <div
                  className={`text-sm flex items-center gap-1 ${
                    stock.change_pct >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}
                >
                  {stock.change_pct >= 0 ? (
                    <TrendingUp className="w-3 h-3" />
                  ) : (
                    <TrendingDown className="w-3 h-3" />
                  )}
                  {stock.change_pct?.toFixed(2)}%
                </div>
              </div>

              {isSelected(stock.symbol) ? (
                <X className="w-5 h-5 text-red-400" />
              ) : (
                <Plus className="w-5 h-5 text-slate-400" />
              )}
            </div>
          </div>
        ))}
      </div>

      {filteredStocks.length === 0 && (
        <div className="text-center py-8 text-slate-400">
          No stocks found matching your criteria
        </div>
      )}
    </div>
  );
}
