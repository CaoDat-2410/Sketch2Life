export interface ApiResponse<T> { data: T; status: number; }
export async function request<T>(url: string): Promise<ApiResponse<T>> {
  const r = await fetch(url);
  return { data: await r.json(), status: r.status };
}
