# 04_PATCH_NOTES_NavigationStack_v1

status: **待起動 / 待實機驗證** — 當下狀態 2026-10-03（沙盒）
reference: `MRL_Reference_Layer/MRL_SwiftUI_NavigationCookbook_Reference_v1.md`（Apple WWDC22 session 10054「The SwiftUI cookbook for navigation」）

## 新增項目（Additive-Only）

1. `ios/MRL_3DScanner_iOS/Views/ScansStackListView.swift`（新檔，iOS 16+，型別皆標 `@available(iOS 16.0, *)`）
   - `ScanRoute` — 值導航路由 `enum ScanRoute: Hashable, Codable { case detail(UUID); case bridge(UUID) }`
   - `ScanNavigationModel` — `ObservableObject`（`@MainActor`），持有 `@Published var path: [ScanRoute]`；`jsonData` / `restore(from:)` / `open(url:)` / `routes(for:)`
   - `ScansStackListView` — 與 `ScansListView` 同 UI / 同行為（Create Scan Folder、Scans 清單、Reload toolbar、標題 `MRL 3D Scanner`），改用 `NavigationStack(path:)`
   - `ScanStackDetailView` — 與 `ScanDetailView` 同內容，Bridge 連結改為 `NavigationLink("Reconstruction Bridge", value: ScanRoute.bridge(scan.id))`；目的地沿用既有 `ReconstructionBridgeView(scan:)`
2. `docs/04_PATCH_NOTES_NavigationStack_v1.md`（本檔）
3. `CHECKSUMS.sha256` / `MANIFEST.json` 追加上述兩檔；`MANIFEST.json` 的 `file_count` 30 → 32（唯一更動的既有欄位）。

## 未改動（byte-identical）

- `ios/MRL_3DScanner_iOS/PhotogramApp.swift`（入口仍為 `ScansListView()`）
- `ios/MRL_3DScanner_iOS/Views/ScansListView.swift`（`ScansListView` / `ScanDetailView`）
- `ios/MRL_3DScanner_iOS/Views/ReconstructionBridgeView.swift`
- `ios/MRL_3DScanner_iOS/Models/Scan.swift`（`Scan` 未加任何 extension / conformance；路由以 `scan.id: UUID` 為鍵，避開 `Scan` 非 `Hashable`）
- 其餘既有檔案與其 CHECKSUMS / MANIFEST 條目。

## 設計

| 面向 | 實作 | 說明 |
|---|---|---|
| Routes | `ScanRoute.detail(UUID)` / `.bridge(UUID)` | 連結只帶值（scan id），不直接建構目的 View；`Hashable` + `Codable` 皆由編譯器合成（Swift 5.5+ 支援帶 associated value 的 enum Codable 合成）|
| Path | `@Published var path: [ScanRoute]` 綁定 `NavigationStack(path: $model.path)` | 型別化陣列，可程式化 push / pop-to-root、可序列化 |
| Destination | 單一 `.navigationDestination(for: ScanRoute.self)`（掛在 root `List` 上）| 依 id 從 `store.scans` 取回 `Scan`；找不到（已刪除 / 還原到舊 id / 錯誤 deep link）時顯示 `Text("Scan not found")`，不 crash |
| 狀態還原 | `@SceneStorage("mrl3d.navigation.path") var pathData: Data?` | `onAppear` 還原一次（`restore(from:)`，JSON 解碼失敗則忽略、維持空 path）；`onChange(of: model.path)` 時寫回 `jsonData` |
| Deep link | `.onOpenURL { model.open(url:) }` | 見下表；合法連結**取代**整條 path（等同回 root 再 push）；非法連結回傳 `false` 並忽略 |

Deep link 對照：

| URL | 結果 path |
|---|---|
| `mrl3d://scan/<uuid>` | `[.detail(uuid)]` |
| `mrl3d://scan/<uuid>/bridge` | `[.detail(uuid), .bridge(uuid)]` |
| 其他 scheme / host 非 `scan` / uuid 無法解析 / 多餘路徑段 | 忽略（`open(url:)` 回傳 `false`）|

- scheme 與 host 比對不分大小寫；結尾斜線（`mrl3d://scan/<uuid>/`）視同無斜線。
- 啟動順序保護：若 deep link 先於 `onAppear` 到達，`didRestore` 旗標使已儲存的舊 path 不會覆蓋 deep link。
- URL 解析為純函式 `ScanNavigationModel.routes(for:)`（`nonisolated static`），可獨立單元測試。

## 起動方式（待起動 — 本次未套用）

起動 = 改 `PhotogramApp.swift` 一行（前提：Xcode target 的 iOS Deployment Target ≥ 16.0）：

```swift
// 現況
ScansListView()
// 起動後
ScansStackListView()
```

`.environmentObject(store)` 保持不變（`ScansStackListView` 同樣以 `@EnvironmentObject` 取得 `ScanStore`）。

- 若 Deployment Target < 16.0：改用 `if #available(iOS 16.0, *) { ScansStackListView() } else { ScansListView() }`，兩者都需掛 `.environmentObject(store)`。
- Deep link 須另在 Xcode target → Info → URL Types 新增 URL Scheme `mrl3d`（即 Info.plist 的 `CFBundleURLTypes` / `CFBundleURLSchemes`）。未註冊時 `onOpenURL` 不會觸發，但清單、推疊導航與狀態還原不受影響。
- **本包未做 URL scheme 註冊**：本包內沒有 Xcode 專案或 Info.plist 可改。2026-10-03（沙盒）以 `find` 查核：本包內無 `*.xcodeproj`、`*.xcworkspace`、`Info.plist`／任何 `*.plist`、`Package.swift`、`*.entitlements`；`included/*.zip` 三個壓縮檔內亦無上述檔案與 `.swift` 檔；整個 repo 亦無 `*.xcodeproj` / `Info.plist`。Xcode 專案位於本包以外（使用者實機端）。

## 回退（Rollback）

- 把 `PhotogramApp.swift` 該行改回 `ScansListView()` 即完成回退（怎麼過去，就怎麼回來）。
- `ScansStackListView.swift` 可留在 target 內（未被引用，不影響行為），或自 target 移除。
- SceneStorage key `mrl3d.navigation.path` 殘留無害；若已加 URL Types `mrl3d`，可保留或移除（回退後無人處理該 URL）。

## 驗收重點（全部待實機）

- [ ] Xcode（iOS 16+ SDK）編譯通過，無新增錯誤（`NavigationStack(path:root:)`、`navigationDestination(for:destination:)`、`NavigationLink(value:)`、`onChange(of:perform:)`、`@SceneStorage` `Data?`）
- [ ] 清單 / 建立掃描資料夾 / Reload 行為與 `ScansListView` 一致
- [ ] 清單 → Detail → Reconstruction Bridge 推疊與返回正常
- [ ] 狀態還原：進入 Bridge 後切到背景，由 Xcode 停止 app，重新啟動後回到同一畫面（使用者在 App Switcher 手動滑掉時系統會丟棄 scene 狀態，屬正常）
- [ ] Deep link：`xcrun simctl openurl booted "mrl3d://scan/<uuid>"` 與 `.../bridge`（需先註冊 URL Types）
- [ ] 非法 deep link（錯 scheme、非 UUID、多餘路徑段）被忽略，不 crash
- [ ] 已刪除掃描的還原 / deep link 顯示「Scan not found」，不 crash
- 備註：`onChange(of:perform:)` 於 iOS 17 SDK 標為 deprecated；Deployment Target 維持 16 時無警告，若提升至 17+ 會出現 deprecation warning（非錯誤），屆時可改用雙參數版 `onChange(of:) { old, new in }`。

## 誠實狀態

- 沙盒（Linux）無 `swiftc` / `swift` / `xcodebuild`，且 Linux 無 SwiftUI：**未編譯、未實跑、未做 UI 驗收**。
- 沙盒僅做 lexical 檢查（括號配對、4 空白縮排、無 tab / 行尾空白）——**不是編譯**，不能代替 Xcode build。
- 入口未接線：`PhotogramApp` 仍使用 `ScansListView`，本次新增不影響既有行為。
- 待起動 / 待實機驗證 — 當下狀態 2026-10-03（沙盒）。
