export interface ApiResponseFailure {
  message: string;
  code: string;
  statusCode: number;
  retryable: boolean;
}

export declare function classifyApiResponseError(input: {
  body: unknown;
  statusCode: number;
  isJson: boolean;
  responseOk?: boolean;
}): ApiResponseFailure;
