import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import type { ChurnRiskDistribution } from '@/lib/types';

interface ChurnRiskHistogramProps {
  data: ChurnRiskDistribution[];
  onBarClick?: (range: string) => void;
}

const RISK_COLORS = [
  'hsl(160, 84%, 39%)', // Low - green
  'hsl(38, 92%, 50%)',  // Medium - yellow
  'hsl(25, 95%, 53%)',  // High - orange
  'hsl(0, 72%, 51%)',   // Critical - red
];

export function ChurnRiskHistogram({ data, onBarClick }: ChurnRiskHistogramProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
        <XAxis
          dataKey="range"
          tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip
          content={({ active, payload }) => {
            if (active && payload && payload.length) {
              const data = payload[0].payload;
              return (
                <div className="bg-popover border border-border rounded-lg shadow-lg p-3">
                  <p className="font-medium text-foreground">{data.range}</p>
                  <p className="text-sm text-muted-foreground">
                    {data.count.toLocaleString()} customers ({data.percentage}%)
                  </p>
                </div>
              );
            }
            return null;
          }}
        />
        <Bar
          dataKey="count"
          radius={[4, 4, 0, 0]}
          onClick={(data) => onBarClick?.(data.range)}
          style={{ cursor: 'pointer' }}
        >
          {data.map((_, index) => (
            <Cell key={`cell-${index}`} fill={RISK_COLORS[index]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
