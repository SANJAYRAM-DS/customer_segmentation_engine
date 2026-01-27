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
import type { SegmentDistribution } from '../../lib/types';

interface SegmentBarChartProps {
  data: any[]; // Relax type to allow ad-hoc objects from Segmentation.tsx
  dataKey: string;
  onBarClick?: (segment: string) => void;
  color?: string; // Add color prop
}

const SEGMENT_COLORS = {
  Loyal: 'hsl(160, 84%, 39%)',
  Active: 'hsl(199, 89%, 48%)',
  New: 'hsl(262, 83%, 58%)',
  'At-Risk': 'hsl(38, 92%, 50%)',
  Churned: 'hsl(0, 72%, 51%)',
};

export function SegmentBarChart({ data, dataKey, onBarClick, color }: SegmentBarChartProps) {
  const formatValue = (value: number) => {
    if (dataKey === 'avgClv') {
      return `$${value.toLocaleString()}`;
    }
    if (dataKey === 'avgChurnRisk') {
      return `${value}%`;
    }
    if (dataKey === 'val') { // Health Score
      return value.toString();
    }
    return value.toLocaleString();
  };

  const getLabel = () => {
    switch (dataKey) {
      case 'avgClv':
        return 'Avg CLV';
      case 'count':
        return 'Customers';
      case 'avgChurnRisk':
        return 'Avg Churn Risk';
      case 'val':
        return 'Avg Health Score';
      default:
        return '';
    }
  };

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
        <XAxis
          dataKey="segment"
          tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(value) => {
            if (dataKey === 'avgClv') return `$${(value / 1000).toFixed(0)}K`;
            if (dataKey === 'avgChurnRisk') return `${value}%`;
            return value;
          }}
        />
        <Tooltip
          content={({ active, payload }) => {
            if (active && payload && payload.length) {
              const item = payload[0].payload;
              return (
                <div className="bg-popover border border-border rounded-lg shadow-lg p-3">
                  <p className="font-medium text-foreground">{item.segment}</p>
                  <p className="text-sm text-muted-foreground">
                    {getLabel()}: {formatValue(item[dataKey])}
                  </p>
                </div>
              );
            }
            return null;
          }}
        />
        <Bar
          dataKey={dataKey}
          radius={[4, 4, 0, 0]}
          onClick={(data) => onBarClick?.(data.segment)}
          style={{ cursor: 'pointer' }}
        >
          {data.map((entry) => (
            <Cell
              key={`cell-${entry.segment}`}
              fill={color || SEGMENT_COLORS[entry.segment as keyof typeof SEGMENT_COLORS] || '#8884d8'}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
