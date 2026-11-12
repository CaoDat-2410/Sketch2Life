import { pointsToSvgPath } from '../utils/svgPathBuilder'

describe('svgPathBuilder', () => {
  it('converts point array to svg path data string', () => {
    const pts = [{ x: 10, y: 20 }, { x: 30, y: 40 }]
    expect(pointsToSvgPath(pts)).toBe('M 10 20 L 30 40')
  })
})
