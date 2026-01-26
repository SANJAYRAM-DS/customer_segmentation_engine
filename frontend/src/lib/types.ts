// Customer Intelligence Dashboard Type Definitions

export interface Customer {
  id: string;
  name: string;
  email: string;
  company?: string;
  segment: SegmentType;
  healthScore: number;
  healthBand: HealthBand;
  churnProbability: number;
  clv12m: number;
  investmentPriority: InvestmentPriority;
  lastActivity: string;
  createdAt: string;
  orders: number;
  totalSpend: number;
  sessions: number;
  recency: number;
  flags: CustomerFlag[];
  trends: CustomerTrends;
}

export type SegmentType = 'Loyal' | 'Active' | 'New' | 'At-Risk' | 'Churned';

export type HealthBand = 'Excellent' | 'Good' | 'Watch' | 'Critical';

export type InvestmentPriority = 'High Value - Retain' | 'High Value - Grow' | 'Low Value - Nurture' | 'Low Value - Monitor';

export interface CustomerFlag {
  type: 'risk_increase' | 'inactive' | 'health_drop' | 'high_value';
  message: string;
  severity: 'low' | 'medium' | 'high';
  createdAt: string;
}

export interface CustomerTrends {
  churnProbability: TrendData[];
  healthScore: TrendData[];
  spend: TrendData[];
}

export interface TrendData {
  date: string;
  value: number;
}

// KPI Types
export interface KPISummary {
  totalCustomers: number;
  activeCustomers: number;
  atRiskPercentage: number;
  avgClv: number;
  churnRate: number;
  revenueAtRisk: number;
}

// Segment Distribution
export interface SegmentDistribution {
  segment: SegmentType;
  count: number;
  percentage: number;
  avgClv: number;
  avgChurnRisk: number;
}

// Health Distribution
export interface HealthDistribution {
  band: HealthBand;
  count: number;
  percentage: number;
}

// Segment Migration
export interface SegmentMigration {
  date: string;
  fromSegment: SegmentType;
  toSegment: SegmentType;
  count: number;
}

// Churn Risk Distribution
export interface ChurnRiskDistribution {
  range: string;
  count: number;
  percentage: number;
}

// Risk Trend
export interface RiskTrend {
  date: string;
  avgChurnProbability: number;
  highRiskPercentage: number;
}

// CLV Distribution
export interface CLVDistribution {
  range: string;
  count: number;
}

// Alert
export interface Alert {
  id: string;
  type: 'risk_increase' | 'high_clv_inactive' | 'health_drop' | 'segment_change';
  customerId: string;
  customerName: string;
  message: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  createdAt: string;
  acknowledged: boolean;
}

// Filter State
export interface FilterState {
  segment: SegmentType | 'all';
  healthBand: HealthBand | 'all';
  priority: InvestmentPriority | 'all';
  dateRange: {
    start: string;
    end: string;
  };
  searchQuery: string;
}

// Pagination
export interface PaginationState {
  page: number;
  pageSize: number;
  total: number;
}

// API Response Types
export interface ApiResponse<T> {
  data: T;
  pagination?: PaginationState;
  success: boolean;
  error?: string;
}
