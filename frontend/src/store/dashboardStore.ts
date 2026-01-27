import { create } from 'zustand';
import type { FilterState, SegmentType, HealthBand, InvestmentPriority } from '../lib/types';

interface DashboardState {
  // Filter state
  filters: FilterState;
  setSegmentFilter: (segment: SegmentType | 'all') => void;
  setHealthFilter: (health: HealthBand | 'all') => void;
  setPriorityFilter: (priority: InvestmentPriority | 'all') => void;
  setDateRange: (start: string, end: string) => void;
  setSearchQuery: (query: string) => void;
  resetFilters: () => void;

  // UI State
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
  
  // Selected customer for detail view
  selectedCustomerId: string | null;
  setSelectedCustomer: (id: string | null) => void;
}

const defaultFilters: FilterState = {
  segment: 'all',
  healthBand: 'all',
  priority: 'all',
  dateRange: {
    start: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0],
  },
  searchQuery: '',
};

export const useDashboardStore = create<DashboardState>((set) => ({
  filters: defaultFilters,
  
  setSegmentFilter: (segment) =>
    set((state) => ({
      filters: { ...state.filters, segment },
    })),

  setHealthFilter: (healthBand) =>
    set((state) => ({
      filters: { ...state.filters, healthBand },
    })),

  setPriorityFilter: (priority) =>
    set((state) => ({
      filters: { ...state.filters, priority },
    })),

  setDateRange: (start, end) =>
    set((state) => ({
      filters: { ...state.filters, dateRange: { start, end } },
    })),

  setSearchQuery: (searchQuery) =>
    set((state) => ({
      filters: { ...state.filters, searchQuery },
    })),

  resetFilters: () => set({ filters: defaultFilters }),

  sidebarCollapsed: false,
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

  selectedCustomerId: null,
  setSelectedCustomer: (id) => set({ selectedCustomerId: id }),
}));
