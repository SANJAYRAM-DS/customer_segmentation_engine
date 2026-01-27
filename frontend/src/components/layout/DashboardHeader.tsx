import { useLocation } from 'react-router-dom';
import { Bell, Download, RefreshCw } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { useDashboardStore } from '../../store/dashboardStore';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import type { SegmentType, HealthBand } from '../../lib/types';

const pageNames: Record<string, string> = {
  '/': 'Executive Overview',
  '/segmentation': 'Segmentation Analysis',
  '/churn-risk': 'Churn & Risk Analysis',
  '/clv-value': 'CLV & Value Analysis',
  '/customer-health': 'Customer Health & Priority',
  '/customers': 'Customer Directory',
  '/alerts': 'Alerts & Monitoring',
};

export function DashboardHeader() {
  const location = useLocation();
  const { filters, setSegmentFilter, setHealthFilter, resetFilters } = useDashboardStore();

  const pageName = pageNames[location.pathname] || 'Dashboard';

  const handleExport = () => {
    // Open print-ready PDF view
    window.open('http://localhost:8000/api/export/pdf', '_blank');
    console.log('Exporting data...');
  };

  const handleRefresh = () => {
    // Placeholder for refresh functionality
    window.location.reload();
  };

  return (
    <header className="sticky top-0 z-30 bg-card border-b border-border px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-foreground">{pageName}</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {new Date().toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Global Filters */}
          <Select
            value={filters.segment}
            onValueChange={(value) => setSegmentFilter(value as SegmentType | 'all')}
          >
            <SelectTrigger className="w-[140px] h-9">
              <SelectValue placeholder="All Segments" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Segments</SelectItem>
              <SelectItem value="Power User">Power User</SelectItem>
              <SelectItem value="Loyal Customer">Loyal Customer</SelectItem>
              <SelectItem value="At Risk">At Risk</SelectItem>
              <SelectItem value="Hibernating">Hibernating</SelectItem>
            </SelectContent>
          </Select>

          <Select
            value={filters.healthBand}
            onValueChange={(value) => setHealthFilter(value as HealthBand | 'all')}
          >
            <SelectTrigger className="w-[130px] h-9">
              <SelectValue placeholder="All Health" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Health</SelectItem>
              <SelectItem value="Excellent">Excellent</SelectItem>
              <SelectItem value="Good">Good</SelectItem>
              <SelectItem value="Watch">Watch</SelectItem>
              <SelectItem value="Critical">Critical</SelectItem>
            </SelectContent>
          </Select>

          {(filters.segment !== 'all' || filters.healthBand !== 'all') && (
            <Button variant="ghost" size="sm" onClick={resetFilters}>
              Clear filters
            </Button>
          )}

          <div className="h-6 w-px bg-border" />

          {/* Action Buttons */}
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="h-4 w-4 mr-2" />
            Export Data
          </Button>

          <Button variant="outline" size="sm" onClick={handleRefresh}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </header>
  );
}
