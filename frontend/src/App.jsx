import { useState } from 'react';
import { TrendingUp, BarChart3, Shield } from 'lucide-react';
import StockSelector from './components/StockSelector';
import PortfolioBuilder from './components/PortfolioBuilder';
import PortfolioWeights from './components/PortfolioWeights';
import EfficientFrontier from './components/EfficientFrontier';
import RiskMetrics from './components/RiskMetrics';
import CorrelationHeatmap from './components/CorrelationHeatmap';

function App() {
  const [selectedStocks, setSelectedStocks] = useState([]);
  const [optimizationResult, setOptimizationResult] = useState(null);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [activeTab, setActiveTab] = useState('portfolio');

  const handleStockSelect = (symbol) => {
    setSelectedStocks((prev) => [...prev, symbol]);
  };

  const handleStockRemove = (symbol) => {
    setSelectedStocks((prev) => prev.filter((s) => s !== symbol));
  };

  const handleOptimize = (result) => {
    setOptimizationResult(result);
    setActiveTab('results');
  };

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-blue-600 p-2 rounded-lg">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">InvestX</h1>
                <p className="text-sm text-slate-400">Portfolio Optimization</p>
              </div>
            </div>

            {/* Tab Navigation */}
            <div className="flex gap-2">
              <button
                onClick={() => setActiveTab('portfolio')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                  activeTab === 'portfolio'
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                <BarChart3 className="w-4 h-4" />
                Build Portfolio
              </button>
              <button
                onClick={() => setActiveTab('results')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                  activeTab === 'results'
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
                disabled={!optimizationResult}
              >
                <Shield className="w-4 h-4" />
                Results
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'portfolio' ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left: Stock Selector */}
            <div className="lg:col-span-2">
              <StockSelector
                selectedStocks={selectedStocks}
                onStockSelect={handleStockSelect}
                onStockRemove={handleStockRemove}
              />
            </div>

            {/* Right: Portfolio Builder */}
            <div className="space-y-6">
              <PortfolioBuilder
                selectedStocks={selectedStocks}
                onOptimize={handleOptimize}
                isOptimizing={isOptimizing}
                setIsOptimizing={setIsOptimizing}
              />

              {/* Selected Stocks Summary */}
              {selectedStocks.length > 0 && (
                <div className="bg-slate-800 rounded-lg p-6">
                  <h3 className="text-lg font-semibold mb-3">Selected Stocks</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedStocks.map((symbol) => (
                      <span
                        key={symbol}
                        className="px-3 py-1 bg-blue-600/20 text-blue-400 rounded-full text-sm flex items-center gap-1"
                      >
                        {symbol}
                        <button
                          onClick={() => handleStockRemove(symbol)}
                          className="ml-1 hover:text-red-400"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Results Header */}
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold">Optimization Results</h2>
              <button
                onClick={() => setActiveTab('portfolio')}
                className="px-4 py-2 bg-slate-700 text-slate-300 rounded-lg hover:bg-slate-600"
              >
                Modify Portfolio
              </button>
            </div>

            {/* Results Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Portfolio Allocation */}
              <PortfolioWeights portfolio={optimizationResult?.optimal_portfolio} />

              {/* Efficient Frontier */}
              <EfficientFrontier data={optimizationResult} />
            </div>

            {/* Risk Metrics */}
            <RiskMetrics weights={optimizationResult?.optimal_portfolio?.weights} />

            {/* Correlation Heatmap */}
            <CorrelationHeatmap symbols={selectedStocks} />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-slate-800 border-t border-slate-700 mt-12">
        <div className="max-w-7xl mx-auto px-4 py-4 text-center text-slate-400 text-sm">
          InvestX - Portfolio Optimization Tool | Data from Yahoo Finance
        </div>
      </footer>
    </div>
  );
}

export default App;
