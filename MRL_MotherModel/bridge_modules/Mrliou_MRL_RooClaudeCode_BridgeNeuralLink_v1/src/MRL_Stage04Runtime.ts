// origin_signature: MrLiouWord
// Additive Stage04 entry; legacy BridgeOrchestrator retains its original dependencies.
export { TaskDispatcher } from "./TaskDispatcher.ts"
export { EventAggregator } from "./EventAggregator.ts"
export { MetricsCollector } from "./MetricsCollector.ts"
import type { Socket } from "socket.io-client"
import { TaskDispatcher, type TaskDispatcherOptions } from "./TaskDispatcher.ts"
import { EventAggregator } from "./EventAggregator.ts"
import { MetricsCollector } from "./MetricsCollector.ts"

/** Attach existing modules to the caller-owned Socket.IO connection. */
export function createStage04Runtime(socket: Socket, options: TaskDispatcherOptions = {}) {
  const dispatcher = new TaskDispatcher(options)
  const events = new EventAggregator()
  const metrics = new MetricsCollector()
  dispatcher.setSocket(socket)
  events.setSocket(socket)
  metrics.setSocket(socket)
  return { dispatcher, events, metrics }
}
