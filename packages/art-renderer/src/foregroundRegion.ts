export interface NormalizedRegion {
  readonly x: number;
  readonly y: number;
  readonly width: number;
  readonly height: number;
}

/** Selects the most plausible interior drawing component from a paper-removed RGBA canvas. */
export function detectPrimaryForegroundRegion(
  pixels: Uint8ClampedArray,
  width: number,
  height: number,
): NormalizedRegion | null {
  if (width < 2 || height < 2 || pixels.length !== width * height * 4) return null;
  const foreground = new Uint8Array(width * height);
  for (let index = 0; index < foreground.length; index += 1) {
    foreground[index] = pixels[index * 4 + 3] >= 40 ? 1 : 0;
  }
  const expanded = dilate(foreground, width, height, 2);
  const visited = new Uint8Array(expanded.length);
  let best: {minX: number; minY: number; maxX: number; maxY: number; area: number; score: number} | null = null;
  const queue = new Int32Array(expanded.length);

  for (let start = 0; start < expanded.length; start += 1) {
    if (expanded[start] === 0 || visited[start] === 1) continue;
    let head = 0;
    let tail = 0;
    queue[tail++] = start;
    visited[start] = 1;
    let minX = width;
    let minY = height;
    let maxX = 0;
    let maxY = 0;
    let area = 0;
    while (head < tail) {
      const current = queue[head++];
      const x = current % width;
      const y = Math.floor(current / width);
      minX = Math.min(minX, x);
      minY = Math.min(minY, y);
      maxX = Math.max(maxX, x);
      maxY = Math.max(maxY, y);
      area += 1;
      if (x > 0) tail = enqueue(current - 1, expanded, visited, queue, tail);
      if (x + 1 < width) tail = enqueue(current + 1, expanded, visited, queue, tail);
      if (y > 0) tail = enqueue(current - width, expanded, visited, queue, tail);
      if (y + 1 < height) tail = enqueue(current + width, expanded, visited, queue, tail);
    }
    if (area < width * height * 0.001) continue;
    const centerX = (minX + maxX) / 2 / width;
    const centerY = (minY + maxY) / 2 / height;
    const centrality = Math.max(0.2, 1 - Math.hypot(centerX - 0.5, centerY - 0.5));
    const touchesBorder = minX <= 2 || minY <= 2 || maxX >= width - 3 || maxY >= height - 3;
    const spanPenalty = (maxX - minX) / width > 0.9 || (maxY - minY) / height > 0.9 ? 0.08 : 1;
    const score = area * centrality * (touchesBorder ? 0.18 : 1) * spanPenalty;
    if (best === null || score > best.score) best = {minX, minY, maxX, maxY, area, score};
  }
  if (best === null) return null;
  const paddingX = Math.max(3, Math.round((best.maxX - best.minX + 1) * 0.04));
  const paddingY = Math.max(3, Math.round((best.maxY - best.minY + 1) * 0.04));
  const minX = Math.max(0, best.minX - paddingX);
  const minY = Math.max(0, best.minY - paddingY);
  const maxX = Math.min(width - 1, best.maxX + paddingX);
  const maxY = Math.min(height - 1, best.maxY + paddingY);
  const regionWidth = maxX - minX + 1;
  const regionHeight = maxY - minY + 1;
  if (regionWidth * regionHeight > width * height * 0.85) return null;
  return {x: minX / width, y: minY / height, width: regionWidth / width, height: regionHeight / height};
}

function dilate(source: Uint8Array, width: number, height: number, radius: number): Uint8Array {
  const output = new Uint8Array(source);
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      if (source[y * width + x] === 0) continue;
      for (let dy = -radius; dy <= radius; dy += 1) {
        const nextY = y + dy;
        if (nextY < 0 || nextY >= height) continue;
        for (let dx = -radius; dx <= radius; dx += 1) {
          const nextX = x + dx;
          if (nextX >= 0 && nextX < width) output[nextY * width + nextX] = 1;
        }
      }
    }
  }
  return output;
}

function enqueue(
  index: number,
  source: Uint8Array,
  visited: Uint8Array,
  queue: Int32Array,
  tail: number,
): number {
  if (source[index] === 0 || visited[index] === 1) return tail;
  visited[index] = 1;
  queue[tail] = index;
  return tail + 1;
}
