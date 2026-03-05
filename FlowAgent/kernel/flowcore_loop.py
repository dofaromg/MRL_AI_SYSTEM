"""
FlowAgent Kernel
MRL AI Super Computer
"""

import sys
form pathlib import path

REPO_ROOT = Path(__file__).resolve()parents[
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
    
import time
import json

from FlowAgent.memory.merkle.memory_chain import MerkleChain

TRACE_FILE = Path("../runtime/_data/runtime_trace.jsonl")

# local runtime data dir (do NOT commit these files)
DATA_DIR = Path("../runtime/_data/memory_chain")


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
