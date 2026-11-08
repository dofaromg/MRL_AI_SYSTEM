// 以 PVM v1.2 執行 PVM JSON 程式，輸出最終 ACC 與 stack（供差分測試）
// 用法：node run_pvm.mjs program.json
import { readFileSync } from "fs";
import { ParticleVM } from "./pvm_v1_2.js";
const prog = JSON.parse(readFileSync(process.argv[2], "utf8"));
const r = new ParticleVM().execute(prog);
// -0 / NaN / Infinity 會被 JSON 吃掉，改成字串保真
const keep = (k,v)=>typeof v==="number"?(Object.is(v,-0)?"-0":Number.isFinite(v)?v:String(v)):v;
console.log(JSON.stringify({ acc: r.state.registers.ACC, stack: r.state.stack, halted: r.state.halted, steps: r.state.steps }, keep));
