# MRL_WorldRuntime_Report

origin_signature: `MrLiouWord`

- world_count：`2`
- synchronization_active：`True`
- sync.merged_keys：`['graph_hash', 'metair_hash']`

## worlds

```json
{
  "world_alpha": {
    "member_worlds": [
      "context_world"
    ],
    "context_keys": [
      "graph_hash",
      "metair_hash"
    ]
  },
  "world_beta": {
    "member_worlds": [
      "context_world"
    ],
    "context_keys": [
      "graph_hash",
      "metair_hash"
    ]
  }
}
```

- replay.exact：`True`
- restore.exact：`True`
- persistent_loop：`{'iteration': 3, 'survives_restart': True}`
- roundtrip.exact：`True`
