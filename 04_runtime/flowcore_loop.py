"""
FlowAgent Kernel
MRL AI Super Computer
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Add merkle module to path (03_memory/merkle/ is not a Python package due to numeric prefix)
sys.path.insert(0, str(REPO_ROOT / "03_memory" / "merkle"))

import time
import json

from memory_chain import MerkleChain

# local runtime data dir (do NOT commit these files)
TRACE_FILE = REPO_ROOT / "06_trace" / "traces" / "_data" / "runtime_trace.jsonl"
DATA_DIR = REPO_ROOT / "03_memory" / "_data" / "memory_chain"


def log_event(event):
    TRACE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TRACE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def main_loop():
    print("FlowAgent Kernel started")

    tick = 0
    chain = MerkleChain(DATA_DIR)

    while True:
        event = {
            "system": "FlowAgent",
            "tick": tick,
            "action": "heartbeat",
            "timestamp": time.time()
        }

        # operational trace
        log_event(event)

        # canonical immutable chain
        chain.commit(
            payload=event,
            layer="L1",
            tags=["heartbeat"],
            meta={"source": "kernel"}
        )

        print("tick:", tick)
        tick += 1
        time.sleep(5)


if __name__ == "__main__":
    main_loop()
