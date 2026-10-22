import { useState, useEffect } from 'react';

export function useSessionLobby() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  return { data, loading, refresh: () => {} };
}
