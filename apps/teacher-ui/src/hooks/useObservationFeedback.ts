import { useState } from 'react';

export function useObservationFeedback() {
  const [data] = useState<any>(null);
  const [loading] = useState(false);
  return { data, loading, refresh: () => {} };
}
