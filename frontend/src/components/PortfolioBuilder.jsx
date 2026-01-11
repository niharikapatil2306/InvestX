import { useState } from 'react';
import { Loader2, Sparkles, Scale, Target } from 'lucide-react';
import { optimizePortfolio } from '../services/api';

export default function PortfolioBuilder({
  selectedStocks,
  onOptimize,
  isOptimizing,
  setIsOptimizing,
}) {
  const [target, setTarget] = useState('max_sharpe');
  const [maxWeight, setMaxWeight] = useState(1.0);
  const [minWeight, setMinWeight] = useState(0.0);
  const [targetReturn, setTargetReturn] = useState(0.15);

  const handleOptimize = async () => {
    if (selectedStocks.length < 2) return;

    setIsOptimizing(true);
    try {
      const result = await optimizePortfolio(selectedStocks, target, {
        maxWeight,
        minWeight,
        targetReturn: target === 'target_return' ? targetReturn : undefined,
      });
      onOptimize(result);
    } catch (err) {
      console.error('Optimization failed:', err);
    } finally {
      setIsOptimizing(false);
    }
  };

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-4">Optimization Settings</h2>

      {/* Optimization Target */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-slate-300 mb-2">
          Optimization Target
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <button
            onClick={() => setTarget('max_sharpe')}
            className={`flex items-center gap-2 p-3 rounded-lg border transition-colors ${
              target === 'max_sharpe'
                ? 'bg-blue-600/20 border-blue-500 text-blue-400'
                : 'bg-slate-700 border-slate-600 hover:border-slate-500'
            }`}
          >
            <Sparkles className="w-5 h-5" />
            <div className="text-left">
              <div className="font-medium">Max Sharpe</div>
              <div className="text-xs text-slate-400">Best risk-adjusted</div>
            </div>
          </button>

          <button
            onClick={() => setTarget('min_vol')}
            className={`flex items-center gap-2 p-3 rounded-lg border transition-colors ${
              target === 'min_vol'
                ? 'bg-blue-600/20 border-blue-500 text-blue-400'
                : 'bg-slate-700 border-slate-600 hover:border-slate-500'
            }`}
          >
            <Scale className="w-5 h-5" />
            <div className="text-left">
              <div className="font-medium">Min Volatility</div>
              <div className="text-xs text-slate-400">Lowest risk</div>
            </div>
          </button>

          <button
            onClick={() => setTarget('target_return')}
            className={`flex items-center gap-2 p-3 rounded-lg border transition-colors ${
              target === 'target_return'
                ? 'bg-blue-600/20 border-blue-500 text-blue-400'
                : 'bg-slate-700 border-slate-600 hover:border-slate-500'
            }`}
          >
            <Target className="w-5 h-5" />
            <div className="text-left">
              <div className="font-medium">Target Return</div>
              <div className="text-xs text-slate-400">Specific goal</div>
            </div>
          </button>
        </div>
      </div>

      {/* Target Return Input */}
      {target === 'target_return' && (
        <div className="mb-6">
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Target Annual Return: {(targetReturn * 100).toFixed(0)}%
          </label>
          <input
            type="range"
            min="0"
            max="0.5"
            step="0.01"
            value={targetReturn}
            onChange={(e) => setTargetReturn(parseFloat(e.target.value))}
            className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
          />
          <div className="flex justify-between text-xs text-slate-400 mt-1">
            <span>0%</span>
            <span>50%</span>
          </div>
        </div>
      )}

      {/* Weight Constraints */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Max Weight: {(maxWeight * 100).toFixed(0)}%
          </label>
          <input
            type="range"
            min="0.1"
            max="1"
            step="0.05"
            value={maxWeight}
            onChange={(e) => setMaxWeight(parseFloat(e.target.value))}
            className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Min Weight: {(minWeight * 100).toFixed(0)}%
          </label>
          <input
            type="range"
            min="0"
            max="0.2"
            step="0.01"
            value={minWeight}
            onChange={(e) => setMinWeight(parseFloat(e.target.value))}
            className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
          />
        </div>
      </div>

      {/* Optimize Button */}
      <button
        onClick={handleOptimize}
        disabled={selectedStocks.length < 2 || isOptimizing}
        className={`w-full py-3 rounded-lg font-semibold flex items-center justify-center gap-2 transition-colors ${
          selectedStocks.length < 2 || isOptimizing
            ? 'bg-slate-600 text-slate-400 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-700 text-white'
        }`}
      >
        {isOptimizing ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Optimizing...
          </>
        ) : (
          <>
            <Sparkles className="w-5 h-5" />
            Optimize Portfolio
          </>
        )}
      </button>

      {selectedStocks.length < 2 && (
        <p className="text-sm text-slate-400 text-center mt-2">
          Select at least 2 stocks to optimize
        </p>
      )}
    </div>
  );
}
