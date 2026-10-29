import test from "node:test"
import assert from "node:assert/strict"
import { MetricsCollector } from "../src/MetricsCollector.ts"

test("MRL 百分位不重複累加直方圖桶", () => {
  const collector = new MetricsCollector()
  for (const latency of [5, 45, 90, 450, 900]) collector.recordLatency("latency", latency)
  assert.equal(collector.getPercentile("latency", 50), 100)
  assert.equal(collector.getPercentile("latency", 95), 1000)
  assert.equal(collector.getPercentile("latency", 99), 1000)
})

test("MRL 帶標籤直方圖彙整保留各維度統計", () => {
  const collector = new MetricsCollector()
  collector.recordLatency("latency", 45, { node: "a" })
  collector.recordLatency("latency", 900, { node: "b" })
  const metrics = collector.getMetrics()
  assert.deepEqual(metrics.histograms["latency{node=a}"], collector.getHistogramStats("latency", { node: "a" }))
  assert.deepEqual(metrics.histograms["latency{node=b}"], collector.getHistogramStats("latency", { node: "b" }))
  assert.equal(metrics.histograms["latency{node=a}"].count, 1)
  assert.equal(metrics.histograms["latency{node=b}"].avg, 900)
})
