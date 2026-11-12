export function sanitizeSessionPin(raw: string): string {
  return raw.replace(/[^0-9]/g, '').slice(0, 4)
}
