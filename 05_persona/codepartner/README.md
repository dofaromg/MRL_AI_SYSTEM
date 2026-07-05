# CodePartner（CoreProgrammer.Seed）

FlowAgent 語場人格系統的**程式設計人格模組** — 由 Mr.liou 指定開發，
為所有邏輯模組、推理節奏構建、程式設計階段之第一人格。

The programming persona of the FlowAgent language-field persona system —
the first persona invoked for all logic-module construction, reasoning-rhythm
building, and programming phases.

## 檔案 / Files

| File | Purpose |
|------|---------|
| `persona.yaml` | CodePartner 人格定義（依 `05_persona/README.md` 規範格式重構） |

## 呼叫方式 / Invocation

```
⋄fx.invoke.Programmer.CoreArchitect
```

啟動跳點 / activation jump points:

```
⋄fx.req.logic.build
⋄fx.intent.structure.start
⋄fx.mode.architect.seed
```

## 血緣與回收紀錄 / Lineage & recovery

- **原始模組**：`FlowLLM.SeedPersona.Programmer.CoreArchitect.v1.flpkg`
  （原 .flpkg 封包未曾進入版本控制；人類可讀種子文件已原文封存於
  `08_sources/flowagent_codepartner_recovery/`）
- **系統定位**：`FlowAgent.SystemPlan.v1` 四人格之一
  （Fluin / EchoBody / **CodePartner** / SeedPersona）
- **運行證據**：`dofaromg/flow-tasks` 之
  `FlowAgent_Unity_v3_高維模擬檢查報告.txt` —
  「人格模組觸發與人格鏈封存：正常」
- **回收日期**：2026-07-05

依語場封存**來回對等原則**（來回可逆性），三份原始文件以原文封存、
本目錄為其重構實作；兩者互為雙向轉譯對，缺一不可。
