import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { DashboardLayout } from '../components/layout/DashboardLayout';
import { ChartContainer } from '../components/dashboard/ChartContainer';
import { KPICard } from '../components/dashboard/KPICard';
import { Button } from '../components/ui/button';
import { fetchAlerts, acknowledgeAlert } from '../lib/api';
import type { Alert } from '../lib/types';
import { cn } from '../lib/utils';
import {
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Activity,
  Check,
  Bell,
  BellOff,
  Clock,
} from 'lucide-react';

export default function Alerts() {
  const navigate = useNavigate();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'unacknowledged'>('unacknowledged');

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const res = await fetchAlerts();
      if (res.success) setAlerts(res.data);
      setLoading(false);
    }
    loadData();
  }, []);

  const handleAcknowledge = async (alertId: string) => {
    await acknowledgeAlert(alertId);
    setAlerts((prev) =>
      prev.map((a) => (a.id === alertId ? { ...a, acknowledged: true } : a))
    );
  };

  const handleViewCustomer = (customerId: string) => {
    navigate(`/customers?id=${customerId}`);
  };

  const filteredAlerts = filter === 'all'
    ? alerts
    : alerts.filter(a => !a.acknowledged);

  const criticalCount = alerts.filter(a => a.severity === 'critical' && !a.acknowledged).length;
  const highCount = alerts.filter(a => a.severity === 'high' && !a.acknowledged).length;
  // Pending review = all unacknowledged (active) alerts
  const unacknowledgedCount = alerts.filter(a => !a.acknowledged).length;

  const getAlertIcon = (type: Alert['type']) => {
    switch (type) {
      case 'risk_increase':
        return TrendingUp;
      case 'high_clv_inactive':
        return Clock;
      case 'health_drop':
        return TrendingDown;
      default:
        return Activity;
    }
  };

  const getSeverityStyles = (severity: Alert['severity']) => {
    switch (severity) {
      case 'critical':
        return 'border-l-danger bg-danger/5';
      case 'high':
        return 'border-l-warning bg-warning/5';
      case 'medium':
        return 'border-l-info bg-info/5';
      default:
        return 'border-l-muted bg-muted/5';
    }
  };

  const getSeverityBadge = (severity: Alert['severity']) => {
    const styles = {
      critical: 'bg-danger/10 text-danger',
      high: 'bg-warning/10 text-warning',
      medium: 'bg-info/10 text-info',
      low: 'bg-muted text-muted-foreground',
    };
    return (
      <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium', styles[severity])}>
        {severity.charAt(0).toUpperCase() + severity.slice(1)}
      </span>
    );
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-[60vh]">
          <div className="animate-pulse text-muted-foreground">Loading alerts...</div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <KPICard
            title="Critical Alerts"
            value={criticalCount}
            icon={AlertTriangle}
            variant="danger"
          />
          <KPICard
            title="High Priority"
            value={highCount}
            icon={Bell}
            variant="warning"
          />
          <KPICard
            title="Pending Review"
            value={unacknowledgedCount}
            icon={Activity}
            variant="info"
          />
        </div>

        {/* Alert List */}
        <ChartContainer
          title="Alert Feed"
          subtitle="Real-time notifications requiring attention"
          action={
            <div className="flex gap-2">
              <Button
                variant={filter === 'unacknowledged' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilter('unacknowledged')}
              >
                <Bell className="h-4 w-4 mr-1" />
                Active
              </Button>
              <Button
                variant={filter === 'all' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilter('all')}
              >
                <BellOff className="h-4 w-4 mr-1" />
                All
              </Button>
            </div>
          }
        >
          <div className="space-y-3">
            {filteredAlerts.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <Bell className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>No alerts to display</p>
              </div>
            ) : (
              filteredAlerts.map((alert) => {
                const Icon = getAlertIcon(alert.type);
                return (
                  <div
                    key={alert.id}
                    className={cn(
                      'p-4 rounded-lg border-l-4 border transition-all',
                      getSeverityStyles(alert.severity),
                      alert.acknowledged && 'opacity-60'
                    )}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3">
                        <div
                          className={cn(
                            'p-2 rounded-lg',
                            alert.severity === 'critical'
                              ? 'bg-danger/10 text-danger'
                              : alert.severity === 'high'
                                ? 'bg-warning/10 text-warning'
                                : 'bg-info/10 text-info'
                          )}
                        >
                          <Icon className="h-5 w-5" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <button
                              onClick={() => handleViewCustomer(alert.customerId)}
                              className="font-medium text-foreground hover:text-primary transition-colors"
                            >
                              {alert.customerName}
                            </button>
                            {getSeverityBadge(alert.severity)}
                          </div>
                          <p className="text-sm text-muted-foreground">{alert.message}</p>
                          <p className="text-xs text-muted-foreground mt-1">
                            {new Date(alert.createdAt).toLocaleString()}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {!alert.acknowledged && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleAcknowledge(alert.id)}
                          >
                            <Check className="h-4 w-4 mr-1" />
                            Acknowledge
                          </Button>
                        )}
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleViewCustomer(alert.customerId)}
                        >
                          View Customer
                        </Button>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </ChartContainer>
      </div>
    </DashboardLayout>
  );
}
