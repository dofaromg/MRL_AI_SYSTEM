import type { Socket } from "socket.io-client"

/**
 * Task dispatcher interface.
 */
export interface DispatchedTask {
	id: string
	type: string
	priority: number // 0 = lowest, 10 = highest
	payload: Record<string, unknown>
	createdAt: number
	timeoutMs: number
	maxRetries: number
	retryCount: number
	status: "queued" | "running" | "completed" | "failed" | "cancelled"
	result?: unknown
	error?: string
}

export interface TaskDispatcherOptions {
	maxQueueSize?: number
	defaultTimeout?: number
	defaultMaxRetries?: number
}

/**
 * Task dispatcher for managing task queues and scheduling.
 * Handles task prioritization, timeout management, and retry logic.
 *
 * Features:
 * - Priority-based task queue
 * - Automatic timeout handling
 * - Configurable retry mechanism
 * - Task status tracking
 * - Event emission on task state changes
 */
export class TaskDispatcher {
	private queue: Map<string, DispatchedTask> = new Map()
	private running: Map<string, DispatchedTask> = new Map()
	private completed: Map<string, DispatchedTask> = new Map()
	private failed: Map<string, DispatchedTask> = new Map()

	private readonly maxQueueSize: number
	private readonly defaultTimeout: number
	private readonly defaultMaxRetries: number

	private socket: Socket | null = null
	private taskIdCounter = 0

	constructor(options: TaskDispatcherOptions = {}) {
		this.maxQueueSize = options.maxQueueSize ?? 1000
		this.defaultTimeout = options.defaultTimeout ?? 30000 // 30 seconds
		this.defaultMaxRetries = options.defaultMaxRetries ?? 3
	}

	/**
	 * Set the socket for event emission.
	 */
	public setSocket(socket: Socket): void {
		this.socket = socket
	}

	/**
	 * Dispatch a new task to the queue.
	 */
	public dispatch(task: Omit<DispatchedTask, "id" | "createdAt" | "retryCount" | "status" | "result" | "error">): DispatchedTask {
		if (this.queue.size >= this.maxQueueSize) {
			throw new Error(`Task queue is full (max ${this.maxQueueSize})`)
		}

		const dispatchedTask: DispatchedTask = {
			...task,
			id: this.generateTaskId(),
			createdAt: Date.now(),
			retryCount: 0,
			status: "queued",
		}

		this.queue.set(dispatchedTask.id, dispatchedTask)
		this.emit("taskQueued", dispatchedTask)

		return dispatchedTask
	}

	/**
	 * Get the next task to execute based on priority.
	 */
	public getNextTask(): DispatchedTask | null {
		if (this.queue.size === 0) {
			return null
		}

		// Find highest priority task
		let nextTask: DispatchedTask | null = null
		let highestPriority = -1

		for (const task of this.queue.values()) {
			if (task.priority > highestPriority) {
				highestPriority = task.priority
				nextTask = task
			}
		}

		if (nextTask) {
			this.queue.delete(nextTask.id)
			nextTask.status = "running"
			this.running.set(nextTask.id, nextTask)

			// Set timeout
			this.setupTimeout(nextTask)

			this.emit("taskStarted", nextTask)
		}

		return nextTask
	}

	/**
	 * Mark a task as completed.
	 */
	public completeTask(taskId: string, result: unknown): void {
		const task = this.running.get(taskId)
		if (!task) {
			console.warn(`[TaskDispatcher] Task ${taskId} not found in running queue`)
			return
		}

		this.running.delete(taskId)
		task.status = "completed"
		task.result = result

		this.completed.set(taskId, task)
		this.emit("taskCompleted", task)
	}

	/**
	 * Mark a task as failed and optionally retry.
	 */
	public failTask(taskId: string, error: string): void {
		const task = this.running.get(taskId)
		if (!task) {
			console.warn(`[TaskDispatcher] Task ${taskId} not found in running queue`)
			return
		}

		task.error = error
		task.retryCount++

		if (task.retryCount < task.maxRetries) {
			// Retry
			this.running.delete(taskId)
			task.status = "queued"
			this.queue.set(taskId, task)

			this.emit("taskRetried", { task, attempt: task.retryCount })
		} else {
			// Permanent failure
			this.running.delete(taskId)
			task.status = "failed"
			this.failed.set(taskId, task)

			this.emit("taskFailed", task)
		}
	}

	/**
	 * Cancel a task.
	 */
	public cancelTask(taskId: string): boolean {
		let task = this.queue.get(taskId)
		if (task) {
			this.queue.delete(taskId)
			task.status = "cancelled"
			this.completed.set(taskId, task)
			this.emit("taskCancelled", task)
			return true
		}

		task = this.running.get(taskId)
		if (task) {
			this.running.delete(taskId)
			task.status = "cancelled"
			this.completed.set(taskId, task)
			this.emit("taskCancelled", task)
			return true
		}

		return false
	}

	/**
	 * Get task statistics.
	 */
	public getStats(): {
		queued: number
		running: number
		completed: number
		failed: number
		total: number
		avgWaitTime: number
	} {
		const total = this.queue.size + this.running.size + this.completed.size + this.failed.size

		let totalWaitTime = 0
		let completedCount = 0

		for (const task of this.completed.values()) {
			totalWaitTime += task.createdAt
			completedCount++
		}

		const avgWaitTime = completedCount > 0 ? totalWaitTime / completedCount : 0

		return {
			queued: this.queue.size,
			running: this.running.size,
			completed: this.completed.size,
			failed: this.failed.size,
			total,
			avgWaitTime,
		}
	}

	/**
	 * Clear all tasks.
	 */
	public clear(): void {
		this.queue.clear()
		this.running.clear()
		this.completed.clear()
		this.failed.clear()
	}

	private setupTimeout(task: DispatchedTask): void {
		setTimeout(() => {
			if (this.running.has(task.id)) {
				this.failTask(task.id, `Task timeout after ${task.timeoutMs}ms`)
			}
		}, task.timeoutMs)
	}

	private generateTaskId(): string {
		return `task_${Date.now()}_${++this.taskIdCounter}`
	}

	private emit(eventName: string, data: unknown): void {
		if (this.socket) {
			this.socket.emit(`dispatcher:${eventName}`, data)
		}
	}
}
