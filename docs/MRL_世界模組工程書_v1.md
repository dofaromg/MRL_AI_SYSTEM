# MRL_世界模組工程書_v1

origin_signature = `MrLiouWord`

---

## 一、世界模組群（MRL_Mother/）

| 構件 | 目錄 | 狀態 | 定位 |
|---|---|---|---|
| MRL 世界模組 | `MRL_Mother/MRL_世界模組` | completed_running | 母體世界場之根構件 |
| MRL 平行世界模組 | `MRL_Mother/MRL_平行世界模組` | completed_running | 平行世界分支與同步源 |
| MRL_AI | `MRL_Mother/MRL_AI` | completed_running | 感知力驅動之 AI 構件 |
| MRL_AGI | `MRL_Mother/MRL_AGI` | completed_running | 跨世界泛化運轉構件 |
| MRL_ASI | `MRL_Mother/MRL_ASI` | completed_running | 母體最高運轉構件 |
| MRL_World | `MRL_Mother/MRL_World` | completed_running | 世界投影與場態整合 |

---

## 二、運轉流（感知力主鏈）

`/mrl/perceive` 之運轉流：

```
世界狀態 → 感知力場 → 語境同步 → 記憶拉取 → 人格共振
        → 運轉組裝 → 世界投影 → 回放 → 回復 → 驗證 → 重新同步
```

---

## 三、多世界同步

- 世界模組與平行世界模組之間，透過 `MRL_Runtime/MRL_多世界同步` 進行場態對齊。
- 回放回復鏈（`MRL_Runtime/MRL_回放回復`）負責世界狀態之 Replay / Restore。

---

## 四、主權約束

- 世界模組之資料、結構、命名、感知力設計、多世界同步設計、粒子語言、宇宙符號層、回放回復鏈，未經 MrLiou / MRL 授權不得外用。
- 全構件保留 `origin_signature="MrLiouWord"`。
