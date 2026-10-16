export interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}

export async function request<T>(endpoint: string, options?: RequestInit): Promise<ApiResponse<T>> {
  const res = await fetch(endpoint, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options?.headers },
  });
  return { data: await res.json(), status: res.status };
}
