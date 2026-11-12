import { DrawingStorage } from '../services/drawingStorage'

describe('DrawingStorage', () => {
  it('saves and retrieves cached strokes', () => {
    DrawingStorage.save({ sessionId: '123', childName: 'Mây', strokes: [], timestamp: 100 })
    expect(DrawingStorage.get()?.childName).toBe('Mây')
  })
})
