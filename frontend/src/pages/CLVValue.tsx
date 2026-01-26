import { useEffect, useState } from 'react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { ChartContainer } from '@/components/dashboard/ChartContainer';
import { CLVDistributionChart } from '@/components/charts/CLVDistributionChart';
import { CLVTrendChart } from '@/components/charts/CLVTrendChart';
import { SegmentBarChart } from '@/components/charts/SegmentBarChart';
import { KPICard } from '@/components/dashboard/KPICard';
import { DollarSign, TrendingUp, Users, Award } from 'lucide-react';
import {
  fetchCLVDistribution,
  fetchCLVTrend,
  fetchSegmentDistribution,
  fetchKPISummary,
} from '../lib/api';
import type { CLVDistribution, SegmentDistribution, KPISummary } from '../lib/types';

export default function CLVValue() {
  const [clvDistribution, setCLVDistribution] = useState<CLVDistribution[]>([]);
  const [clvTrend, setCLVTrend] = useState<{ month: string; avgClv: number; totalClv: number }[]>([]);
  const [segmentData, setSegmentData] = useState<SegmentDistribution[]>([]);
  const [kpi, setKPI] = useState<KPISummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const [distRes, trendRes, segmentRes, kpiRes] = await Promise.all([
        fetchCLVDistribution(),
        fetchCLVTrend(),
        fetchSegmentDistribution(),
        fetchKPISummary(),
      ]);

      if (distRes.success) setCLVDistribution(distRes.data);
      if (trendRes.success) setCLVTrend(trendRes.data);
      if (segmentRes.success) setSegmentData(segmentRes.data);
      if (kpiRes.success) setKPI(kpiRes.data);
      setLoading(false);
    }
    loadData();
  }, []);

  if (loading || !kpi) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-[60vh]">
          <div className="animate-pulse text-muted-foreground">Loading CLV data...</div>
        </div>
      </DashboardLayout>
    );
  }

  // Calculate additional metrics
  const totalCLV = segmentData.reduce((sum, s) => sum + s.avgClv * s.count, 0);
  const topSegment = [...segmentData].sort((a, b) => b.avgClv - a.avgClv)[0];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <KPICard
            title="Total CLV"
            value={totalCLV}
            icon={DollarSign}
            variant="success"
            format="currency"
            change={{ value: 18, isPositive: true }}
          />
          <KPICard
            title="Avg CLV per Customer"
            value={kpi.avgClv}
            icon={TrendingUp}
            variant="info"
            format="currency"
            change={{ value: 12, isPositive: true }}
          />
          <KPICard
            title="Total Customers"
            value={kpi.totalCustomers}
            icon={Users}
            variant="default"
          />
          <KPICard
            title="Highest CLV Segment"
            value={topSegment?.segment || 'N/A'}
            icon={Award}
            variant="success"
          />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ChartContainer
            title="CLV Distribution"
            subtitle="Number of customers by CLV range"
          >
            <CLVDistributionChart data={clvDistribution} />
          </ChartContainer>

          <ChartContainer
            title="Average CLV by Segment"
            subtitle="Compare customer value across segments"
          >
            <SegmentBarChart data={segmentData} dataKey="avgClv" />
          </ChartContainer>
        </div>

        {/* CLV Trend */}
        <ChartContainer
          title="CLV Trend Over Time"
          subtitle="Monthly average CLV for the past 12 months"
        >
          <CLVTrendChart data={clvTrend} />
        </ChartContainer>
      </div>
    </DashboardLayout>
  );
}
