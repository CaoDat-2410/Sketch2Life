export interface SubjectCutoutLayers {
  readonly backgroundPixels: Uint8ClampedArray;
  readonly subjectPixels: Uint8ClampedArray;
  readonly sourceRegion: {readonly x: number; readonly y: number; readonly width: number; readonly height: number};
}

export function requireVerifiedCutoutMask(tier: string, hasVerifiedMask: boolean): void {
  if (tier === 'CUTOUT_MICRO_MOTION' && !hasVerifiedMask) {
    throw new Error('SUBJECT_MASK_UNAVAILABLE');
  }
}

export function matchesDerivedMaskProvenance(
  artifact: unknown,
  sourceSha256: string,
  expectedMaskSha256: string,
): boolean {
  if (typeof artifact !== 'object' || artifact === null) return false;
  const value = artifact as {role?: unknown; sourceSha256?: unknown; sha256?: unknown; contentType?: unknown};
  return value.role === 'ORIGINAL_DERIVED_MASK'
    && value.sourceSha256 === sourceSha256
    && value.sha256 === expectedMaskSha256
    && value.contentType === 'image/png';
}

/** Apply an already hash-verified SAM mask while preserving the original source pixels. */
export function createSubjectCutoutLayers(
  sourcePixels: Uint8ClampedArray,
  maskPixels: Uint8ClampedArray,
  width: number,
  height: number,
): SubjectCutoutLayers {
  const expectedLength = width * height * 4;
  if (!Number.isInteger(width) || !Number.isInteger(height) || width < 2 || height < 2
    || width * height > 4_000_000
    || sourcePixels.length !== expectedLength || maskPixels.length !== expectedLength) {
    throw new Error('MASK_DIMENSIONS_INVALID');
  }

  const paper = estimatePaperColor(sourcePixels, width, height);
  const backgroundPixels = new Uint8ClampedArray(sourcePixels);
  const subjectPixels = new Uint8ClampedArray(sourcePixels);
  let minX = width;
  let minY = height;
  let maxX = -1;
  let maxY = -1;
  let foregroundCount = 0;

  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const offset = (y * width + x) * 4;
      const maskAlpha = Math.round((maskPixels[offset] + maskPixels[offset + 1] + maskPixels[offset + 2]) / 3)
        * maskPixels[offset + 3] / 255;
      if (maskAlpha <= 8) {
        subjectPixels[offset + 3] = 0;
        continue;
      }
      foregroundCount += 1;
      minX = Math.min(minX, x);
      minY = Math.min(minY, y);
      maxX = Math.max(maxX, x);
      maxY = Math.max(maxY, y);

      const coverage = Math.min(1, maskAlpha / 255);
      for (let channel = 0; channel < 3; channel += 1) {
        backgroundPixels[offset + channel] = Math.round(
          sourcePixels[offset + channel] * (1 - coverage) + paper[channel] * coverage,
        );
      }
      subjectPixels[offset + 3] = Math.round(sourcePixels[offset + 3] * coverage);
    }
  }

  const areaFraction = foregroundCount / (width * height);
  if (maxX < minX || areaFraction < 0.001 || areaFraction > 0.75) {
    throw new Error('MASK_AREA_INVALID');
  }
  return {
    backgroundPixels,
    subjectPixels,
    sourceRegion: {
      x: minX / width,
      y: minY / height,
      width: (maxX + 1 - minX) / width,
      height: (maxY + 1 - minY) / height,
    },
  };
}

function estimatePaperColor(pixels: Uint8ClampedArray, width: number, height: number): [number, number, number] {
  const corners = [0, width - 1, (height - 1) * width, height * width - 1];
  const samples = corners.map((pixel) => [0, 1, 2].map((channel) => pixels[pixel * 4 + channel]));
  const luminance = samples.map(([red, green, blue]) => (red * 0.2126 + green * 0.7152 + blue * 0.0722));
  const chroma = samples.map((sample) => Math.max(...sample) - Math.min(...sample));
  if (
    Math.min(...luminance) < 155
    || Math.max(...luminance) - Math.min(...luminance) > 48
    || Math.max(...chroma) > 36
  ) throw new Error('MASK_BACKGROUND_PATCH_UNSAFE');
  return [0, 1, 2].map((channel) => Math.round(
    corners.reduce((sum, pixel) => sum + pixels[pixel * 4 + channel], 0) / corners.length,
  )) as [number, number, number];
}
