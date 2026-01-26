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
import type { HealthDistribution } from '@/lib/types';

interface HealthDistributionChartProps {
  data: HealthDistribution[];
  onBarClick?: (band: string) => void;
}

const HEALTH_COLORS = {
  Excellent: 'hsl(160, 84%, 39%)',
  Good: 'hsl(160, 60%, 50%)',
  Watch: 'hsl(38, 92%, 50%)',
  Critical: 'hsl(0, 72%, 51%)',
};

export function HealthDistributionChart({ data, onBarClick }: HealthDistributionChartProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} layout="vertical" margin={{ left: 20, right: 20 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal vertical={false} stroke="hsl(var(--border))" />
        <XAxis type="number" tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }} />
        <YAxis
          type="category"
          dataKey="band"
          tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
          width={80}
        />
        <Tooltip
          content={({ active, payload }) => {
            if (active && payload && payload.length) {
              const data = payload[0].payload;
              return (
                <div className="bg-popover border border-border rounded-lg shadow-lg p-3">
                  <p className="font-medium text-foreground">{data.band}</p>
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
          radius={[0, 4, 4, 0]}
          onClick={(data) => onBarClick?.(data.band)}
          style={{ cursor: 'pointer' }}
        >
          {data.map((entry) => (
            <Cell
              key={`cell-${entry.band}`}
              fill={HEALTH_COLORS[entry.band as keyof typeof HEALTH_COLORS]}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
