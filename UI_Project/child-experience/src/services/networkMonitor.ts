export class NetworkMonitor {
  private static listeners: ((online: boolean) => void)[] = []

  static subscribe(fn: (online: boolean) => void) {
    this.listeners.push(fn)
    return () => {
      this.listeners = this.listeners.filter((l) => l !== fn)
    }
  }
}
