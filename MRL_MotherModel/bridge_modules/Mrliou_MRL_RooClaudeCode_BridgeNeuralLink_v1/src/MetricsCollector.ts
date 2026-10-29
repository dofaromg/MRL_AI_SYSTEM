import type { Socket } from "socket.io-client"

/**
 * Metric data point.
 */
export interface MetricDataPoint {
	timestamp: number
	value: number
}

/**
 * Metric counter.
 */
export interface MetricCounter {
	name: string
	value: number
	unit: string
	tags: Record<string, string>
	lastUpdated: number
}

/**
 * Metric histogram for latency tracking.
 */
export interface MetricHistogram {
	name: string
	buckets: Map<number, number> // bucket edge -> count
	sum: number
	count: number
	min: number
	max: number
	tags: Record<string, string>
	lastUpdated: number
}

/**
 * Metrics collector for tracking performance and system health.
 *
 * Features:
 * - Counter metrics (requests, errors, etc.)
 * - Histogram metrics (latency, response size)
 * - Gauge metrics (active connections, memory usage)
 * - Automatic metric aggregation
 * - Percentile calculation
 */
export class MetricsCollector {
	private counters: Map<string, MetricCounter> = new Map()
	private histograms: Map<string, MetricHistogram> = new Map()
	private gauges: Map<string, number> = new Map()

	private socket: Socket | null = null

	// Default histogram buckets (milliseconds)
	private static readonly DEFAULT_BUCKETS = [10, 50, 100, 500, 1000, 5000]

	constructor() {
		// Initialize common metrics
		this.initializeMetrics()
	}

	/**
	 * Set the socket for metric emission.
	 */
	public setSocket(socket: Socket): void {
		this.socket = socket
	}

	/**
	 * Increment a counter.
	 */
	public incrementCounter(name: string, value: number = 1, unit: string = "count", tags: Record<string, string> = {}): void {
		const key = this.getMetricKey(name, tags)

		if (!this.counters.has(key)) {
			this.counters.set(key, {
				name,
				value: 0,
				unit,
				tags,
				lastUpdated: Date.now(),
			})
		}

		const counter = this.counters.get(key)!
		counter.value += value
		counter.lastUpdated = Date.now()

		this.emitMetric("counter", counter)
	}

	/**
	 * Record a latency measurement in a histogram.
	 */
	public recordLatency(name: string, durationMs: number, tags: Record<string, string> = {}): void {
		const key = this.getMetricKey(name, tags)

		if (!this.histograms.has(key)) {
			this.histograms.set(key, {
				name,
				buckets: new Map(MetricsCollector.DEFAULT_BUCKETS.map((b) => [b, 0])),
				sum: 0,
				count: 0,
				min: Infinity,
				max: -Infinity,
				tags,
				lastUpdated: Date.now(),
			})
		}

		const histogram = this.histograms.get(key)!
		histogram.sum += durationMs
		histogram.count++
		histogram.min = Math.min(histogram.min, durationMs)
		histogram.max = Math.max(histogram.max, durationMs)
		histogram.lastUpdated = Date.now()

		// Update buckets
		for (const [bucket, _] of histogram.buckets) {
			if (durationMs <= bucket) {
				histogram.buckets.set(bucket, (histogram.buckets.get(bucket) ?? 0) + 1)
			}
		}

		this.emitMetric("histogram", histogram)
	}

	/**
	 * Set a gauge value (e.g., active connections).
	 */
	public setGauge(name: string, value: number, tags: Record<string, string> = {}): void {
		const key = this.getMetricKey(name, tags)
		this.gauges.set(key, value)

		this.emitMetric("gauge", {
			name,
			value,
			tags,
			timestamp: Date.now(),
		})
	}

	/**
	 * Get counter value.
	 */
	public getCounter(name: string, tags: Record<string, string> = {}): number {
		const key = this.getMetricKey(name, tags)
		return this.counters.get(key)?.value ?? 0
	}

	/**
	 * Get histogram percentile.
	 */
	public getPercentile(name: string, percentile: number, tags: Record<string, string> = {}): number {
		const key = this.getMetricKey(name, tags)
		const histogram = this.histograms.get(key)

		if (!histogram || histogram.count === 0) {
			return 0
		}

		const targetCount = (histogram.count * percentile) / 100

		let cumulative = 0
		for (const [bucket, count] of histogram.buckets) {
			cumulative += count
			if (cumulative >= targetCount) {
				return bucket
			}
		}

		return histogram.max
	}

	/**
	 * Get histogram statistics.
	 */
	public getHistogramStats(name: string, tags: Record<string, string> = {}): {
		min: number
		max: number
		avg: number
		p50: number
		p95: number
		p99: number
		count: number
	} {
		const key = this.getMetricKey(name, tags)
		const histogram = this.histograms.get(key)

		if (!histogram || histogram.count === 0) {
			return { min: 0, max: 0, avg: 0, p50: 0, p95: 0, p99: 0, count: 0 }
		}

		return {
			min: histogram.min,
			max: histogram.max,
			avg: histogram.sum / histogram.count,
			p50: this.getPercentile(name, 50, tags),
			p95: this.getPercentile(name, 95, tags),
			p99: this.getPercentile(name, 99, tags),
			count: histogram.count,
		}
	}

	/**
	 * Get gauge value.
	 */
	public getGauge(name: string, tags: Record<string, string> = {}): number {
		const key = this.getMetricKey(name, tags)
		return this.gauges.get(key) ?? 0
	}

	/**
	 * Export metrics in Prometheus format.
	 */
	public exportPrometheus(): string {
		let output = ""

		// Counters
		for (const counter of this.counters.values()) {
			output += this.formatPrometheusLine(counter.name, counter.value, counter.tags)
		}

		// Gauges
		for (const [key, value] of this.gauges) {
			output += `${key} ${value}\n`
		}

		// Histograms
		for (const histogram of this.histograms.values()) {
			output += `${histogram.name}_sum${this.formatTags(histogram.tags)} ${histogram.sum}\n`
			output += `${histogram.name}_count${this.formatTags(histogram.tags)} ${histogram.count}\n`
			output += `${histogram.name}_bucket{le="+Inf"${this.formatTagsWithoutBrace(histogram.tags)}} ${histogram.count}\n`
		}

		return output
	}

	/**
	 * Get all metrics.
	 */
	public getMetrics(): {
		counters: Record<string, number>
		gauges: Record<string, number>
		histograms: Record<string, ReturnType<typeof this.getHistogramStats>>
	} {
		const counters: Record<string, number> = {}
		const gauges: Record<string, number> = {}
		const histograms: Record<string, ReturnType<typeof this.getHistogramStats>> = {}

		for (const [key, counter] of this.counters) {
			counters[key] = counter.value
		}

		for (const [key, value] of this.gauges) {
			gauges[key] = value
		}

		for (const [key] of this.histograms) {
			histograms[key] = this.getHistogramStats(key)
		}

		return { counters, gauges, histograms }
	}

	/**
	 * Reset metrics.
	 */
	public reset(): void {
		this.counters.clear()
		this.histograms.clear()
		this.gauges.clear()
		this.initializeMetrics()
	}

	private initializeMetrics(): void {
		// Initialize with zero counters for common metrics
		this.incrementCounter("runtime.requests", 0, "count")
		this.incrementCounter("runtime.errors", 0, "count")
		this.setGauge("runtime.active_connections", 0)
		this.setGauge("runtime.memory_usage_mb", 0)
	}

	private getMetricKey(name: string, tags: Record<string, string> = {}): string {
		if (Object.keys(tags).length === 0) {
			return name
		}

		const tagStr = Object.entries(tags)
			.sort()
			.map(([k, v]) => `${k}=${v}`)
			.join(",")

		return `${name}{${tagStr}}`
	}

	private formatPrometheusLine(name: string, value: number, tags: Record<string, string> = {}): string {
		const tagStr = this.formatTags(tags)
		return `${name}${tagStr} ${value}\n`
	}

	private formatTags(tags: Record<string, string> = {}): string {
		if (Object.keys(tags).length === 0) {
			return ""
		}

		const tagStr = Object.entries(tags)
			.map(([k, v]) => `${k}="${v}"`)
			.join(",")

		return `{${tagStr}}`
	}

	private formatTagsWithoutBrace(tags: Record<string, string> = {}): string {
		if (Object.keys(tags).length === 0) {
			return ""
		}

		return (
			"," +
			Object.entries(tags)
				.map(([k, v]) => `${k}="${v}"`)
				.join(",")
		)
	}

	private emitMetric(type: string, data: unknown): void {
		if (this.socket) {
			this.socket.emit(`metrics:${type}`, data)
		}
	}
}
