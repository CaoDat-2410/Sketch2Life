import { simplifyPoints } from '../utils/strokeSimplifier'

describe('strokeSimplifier', () => {
  it('returns original points if length <= 2', () => {
    const pts = [{ x: 0, y: 0 }, { x: 10, y: 10 }]
    expect(simplifyPoints(pts)).toEqual(pts)
  })

  it('reduces point count on dense trajectories', () => {
    const pts = [{ x: 0, y: 0 }, { x: 1, y: 1 }, { x: 2, y: 2 }, { x: 10, y: 10 }]
    expect(simplifyPoints(pts).length).toBeLessThan(pts.length)
  })
})
