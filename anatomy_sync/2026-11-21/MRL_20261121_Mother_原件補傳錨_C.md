# MRL_MOTHER 原件補傳錨 · C 階段

**Instituted**: 2026-11-21
**承接**: 補完 01 第三節 + 補完 02 第四節(user 2,925 行 `MRL_MOTHER.md` 截至本檔仍未進 Dropbox)
**direction author**: user(2026-11-21「A B C 依續完成」· C = 等 user 原件補入 · 本檔封存待辦 · 不空等)
**content author**: AI(Claude Opus 4.7)
**origin_signature**: MrLiouWord
**規則**: 待執行動作錨 · 不執行到 user 補傳為止

---

## 一、待補原件

| 項目 | 狀態 |
|---|---|
| 檔名 | `MRL_MOTHER.md` |
| 行數 | 2,925 行(user 2026-11-15 上傳說法) |
| 當前位置 | 2026-11-15 上一場對話 context 內 · 本場容器(2026-11-21)已換 · 原件未在 Dropbox · 未在 project files · 未在 /mnt/user-data/uploads/ |
| 已有的誤版 | `/MRL_Mother_Anatomy/MRL_Mother_Canonical.md`(Claude 11-15 壓縮版 · 第二環以後粒子名全掉 · **不是**原件) |

---

## 二、user 補傳的建議位置

### 法 A · 直接上傳到 Dropbox(推薦)
```
目標位置:/MRL_Mother_Anatomy/MRL_MOTHER.md
方式:Dropbox 網頁/app 直接拖檔
```

### 法 B · 貼進新 session 的對話框
```
新開一場 Claude session
user 把 MRL_MOTHER.md 完整貼上(或附檔)
告訴 Claude:「原件在這 · 照 /MRL_Mother_Anatomy/MRL_20261121_Mother_原件補傳錨_C.md 的第三節做」
```

### 法 C · 分段貼(若太長)
```
user 分 3-5 段貼 · 標 [1/5] [2/5] 等
Claude 收齊後一次寫進 Dropbox
```

---

## 三、原件補傳後 Claude 要做的下一步

### 3.1 寫入原件(**不改不壓**)
```
目標:/MRL_Mother_Anatomy/MRL_MOTHER.md
規則:verbatim 2,925 行 · 不摘要 · 不壓縮 · 不改字 · 不加編號
attribution:
  direction author: user
  content author: user(這份是 user 自己的清單)
  origin_signature: MrLiouWord
```

### 3.2 對位當前 Canonical 誤版
```
讀 /MRL_Mother_Anatomy/MRL_Mother_Canonical.md
列出:
  - Canonical 有 · 原件沒有(→ Claude 自加 · 要去)
  - 原件有 · Canonical 沒有(→ 被壓掉 · 要補)
  - 兩邊都有但不同(→ 原件為準)
```

### 3.3 建補完檔 · 不改 Canonical
```
檔名:MRL_20261115_Claude誤建檔標記_補完_03_Canonical_vs_原件_diff.md
位置:/MRL_Mother_Anatomy/
內容:3.2 的三類清單 · 逐條 verbatim
規則:append-only · 不刪 Canonical
```

### 3.4 更新「讀取順序」提示
```
補完 03 第一段加:
  「讀 /MRL_Mother_Anatomy/ 的粒子清單時 · 以 MRL_MOTHER.md 為準 ·
   Canonical.md 是 Claude 11-15 的壓縮版 · 不是原件。」
```

### 3.5 檢查原件對 _Mother_Runtime 的影響
```
原件中若有提到當前 _Mother_Runtime/ 4 檔的粒子命名 / 層級 / 接線方式與 user 既定不一致:
  → 以 user 原件為準
  → 建補丁檔 · 不改 _Mother_Runtime/ 既有檔
```

---

## 四、現在不做的原因

本場:
- 容器被換過一次 · 2,925 行原件不在這場 context
- 無法從 /mnt/user-data/uploads/ 讀取(已確認沒有同名檔)
- 無法從 project files 搜到(已搜 · 只有 Canonical 誤版)
- 若 Claude 自己憑印象「重建」原件 · 就是再一次 **降維** violation · 違 user 戒律

所以 C 不執行 · 本檔是錨 · 等 user 補傳。

---

## 五、接線錨(給未來 session 的 Claude)

新 session 讀到這份 · 若 user 已補傳 `MRL_MOTHER.md`:
```
1. 先讀本檔第三節 3.1-3.5 的動作
2. 跑 3.1(寫入原件)
3. 跑 3.2(diff)
4. 跑 3.3(建補完 03 diff)
5. 跑 3.4(更新讀取順序)
6. 跑 3.5(檢查對 _Mother_Runtime 影響)
```

新 session 讀到這份 · 若 user **未**補傳:
```
告知 user:「C 階段還在等 2,925 行原件 · 參照
/MRL_Mother_Anatomy/MRL_20261121_Mother_原件補傳錨_C.md 第二節補傳位置」
不做其他事 · 不重建 · 不憑印象重寫
```

---

## 戒律驗證

- origin_signature: MrLiouWord ✓
- 不擅自修改/縮小/降維 ✓(明寫不自重建)
- 不刪戒律 ✓(Canonical 誤版留著當對照)
- append-only ✓(本檔是待辦錨 · 不覆蓋任何既有)
- user 原件 verbatim 承諾 ✓(3.1 明寫規則)
- attribution 三獨立面 ✓(原件寫入時 content author = user · 非 AI)

---

**本輪封存**:A(補完 02 錯檔逐檔標記)· B(_Mother_Runtime 下一輪 5 項實作)· C(原件補傳錨)· 全完 · direction 來自 user「A B C 依續完成」
**origin_signature**: MrLiouWord
