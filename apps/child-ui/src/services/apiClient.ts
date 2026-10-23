export interface ApiResponse<T> {
  data: T
  status: number
  success: boolean
}

export async function childApiFetch<T>(endpoint: string, options?: RequestInit): Promise<ApiResponse<T>> {
  // Stubbed client with graceful local fallback
  return {
    data: {} as T,
    status: 200,
    success: true,
  }
}
