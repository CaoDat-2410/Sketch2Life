import { computeTabletScale } from '../utils/screenScaler'

describe('screenScaler', () => {
  it('calculates proper scale for 1024 width tablet', () => {
    expect(computeTabletScale(1024, 768)).toBe(1)
  })
})
