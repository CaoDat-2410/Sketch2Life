import { serializeStrokes, deserializeStrokes } from '../utils/sessionCache'

describe('sessionCache', () => {
  it('serializes and deserializes strokes accurately', () => {
    const original = [{ color: '#1685F8', size: 6, points: [] }]
    const serialized = serializeStrokes(original)
    expect(deserializeStrokes(serialized)).toEqual(original)
  })
})
