import { MONTESSORI_COLORS } from '../constants/palette'

describe('palette constants', () => {
  it('contains expected primary nature colors', () => {
    expect(MONTESSORI_COLORS.length).toBe(6)
  })
})
