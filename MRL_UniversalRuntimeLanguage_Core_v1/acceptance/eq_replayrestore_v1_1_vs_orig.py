import sys, json, time, random, importlib.util, tempfile
sys.path.insert(0, "/home/claude/mrl_ai_system")
def load(name, path):
    sp = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
O = load("rrc_o", sys.argv[1]); N = load("rrc_n", sys.argv[2])
intents = ["a", "b", "c", "observe", "jump"]
ok = 0
for t in range(300):
    n = random.randint(0, 200)
    ev = [{"node_id": f"n{i}", "intent": random.choice(intents)} for i in range(n)]
    ro, rn = O.MRL_ReplayRestore_Core(ev), N.MRL_ReplayRestore_Core(ev)
    if n == 0:
        assert ro.execute() == rn.execute(); ok += 1; continue
    a = [ro.execute(), ro.replay(), ro.restore(), {k: v for k, v in ro.checkpoints.items()}]
    b = [rn.execute(), rn.replay(), rn.restore(), {k: dict(v.items()) for k, v in rn.checkpoints.items()}]
    k = random.choice(list(ro.checkpoints)); a.append(ro.restore(k)); b.append(rn.restore(k))
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True), t
    ok += 1
print("equivalence", ok, "/ 300")
for n in (20000, 60000):
    ev = [{"node_id": f"n{i}", "intent": random.choice(intents)} for i in range(n)]
    for M in (O, N):
        r = M.MRL_ReplayRestore_Core(ev); t0 = time.time(); r.execute(); r.replay(); x = r.restore(); print(M.__name__, n, round(time.time() - t0, 2), x["exact"])
