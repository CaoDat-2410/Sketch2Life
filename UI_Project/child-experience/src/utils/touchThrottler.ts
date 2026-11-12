export function throttleTouch<T extends (...args: any[]) => void>(func: T, limitMs = 16): T {
  let inThrottle = false
  return function(this: any, ...args: any[]) {
    if (!inThrottle) {
      func.apply(this, args)
      inThrottle = true
      setTimeout(() => (inThrottle = false), limitMs)
    }
  } as T
}
