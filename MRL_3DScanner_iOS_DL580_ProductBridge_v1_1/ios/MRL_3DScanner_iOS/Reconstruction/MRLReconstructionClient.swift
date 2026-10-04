import Foundation
import Combine

enum MRLReconstructionClientError: LocalizedError {
    case badServerURL(String)
    case noCaptureFiles(String)

    var errorDescription: String? {
        switch self {
        case .badServerURL(let value): return "Invalid DL580 server URL: \(value)"
        case .noCaptureFiles(let path): return "No supported image files found in raw folder: \(path)"
        }
    }
}

final class MRLReconstructionClient: ObservableObject {
    @Published var serverBaseURL: String = UserDefaults.standard.string(forKey: "MRL_DL580_ServerURL") ?? "http://127.0.0.1:3050"
    typealias FileUpload = (URLRequest, URL) async throws -> (Data, URLResponse)
    private let uploadFile: FileUpload
    private let temporaryDirectory: URL

    init(temporaryDirectory: URL = FileManager.default.temporaryDirectory,
         uploadFile: @escaping FileUpload = { request, file in
             try await URLSession.shared.upload(for: request, fromFile: file)
         }) {
        self.temporaryDirectory = temporaryDirectory
        self.uploadFile = uploadFile
    }

    func saveServerURL(_ url: String) {
        serverBaseURL = normalized(url)
        UserDefaults.standard.set(serverBaseURL, forKey: "MRL_DL580_ServerURL")
    }

    func upload(scan: Scan) async throws -> MRLUploadResponse {
        let boundary = "MRLBOUNDARY-\(UUID().uuidString)"
        var request = URLRequest(url: try endpoint("/api/scans/upload"))
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        request.setValue(scan.id.uuidString, forHTTPHeaderField: "X-MRL-Scan-ID")
        request.setValue(scan.name, forHTTPHeaderField: "X-MRL-Scan-Name")

        let files = (try? FileManager.default.imageFileURLs(in: scan.rawFolder)) ?? []
        guard !files.isEmpty else { throw MRLReconstructionClientError.noCaptureFiles(scan.rawFolder.path) }

        let body = try MRLMultipartBody.write(files: files, boundary: boundary, in: temporaryDirectory)
        defer { body.remove() }
        try Task.checkCancellation()
        let (data, response) = try await uploadFile(request, body.fileURL)
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            throw URLError(.badServerResponse)
        }
        return try JSONDecoder().decode(MRLUploadResponse.self, from: data)
    }

    func createJob(scanId: UUID, mode: String = "auto") async throws -> MRLJobCreateResponse {
        var request = URLRequest(url: try endpoint("/api/reconstruction/jobs"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: ["scanId": scanId.uuidString, "mode": mode])
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else { throw URLError(.badServerResponse) }
        return try JSONDecoder().decode(MRLJobCreateResponse.self, from: data)
    }

    func getJob(jobId: String) async throws -> MRLReconstructionJob {
        let (data, response) = try await URLSession.shared.data(from: try endpoint("/api/reconstruction/jobs/\(jobId)"))
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else { throw URLError(.badServerResponse) }
        return try JSONDecoder().decode(MRLReconstructionJob.self, from: data)
    }

    private func endpoint(_ path: String) throws -> URL {
        let base = normalized(serverBaseURL)
        guard let url = URL(string: "\(base)\(path)") else { throw MRLReconstructionClientError.badServerURL(serverBaseURL) }
        return url
    }

    private func normalized(_ value: String) -> String {
        var v = value.trimmingCharacters(in: .whitespacesAndNewlines)
        while v.hasSuffix("/") { v.removeLast() }
        return v
    }

}

// A unique file per upload avoids retaining the scan in RAM. Keep it alive
// through the awaited upload, including retries, then clean up on every exit.
struct MRLMultipartBody {
    let fileURL: URL
    static let chunkSize = 64 * 1024

    func remove() {
        try? FileManager.default.removeItem(at: fileURL.deletingLastPathComponent())
    }

    static func write(files: [URL], boundary: String, in temporaryDirectory: URL) throws -> Self {
        try Task.checkCancellation()
        let directory = temporaryDirectory.appendingPathComponent("MRLUpload-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        let body = Self(fileURL: directory.appendingPathComponent("multipart.body"))
        var complete = false
        defer { if !complete { body.remove() } }
        guard FileManager.default.createFile(atPath: body.fileURL.path, contents: nil) else {
            throw CocoaError(.fileWriteUnknown)
        }
        let output = try FileHandle(forWritingTo: body.fileURL)
        defer { try? output.close() }
        for file in files {
            try Task.checkCancellation()
            let input = try FileHandle(forReadingFrom: file)
            defer { try? input.close() }
            // Percent-escape characters that could break a multipart header.
            let filename = file.lastPathComponent
                .replacingOccurrences(of: "%", with: "%25")
                .replacingOccurrences(of: "\r", with: "%0D")
                .replacingOccurrences(of: "\n", with: "%0A")
                .replacingOccurrences(of: "\"", with: "%22")
            try output.write(contentsOf: Data("--\(boundary)\r\nContent-Disposition: form-data; name=\"files\"; filename=\"\(filename)\"\r\nContent-Type: \(mimeType(for: file))\r\n\r\n".utf8))
            while try autoreleasepool(invoking: {
                try Task.checkCancellation()
                guard let chunk = try input.read(upToCount: chunkSize), !chunk.isEmpty else { return false }
                try output.write(contentsOf: chunk)
                return true
            }) {}
            try output.write(contentsOf: Data("\r\n".utf8))
        }
        try output.write(contentsOf: Data("--\(boundary)--\r\n".utf8))
        try output.close()
        complete = true
        return body
    }

    private static func mimeType(for file: URL) -> String {
        switch file.pathExtension.lowercased() {
        case "png": return "image/png"
        case "heic": return "image/heic"
        case "jpg", "jpeg": return "image/jpeg"
        default: return "application/octet-stream"
        }
    }
}
