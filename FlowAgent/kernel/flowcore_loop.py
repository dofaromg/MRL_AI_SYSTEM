"""
FlowAgent Kernel
MRL AI Super Computer
"""

import time
import json
from pathlib import Path


TRACE_FILE = Path("../runtime/runtime_trace.jsonl")


def log_event(event):

    TRACE_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(TRACE_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")


def heartbeat(tick):

    event = {
        "system": "FlowAgent",
        "tick": tick,
        "action": "heartbeat",
        "timestamp": time.time()
    }

    log_event(event)


def main_loop():

    print("FlowAgent Kernel started")

    tick = 0

    while True:

        heartbeat(tick)

        print("tick:", tick)

        tick += 1

        time.sleep(5)


if __name__ == "__main__":
    main_loop()
