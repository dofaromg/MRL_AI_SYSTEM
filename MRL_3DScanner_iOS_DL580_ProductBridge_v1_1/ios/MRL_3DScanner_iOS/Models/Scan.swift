import Foundation
import Combine

struct Scan: Identifiable, Codable, Equatable {
    let id: UUID
    var name: String
    var createdAt: Date
    var imageCount: Int
    var vertsHint: Int?
    var sizeMB: Double
    var hasTexture: Bool
    var folder: URL
    var modelURL: URL?

    var rawFolder: URL { folder.appendingPathComponent("raw", isDirectory: true) }
    var manifestURL: URL { folder.appendingPathComponent("manifest.json") }
    var metaURL: URL { folder.appendingPathComponent("scan.json") }

    // The enumerated directory is authoritative after an iOS container move.
    // Preserve external URLs; only descendants of the old scan folder move.
    func rebased(to currentFolder: URL) -> Scan {
        var scan = self
        if let model = modelURL, model.isFileURL, folder.isFileURL {
            let oldComponents = folder.standardizedFileURL.pathComponents
            let modelComponents = model.standardizedFileURL.pathComponents
            if modelComponents.count > oldComponents.count,
               modelComponents.starts(with: oldComponents) {
                scan.modelURL = modelComponents.dropFirst(oldComponents.count)
                    .reduce(currentFolder) { $0.appendingPathComponent($1) }
            }
        }
        scan.folder = currentFolder
        return scan
    }

    static func makeNew(base: URL, name: String) throws -> Scan {
        let id = UUID()
        let folder = base.appendingPathComponent("Scans", isDirectory: true).appendingPathComponent(id.uuidString, isDirectory: true)
        let rawFolder = folder.appendingPathComponent("raw", isDirectory: true)
        try FileManager.default.createDirectory(at: rawFolder, withIntermediateDirectories: true)
        return Scan(id: id, name: name, createdAt: Date(), imageCount: 0, vertsHint: nil, sizeMB: 0, hasTexture: false, folder: folder, modelURL: nil)
    }
}

@MainActor
final class ScanStore: ObservableObject {
    @Published var scans: [Scan] = []
    let base: URL
    init(base: URL = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]) {
        self.base = base
        load()
    }
    func load() {
        let scansDir = base.appendingPathComponent("Scans", isDirectory: true)
        guard let children = try? FileManager.default.contentsOfDirectory(at: scansDir, includingPropertiesForKeys: nil) else { scans = []; return }
        scans = children.compactMap { dir in
            let meta = dir.appendingPathComponent("scan.json")
            guard let data = try? Data(contentsOf: meta), let scan = try? JSONDecoder.scanDecoder.decode(Scan.self, from: data) else { return nil }
            return scan.rebased(to: dir)
        }.sorted { $0.createdAt > $1.createdAt }
    }
    func save(_ scan: Scan) {
        do {
            let data = try JSONEncoder.scanEncoder.encode(scan)
            try data.write(to: scan.metaURL, options: [.atomic])
            if let idx = scans.firstIndex(where: { $0.id == scan.id }) { scans[idx] = scan } else { scans.insert(scan, at: 0) }
            scans.sort { $0.createdAt > $1.createdAt }
        } catch { print("save scan failed", error) }
    }
}

extension JSONEncoder {
    static var scanEncoder: JSONEncoder { let e = JSONEncoder(); e.dateEncodingStrategy = .iso8601; e.outputFormatting = [.prettyPrinted, .sortedKeys]; return e }
}
extension JSONDecoder {
    static var scanDecoder: JSONDecoder { let d = JSONDecoder(); d.dateDecodingStrategy = .iso8601; return d }
}
