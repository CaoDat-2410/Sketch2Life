import { sanitizeSessionPin } from '../utils/codeFormatter'

describe('codeFormatter', () => {
  it('strips non-numeric characters and limits to 4 digits', () => {
    expect(sanitizeSessionPin('2a0b2c6d99')).toBe('2026')
  })
})
