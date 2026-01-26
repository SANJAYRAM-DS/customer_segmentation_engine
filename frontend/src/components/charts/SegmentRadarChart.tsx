import {
  RadarChart as RechartsRadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from 'recharts';

interface SegmentRadarChartProps {
  data: {
    segments: string[];
    metrics: { name: string; values: number[] }[];
  };
}

const SEGMENT_COLORS = [
  'hsl(160, 84%, 39%)', // Loyal
  'hsl(199, 89%, 48%)', // Active
  'hsl(262, 83%, 58%)', // New
  'hsl(38, 92%, 50%)',  // At-Risk
];

export function SegmentRadarChart({ data }: SegmentRadarChartProps) {
  // Transform data for Recharts radar format
  const chartData = data.metrics.map(metric => ({
    metric: metric.name,
    ...Object.fromEntries(
      data.segments.map((seg, i) => [seg, metric.values[i]])
    ),
  }));

  return (
    <ResponsiveContainer width="100%" height={350}>
      <RechartsRadarChart cx="50%" cy="50%" outerRadius="70%" data={chartData}>
        <PolarGrid stroke="hsl(var(--border))" />
        <PolarAngleAxis
          dataKey="metric"
          tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
        />
        <PolarRadiusAxis
          angle={30}
          domain={[0, 100]}
          tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
        />
        <Tooltip
          content={({ active, payload }) => {
            if (active && payload && payload.length) {
              return (
                <div className="bg-popover border border-border rounded-lg shadow-lg p-3">
                  <p className="font-medium text-foreground mb-2">{payload[0]?.payload?.metric}</p>
                  {payload.map((entry, index) => (
                    <p key={index} className="text-sm" style={{ color: entry.color }}>
                      {entry.name}: {entry.value}
                    </p>
                  ))}
                </div>
              );
            }
            return null;
          }}
        />
        {data.segments.map((segment, index) => (
          <Radar
            key={segment}
            name={segment}
            dataKey={segment}
            stroke={SEGMENT_COLORS[index]}
            fill={SEGMENT_COLORS[index]}
            fillOpacity={0.15}
            strokeWidth={2}
          />
        ))}
        <Legend
          wrapperStyle={{ paddingTop: 20 }}
          formatter={(value) => (
            <span className="text-sm text-muted-foreground">{value}</span>
          )}
        />
      </RechartsRadarChart>
    </ResponsiveContainer>
  );
}
