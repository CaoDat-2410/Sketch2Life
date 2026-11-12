export interface ApiClientPort {
  get<TResponse>(path: string): Promise<TResponse>;
  post<TRequest, TResponse>(path: string, body: TRequest): Promise<TResponse>;
}

export interface AppDependencies {
  apiClient: ApiClientPort;
}
