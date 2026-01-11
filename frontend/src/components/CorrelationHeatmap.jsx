import { useState, useEffect } from 'react';
import { getCorrelation } from '../services/api';

export default function CorrelationHeatmap({ symbols }) {
  const [correlation, setCorrelation] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadCorrelation = async () => {
    setLoading(true);
    try {
      const data = await getCorrelation(symbols);
      setCorrelation(data);
    } catch (err) {
      console.error('Failed to load correlation:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (symbols && symbols.length >= 2) {
      loadCorrelation();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(symbols)]);

  const getColor = (value) => {
    // Color scale from red (-1) to white (0) to green (+1)
    if (value >= 0) {
      const intensity = Math.floor(value * 255);
      return `rgb(${255 - intensity}, 255, ${255 - intensity})`;
    } else {
      const intensity = Math.floor(-value * 255);
      return `rgb(255, ${255 - intensity}, ${255 - intensity})`;
    }
  };

  const getTextColor = (value) => {
    return Math.abs(value) > 0.5 ? 'text-slate-900' : 'text-slate-200';
  };

  if (!symbols || symbols.length < 2) {
    return (
      <div className="bg-slate-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Correlation Matrix</h2>
        <div className="text-slate-400 text-center py-8">
          Select at least 2 stocks to see correlations
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="bg-slate-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Correlation Matrix</h2>
        <div className="animate-pulse">
          <div className="h-64 bg-slate-700 rounded"></div>
        </div>
      </div>
    );
  }

  if (!correlation) return null;

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-4">Correlation Matrix</h2>

      {/* Color Legend */}
      <div className="flex items-center justify-center gap-4 mb-4 text-sm">
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: 'rgb(255, 0, 0)' }}></div>
          <span className="text-slate-400">-1 (Negative)</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 rounded bg-white"></div>
          <span className="text-slate-400">0 (None)</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: 'rgb(0, 255, 0)' }}></div>
          <span className="text-slate-400">+1 (Positive)</span>
        </div>
      </div>

      {/* Matrix */}
      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead>
            <tr>
              <th className="p-2"></th>
              {correlation.symbols.map((symbol) => (
                <th
                  key={symbol}
                  className="p-2 text-xs font-medium text-slate-400 text-center"
                  style={{ writingMode: 'vertical-lr', transform: 'rotate(180deg)' }}
                >
                  {symbol}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {correlation.symbols.map((rowSymbol, rowIndex) => (
              <tr key={rowSymbol}>
                <td className="p-2 text-xs font-medium text-slate-400 text-right">
                  {rowSymbol}
                </td>
                {correlation.matrix[rowIndex].map((value, colIndex) => (
                  <td
                    key={`${rowIndex}-${colIndex}`}
                    className={`p-1 text-center text-xs font-medium ${getTextColor(value)}`}
                    style={{ backgroundColor: getColor(value) }}
                    title={`${rowSymbol} vs ${correlation.symbols[colIndex]}: ${value.toFixed(3)}`}
                  >
                    {value.toFixed(2)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Insights */}
      <div className="mt-4 p-3 bg-slate-700/50 rounded-lg">
        <div className="text-sm text-slate-400">
          <strong className="text-slate-300">Diversification Tip:</strong> Look for stocks with low
          or negative correlations to reduce portfolio risk through diversification.
        </div>
      </div>
    </div>
  );
}
