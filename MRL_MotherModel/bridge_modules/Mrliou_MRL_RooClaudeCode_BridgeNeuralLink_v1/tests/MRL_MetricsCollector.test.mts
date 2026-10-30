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


// origin_signature: MrLiouWord
for (const samples of [[5,45,90,450,900], [10,50,100,500,1000,5000], [6000], [1], [50,50,50]]) {
  test(`MRL 累計桶、百分位與 Prometheus 一致 ${JSON.stringify(samples)}`, () => {
    const c = new MetricsCollector()
    for (const value of samples) c.recordLatency("latency", value, {node: "a"})
    const edges = [10,50,100,500,1000,5000]
    const counts = edges.map(edge => samples.filter(x => x <= edge).length)
    const output = c.exportPrometheus()
    for (const [i, edge] of edges.entries()) {
      assert.ok(output.includes(`latency_bucket{le="${edge}",node="a"} ${counts[i]}\n`))
    }
    assert.ok(output.includes(`latency_bucket{le="+Inf",node="a"} ${samples.length}\n`))
    assert.ok(output.includes(`latency_sum{node="a"} ${samples.reduce((a,b)=>a+b,0)}\n`))
    assert.ok(output.includes(`latency_count{node="a"} ${samples.length}\n`))
    const stats = c.getHistogramStats("latency", {node:"a"})
    for (const percentile of [50,95,99]) {
      const edge = edges.find((_,i) => counts[i] >= samples.length * percentile / 100)
      const expected = edge ?? Math.max(...samples)
      assert.equal(c.getPercentile("latency", percentile, {node:"a"}), expected)
      assert.equal(stats[`p${percentile}`], expected)
    }
    assert.deepEqual(c.getMetrics().histograms['latency{node=a}'], stats)
  })
}
test("MRL 空資料與重設", () => {
  const c = new MetricsCollector()
  assert.equal(c.getPercentile("missing", 99), 0)
  c.recordLatency("latency", 900)
  c.reset()
  assert.equal(c.getHistogramStats("latency").count, 0)
})
