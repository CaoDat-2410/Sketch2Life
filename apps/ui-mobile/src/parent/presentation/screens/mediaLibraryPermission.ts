export function shouldRequestMediaLibraryPermission(platform: string, version: number | string): boolean {
  if (platform !== 'android') return true;

  const apiLevel = typeof version === 'number' ? version : Number.parseInt(version, 10);
  return !Number.isFinite(apiLevel) || apiLevel < 33;
}
