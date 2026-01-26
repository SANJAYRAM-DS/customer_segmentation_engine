import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { ChartContainer } from '@/components/dashboard/ChartContainer';
import { SegmentBarChart } from '@/components/charts/SegmentBarChart';
import { SegmentRadarChart } from '@/components/charts/SegmentRadarChart';
import { DataTable } from '@/components/dashboard/DataTable';
import { StatusBadge } from '@/components/dashboard/StatusBadge';
import { fetchSegmentDistribution, fetchSegmentComparison } from '@/lib/api';
import type { SegmentDistribution } from '@/lib/types';
import { useDashboardStore } from '@/store/dashboardStore';
import { ColumnDef } from '@tanstack/react-table';

const segmentColumns: ColumnDef<SegmentDistribution>[] = [
  {
    accessorKey: 'segment',
    header: 'Segment',
    cell: ({ row }) => <StatusBadge status={row.original.segment} />,
  },
  {
    accessorKey: 'count',
    header: 'Customer Count',
    cell: ({ row }) => (
      <span className="font-medium">{row.original.count.toLocaleString()}</span>
    ),
  },
  {
    accessorKey: 'percentage',
    header: '% of Total',
    cell: ({ row }) => <span>{row.original.percentage}%</span>,
  },
  {
    accessorKey: 'avgClv',
    header: 'Avg CLV',
    cell: ({ row }) => (
      <span className="font-medium text-success">
        ${row.original.avgClv.toLocaleString()}
      </span>
    ),
  },
  {
    accessorKey: 'avgChurnRisk',
    header: 'Avg Churn Risk',
    cell: ({ row }) => (
      <span
        className={
          row.original.avgChurnRisk > 50
            ? 'text-danger font-medium'
            : row.original.avgChurnRisk > 25
              ? 'text-warning font-medium'
              : 'text-success font-medium'
        }
      >
        {row.original.avgChurnRisk}%
      </span>
    ),
  },
];

export default function Segmentation() {
  const navigate = useNavigate();
  const { setSegmentFilter } = useDashboardStore();

  const [segmentData, setSegmentData] = useState<SegmentDistribution[]>([]);
  const [radarData, setRadarData] = useState<{
    segments: string[];
    metrics: { name: string; values: number[] }[];
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const [segmentRes, radarRes] = await Promise.all([
        fetchSegmentDistribution(),
        fetchSegmentComparison(),
      ]);

      if (segmentRes.success) setSegmentData(segmentRes.data);
      if (radarRes.success) setRadarData(radarRes.data);
      setLoading(false);
    }
    loadData();
  }, []);

  const handleSegmentClick = (segment: string) => {
    setSegmentFilter(segment as any);
    navigate('/customers');
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-[60vh]">
          <div className="animate-pulse text-muted-foreground">Loading segmentation data...</div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Segment Summary Table */}
        <ChartContainer
          title="Segment Overview"
          subtitle="Key metrics by customer segment"
        >
          <DataTable
            data={segmentData}
            columns={segmentColumns}
            searchPlaceholder="Search segments..."
            pageSize={5}
          />
        </ChartContainer>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ChartContainer
            title="Segment Size & Value"
            subtitle="Average CLV by segment"
          >
            <SegmentBarChart
              data={segmentData}
              dataKey="avgClv"
              onBarClick={handleSegmentClick}
            />
          </ChartContainer>

          <ChartContainer
            title="Segment Churn Risk"
            subtitle="Average churn probability by segment"
          >
            <SegmentBarChart
              data={segmentData}
              dataKey="avgChurnRisk"
              onBarClick={handleSegmentClick}
            />
          </ChartContainer>
        </div>

        {/* Radar Chart */}
        {radarData && (
          <ChartContainer
            title="Segment Health Comparison"
            subtitle="Average Health Score by Segment"
          >
            <SegmentBarChart
              data={radarData ? radarData.segments.map((s, i) => ({
                segment: s,
                // We need to map back from the array struct. 
                // radarData has { segments: [], metrics: [{name, values}] }
                // match index
                val: radarData.metrics.find(m => m.name === 'Health Score')?.values[i] || 0
              })) : []}
              dataKey="val"
              color="#10b981" // Success color for health
            />
          </ChartContainer>
        )}
      </div>
    </DashboardLayout>
  );
}
