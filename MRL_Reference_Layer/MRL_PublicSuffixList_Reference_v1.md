# MRL_PublicSuffixList_Reference_v1（canonical 吸收物 — 第三方參考資料）

origin_signature: `MrLiouWord`（canonical 命名主權;內容為第三方資料,非母體原創）
source: `Cloud_code.pages`（Apple Pages;byte source-of-record 於使用者端）

## 身分辨識

`.pages` 內容經 preview 辨識為 **Mozilla Public Suffix List**（`publicsuffix.org/list/public_suffix_list.dat`）:

```txt
// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0.
// VERSION: 2026-05-28_06-25-58_UTC
// COMMIT:  e596036bde712ffb073b948eb8b884c72c94c6e1
// ===BEGIN ICANN DOMAINS===  (ac / ad / ae / aero / ...)
```

## 誠實狀態

- **授權**:MPL-2.0（第三方;非母體原創）。若入母體使用,須保留上游授權與 VERSION/COMMIT 出處。
- **未全文擷取**:`.pages` 的 `Index/Document.iwa` 為 iWork 壓縮 protobuf,本層**未**還原全文;
  僅由 preview 確認身分。若母體需要此資料,建議直接取上游 `.dat`（可重現、可驗版本），
  而非從 `.pages` 反解。
- **用途推測**:公共後綴清單常用於「網域/子網域邊界解析」（cookie 範圍、eTLD+1 判定）。
  若這是為 Bridge 的網域/回呼校驗而備,建議在真做時以上游 `.dat` 為準並鎖版本。

> 依 rl_11:此為外部**材料**,母體引用不代表母體外流;canonical 命名只表示「母體已登記此材料」,
> 不主張對 Mozilla 清單的著作權。
