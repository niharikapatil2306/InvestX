import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

const COLORS = [
  '#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6',
  '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1',
];

export default function PortfolioWeights({ portfolio }) {
  if (!portfolio) {
    return (
      <div className="bg-slate-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Portfolio Allocation</h2>
        <div className="text-slate-400 text-center py-8">
          Optimize a portfolio to see allocation
        </div>
      </div>
    );
  }

  const { weights, expected_return, volatility, sharpe_ratio } = portfolio;

  // Prepare data for pie chart
  const pieData = Object.entries(weights)
    .filter(([_, weight]) => weight > 0.001)
    .map(([symbol, weight]) => ({
      name: symbol,
      value: weight * 100,
    }))
    .sort((a, b) => b.value - a.value);

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-2 shadow-lg">
          <p className="text-white font-medium">{payload[0].name}</p>
          <p className="text-slate-300">{payload[0].value.toFixed(2)}%</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-4">Portfolio Allocation</h2>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-slate-700/50 rounded-lg p-3 text-center">
          <div className="text-sm text-slate-400">Expected Return</div>
          <div className="text-xl font-bold text-green-400">
            {(expected_return * 100).toFixed(2)}%
          </div>
        </div>
        <div className="bg-slate-700/50 rounded-lg p-3 text-center">
          <div className="text-sm text-slate-400">Volatility</div>
          <div className="text-xl font-bold text-yellow-400">
            {(volatility * 100).toFixed(2)}%
          </div>
        </div>
        <div className="bg-slate-700/50 rounded-lg p-3 text-center">
          <div className="text-sm text-slate-400">Sharpe Ratio</div>
          <div className="text-xl font-bold text-blue-400">
            {sharpe_ratio.toFixed(2)}
          </div>
        </div>
      </div>

      {/* Pie Chart */}
      <div className="h-64 mb-4">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={90}
              paddingAngle={2}
              dataKey="value"
              label={({ name, value }) => `${name}: ${value.toFixed(1)}%`}
              labelLine={false}
            >
              {pieData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={COLORS[index % COLORS.length]}
                />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Weight List */}
      <div className="space-y-2 max-h-48 overflow-y-auto">
        {pieData.map((item, index) => (
          <div
            key={item.name}
            className="flex items-center justify-between p-2 bg-slate-700/30 rounded"
          >
            <div className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: COLORS[index % COLORS.length] }}
              ></div>
              <span className="font-medium">{item.name}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-24 h-2 bg-slate-600 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${item.value}%`,
                    backgroundColor: COLORS[index % COLORS.length],
                  }}
                ></div>
              </div>
              <span className="text-sm text-slate-400 w-16 text-right">
                {item.value.toFixed(1)}%
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
