-- =========================================================
-- MRL_WorldDefinition_v1.sql
-- version: v1.0
-- owner: MrLiou / MRL System
-- origin_signature: MrLiouWord
-- layer: L∞ WORLD DEFINITION
-- purpose: 世界定義層（World Definition Layer）
--          11 個世界基本原語，作為世界模型的最高定義層。
--          本檔為 MRL_BaseWorld_DB_v1.sql 的 additive 擴充，
--          不修改原有 27 張表。
--
-- World Definition
-- │
-- ├── Space（空間）
-- ├── Time（時間）
-- ├── Entity（實體）
-- ├── Identity（身份）
-- ├── State（狀態）
-- ├── Relation（關係）
-- ├── Event（事件）
-- ├── Rule（規則）
-- ├── Memory（記憶）
-- ├── Evolution（演化）
-- └── Observation（觀測）
-- =========================================================

PRAGMA foreign_keys = ON;

-- =========================================================
-- 1. Space（空間）— 世界中的區域或領域
-- =========================================================

CREATE TABLE IF NOT EXISTS MRL_WorldDef_Space (
    space_id       TEXT PRIMARY KEY,
    space_name     TEXT NOT NULL UNIQUE,
    dimension      INTEGER DEFAULT 0,
    space_type     TEXT,
    attributes     TEXT,
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    status         TEXT NOT NULL DEFAULT 'active',
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);

-- =========================================================
-- 2. Time（時間）— 時序標記或時間區間
-- =========================================================

CREATE TABLE IF NOT EXISTS MRL_WorldDef_Time (
    time_id        TEXT PRIMARY KEY,
    time_name      TEXT NOT NULL UNIQUE,
    ts_ms          INTEGER NOT NULL,
    duration_ms    INTEGER DEFAULT 0,
    reference_frame TEXT,
    attributes     TEXT,
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    status         TEXT NOT NULL DEFAULT 'active',
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);

-- =========================================================
-- 3. Entity（實體）— 存在於世界中的具體事物
-- =========================================================

CREATE TABLE IF NOT EXISTS MRL_WorldDef_Entity (
    entity_id      TEXT PRIMARY KEY,
    entity_name    TEXT NOT NULL UNIQUE,
    entity_type    TEXT,
    space_ref      TEXT,
    time_ref       TEXT,
    attributes     TEXT,
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    status         TEXT NOT NULL DEFAULT 'active',
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL,
    FOREIGN KEY (space_ref) REFERENCES MRL_WorldDef_Space(space_name),
    FOREIGN KEY (time_ref)  REFERENCES MRL_WorldDef_Time(time_name)
);

-- =========================================================
-- 4. Identity（身份）— 實體的唯一識別
-- =========================================================

CREATE TABLE IF NOT EXISTS MRL_WorldDef_Identity (
    identity_id    TEXT PRIMARY KEY,
    entity_ref     TEXT NOT NULL,
    owner          TEXT NOT NULL,
    signature      TEXT NOT NULL DEFAULT 'MrLiouWord',
    authority      TEXT,
    attributes     TEXT,
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    status         TEXT NOT NULL DEFAULT 'active',
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL,
    FOREIGN KEY (entity_ref) REFERENCES MRL_WorldDef_Entity(entity_name)
);

-- =========================================================
-- 5. State（狀態）— 實體或系統的當前狀況
-- =========================================================

CREATE TABLE IF NOT EXISTS MRL_WorldDef_State (
    state_id       TEXT PRIMARY KEY,
    entity_ref     TEXT NOT NULL,
    state_key      TEXT NOT NULL,
    state_value    TEXT,
    state_version  INTEGER NOT NULL DEFAULT 1,
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL,
    FOREIGN KEY (entity_ref) REFERENCES MRL_WorldDef_Entity(entity_name)
);

-- =========================================================
-- 6. Relation（關係）— 兩個實體之間的關聯
-- =========================================================

CREATE TABLE IF NOT EXISTS MRL_WorldDef_Relation (
    relation_id    TEXT PRIMARY KEY,
    from_entity    TEXT NOT NULL,
    rel_type       TEXT NOT NULL,
    to_entity      TEXT NOT NULL,
    direction      TEXT NOT NULL DEFAULT 'directed',
    weight         REAL DEFAULT 1.0,
    attributes     TEXT,
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    created_at     TEXT NOT NULL
);

-- =========================================================
-- 7. Event（事件）— 在特定時間點發生的事
-- =========================================================

CREATE TABLE IF NOT EXISTS MRL_WorldDef_Event (
    event_id       TEXT PRIMARY KEY,
    entity_ref     TEXT NOT NULL,
    event_type     TEXT NOT NULL,
    payload        TEXT,
    ts_ms          INTEGER NOT NULL,
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    created_at     TEXT NOT NULL
);

-- =========================================================
-- 8. Rule（規則）— 約束或支配行為的法則
-- =========================================================

CREATE TABLE IF NOT EXISTS MRL_WorldDef_Rule (
    rule_id        TEXT PRIMARY KEY,
    rule_name      TEXT NOT NULL UNIQUE,
    condition_expr TEXT NOT NULL,
    action_expr    TEXT NOT NULL,
    priority       INTEGER NOT NULL DEFAULT 0,
    scope          TEXT,
    attributes     TEXT,
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    status         TEXT NOT NULL DEFAULT 'active',
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);

-- =========================================================
-- 9. Memory（記憶）— 過去狀態或事件的儲存記錄
-- =========================================================

CREATE TABLE IF NOT EXISTS MRL_WorldDef_Memory (
    memory_id      TEXT PRIMARY KEY,
    entity_ref     TEXT NOT NULL,
    memory_type    TEXT NOT NULL DEFAULT 'state_snapshot',
    snapshot       TEXT,
    ts_ms          INTEGER NOT NULL,
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    created_at     TEXT NOT NULL
);

-- =========================================================
-- 10. Evolution（演化）— 隨時間的變化或轉換
-- =========================================================

CREATE TABLE IF NOT EXISTS MRL_WorldDef_Evolution (
    evolution_id   TEXT PRIMARY KEY,
    entity_ref     TEXT NOT NULL,
    state_before   TEXT,
    state_after    TEXT,
    delta_hash     TEXT,
    description    TEXT,
    ts_ms          INTEGER NOT NULL,
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    created_at     TEXT NOT NULL
);

-- =========================================================
-- 11. Observation（觀測）— 感知或測量的行為
-- =========================================================

CREATE TABLE IF NOT EXISTS MRL_WorldDef_Observation (
    observation_id TEXT PRIMARY KEY,
    observer       TEXT NOT NULL,
    target_ref     TEXT NOT NULL,
    obs_key        TEXT NOT NULL,
    obs_value      TEXT,
    ts_ms          INTEGER NOT NULL,
    attributes     TEXT,
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    created_at     TEXT NOT NULL
);

-- =========================================================
-- INDEXES
-- =========================================================

CREATE INDEX IF NOT EXISTS idx_worlddef_entity_space  ON MRL_WorldDef_Entity(space_ref);
CREATE INDEX IF NOT EXISTS idx_worlddef_entity_time   ON MRL_WorldDef_Entity(time_ref);
CREATE INDEX IF NOT EXISTS idx_worlddef_identity_entity ON MRL_WorldDef_Identity(entity_ref);
CREATE INDEX IF NOT EXISTS idx_worlddef_state_entity  ON MRL_WorldDef_State(entity_ref, state_key);
CREATE INDEX IF NOT EXISTS idx_worlddef_relation_from ON MRL_WorldDef_Relation(from_entity);
CREATE INDEX IF NOT EXISTS idx_worlddef_relation_to   ON MRL_WorldDef_Relation(to_entity);
CREATE INDEX IF NOT EXISTS idx_worlddef_event_entity  ON MRL_WorldDef_Event(entity_ref, event_type);
CREATE INDEX IF NOT EXISTS idx_worlddef_event_ts      ON MRL_WorldDef_Event(ts_ms);
CREATE INDEX IF NOT EXISTS idx_worlddef_rule_priority ON MRL_WorldDef_Rule(priority DESC);
CREATE INDEX IF NOT EXISTS idx_worlddef_memory_entity ON MRL_WorldDef_Memory(entity_ref, ts_ms);
CREATE INDEX IF NOT EXISTS idx_worlddef_evolution_entity ON MRL_WorldDef_Evolution(entity_ref, ts_ms);
CREATE INDEX IF NOT EXISTS idx_worlddef_observation_observer ON MRL_WorldDef_Observation(observer);
CREATE INDEX IF NOT EXISTS idx_worlddef_observation_target ON MRL_WorldDef_Observation(target_ref, obs_key);
