import { useEffect, useState, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { ChartContainer } from '@/components/dashboard/ChartContainer';
import { DataTable } from '@/components/dashboard/DataTable';
import { StatusBadge, PriorityBadge } from '@/components/dashboard/StatusBadge';
import { HealthGauge } from '@/components/charts/HealthGauge';
import { RiskTrendChart } from '@/components/charts/RiskTrendChart';
import { KPICard } from '@/components/dashboard/KPICard';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { fetchCustomers, fetchCustomerById } from '../lib/api';
import { useDashboardStore } from '@/store/dashboardStore';
import type { Customer } from '../lib/types';
import { ColumnDef } from '@tanstack/react-table';
import {
  DollarSign,
  ShoppingCart,
  Clock,
  Activity,
  ArrowLeft,
  Mail,
  Phone,
  Building,
} from 'lucide-react';

const customerColumns: ColumnDef<Customer>[] = [
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
    accessorKey: 'segment',
    header: 'Segment',
    cell: ({ row }) => <StatusBadge status={row.original.segment} />,
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
  {
    accessorKey: 'recency',
    header: 'Last Activity',
    cell: ({ row }) => (
      <span className="text-muted-foreground">{row.original.recency} days ago</span>
    ),
  },
];

function CustomerProfile({ customer, onClose }: { customer: Customer; onClose: () => void }) {
  // Debug logging
  console.log('Customer trends:', customer.trends);
  console.log('Churn probability trends:', customer.trends?.churnProbability);
  console.log('Health score trends:', customer.trends?.healthScore);

  // Transform trends for the chart
  const trendData = customer.trends?.churnProbability?.map((cp, i) => ({
    date: cp.date,
    avgChurnProbability: cp.value * 100, // Convert to percentage
    highRiskPercentage: customer.trends?.healthScore?.[i]?.value || 0,
  })) || [];

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <Button variant="ghost" size="sm" onClick={onClose}>
              <ArrowLeft className="h-4 w-4 mr-1" />
              Back
            </Button>
            <span>{customer.name}</span>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          {/* Customer Info */}
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <StatusBadge status={customer.segment} />
                <StatusBadge status={customer.healthBand} />
                <PriorityBadge priority={customer.investmentPriority} />
              </div>
              <div className="space-y-1 text-sm text-muted-foreground">
                <p className="flex items-center gap-2">
                  <Mail className="h-4 w-4" />
                  {customer.email}
                </p>
                <p className="flex items-center gap-2">
                  <Building className="h-4 w-4" />
                  {customer.company}
                </p>
              </div>
            </div>
            <HealthGauge score={customer.healthScore} size="md" />
          </div>

          {/* KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KPICard
              title="CLV (12m)"
              value={customer.clv12m}
              icon={DollarSign}
              variant="success"
              format="currency"
            />
            <KPICard
              title="Total Orders"
              value={customer.orders}
              icon={ShoppingCart}
              variant="info"
            />
            <KPICard
              title="Total Sessions"
              value={customer.sessions}
              icon={Activity}
              variant="default"
            />
            <KPICard
              title="Days Since Activity"
              value={customer.recency}
              icon={Clock}
              variant={customer.recency > 30 ? 'warning' : 'success'}
            />
          </div>

          {/* Trend Chart */}
          <ChartContainer
            title="Risk & Health Trends"
            subtitle="90-day trend of churn probability and health score"
          >
            <RiskTrendChart data={trendData.slice(-30)} />
          </ChartContainer>

          {/* Actions */}
          <div className="flex gap-3">
            <Button className="flex-1">
              <Mail className="h-4 w-4 mr-2" />
              Send Email
            </Button>
            <Button variant="outline" className="flex-1">
              <Phone className="h-4 w-4 mr-2" />
              Schedule Call
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default function Customers() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { filters } = useDashboardStore();

  const [customers, setCustomers] = useState<Customer[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const res = await fetchCustomers(filters, { pageSize: 100 });
      if (res.success) setCustomers(res.data);
      setLoading(false);
    }
    loadData();
  }, [filters]);

  // Handle URL-based customer selection
  useEffect(() => {
    const customerId = searchParams.get('id');
    if (customerId) {
      fetchCustomerById(customerId).then((res) => {
        if (res.success && res.data) {
          setSelectedCustomer(res.data);
        }
      });
    }
  }, [searchParams]);

  const handleCustomerClick = (customer: Customer) => {
    setSelectedCustomer(customer);
    setSearchParams({ id: customer.id });
  };

  const handleCloseProfile = () => {
    setSelectedCustomer(null);
    setSearchParams({});
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-[60vh]">
          <div className="animate-pulse text-muted-foreground">Loading customers...</div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <ChartContainer
          title="Customer Directory"
          subtitle={`${customers.length} customers matching current filters`}
        >
          <DataTable
            data={customers}
            columns={customerColumns}
            searchPlaceholder="Search by name, email, or company..."
            pageSize={15}
            onRowClick={handleCustomerClick}
          />
        </ChartContainer>

        {selectedCustomer && (
          <CustomerProfile customer={selectedCustomer} onClose={handleCloseProfile} />
        )}
      </div>
    </DashboardLayout>
  );
}
