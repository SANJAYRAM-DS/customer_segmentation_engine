import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { ChartContainer } from '@/components/dashboard/ChartContainer';
import { ChurnRiskHistogram } from '@/components/charts/ChurnRiskHistogram';
import { RiskTrendChart } from '@/components/charts/RiskTrendChart';
import { DataTable } from '@/components/dashboard/DataTable';
import { StatusBadge, PriorityBadge } from '@/components/dashboard/StatusBadge';
import { Button } from '@/components/ui/button';
import {
  fetchChurnRiskDistribution,
  fetchRiskTrend,
  fetchHighValueAtRisk,
} from '@/lib/api';
import type { ChurnRiskDistribution, RiskTrend, Customer } from '@/lib/types';
import { ColumnDef } from '@tanstack/react-table';
import { Phone, Mail } from 'lucide-react';

const atRiskColumns: ColumnDef<Customer>[] = [
  {
    accessorKey: 'name',
    header: 'Customer',
    cell: ({ row }) => (
      <div>
        <p className="font-medium text-foreground">{row.original.name}</p>
        <p className="text-xs text-muted-foreground">{row.original.email}</p>
      </div>
    ),
  },
  {
    accessorKey: 'company',
    header: 'Company',
  },
  {
    accessorKey: 'clv12m',
    header: 'CLV (12m)',
    cell: ({ row }) => (
      <span className="font-semibold text-success">
        ${row.original.clv12m.toLocaleString()}
      </span>
    ),
  },
  {
    accessorKey: 'churnProbability',
    header: 'Churn Risk',
    cell: ({ row }) => {
      const risk = row.original.churnProbability;
      return (
        <div className="flex items-center gap-2">
          <div className="w-16 h-2 bg-muted rounded-full overflow-hidden">
            <div
              className={`h-full ${
                risk > 0.75 ? 'bg-danger' : risk > 0.5 ? 'bg-warning' : 'bg-success'
              }`}
              style={{ width: `${risk * 100}%` }}
            />
          </div>
          <span className="text-sm font-medium">{Math.round(risk * 100)}%</span>
        </div>
      );
    },
  },
  {
    accessorKey: 'healthScore',
    header: 'Health',
    cell: ({ row }) => <StatusBadge status={row.original.healthBand} />,
  },
  {
    id: 'actions',
    header: 'Action',
    cell: ({ row }) => (
      <div className="flex gap-1">
        <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
          <Phone className="h-4 w-4 text-primary" />
        </Button>
        <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
          <Mail className="h-4 w-4 text-primary" />
        </Button>
      </div>
    ),
  },
];

export default function ChurnRisk() {
  const navigate = useNavigate();
  const [riskDistribution, setRiskDistribution] = useState<ChurnRiskDistribution[]>([]);
  const [riskTrend, setRiskTrend] = useState<RiskTrend[]>([]);
  const [atRiskCustomers, setAtRiskCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const [distRes, trendRes, atRiskRes] = await Promise.all([
        fetchChurnRiskDistribution(),
        fetchRiskTrend(30),
        fetchHighValueAtRisk(),
      ]);

      if (distRes.success) setRiskDistribution(distRes.data);
      if (trendRes.success) setRiskTrend(trendRes.data);
      if (atRiskRes.success) setAtRiskCustomers(atRiskRes.data);
      setLoading(false);
    }
    loadData();
  }, []);

  const handleCustomerClick = (customer: Customer) => {
    navigate(`/customers?id=${customer.id}`);
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-[60vh]">
          <div className="animate-pulse text-muted-foreground">Loading churn data...</div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ChartContainer
            title="Churn Probability Distribution"
            subtitle="Number of customers by risk level"
          >
            <ChurnRiskHistogram data={riskDistribution} />
          </ChartContainer>

          <ChartContainer
            title="Risk Trend (30 Days)"
            subtitle="Average churn probability and high-risk percentage over time"
          >
            <RiskTrendChart data={riskTrend} />
          </ChartContainer>
        </div>

        {/* High-Value At-Risk Table */}
        <ChartContainer
          title="High-Value At-Risk Customers"
          subtitle="Prioritized list of customers requiring immediate attention"
        >
          <DataTable
            data={atRiskCustomers}
            columns={atRiskColumns}
            searchPlaceholder="Search at-risk customers..."
            pageSize={10}
            onRowClick={handleCustomerClick}
          />
        </ChartContainer>
      </div>
    </DashboardLayout>
  );
}
