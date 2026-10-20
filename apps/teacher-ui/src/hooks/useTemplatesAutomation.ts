import { useState, useEffect } from 'react';

export function useTemplatesAutomation() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  return { data, loading, refresh: () => {} };
}
