// origin_signature: MrLiouWord
import test from "node:test"
import assert from "node:assert/strict"
import { createServer } from "node:http"
import { once } from "node:events"
import { Server } from "socket.io"
import { io } from "socket.io-client"
import { createStage04Runtime, TaskDispatcher, EventAggregator } from "../src/MRL_Stage04Runtime.ts"

test("MRL 三模組經實際 Socket.IO 傳送任務、事件與指標", async (t) => {
  const http = createServer()
  const server = new Server(http)
  t.after(() => server.close())
  http.listen(0, "127.0.0.1")
  await once(http, "listening")
  const port = (http.address() as {port:number}).port
  const connected = once(server, "connection")
  const socket = io(`http://127.0.0.1:${port}`, {transports:["websocket"], reconnection:false})
  t.after(() => socket.disconnect())
  const [peer] = await connected
  const runtime = createStage04Runtime(socket)
  t.after(() => runtime.dispatcher.clear())
  const queueEvent = once(peer, "dispatcher:taskQueued")
  const task = runtime.dispatcher.dispatch({type:"verify", priority:5, payload:{}, timeoutMs:1000, maxRetries:1})
  assert.equal((await queueEvent)[0].id, task.id)
  assert.equal(runtime.dispatcher.getNextTask()?.id, task.id)
  const completed = once(peer, "dispatcher:taskCompleted")
  runtime.dispatcher.completeTask(task.id, {ok:true})
  assert.equal((await completed)[0].status, "completed")
  runtime.events.subscribe("task_complete", () => runtime.metrics.incrementCounter("tasks_completed"))
  const aggregated = once(peer, "aggregator:event")
  const metric = once(peer, "metrics:counter")
  runtime.events.emit("dispatcher", "task_complete", "info", {taskId:task.id})
  assert.equal((await aggregated)[0].data.taskId, task.id)
  assert.equal((await metric)[0].value, 1)
  assert.equal(runtime.metrics.getCounter("tasks_completed"), 1)
})

test("MRL 重試不受上一輪計時器提前終止，完成與清除會釋放計時器", (t) => {
  t.mock.timers.enable({apis:["setTimeout"]})
  const d = new TaskDispatcher()
  const task = d.dispatch({type:"retry", priority:1, payload:{}, timeoutMs:10, maxRetries:3})
  d.getNextTask()
  t.mock.timers.tick(5)
  d.failTask(task.id,"retry")
  d.getNextTask()
  t.mock.timers.tick(5)
  assert.equal(task.status,"running")
  t.mock.timers.tick(5)
  assert.equal(task.status,"queued")
  d.getNextTask()
  d.completeTask(task.id,{ok:true})
  t.mock.timers.tick(100)
  assert.equal(task.status,"completed")
  d.clear()
  assert.equal(d.getStats().total,0)
})

test("MRL 優先級與事件過濾、轉換、取消訂閱", () => {
  const d = new TaskDispatcher({maxQueueSize:2})
  const low = d.dispatch({type:"a",priority:1,payload:{},timeoutMs:10,maxRetries:1})
  const high = d.dispatch({type:"b",priority:9,payload:{},timeoutMs:10,maxRetries:1})
  assert.throws(() => d.dispatch({type:"c",priority:0,payload:{},timeoutMs:10,maxRetries:1}))
  assert.equal(d.getNextTask()?.id,high.id)
  d.cancelTask(high.id)
  assert.equal(d.getNextTask()?.id,low.id)
  d.clear()
  const e = new EventAggregator(2)
  e.addFilter(event => event.severity !== "info")
  e.addTransformer(event => ({...event,tags:["MRL"]}))
  let seen = 0
  const unsubscribe = e.subscribe("done", () => seen++)
  e.emit("runtime","done","info",{})
  assert.equal(e.getStats().total,0)
  e.emit("runtime","done","error",{})
  assert.equal(seen,1)
  assert.equal(e.getByTag("MRL").length,1)
  unsubscribe()
  e.emit("runtime","done","error",{})
  e.emit("runtime","done","error",{})
  assert.equal(seen,1)
  assert.equal(e.getStats().total,2)
})
