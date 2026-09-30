import { manipulateAsync, SaveFormat } from 'expo-image-manipulator';
import type { ImagePickerAsset } from 'expo-image-picker';
import * as FileSystem from 'expo-file-system';
import {
  MAX_IMAGE_BYTES,
} from '../demo/api';
import {
  inspectImagePickerMetadata,
  MAX_SOURCE_IMAGE_BYTES,
  sourceImageExceedsDecodeBudget,
  targetImageDimensions,
  type SourceImageMimeType,
  type SupportedImageMimeType,
} from './workflowSafety';

export type ImageNormalizationPolicy =
  | 'IDENTITY_V1'
  | 'EXPO_IMAGE_MANIPULATOR_JPEG_V1'
  | 'EXPO_IMAGE_MANIPULATOR_PNG_V1';

export type PreparedImage = {
  /** Keep the adult-selected source for preview and the session's immutable original. */
  uri: string;
  uploadUri?: string;
  fileName: string;
  mimeType: string;
  fileSize: number;
  sourceMimeType: SourceImageMimeType | 'application/octet-stream';
  normalizationPolicy: ImageNormalizationPolicy;
};

export class ImageIntakeError extends Error {
  constructor(readonly code: string) {
    super(code);
    this.name = 'ImageIntakeError';
  }
}

const OUTPUT_LIMITS = { maxPixels: 4_000_000, maxEdge: 4_096 } as const;

/**
 * Bounds picker metadata before decoding. Only supported non-JPEG/PNG inputs and JPEG/PNG
 * that exceed backend limits are decoded/re-encoded; small JPEG/PNG remain byte-identical.
 */
export async function preparePickedImage(asset: ImagePickerAsset): Promise<PreparedImage> {
  if (asset.type && asset.type !== 'image') throw new ImageIntakeError('IMAGE_ANIMATED_UNSUPPORTED');

  const metadata = inspectImagePickerMetadata(asset.fileName, asset.mimeType);
  if (metadata.unsupportedAnimation) throw new ImageIntakeError('IMAGE_ANIMATED_UNSUPPORTED');
  if (metadata.metadataConflict) throw new ImageIntakeError('IMAGE_METADATA_CONFLICT');

  let sourceBytes = asset.fileSize;
  try {
    if (sourceBytes === undefined || !Number.isFinite(sourceBytes)) {
      const info = await FileSystem.getInfoAsync(asset.uri, { size: true });
      sourceBytes = info.exists ? info.size : undefined;
    }
  } catch {
    throw new ImageIntakeError('IMAGE_ACCESS_UNAVAILABLE');
  }
  if (sourceBytes === undefined || sourceBytes < 1) {
    throw new ImageIntakeError('IMAGE_ACCESS_UNAVAILABLE');
  }
  if (sourceBytes > MAX_SOURCE_IMAGE_BYTES) throw new ImageIntakeError('IMAGE_TOO_LARGE');

  const sourceFormat = metadata.format;
  const sourceMimeType = sourceFormat ?? 'application/octet-stream';
  const knownDimensions = Number.isFinite(asset.width) && Number.isFinite(asset.height)
    && asset.width >= 1 && asset.height >= 1;
  const isSupportedOriginal = sourceFormat === 'image/jpeg' || sourceFormat === 'image/png'
    || sourceFormat === 'image/webp' || sourceFormat === 'image/heic' || sourceFormat === 'image/heif';
  const needsTranscode = sourceFormat === 'image/webp' || sourceFormat === 'image/heic'
    || sourceFormat === 'image/heif';
  const withinOutputBounds = knownDimensions
    && targetImageDimensions(asset.width, asset.height, OUTPUT_LIMITS.maxPixels, OUTPUT_LIMITS.maxEdge)
      ?.width === asset.width
    && targetImageDimensions(asset.width, asset.height, OUTPUT_LIMITS.maxPixels, OUTPUT_LIMITS.maxEdge)
      ?.height === asset.height;

  // Unknown extensions/MIME are passed through only within the byte limit. The backend
  // identifies their true container from the bounded bytes and rejects unsupported formats.
  // Never ask a native decoder to guess at an unknown format.
  if (!isSupportedOriginal) {
    if (sourceBytes > MAX_IMAGE_BYTES) throw new ImageIntakeError('IMAGE_UNSUPPORTED_FORMAT');
    return {
      uri: asset.uri,
      fileName: 'drawing.upload',
      mimeType: 'application/octet-stream',
      fileSize: sourceBytes,
      sourceMimeType,
      normalizationPolicy: 'IDENTITY_V1',
    };
  }

  if (!needsTranscode && sourceBytes <= MAX_IMAGE_BYTES && withinOutputBounds) {
    return {
      uri: asset.uri,
      fileName: sourceFormat === 'image/png' ? 'drawing.png' : 'drawing.jpg',
      mimeType: sourceFormat as SupportedImageMimeType,
      fileSize: sourceBytes,
      sourceMimeType,
      normalizationPolicy: 'IDENTITY_V1',
    };
  }

  if (!knownDimensions) throw new ImageIntakeError('IMAGE_DIMENSIONS_UNAVAILABLE');
  if (sourceImageExceedsDecodeBudget(asset.width, asset.height)) {
    throw new ImageIntakeError('IMAGE_DIMENSIONS_TOO_LARGE');
  }

  const target = targetImageDimensions(
    asset.width,
    asset.height,
    OUTPUT_LIMITS.maxPixels,
    OUTPUT_LIMITS.maxEdge,
  );
  if (!target) throw new ImageIntakeError('IMAGE_DIMENSIONS_UNAVAILABLE');

  const preserveAlpha = sourceFormat === 'image/png' || sourceFormat === 'image/webp'
    || (!sourceFormat && metadata.metadataMissing);
  const outputMimeType: SupportedImageMimeType = preserveAlpha ? 'image/png' : 'image/jpeg';
  const outputFormat = preserveAlpha ? SaveFormat.PNG : SaveFormat.JPEG;
  const normalizationPolicy: ImageNormalizationPolicy = preserveAlpha
    ? 'EXPO_IMAGE_MANIPULATOR_PNG_V1'
    : 'EXPO_IMAGE_MANIPULATOR_JPEG_V1';

  try {
    const actions = target.width !== asset.width || target.height !== asset.height
      ? [{ resize: { width: target.width, height: target.height } }]
      : [];
    const normalized = await manipulateAsync(asset.uri, actions, {
      format: outputFormat,
      ...(outputMimeType === 'image/jpeg' ? { compress: 0.92 } : {}),
    });
    if (
      !Number.isFinite(normalized.width)
      || !Number.isFinite(normalized.height)
      || normalized.width < 1
      || normalized.height < 1
      || normalized.width * normalized.height > OUTPUT_LIMITS.maxPixels
      || Math.max(normalized.width, normalized.height) > OUTPUT_LIMITS.maxEdge
    ) {
      throw new ImageIntakeError('IMAGE_NORMALIZATION_DIMENSIONS_FAILED');
    }
    let outputBytes: number | null;
    try {
      const info = await FileSystem.getInfoAsync(normalized.uri, { size: true });
      outputBytes = info.exists ? info.size : null;
    } catch {
      throw new ImageIntakeError('IMAGE_NORMALIZATION_FAILED');
    }
    if (outputBytes === null || outputBytes < 1) {
      throw new ImageIntakeError('IMAGE_NORMALIZATION_FAILED');
    }
    if (outputBytes > MAX_IMAGE_BYTES) throw new ImageIntakeError('IMAGE_NORMALIZED_TOO_LARGE');

    return {
      uri: asset.uri,
      uploadUri: normalized.uri,
      fileName: outputMimeType === 'image/png' ? 'drawing.png' : 'drawing.jpg',
      mimeType: outputMimeType,
      fileSize: sourceBytes,
      sourceMimeType,
      normalizationPolicy,
    };
  } catch (error) {
    if (error instanceof ImageIntakeError) throw error;
    throw new ImageIntakeError('IMAGE_NORMALIZATION_FAILED');
  }
}

export function imageIntakeErrorMessage(code: string): string {
  const messages: Record<string, string> = {
    IMAGE_ANIMATED_UNSUPPORTED: 'Ảnh động/Live Photo chưa được hỗ trợ. Hãy chọn một khung hình tĩnh rồi thử lại.',
    IMAGE_METADATA_CONFLICT: 'Thông tin định dạng của ảnh không khớp. Hãy xuất ảnh thành PNG hoặc JPEG rồi chọn lại.',
    IMAGE_TOO_LARGE: 'Ảnh gốc vượt giới hạn 15 MB. Hãy chọn hoặc xuất ảnh nhỏ hơn.',
    IMAGE_DIMENSIONS_TOO_LARGE: 'Kích thước ảnh quá lớn để xử lý an toàn trên thiết bị. Hãy giảm kích thước ảnh rồi thử lại.',
    IMAGE_DIMENSIONS_UNAVAILABLE: 'Không xác minh được kích thước ảnh để chuyển đổi an toàn. Hãy xuất ảnh thành PNG hoặc JPEG rồi thử lại.',
    IMAGE_ACCESS_UNAVAILABLE: 'Không đọc được ảnh đã chọn. Có thể quyền truy cập tệp đã hết hạn; hãy chọn lại ảnh.',
    IMAGE_UNSUPPORTED_FORMAT: 'Định dạng ảnh chưa được hỗ trợ. Hãy xuất ảnh tĩnh thành PNG hoặc JPEG rồi thử lại.',
    IMAGE_NORMALIZATION_FAILED: 'Không thể chuyển ảnh sang định dạng dùng được. Ảnh gốc vẫn được giữ; hãy xuất PNG/JPEG hoặc chọn ảnh khác.',
    IMAGE_NORMALIZATION_DIMENSIONS_FAILED: 'Ảnh sau chuyển đổi vẫn vượt giới hạn kích thước. Hãy giảm kích thước rồi thử lại.',
    IMAGE_NORMALIZED_TOO_LARGE: 'Ảnh sau chuyển đổi vẫn vượt 5 MB. Hãy xuất ảnh nhỏ hơn; ảnh gốc không bị thay đổi.',
  };
  return messages[code] ?? 'Không xử lý được ảnh đã chọn. Ảnh trước đó vẫn được giữ nguyên.';
}
