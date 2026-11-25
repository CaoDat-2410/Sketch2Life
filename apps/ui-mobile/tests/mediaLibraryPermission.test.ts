import { describe, expect, it } from 'vitest';
import { shouldRequestMediaLibraryPermission } from '../src/parent/presentation/screens/mediaLibraryPermission';

describe('Android system photo picker permission policy', () => {
  it('uses the Android system picker without broad media permission on API 33+', () => {
    expect(shouldRequestMediaLibraryPermission('android', 33)).toBe(false);
    expect(shouldRequestMediaLibraryPermission('android', 34)).toBe(false);
    expect(shouldRequestMediaLibraryPermission('android', '36')).toBe(false);
  });

  it('keeps the legacy permission path on older Android and iOS', () => {
    expect(shouldRequestMediaLibraryPermission('android', 32)).toBe(true);
    expect(shouldRequestMediaLibraryPermission('android', 'unknown')).toBe(true);
    expect(shouldRequestMediaLibraryPermission('ios', '18.0')).toBe(true);
  });
});
