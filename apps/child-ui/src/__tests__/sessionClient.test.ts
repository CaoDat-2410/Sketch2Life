import { verifySessionPin } from '../services/sessionClient'

describe('verifySessionPin', () => {
  it('returns valid for 4-digit code', async () => {
    const res = await verifySessionPin('1234')
    expect(res.valid).toBe(true)
  })
})
