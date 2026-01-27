import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import type { RiskTrend } from '../../lib/types';

interface RiskTrendChartProps {
  data: RiskTrend[];
}

export function RiskTrendChart({ data }: RiskTrendChartProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
        <XAxis
          dataKey="date"
          tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
          tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
          interval="preserveStartEnd"
        />
        <YAxis
          tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
          tickFormatter={(value) => `${value}%`}
          domain={[0, 50]}
        />
        <Tooltip
          content={({ active, payload, label }) => {
            if (active && payload && payload.length) {
              return (
                <div className="bg-popover border border-border rounded-lg shadow-lg p-3">
                  <p className="font-medium text-foreground mb-2">
                    {new Date(label).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
                  </p>
                  {payload.map((entry, index) => (
                    <p key={index} className="text-sm" style={{ color: entry.color }}>
                      {entry.name}: {entry.value}%
                    </p>
                  ))}
                </div>
              );
            }
            return null;
          }}
        />
        <Legend
          verticalAlign="top"
          height={36}
          formatter={(value) => (
            <span className="text-sm text-muted-foreground">{value}</span>
          )}
        />
        <Line
          type="monotone"
          dataKey="avgChurnProbability"
          name="Avg Churn Probability"
          stroke="hsl(38, 92%, 50%)"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, fill: 'hsl(38, 92%, 50%)' }}
        />
        <Line
          type="monotone"
          dataKey="highRiskPercentage"
          name="High Risk %"
          stroke="hsl(0, 72%, 51%)"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, fill: 'hsl(0, 72%, 51%)' }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
