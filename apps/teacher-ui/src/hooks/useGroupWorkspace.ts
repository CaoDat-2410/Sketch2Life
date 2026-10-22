import { useState, useEffect } from 'react';

export function useGroupWorkspace() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  return { data, loading, refresh: () => {} };
}
