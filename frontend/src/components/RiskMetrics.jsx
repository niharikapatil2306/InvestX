import { useState, useEffect } from 'react';
import { AlertTriangle, TrendingDown, Activity, Shield } from 'lucide-react';
import { analyzeRisk } from '../services/api';

export default function RiskMetrics({ weights }) {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadRiskMetrics = async () => {
    setLoading(true);
    try {
      const data = await analyzeRisk(weights);
      setMetrics(data);
    } catch (err) {
      console.error('Failed to load risk metrics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (weights && Object.keys(weights).length > 0) {
      loadRiskMetrics();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(weights)]);

  if (!weights || Object.keys(weights).length === 0) {
    return (
      <div className="bg-slate-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Risk Metrics</h2>
        <div className="text-slate-400 text-center py-8">
          Optimize a portfolio to see risk metrics
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="bg-slate-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Risk Metrics</h2>
        <div className="animate-pulse space-y-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-20 bg-slate-700 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  if (!metrics) return null;

  const metricCards = [
    {
      label: 'Volatility',
      value: `${(metrics.volatility * 100).toFixed(2)}%`,
      description: 'Annualized standard deviation',
      icon: Activity,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/10',
    },
    {
      label: 'VaR (95%)',
      value: `${(metrics.var_95 * 100).toFixed(2)}%`,
      description: '95% confidence max daily loss',
      icon: AlertTriangle,
      color: 'text-yellow-400',
      bgColor: 'bg-yellow-500/10',
    },
    {
      label: 'VaR (99%)',
      value: `${(metrics.var_99 * 100).toFixed(2)}%`,
      description: '99% confidence max daily loss',
      icon: AlertTriangle,
      color: 'text-orange-400',
      bgColor: 'bg-orange-500/10',
    },
    {
      label: 'CVaR (95%)',
      value: `${(metrics.cvar_95 * 100).toFixed(2)}%`,
      description: 'Expected loss beyond VaR',
      icon: TrendingDown,
      color: 'text-red-400',
      bgColor: 'bg-red-500/10',
    },
    {
      label: 'Max Drawdown',
      value: `${(metrics.max_drawdown * 100).toFixed(2)}%`,
      description: 'Largest peak-to-trough decline',
      icon: TrendingDown,
      color: 'text-red-400',
      bgColor: 'bg-red-500/10',
    },
    {
      label: 'Sharpe Ratio',
      value: metrics.sharpe_ratio.toFixed(2),
      description: 'Risk-adjusted return',
      icon: Shield,
      color: metrics.sharpe_ratio >= 1 ? 'text-green-400' : 'text-yellow-400',
      bgColor: metrics.sharpe_ratio >= 1 ? 'bg-green-500/10' : 'bg-yellow-500/10',
    },
    {
      label: 'Sortino Ratio',
      value: metrics.sortino_ratio.toFixed(2),
      description: 'Downside risk-adjusted return',
      icon: Shield,
      color: metrics.sortino_ratio >= 1.5 ? 'text-green-400' : 'text-yellow-400',
      bgColor: metrics.sortino_ratio >= 1.5 ? 'bg-green-500/10' : 'bg-yellow-500/10',
    },
  ];

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-4">Risk Metrics</h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {metricCards.map((metric) => (
          <div
            key={metric.label}
            className={`${metric.bgColor} rounded-lg p-4 border border-slate-700`}
          >
            <div className="flex items-center gap-2 mb-2">
              <metric.icon className={`w-5 h-5 ${metric.color}`} />
              <span className="text-sm text-slate-400">{metric.label}</span>
            </div>
            <div className={`text-2xl font-bold ${metric.color}`}>
              {metric.value}
            </div>
            <div className="text-xs text-slate-500 mt-1">{metric.description}</div>
          </div>
        ))}
      </div>

      {/* Risk Level Indicator */}
      <div className="mt-6 p-4 bg-slate-700/50 rounded-lg">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-slate-400">Overall Risk Level</span>
          <span
            className={`text-sm font-medium ${
              metrics.volatility < 0.15
                ? 'text-green-400'
                : metrics.volatility < 0.25
                ? 'text-yellow-400'
                : 'text-red-400'
            }`}
          >
            {metrics.volatility < 0.15
              ? 'Low'
              : metrics.volatility < 0.25
              ? 'Medium'
              : 'High'}
          </span>
        </div>
        <div className="w-full h-2 bg-slate-600 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              metrics.volatility < 0.15
                ? 'bg-green-500'
                : metrics.volatility < 0.25
                ? 'bg-yellow-500'
                : 'bg-red-500'
            }`}
            style={{ width: `${Math.min(metrics.volatility * 200, 100)}%` }}
          ></div>
        </div>
      </div>
    </div>
  );
}
