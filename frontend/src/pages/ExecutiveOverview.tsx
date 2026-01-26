import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users,
  UserCheck,
  AlertTriangle,
  DollarSign,
  TrendingDown,
  Activity,
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { KPICard } from '@/components/dashboard/KPICard';
import { ChartContainer } from '@/components/dashboard/ChartContainer';
import { SegmentDonutChart } from '@/components/charts/SegmentDonutChart';
import { HealthDistributionChart } from '@/components/charts/HealthDistributionChart';
import { DataTable } from '@/components/dashboard/DataTable';
import { StatusBadge, PriorityBadge } from '@/components/dashboard/StatusBadge';
import {
  fetchKPISummary,
  fetchSegmentDistribution,
  fetchHealthDistribution,
  fetchHighValueAtRisk,
} from '@/lib/api';
import type { KPISummary, SegmentDistribution, HealthDistribution, Customer } from '@/lib/types';
import { useDashboardStore } from '@/store/dashboardStore';
import { ColumnDef } from '@tanstack/react-table';

const atRiskColumns: ColumnDef<Customer>[] = [
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
    accessorKey: 'clv12m',
    header: 'CLV (12m)',
    cell: ({ row }) => (
      <span className="font-medium">${row.original.clv12m.toLocaleString()}</span>
    ),
  },
  {
    accessorKey: 'churnProbability',
    header: 'Churn Risk',
    cell: ({ row }) => (
      <span className="font-medium text-danger">
        {Math.round(row.original.churnProbability * 100)}%
      </span>
    ),
  },
  {
    accessorKey: 'healthBand',
    header: 'Health',
    cell: ({ row }) => <StatusBadge status={row.original.healthBand} />,
  },
  {
    accessorKey: 'investmentPriority',
    header: 'Priority',
    cell: ({ row }) => <PriorityBadge priority={row.original.investmentPriority} />,
  },
];

export default function ExecutiveOverview() {
  const navigate = useNavigate();
  const { filters, setSegmentFilter, setHealthFilter } = useDashboardStore();

  const [kpi, setKpi] = useState<KPISummary | null>(null);
  const [segmentData, setSegmentData] = useState<SegmentDistribution[]>([]);
  const [healthData, setHealthData] = useState<HealthDistribution[]>([]);
  const [atRiskCustomers, setAtRiskCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const [kpiRes, segmentRes, healthRes, atRiskRes] = await Promise.all([
        fetchKPISummary(filters),
        fetchSegmentDistribution(filters),
        fetchHealthDistribution(filters),
        fetchHighValueAtRisk(), // Assume this doesn't need filters or is critical list
      ]);

      if (kpiRes.success) setKpi(kpiRes.data);
      if (segmentRes.success) setSegmentData(segmentRes.data);
      if (healthRes.success) setHealthData(healthRes.data);
      if (atRiskRes.success) setAtRiskCustomers(atRiskRes.data);
      setLoading(false);
    }
    loadData();
  }, [filters]);

  const handleSegmentClick = (segment: string) => {
    setSegmentFilter(segment as any);
    navigate('/customers');
  };

  const handleHealthClick = (band: string) => {
    setHealthFilter(band as any);
    navigate('/customers');
  };

  const handleCustomerClick = (customer: Customer) => {
    navigate(`/customers?id=${customer.id}`);
  };

  if (loading || !kpi) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-[60vh]">
          <div className="animate-pulse text-muted-foreground">Loading dashboard...</div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          <KPICard
            title="Total Customers"
            value={kpi.totalCustomers}
            icon={Users}
            variant="info"
            change={{ value: 12, isPositive: true }}
          />
          <KPICard
            title="Active Customers"
            value={kpi.activeCustomers}
            icon={UserCheck}
            variant="success"
            change={{ value: 8, isPositive: true }}
          />
          <KPICard
            title="At-Risk %"
            value={kpi.atRiskPercentage}
            icon={AlertTriangle}
            variant="warning"
            format="percentage"
            change={{ value: 2, isPositive: false }}
          />
          <KPICard
            title="Avg CLV"
            value={kpi.avgClv}
            icon={DollarSign}
            variant="success"
            format="currency"
            change={{ value: 15, isPositive: true }}
          />
          <KPICard
            title="Churn Rate"
            value={kpi.churnRate}
            icon={TrendingDown}
            variant="danger"
            format="percentage"
            change={{ value: 1.5, isPositive: false }}
          />
          <KPICard
            title="Revenue at Risk"
            value={kpi.revenueAtRisk}
            icon={Activity}
            variant="danger"
            format="currency"
          />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ChartContainer
            title="Customer Distribution by Segment"
            subtitle="Click on a segment to view customers"
          >
            <SegmentDonutChart data={segmentData} onSegmentClick={handleSegmentClick} />
          </ChartContainer>

          <ChartContainer
            title="Health Score Distribution"
            subtitle="Customer count by health band"
          >
            <HealthDistributionChart data={healthData} onBarClick={handleHealthClick} />
          </ChartContainer>
        </div>

        {/* High-Value At-Risk Table */}
        <ChartContainer
          title="High-Value At-Risk Customers"
          subtitle="Customers with CLV > $10K and churn probability > 40%"
        >
          <DataTable
            data={atRiskCustomers}
            columns={atRiskColumns}
            searchPlaceholder="Search at-risk customers..."
            pageSize={5}
            onRowClick={handleCustomerClick}
          />
        </ChartContainer>
      </div>
    </DashboardLayout>
  );
}
