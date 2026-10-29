import type { Socket } from "socket.io-client"

/**
 * Event aggregator interface.
 */
export interface AggregatedEvent {
	id: string
	source: string
	type: string
	severity: "info" | "warning" | "error" | "critical"
	timestamp: number
	data: Record<string, unknown>
	tags: string[]
}

export type EventFilter = (event: AggregatedEvent) => boolean
export type EventTransformer = (event: AggregatedEvent) => AggregatedEvent
export type EventHandler = (event: AggregatedEvent) => void

/**
 * Event aggregator for collecting, filtering, and distributing events.
 *
 * Features:
 * - Multi-source event collection
 * - Event filtering and routing
 * - Event transformation pipeline
 * - Pub/Sub pattern support
 * - Event history tracking
 */
export class EventAggregator {
	private events: Map<string, AggregatedEvent> = new Map()
	private subscribers: Map<string, EventHandler[]> = new Map()
	private filters: EventFilter[] = []
	private transformers: EventTransformer[] = []

	private eventIdCounter = 0
	private maxHistorySize = 10000
	private socket: Socket | null = null

	constructor(maxHistorySize: number = 10000) {
		this.maxHistorySize = maxHistorySize
	}

	/**
	 * Set the socket for event emission.
	 */
	public setSocket(socket: Socket): void {
		this.socket = socket
	}

	/**
	 * Register an event source and collect events from it.
	 */
	public registerSource(source: string): void {
		if (!this.subscribers.has(source)) {
			this.subscribers.set(source, [])
		}
	}

	/**
	 * Emit an event from a source.
	 */
	public emit(
		source: string,
		type: string,
		severity: AggregatedEvent["severity"],
		data: Record<string, unknown>,
		tags: string[] = [],
	): AggregatedEvent {
		let event: AggregatedEvent = {
			id: this.generateEventId(),
			source,
			type,
			severity,
			timestamp: Date.now(),
			data,
			tags,
		}

		// Apply filters
		for (const filter of this.filters) {
			if (!filter(event)) {
				return event // Event filtered out
			}
		}

		// Apply transformers
		for (const transformer of this.transformers) {
			event = transformer(event)
		}

		// Store event
		this.events.set(event.id, event)
		if (this.events.size > this.maxHistorySize) {
			const firstKey = this.events.keys().next().value
			this.events.delete(firstKey)
		}

		// Distribute to subscribers
		this.distributeEvent(event)

		// Emit via socket
		this.emitSocket(event)

		return event
	}

	/**
	 * Subscribe to events of a specific type.
	 */
	public subscribe(type: string, handler: EventHandler): () => void {
		if (!this.subscribers.has(type)) {
			this.subscribers.set(type, [])
		}

		const handlers = this.subscribers.get(type)!
		handlers.push(handler)

		// Return unsubscribe function
		return () => {
			const index = handlers.indexOf(handler)
			if (index > -1) {
				handlers.splice(index, 1)
			}
		}
	}

	/**
	 * Add an event filter.
	 */
	public addFilter(filter: EventFilter): void {
		this.filters.push(filter)
	}

	/**
	 * Add an event transformer.
	 */
	public addTransformer(transformer: EventTransformer): void {
		this.transformers.push(transformer)
	}

	/**
	 * Get events matching criteria.
	 */
	public query(
		predicate: (event: AggregatedEvent) => boolean,
		limit: number = 100,
	): AggregatedEvent[] {
		const result: AggregatedEvent[] = []

		for (const event of this.events.values()) {
			if (predicate(event)) {
				result.push(event)
				if (result.length >= limit) break
			}
		}

		return result
	}

	/**
	 * Get recent events by type.
	 */
	public getRecent(type?: string, limit: number = 50): AggregatedEvent[] {
		const events = Array.from(this.events.values())
			.filter((e) => !type || e.type === type)
			.sort((a, b) => b.timestamp - a.timestamp)
			.slice(0, limit)

		return events
	}

	/**
	 * Get events by severity.
	 */
	public getBySeverity(severity: AggregatedEvent["severity"], limit: number = 100): AggregatedEvent[] {
		return this.query((e) => e.severity === severity, limit)
	}

	/**
	 * Get events by source.
	 */
	public getBySource(source: string, limit: number = 100): AggregatedEvent[] {
		return this.query((e) => e.source === source, limit)
	}

	/**
	 * Get events by tag.
	 */
	public getByTag(tag: string, limit: number = 100): AggregatedEvent[] {
		return this.query((e) => e.tags.includes(tag), limit)
	}

	/**
	 * Get event statistics.
	 */
	public getStats(): {
		total: number
		byType: Record<string, number>
		bySeverity: Record<string, number>
		bySource: Record<string, number>
	} {
		const stats = {
			total: this.events.size,
			byType: {} as Record<string, number>,
			bySeverity: {} as Record<string, number>,
			bySource: {} as Record<string, number>,
		}

		for (const event of this.events.values()) {
			stats.byType[event.type] = (stats.byType[event.type] ?? 0) + 1
			stats.bySeverity[event.severity] = (stats.bySeverity[event.severity] ?? 0) + 1
			stats.bySource[event.source] = (stats.bySource[event.source] ?? 0) + 1
		}

		return stats
	}

	/**
	 * Clear event history.
	 */
	public clear(): void {
		this.events.clear()
	}

	private distributeEvent(event: AggregatedEvent): void {
		// Global subscribers
		const globalHandlers = this.subscribers.get("*") ?? []
		for (const handler of globalHandlers) {
			try {
				handler(event)
			} catch (error) {
				console.error(`[EventAggregator] Handler error: ${error}`)
			}
		}

		// Type-specific subscribers
		const typeHandlers = this.subscribers.get(event.type) ?? []
		for (const handler of typeHandlers) {
			try {
				handler(event)
			} catch (error) {
				console.error(`[EventAggregator] Handler error: ${error}`)
			}
		}
	}

	private emitSocket(event: AggregatedEvent): void {
		if (this.socket) {
			this.socket.emit("aggregator:event", event)
		}
	}

	private generateEventId(): string {
		return `evt_${Date.now()}_${++this.eventIdCounter}`
	}
}
