function isRecord(value) {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

export function classifyApiResponseError({ body, statusCode, isJson, responseOk = false }) {
  if (isRecord(body) && isRecord(body.failure)) {
    return {
      message: typeof body.failure.safe_message === 'string'
        ? body.failure.safe_message
        : 'Backend rejected the request.',
      code: typeof body.failure.code === 'string' ? body.failure.code : 'REQUEST_FAILED',
      statusCode,
      retryable: body.failure.retryable === true,
    };
  }

  if (statusCode === 422) {
    if (isJson && isRecord(body) && Array.isArray(body.detail)) {
      return {
        message: 'Thông tin gửi lên chưa hợp lệ. Hãy kiểm tra hồ sơ của bé rồi thử lại.',
        code: 'REQUEST_VALIDATION_FAILED',
        statusCode,
        retryable: false,
      };
    }
    return {
      message: 'Máy chủ trả về lỗi kiểm tra dữ liệu không đúng định dạng. Hãy kiểm tra phiên bản backend và địa chỉ API; không cần nhập lại thông tin của bé.',
      code: 'VALIDATION_RESPONSE_UNRECOGNIZED',
      statusCode,
      retryable: false,
    };
  }

  if ([502, 503, 504].includes(statusCode)) {
    return {
      message: 'Dịch vụ AI tạm thời chưa sẵn sàng. Bạn có thể bỏ qua bước này hoặc thử lại sau.',
      code: 'UPSTREAM_UNAVAILABLE',
      statusCode,
      retryable: true,
    };
  }

  if (!isJson) {
    return {
      message: 'API hoặc proxy trả về nội dung không phải JSON. Hãy kiểm tra địa chỉ API, route và phiên bản backend.',
      code: 'NON_JSON_RESPONSE',
      statusCode,
      retryable: false,
    };
  }

  if (statusCode === 404) {
    return {
      message: 'Backend đang chạy phiên bản chưa có bước này. Hãy cập nhật hoặc khởi động lại backend rồi thử lại.',
      code: 'ENDPOINT_UNAVAILABLE',
      statusCode,
      retryable: false,
    };
  }

  if (statusCode === 401 || statusCode === 403) {
    return {
      message: 'Phiên làm việc chưa được cấp quyền. Hãy đăng nhập lại hoặc kiểm tra cấu hình xác thực.',
      code: 'AUTHORIZATION_ERROR',
      statusCode,
      retryable: false,
    };
  }

  if (statusCode >= 500) {
    return {
      message: 'Backend gặp lỗi khi xử lý. Bạn có thể bỏ qua bước AI hoặc thử lại sau.',
      code: 'BACKEND_ERROR',
      statusCode,
      retryable: false,
    };
  }

  if (responseOk) {
    return {
      message: 'API trả về dữ liệu không đúng định dạng mong đợi. Hãy kiểm tra địa chỉ API và phiên bản backend.',
      code: 'INVALID_RESPONSE',
      statusCode,
      retryable: false,
    };
  }

  return {
    message: 'Backend từ chối yêu cầu. Hãy kiểm tra thông tin hoặc phiên bản API.',
    code: 'BACKEND_REJECTED_REQUEST',
    statusCode,
    retryable: false,
  };
}
