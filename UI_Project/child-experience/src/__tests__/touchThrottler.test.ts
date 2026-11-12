import { throttleTouch } from '../utils/touchThrottler'

describe('touchThrottler', () => {
  it('throttles rapid sequential invocations', () => {
    let count = 0
    const throttled = throttleTouch(() => count++, 50)
    throttled()
    throttled()
    expect(count).toBe(1)
  })
})
