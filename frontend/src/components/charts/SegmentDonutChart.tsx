import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from 'recharts';
import type { SegmentDistribution } from '../../lib/types';

interface SegmentDonutChartProps {
  data: SegmentDistribution[];
  onSegmentClick?: (segment: string) => void;
}

const SEGMENT_COLORS = {
  Loyal: 'hsl(160, 84%, 39%)',
  Active: 'hsl(199, 89%, 48%)',
  New: 'hsl(262, 83%, 58%)',
  'At-Risk': 'hsl(38, 92%, 50%)',
  Churned: 'hsl(0, 72%, 51%)',
};

export function SegmentDonutChart({ data, onSegmentClick }: SegmentDonutChartProps) {
  const chartData = data.map(item => ({
    name: item.segment,
    value: item.count,
    percentage: item.percentage,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={100}
          paddingAngle={2}
          dataKey="value"
          onClick={(data) => onSegmentClick?.(data.name)}
          style={{ cursor: 'pointer' }}
        >
          {chartData.map((entry) => (
            <Cell
              key={`cell-${entry.name}`}
              fill={SEGMENT_COLORS[entry.name as keyof typeof SEGMENT_COLORS]}
              stroke="transparent"
            />
          ))}
        </Pie>
        <Tooltip
          content={({ active, payload }) => {
            if (active && payload && payload.length) {
              const data = payload[0].payload;
              return (
                <div className="bg-popover border border-border rounded-lg shadow-lg p-3">
                  <p className="font-medium text-foreground">{data.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {data.value.toLocaleString()} customers ({data.percentage}%)
                  </p>
                </div>
              );
            }
            return null;
          }}
        />
        <Legend
          verticalAlign="bottom"
          height={36}
          formatter={(value) => (
            <span className="text-sm text-muted-foreground">{value}</span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
