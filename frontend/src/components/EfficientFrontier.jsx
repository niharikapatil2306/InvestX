import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

export default function EfficientFrontier({ data, optimalPortfolio }) {
  if (!data) {
    return (
      <div className="bg-slate-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Efficient Frontier</h2>
        <div className="h-80 flex items-center justify-center text-slate-400">
          Run optimization to see the efficient frontier
        </div>
      </div>
    );
  }

  const { efficient_frontier, individual_stocks, optimal_portfolio } = data;

  // Prepare data for the chart
  const frontierData = efficient_frontier.map((point) => ({
    x: point.volatility * 100,
    y: point.expected_return * 100,
    type: 'frontier',
  }));

  const stocksData = individual_stocks.map((stock) => ({
    x: stock.volatility * 100,
    y: stock.expected_return * 100,
    name: stock.symbol,
    type: 'stock',
  }));

  const optimalData = optimal_portfolio
    ? [
        {
          x: optimal_portfolio.volatility * 100,
          y: optimal_portfolio.expected_return * 100,
          type: 'optimal',
        },
      ]
    : [];

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-3 shadow-lg">
          {data.name && (
            <p className="font-semibold text-white mb-1">{data.name}</p>
          )}
          <p className="text-sm text-slate-300">
            Return: <span className="text-green-400">{data.y.toFixed(2)}%</span>
          </p>
          <p className="text-sm text-slate-300">
            Volatility: <span className="text-yellow-400">{data.x.toFixed(2)}%</span>
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-4">Efficient Frontier</h2>

      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              type="number"
              dataKey="x"
              name="Volatility"
              unit="%"
              stroke="#94a3b8"
              tick={{ fill: '#94a3b8' }}
              label={{
                value: 'Volatility (%)',
                position: 'bottom',
                fill: '#94a3b8',
              }}
            />
            <YAxis
              type="number"
              dataKey="y"
              name="Return"
              unit="%"
              stroke="#94a3b8"
              tick={{ fill: '#94a3b8' }}
              label={{
                value: 'Expected Return (%)',
                angle: -90,
                position: 'left',
                fill: '#94a3b8',
              }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />

            {/* Individual Stocks */}
            <Scatter
              name="Individual Stocks"
              data={stocksData}
              fill="#6366f1"
              shape="circle"
            />

            {/* Efficient Frontier */}
            <Scatter
              name="Efficient Frontier"
              data={frontierData}
              fill="#22c55e"
              shape="diamond"
              line={{ stroke: '#22c55e', strokeWidth: 2 }}
            />

            {/* Optimal Portfolio */}
            <Scatter
              name="Optimal Portfolio"
              data={optimalData}
              fill="#f59e0b"
              shape="star"
            />
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="flex justify-center gap-6 mt-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-indigo-500"></div>
          <span className="text-slate-400">Individual Stocks</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-green-500 rotate-45"></div>
          <span className="text-slate-400">Efficient Frontier</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-amber-500"></div>
          <span className="text-slate-400">Optimal Portfolio</span>
        </div>
      </div>
    </div>
  );
}
