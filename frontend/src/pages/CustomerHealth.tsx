import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { ChartContainer } from '@/components/dashboard/ChartContainer';
import { HealthDistributionChart } from '@/components/charts/HealthDistributionChart';
import { HealthGauge } from '@/components/charts/HealthGauge';
import { PriorityMatrix } from '@/components/charts/PriorityMatrix';
import { DataTable } from '@/components/dashboard/DataTable';
import { StatusBadge, PriorityBadge } from '@/components/dashboard/StatusBadge';
import {
  fetchHealthDistribution,
  fetchPriorityMatrix,
  fetchCustomers,
  fetchKPISummary,
} from '@/lib/api';
import type { HealthDistribution, Customer, KPISummary } from '@/lib/types';
import { useDashboardStore } from '@/store/dashboardStore';
import { ColumnDef } from '@tanstack/react-table';

const customerColumns: ColumnDef<Customer>[] = [
  {
    accessorKey: 'name',
    header: 'Customer',
    cell: ({ row }) => (
      <div>
        <p className="font-medium text-foreground">{row.original.name}</p>
        <p className="text-xs text-muted-foreground">{row.original.company}</p>
      </div>
    ),
  },
  {
    accessorKey: 'investmentPriority',
    header: 'Priority',
    cell: ({ row }) => <PriorityBadge priority={row.original.investmentPriority} />,
  },
  {
    accessorKey: 'segment',
    header: 'Segment',
    cell: ({ row }) => <StatusBadge status={row.original.segment} />,
  },
  {
    accessorKey: 'healthScore',
    header: 'Health Score',
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <span className="font-medium">{row.original.healthScore}</span>
        <StatusBadge status={row.original.healthBand} />
      </div>
    ),
  },
  {
    accessorKey: 'clv12m',
    header: 'CLV',
    cell: ({ row }) => (
      <span className="font-medium">${row.original.clv12m.toLocaleString()}</span>
    ),
  },
  {
    accessorKey: 'churnProbability',
    header: 'Churn Risk',
    cell: ({ row }) => (
      <span
        className={
          row.original.churnProbability > 0.5
            ? 'text-danger font-medium'
            : row.original.churnProbability > 0.25
            ? 'text-warning font-medium'
            : 'text-success font-medium'
        }
      >
        {Math.round(row.original.churnProbability * 100)}%
      </span>
    ),
  },
];

export default function CustomerHealth() {
  const navigate = useNavigate();
  const { setPriorityFilter } = useDashboardStore();

  const [healthData, setHealthData] = useState<HealthDistribution[]>([]);
  const [matrixData, setMatrixData] = useState<{
    quadrants: { name: string; customers: number; avgClv: number; avgRisk: number }[];
  } | null>(null);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [kpi, setKPI] = useState<KPISummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const [healthRes, matrixRes, customersRes, kpiRes] = await Promise.all([
        fetchHealthDistribution(),
        fetchPriorityMatrix(),
        fetchCustomers({}, { pageSize: 50 }),
        fetchKPISummary(),
      ]);

      if (healthRes.success) setHealthData(healthRes.data);
      if (matrixRes.success) setMatrixData(matrixRes.data);
      if (customersRes.success) setCustomers(customersRes.data);
      if (kpiRes.success) setKPI(kpiRes.data);
      setLoading(false);
    }
    loadData();
  }, []);

  const handleQuadrantClick = (quadrant: string) => {
    setPriorityFilter(quadrant as any);
    navigate('/customers');
  };

  const handleCustomerClick = (customer: Customer) => {
    navigate(`/customers?id=${customer.id}`);
  };

  // Calculate average health score
  const avgHealthScore = customers.length > 0
    ? Math.round(customers.reduce((sum, c) => sum + c.healthScore, 0) / customers.length)
    : 0;

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-[60vh]">
          <div className="animate-pulse text-muted-foreground">Loading health data...</div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Health Overview Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Health Gauge */}
          <ChartContainer
            title="Overall Health Score"
            subtitle="Weighted average across all customers"
          >
            <div className="flex items-center justify-center py-4">
              <HealthGauge score={avgHealthScore} size="lg" />
            </div>
          </ChartContainer>

          {/* Health Distribution */}
          <ChartContainer
            title="Health Band Distribution"
            subtitle="Customer count by health band"
            className="lg:col-span-2"
          >
            <HealthDistributionChart data={healthData} />
          </ChartContainer>
        </div>

        {/* Priority Matrix */}
        {matrixData && (
          <ChartContainer
            title="Investment Priority Matrix"
            subtitle="Strategic customer segmentation by value and risk"
          >
            <PriorityMatrix data={matrixData} onQuadrantClick={handleQuadrantClick} />
          </ChartContainer>
        )}

        {/* Actionable Customer List */}
        <ChartContainer
          title="Actionable Customer List"
          subtitle="Filter and prioritize customers for action"
        >
          <DataTable
            data={customers}
            columns={customerColumns}
            searchPlaceholder="Search customers..."
            pageSize={10}
            onRowClick={handleCustomerClick}
          />
        </ChartContainer>
      </div>
    </DashboardLayout>
  );
}
