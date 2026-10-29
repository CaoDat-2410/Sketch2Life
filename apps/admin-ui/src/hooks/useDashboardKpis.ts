import { useState, useEffect } from 'react';
import { dashboardService } from '../services/dashboardService';

export function useDashboardKpis() {
  const [kpis, setKpis] = useState<any>(null);
  useEffect(() => { dashboardService.getKpis().then(setKpis); }, []);
  return { kpis, isLoading: !kpis };
}
