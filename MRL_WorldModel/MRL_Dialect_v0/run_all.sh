#!/usr/bin/env bash
# MRL Dialect v0 全部驗收 —— 需要 python3、node、LLVM（lli / llc）
set -euo pipefail
cd "$(dirname "$0")"
echo "== 1. 全語料可逆（pcode/fltnz/flynz.map → IR → 原檔）"; python3 tests/test_corpus_roundtrip.py
echo "== 2. PVM v1.2 vs LLVM 差分（固定程式）";          python3 tests/test_llvm_differential.py
echo "== 3. PVM v1.2 vs LLVM 隨機差分";                   python3 tests/test_fuzz_differential.py 300
echo "== 4. 世界圖";                                       python3 mrl_world_graph.py > world_graph_repo.json && python3 -c "import json;d=json.load(open('world_graph_repo.json'));print({k:d[k] for k in ('unique_files','nodes','edges','tiers','line_counts')})"
