import SwiftUI

// NavigationStack variant of ScansListView (iOS 16+). Additive: ScansListView / ScanDetailView are untouched.
// Status: 待起動 — not wired into PhotogramApp. 待實機驗證 — not compiled (needs Xcode / iOS 16+ SDK).
// See docs/04_PATCH_NOTES_NavigationStack_v1.md for activation / rollback.

@available(iOS 16.0, *)
enum ScanRoute: Hashable, Codable {
    case detail(UUID)
    case bridge(UUID)
}

@available(iOS 16.0, *)
@MainActor
final class ScanNavigationModel: ObservableObject {
    @Published var path: [ScanRoute] = []

    var jsonData: Data? { try? JSONEncoder().encode(path) }

    @discardableResult
    func restore(from data: Data?) -> Bool {
        guard let data, let restored = try? JSONDecoder().decode([ScanRoute].self, from: data) else { return false }
        path = restored
        return true
    }

    /// mrl3d://scan/<uuid> -> [.detail]; mrl3d://scan/<uuid>/bridge -> [.detail, .bridge]. Anything else is ignored.
    @discardableResult
    func open(url: URL) -> Bool {
        guard let routes = Self.routes(for: url) else { return false }
        path = routes
        return true
    }

    nonisolated static func routes(for url: URL) -> [ScanRoute]? {
        guard url.scheme?.lowercased() == "mrl3d", url.host?.lowercased() == "scan" else { return nil }
        let parts = url.pathComponents.filter { $0 != "/" }
        guard let first = parts.first, let id = UUID(uuidString: first) else { return nil }
        switch parts.count {
        case 1: return [.detail(id)]
        case 2 where parts[1] == "bridge": return [.detail(id), .bridge(id)]
        default: return nil
        }
    }
}

@available(iOS 16.0, *)
struct ScansStackListView: View {
    @EnvironmentObject private var store: ScanStore
    @StateObject private var model = ScanNavigationModel()
    @SceneStorage("mrl3d.navigation.path") private var pathData: Data?
    @State private var didRestore = false
    @State private var newScanName = ""
    @State private var errorText: String?

    var body: some View {
        NavigationStack(path: $model.path) {
            List {
                Section("Create Scan Folder") {
                    TextField("scan name", text: $newScanName)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                    Button("Create") { createScanFolder() }
                    if let errorText { Text(errorText).foregroundColor(.red) }
                }

                Section("Scans") {
                    if store.scans.isEmpty {
                        Text("No scans yet")
                            .foregroundColor(.secondary)
                    } else {
                        ForEach(store.scans) { scan in
                            NavigationLink(value: ScanRoute.detail(scan.id)) {
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(scan.name).font(.headline)
                                    Text("images: \(scan.imageCount) · \(scan.sizeMB, specifier: "%.2f") MB")
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                }
                            }
                        }
                    }
                }
            }
            .navigationTitle("MRL 3D Scanner")
            .toolbar { Button("Reload") { store.load() } }
            .navigationDestination(for: ScanRoute.self) { route in
                destination(for: route)
            }
        }
        .onAppear {
            // Restore once per scene; a deep link that already arrived wins over stored state.
            guard !didRestore else { return }
            didRestore = true
            model.restore(from: pathData)
        }
        .onChange(of: model.path) { _ in
            pathData = model.jsonData
        }
        .onOpenURL { url in
            if model.open(url: url) { didRestore = true }
        }
    }

    @ViewBuilder
    private func destination(for route: ScanRoute) -> some View {
        switch route {
        case .detail(let id):
            if let scan = lookupScan(id) {
                ScanStackDetailView(scan: scan)
            } else {
                missingScan
            }
        case .bridge(let id):
            if let scan = lookupScan(id) {
                ReconstructionBridgeView(scan: scan)
            } else {
                missingScan
            }
        }
    }

    private var missingScan: some View {
        Text("Scan not found").foregroundColor(.secondary)
    }

    private func lookupScan(_ id: UUID) -> Scan? {
        store.scans.first { $0.id == id }
    }

    private func createScanFolder() {
        do {
            let name = newScanName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? makeDefaultScanName() : newScanName
            let scan = try Scan.makeNew(base: store.base, name: name)
            store.save(scan)
            newScanName = ""
            errorText = nil
        } catch {
            errorText = error.localizedDescription
        }
    }

    private func makeDefaultScanName() -> String {
        let f = DateFormatter()
        f.dateFormat = "yyyyMMdd_HHmmss"
        return "scan_\(f.string(from: Date()))"
    }
}

@available(iOS 16.0, *)
struct ScanStackDetailView: View {
    let scan: Scan

    var body: some View {
        Form {
            Section("Scan") {
                Text(scan.name)
                Text(scan.id.uuidString).font(.footnote)
                Text(scan.folder.path).font(.footnote)
                Text("raw: \(scan.rawFolder.path)").font(.footnote)
            }

            Section("DL580") {
                NavigationLink("Reconstruction Bridge", value: ScanRoute.bridge(scan.id))
            }
        }
        .navigationTitle(scan.name)
    }
}
