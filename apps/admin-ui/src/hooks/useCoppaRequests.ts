import { useState, useEffect } from 'react';
import { dataRequestService } from '../services/dataRequestService';

export function useCoppaRequests() {
  const [requests, setRequests] = useState<any[]>([]);
  useEffect(() => { dataRequestService.listRequests().then(setRequests); }, []);
  return { requests };
}
