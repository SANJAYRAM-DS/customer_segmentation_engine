import { cn } from '@/lib/utils';
import type { HealthBand, SegmentType, InvestmentPriority } from '@/lib/types';

interface StatusBadgeProps {
  status: HealthBand | SegmentType | 'low' | 'medium' | 'high' | 'critical';
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const getStyles = () => {
    switch (status) {
      case 'Excellent':
      case 'Loyal':
        return 'bg-success/10 text-success border-success/20';
      case 'Good':
      case 'Active':
        return 'bg-info/10 text-info border-info/20';
      case 'New':
        return 'bg-chart-5/10 text-chart-5 border-chart-5/20';
      case 'Watch':
      case 'At-Risk':
      case 'medium':
        return 'bg-warning/10 text-warning border-warning/20';
      case 'Critical':
      case 'Churned':
      case 'critical':
      case 'high':
        return 'bg-danger/10 text-danger border-danger/20';
      case 'low':
        return 'bg-muted text-muted-foreground border-muted';
      default:
        return 'bg-muted text-muted-foreground border-muted';
    }
  };

  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border',
        getStyles(),
        className
      )}
    >
      {status}
    </span>
  );
}

interface PriorityBadgeProps {
  priority: InvestmentPriority;
  className?: string;
}

export function PriorityBadge({ priority, className }: PriorityBadgeProps) {
  const getStyles = () => {
    switch (priority) {
      case 'High Value - Retain':
        return 'bg-danger/10 text-danger border-danger/20';
      case 'High Value - Grow':
        return 'bg-success/10 text-success border-success/20';
      case 'Low Value - Nurture':
        return 'bg-info/10 text-info border-info/20';
      case 'Low Value - Monitor':
        return 'bg-muted text-muted-foreground border-muted';
      default:
        return 'bg-muted text-muted-foreground border-muted';
    }
  };

  const getShortLabel = () => {
    switch (priority) {
      case 'High Value - Retain':
        return 'Retain';
      case 'High Value - Grow':
        return 'Grow';
      case 'Low Value - Nurture':
        return 'Nurture';
      case 'Low Value - Monitor':
        return 'Monitor';
      default:
        return priority;
    }
  };

  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border',
        getStyles(),
        className
      )}
    >
      {getShortLabel()}
    </span>
  );
}
