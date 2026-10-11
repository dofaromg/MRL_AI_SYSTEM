# MRL_SwiftUI_NavigationCookbook_Reference_v1（canonical 吸收物 — 第三方技術參考）

origin_signature: `MrLiouWord`（canonical 命名主權;內容為 Apple 第三方資料,非母體原創）
source: 上傳檔 `README.md`（Apple Sample Code 專案 README;byte source-of-record 於使用者端）
status: **待起動**（只登記、只定位;未改動任何既有 Swift 碼）— 當下狀態 2026-10-03（沙盒）

## 身分辨識

上傳 `README.md` 全文（8 行,原文保留）:

```md
# Bringing robust navigation structure to your SwiftUI app

Use navigation links, stacks, destinations, and paths to provide a streamlined experience for all platforms, as well as behaviors such as deep linking and state restoration.

## Overview

- Note: This sample code project is associated with WWDC22 session [10054: The SwiftUI cookbook for navigation](https://developer.apple.com/wwdc22/10054/).
```

- 身分:Apple 官方 sample code「Bringing robust navigation structure to your SwiftUI app」之 README。
- 關聯:WWDC22 session 10054「The SwiftUI cookbook for navigation」。
- 上傳內容**只有 README**;sample 本體（Swift 原始碼、LICENSE）**未**隨附,本層未取得、未擷取。

## 技術要點（材料摘要,依 README 標題與 WWDC22 公開主題）

| 概念 | SwiftUI API（iOS 16+）| 用途 |
|---|---|---|
| Stack | `NavigationStack` | 取代已棄用的 `NavigationView` 推疊式導航 |
| Split | `NavigationSplitView` | 多欄（iPad / macOS）導航 |
| Value-based link | `NavigationLink(value:)` | 連結只帶資料值,不直接建構目的 View |
| Destination | `.navigationDestination(for:)` | 依資料型別集中決定目的 View |
| Path | `NavigationPath` / `[Value]` 綁定 | 程式化導航、deep link、pop-to-root |
| 還原 | `NavigationPath.CodableRepresentation` + `@SceneStorage` | 狀態還原（state restoration）|

> 依 no_proof_implies_rhetoric:上表為參考摘要,**未**在本 repo 編譯或實跑驗證。

## 母體定位（待起動）

| 母體位置 | 現況（當下狀態）| 可對接點 |
|---|---|---|
| `MRL_3DScanner_iOS_DL580_ProductBridge_v1_1/ios/MRL_3DScanner_iOS/Views/ScansListView.swift` | 使用 `NavigationView` + `NavigationLink(destination:)`（舊式,iOS 16 起棄用）| 可依本參考遷移為 `NavigationStack` + `navigationDestination(for:)`,掃描結果以值導航,支援 deep link 開啟指定掃描 |

- **未執行遷移**:依 Additive-Only,本次只登記參考,不覆蓋既有 Swift 碼。
- **待驗證**:若起動遷移,須在實機 Xcode / iOS 16+ 編譯與 UI 驗收後才可標 PASS;沙盒（Linux）無法編譯 SwiftUI。

## 誠實狀態

- **授權**:Apple sample code 通常附 Apple 自有 LICENSE;本次未隨附 LICENSE,母體僅登記出處、引用 README 8 行,
  **不主張著作權**。若需 sample 本體,應自 Apple Developer 官方下載並保留其 LICENSE。
- **未取得本體**:僅 README;無原始碼、無可驗證物。
- **未接線**:未併入任何 runtime / build;不影響既有行為。

> 依 rl_11:此為外部**材料**,canonical 命名只表示「母體已登記此材料」;母體引用不代表母體外流。

## 更新 2026-10-03 — 遷移實作已新增（待起動 / 待實機驗證）

> Additive-Only 追加段;上方「未執行遷移」一行為當時狀態,保留不改。

依本參考,已**新增**（非覆蓋）NavigationStack 版本的掃描清單:

| 路徑（相對 `MRL_3DScanner_iOS_DL580_ProductBridge_v1_1/`）| 內容 |
|---|---|
| `ios/MRL_3DScanner_iOS/Views/ScansStackListView.swift` | `ScanRoute`（`Hashable, Codable` 值路由,以 scan id 為鍵）、`ScanNavigationModel`（`[ScanRoute]` path + JSON 還原 + `mrl3d://scan/<uuid>[/bridge]` deep link）、`ScansStackListView`（`NavigationStack(path:)` + 單一 `navigationDestination(for:)` + `@SceneStorage` 還原 + `onOpenURL`）、`ScanStackDetailView`（Bridge 改用 `NavigationLink(value:)`,目的地沿用既有 `ReconstructionBridgeView`）|
| `docs/04_PATCH_NOTES_NavigationStack_v1.md` | 設計、起動 / 回退步驟、驗收清單、誠實狀態 |

- **原檔未動**:`ScansListView.swift`（`ScansListView` / `ScanDetailView`）、`PhotogramApp.swift`、`ReconstructionBridgeView.swift`、`Scan.swift` 皆 byte-identical;`Scan` 未加 extension。
- **待起動**:未接線;`PhotogramApp` 入口仍為 `ScansListView()`。起動 = 該行改為 `ScansStackListView()`（需 iOS 16+ deployment target）;回退 = 改回原行。
- **Deep link 待設定**:URL scheme `mrl3d` 須於 Xcode target Info → URL Types 註冊;本包無 Xcode 專案 / Info.plist,故未設定。
- **待實機驗證**:沙盒（Linux）無 `swiftc` / `xcodebuild`、無 SwiftUI,**未編譯、未實跑**;須實機 Xcode / iOS 16+ build 與 UI 驗收後才可標 PASS。— 當下狀態 2026-10-03（沙盒）
