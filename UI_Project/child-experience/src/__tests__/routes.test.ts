import { SCREEN_SEQUENCE } from '../constants/routes'

describe('routes sequence', () => {
  it('advances join to lobby', () => {
    expect(SCREEN_SEQUENCE.join).toBe('lobby')
  })
  it('advances lobby to draw', () => {
    expect(SCREEN_SEQUENCE.lobby).toBe('draw')
  })
})
