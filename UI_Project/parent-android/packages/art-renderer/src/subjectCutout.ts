export interface SubjectCutoutLayers {
  readonly backgroundPixels: Uint8ClampedArray;
  readonly subjectPixels: Uint8ClampedArray;
  readonly sourceRegion: {readonly x: number; readonly y: number; readonly width: number; readonly height: number};
}

const NEIGHBOR_OFFSETS = [
  [-1, -1], [0, -1], [1, -1],
  [-1, 0],            [1, 0],
  [-1, 1],  [0, 1],    [1, 1],
] as const;
// Paper may sit beyond a dense crayon outline; keep the search local and bounded.
const MAX_LOCAL_BACKGROUND_RADIUS = 12;

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

/** Apply an already hash-verified SAM mask and inpaint only its covered source pixels. */
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

  const pixelCount = width * height;
  const insideMask = new Uint8Array(pixelCount);
  let minX = width;
  let minY = height;
  let maxX = -1;
  let maxY = -1;
  let foregroundCount = 0;
  let paperRedTotal = 0;
  let paperGreenTotal = 0;
  let paperBlueTotal = 0;
  let paperPixelCount = 0;

  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const offset = (y * width + x) * 4;
      const maskAlpha = Math.round((maskPixels[offset] + maskPixels[offset + 1] + maskPixels[offset + 2]) / 3)
        * maskPixels[offset + 3] / 255;
      if (maskAlpha <= 8) {
        // Collect only credible paper from outside the verified mask; this is used solely when
        // pigment hides every nearby donor around a mask component.
        if (sourcePixels[offset + 3] > 8) {
          const red = sourcePixels[offset];
          const green = sourcePixels[offset + 1];
          const blue = sourcePixels[offset + 2];
          const luminance = red * 0.2126 + green * 0.7152 + blue * 0.0722;
          const chroma = Math.max(red, green, blue) - Math.min(red, green, blue);
          if (luminance >= 120 && chroma <= 80) {
            paperRedTotal += red;
            paperGreenTotal += green;
            paperBlueTotal += blue;
            paperPixelCount += 1;
          }
        }
        continue;
      }
      insideMask[y * width + x] = 1;
      foregroundCount += 1;
      minX = Math.min(minX, x);
      minY = Math.min(minY, y);
      maxX = Math.max(maxX, x);
      maxY = Math.max(maxY, y);

    }
  }

  const areaFraction = foregroundCount / pixelCount;
  if (maxX < minX || areaFraction < 0.001 || areaFraction > 0.75) {
    throw new Error('MASK_AREA_INVALID');
  }

  const backgroundPixels = new Uint8ClampedArray(sourcePixels);
  const subjectPixels = new Uint8ClampedArray(sourcePixels);
  const sameImagePaperEstimate: [number, number, number] | null = paperPixelCount >= 8
    ? [
      Math.round(paperRedTotal / paperPixelCount),
      Math.round(paperGreenTotal / paperPixelCount),
      Math.round(paperBlueTotal / paperPixelCount),
    ]
    : null;
  inpaintMaskRegion(
    sourcePixels,
    backgroundPixels,
    insideMask,
    width,
    height,
    foregroundCount,
    sameImagePaperEstimate,
  );
  for (let pixel = 0; pixel < pixelCount; pixel += 1) {
    const offset = pixel * 4;
    if (insideMask[pixel] === 0) {
      subjectPixels[offset + 3] = 0;
      continue;
    }
    const maskAlpha = Math.round((maskPixels[offset] + maskPixels[offset + 1] + maskPixels[offset + 2]) / 3)
      * maskPixels[offset + 3] / 255;
    const coverage = Math.min(1, maskAlpha / 255);
    for (let channel = 0; channel < 3; channel += 1) {
      backgroundPixels[offset + channel] = Math.round(
        sourcePixels[offset + channel] * (1 - coverage) + backgroundPixels[offset + channel] * coverage,
      );
    }
    subjectPixels[offset + 3] = Math.round(sourcePixels[offset + 3] * coverage);
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

function inpaintMaskRegion(
  source: Uint8ClampedArray,
  output: Uint8ClampedArray,
  insideMask: Uint8Array,
  width: number,
  height: number,
  foregroundCount: number,
  sameImagePaperEstimate: readonly [number, number, number] | null,
): void {
  const known = new Uint8Array(insideMask.length);
  const queue = new Uint32Array(foregroundCount);
  for (let pixel = 0; pixel < insideMask.length; pixel += 1) {
    if (insideMask[pixel] === 0) known[pixel] = 1;
  }

  let queued = 0;
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const pixel = y * width + x;
      if (insideMask[pixel] === 0 || !touchesUnmaskedPixel(insideMask, x, y, width, height)) continue;
      const estimate = sampleLocalBackground(source, insideMask, x, y, width, height) ?? sameImagePaperEstimate;
      if (estimate === null) continue;
      writeRgb(output, pixel, estimate);
      known[pixel] = 1;
      queue[queued] = pixel;
      queued += 1;
    }
  }

  let cursor = 0;
  while (cursor < queued) {
    const pixel = queue[cursor];
    cursor += 1;
    const x = pixel % width;
    const y = Math.floor(pixel / width);
    for (const [dx, dy] of NEIGHBOR_OFFSETS) {
      const nextX = x + dx;
      const nextY = y + dy;
      if (nextX < 0 || nextX >= width || nextY < 0 || nextY >= height) continue;
      const nextPixel = nextY * width + nextX;
      if (insideMask[nextPixel] === 0 || known[nextPixel] === 1) continue;
      const estimate = meanKnownNeighbors(output, known, nextX, nextY, width, height);
      if (estimate === null) continue;
      writeRgb(output, nextPixel, estimate);
      known[nextPixel] = 1;
      queue[queued] = nextPixel;
      queued += 1;
    }
  }

  if (queued !== foregroundCount) throw new Error('MASK_BACKGROUND_RECONSTRUCTION_FAILED');
}

function touchesUnmaskedPixel(mask: Uint8Array, x: number, y: number, width: number, height: number): boolean {
  for (const [dx, dy] of NEIGHBOR_OFFSETS) {
    const nextX = x + dx;
    const nextY = y + dy;
    if (nextX < 0 || nextX >= width || nextY < 0 || nextY >= height
      || mask[nextY * width + nextX] === 0) return true;
  }
  return false;
}

function sampleLocalBackground(
  pixels: Uint8ClampedArray,
  mask: Uint8Array,
  x: number,
  y: number,
  width: number,
  height: number,
): [number, number, number] | null {
  // Search a small expanding neighborhood for plausible paper, never use saturated
  // drawing pigment as a donor. If the mask is fully enclosed by pigment, reject it.
  for (let radius = 1; radius <= MAX_LOCAL_BACKGROUND_RADIUS; radius += 1) {
    let redTotal = 0;
    let greenTotal = 0;
    let blueTotal = 0;
    let count = 0;
    for (let dy = -radius; dy <= radius; dy += 1) {
      for (let dx = -radius; dx <= radius; dx += 1) {
        if (Math.max(Math.abs(dx), Math.abs(dy)) !== radius) continue;
        const nextX = x + dx;
        const nextY = y + dy;
        if (nextX < 0 || nextX >= width || nextY < 0 || nextY >= height) continue;
        const nextPixel = nextY * width + nextX;
        if (mask[nextPixel] !== 0) continue;
        const offset = nextPixel * 4;
        if (pixels[offset + 3] <= 8) continue;
        const red = pixels[offset];
        const green = pixels[offset + 1];
        const blue = pixels[offset + 2];
        const luminance = red * 0.2126 + green * 0.7152 + blue * 0.0722;
        const chroma = Math.max(red, green, blue) - Math.min(red, green, blue);
        if (luminance < 120 || chroma > 80) continue;
        redTotal += red;
        greenTotal += green;
        blueTotal += blue;
        count += 1;
      }
    }
    if (count >= 2) {
      return [
        Math.round(redTotal / count),
        Math.round(greenTotal / count),
        Math.round(blueTotal / count),
      ];
    }
  }
  return null;
}

function meanKnownNeighbors(
  pixels: Uint8ClampedArray,
  known: Uint8Array,
  x: number,
  y: number,
  width: number,
  height: number,
): [number, number, number] | null {
  let red = 0;
  let green = 0;
  let blue = 0;
  let count = 0;
  for (const [dx, dy] of NEIGHBOR_OFFSETS) {
    const nextX = x + dx;
    const nextY = y + dy;
    if (nextX < 0 || nextX >= width || nextY < 0 || nextY >= height) continue;
    const nextPixel = nextY * width + nextX;
    if (known[nextPixel] === 0) continue;
    const offset = nextPixel * 4;
    red += pixels[offset];
    green += pixels[offset + 1];
    blue += pixels[offset + 2];
    count += 1;
  }
  return count === 0 ? null : [Math.round(red / count), Math.round(green / count), Math.round(blue / count)];
}

function writeRgb(pixels: Uint8ClampedArray, pixel: number, rgb: readonly [number, number, number]): void {
  const offset = pixel * 4;
  pixels[offset] = rgb[0];
  pixels[offset + 1] = rgb[1];
  pixels[offset + 2] = rgb[2];
}
