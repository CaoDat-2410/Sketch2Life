import { isAccessibleContrast } from '../utils/colorHarmonizer'

describe('colorHarmonizer', () => {
  it('validates high contrast color pairs', () => {
    expect(isAccessibleContrast('#FFFFFF', '#000000')).toBe(true)
  })
})
