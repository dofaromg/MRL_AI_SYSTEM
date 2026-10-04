import XCTest
import Foundation
import Darwin
@testable import MRLScannerCore

final class HardeningTests: XCTestCase {
    private var root: URL!

    override func setUpWithError() throws {
        root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString, isDirectory: true)
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
    }

    override func tearDownWithError() throws {
        try FileManager.default.removeItem(at: root)
    }

    private func file(_ name: String, _ data: Data) throws -> URL {
        let url = root.appendingPathComponent(name)
        try data.write(to: url)
        return url
    }

    private func scanWithImage() throws -> Scan {
        let scan = try Scan.makeNew(base: root, name: "MRL scan")
        try Data([0, 1, 255, 13, 10]).write(to: scan.rawFolder.appendingPathComponent("image.jpg"))
        return scan
    }

    private func temporaryBodies() throws -> [URL] {
        try FileManager.default.contentsOfDirectory(at: root, includingPropertiesForKeys: nil)
            .filter { $0.lastPathComponent.hasPrefix("MRLUpload-") }
    }

    func testMultipartPreservesBinaryBytesBoundariesAndMIMETypes() throws {
        let files = try [file("a.JPG", Data([0, 255, 13, 10])), file("b.png", Data("PNG".utf8)), file("c.heic", Data())]
        let body = try MRLMultipartBody.write(files: files, boundary: "TEST", in: root)
        defer { body.remove() }
        var expected = Data()
        for (index, mime) in ["image/jpeg", "image/png", "image/heic"].enumerated() {
            expected.append(Data("--TEST\r\nContent-Disposition: form-data; name=\"files\"; filename=\"\(files[index].lastPathComponent)\"\r\nContent-Type: \(mime)\r\n\r\n".utf8))
            expected.append(try Data(contentsOf: files[index]))
            expected.append(Data("\r\n".utf8))
        }
        expected.append(Data("--TEST--\r\n".utf8))
        XCTAssertEqual(try Data(contentsOf: body.fileURL), expected)
    }

    func testFilenameCannotInjectMultipartHeaders() throws {
        let input = try file("a\"\r\nInjected.jpg", Data([42]))
        let body = try MRLMultipartBody.write(files: [input], boundary: "TEST", in: root)
        defer { body.remove() }
        let text = try String(contentsOf: body.fileURL, encoding: .utf8)
        XCTAssertTrue(text.contains("filename=\"a%22%0D%0AInjected.jpg\""))
        XCTAssertFalse(text.contains("\r\nInjected"))
    }

    func testPartialBodyIsRemovedWhenAnInputCannotBeRead() throws {
        let first = try file("first.jpg", Data([1]))
        XCTAssertThrowsError(try MRLMultipartBody.write(files: [first, root.appendingPathComponent("missing.jpg")], boundary: "TEST", in: root))
        XCTAssertTrue(try temporaryBodies().isEmpty)
    }

    func testConcurrentBodiesHaveIndependentOwnership() throws {
        let input = try file("a.jpg", Data([1]))
        let first = try MRLMultipartBody.write(files: [input], boundary: "A", in: root)
        let second = try MRLMultipartBody.write(files: [input], boundary: "B", in: root)
        XCTAssertNotEqual(first.fileURL, second.fileURL)
        first.remove()
        XCTAssertTrue(FileManager.default.fileExists(atPath: second.fileURL.path))
        second.remove()
        XCTAssertTrue(try temporaryBodies().isEmpty)
    }

    func testUploadUsesFileAndCleansUpAfterSuccess() async throws {
        let scan = try scanWithImage()
        var uploadedFile: URL?
        let client = MRLReconstructionClient(temporaryDirectory: root) { request, file in
            uploadedFile = file
            XCTAssertNil(request.httpBody)
            XCTAssertNil(request.httpBodyStream)
            XCTAssertEqual(request.httpMethod, "POST")
            XCTAssertEqual(request.url?.path, "/api/scans/upload")
            XCTAssertEqual(request.value(forHTTPHeaderField: "X-MRL-Scan-ID"), scan.id.uuidString)
            XCTAssertEqual(request.value(forHTTPHeaderField: "X-MRL-Scan-Name"), scan.name)
            XCTAssertTrue(FileManager.default.fileExists(atPath: file.path))
            let boundary = try XCTUnwrap(request.value(forHTTPHeaderField: "Content-Type")?.components(separatedBy: "boundary=").last)
            XCTAssertTrue(try Data(contentsOf: file).suffix(Data("--\(boundary)--\r\n".utf8).count) == Data("--\(boundary)--\r\n".utf8))
            let response = HTTPURLResponse(url: request.url!, statusCode: 200, httpVersion: nil, headerFields: nil)!
            return (Data("{\"ok\":true,\"scanId\":\"\(scan.id)\",\"uploaded\":1,\"manifestPath\":\"manifest.json\"}".utf8), response)
        }
        client.serverBaseURL = "https://example.invalid"
        let result = try await client.upload(scan: scan)
        XCTAssertEqual(result.uploaded, 1)
        XCTAssertFalse(FileManager.default.fileExists(atPath: try XCTUnwrap(uploadedFile).path))
        XCTAssertTrue(try temporaryBodies().isEmpty)
    }

    func testUploadCleansUpOnNetworkHTTPDecodeAndCancellationFailures() async throws {
        let scan = try scanWithImage()
        for failure in 0..<4 {
            let client = MRLReconstructionClient(temporaryDirectory: root) { request, file in
                XCTAssertTrue(FileManager.default.fileExists(atPath: file.path))
                if failure == 0 { throw URLError(.networkConnectionLost) }
                if failure == 3 { throw CancellationError() }
                let response = HTTPURLResponse(url: request.url!, statusCode: failure == 1 ? 500 : 200, httpVersion: nil, headerFields: nil)!
                return (Data("invalid JSON".utf8), response)
            }
            client.serverBaseURL = "https://example.invalid"
            do { _ = try await client.upload(scan: scan); XCTFail("Expected failure \(failure)") }
            catch { /* Each failure must release the body. */ }
            XCTAssertTrue(try temporaryBodies().isEmpty)
        }
    }

    func testEmptyScanNeverStartsUpload() async throws {
        let scan = try Scan.makeNew(base: root, name: "empty")
        let client = MRLReconstructionClient(temporaryDirectory: root) { _, _ in
            XCTFail("An empty scan must not upload")
            throw URLError(.unknown)
        }
        do { _ = try await client.upload(scan: scan); XCTFail("Expected noCaptureFiles") }
        catch MRLReconstructionClientError.noCaptureFiles { }
        XCTAssertTrue(try temporaryBodies().isEmpty)
    }

    func testCancellationBeforeBodyCreationLeavesNoFiles() async throws {
        let input = try file("a.jpg", Data([1]))
        let directory = root!
        let task = Task {
            withUnsafeCurrentTask { $0?.cancel() }
            return try MRLMultipartBody.write(files: [input], boundary: "TEST", in: directory)
        }
        do { _ = try await task.value; XCTFail("Expected cancellation") }
        catch is CancellationError { }
        XCTAssertTrue(try temporaryBodies().isEmpty)
    }

    func testLargeScanDoesNotAllocateItsPayloadInMemory() throws {
        // Three 48 MiB images; fixture creation also uses bounded chunks.
        let chunk = Data(repeating: 0xA5, count: 64 * 1024)
        var files: [URL] = []
        for index in 0..<3 {
            let url = try file("large-\(index).jpg", Data())
            let handle = try FileHandle(forWritingTo: url)
            for _ in 0..<768 { try handle.write(contentsOf: chunk) }
            try handle.close()
            files.append(url)
        }
        var before = rusage()
        XCTAssertEqual(getrusage(RUSAGE_SELF, &before), 0)
        let body = try MRLMultipartBody.write(files: files, boundary: "LARGE", in: root)
        defer { body.remove() }
        var after = rusage()
        XCTAssertEqual(getrusage(RUSAGE_SELF, &after), 0)
        let size = try FileManager.default.attributesOfItem(atPath: body.fileURL.path)[.size] as! NSNumber
        XCTAssertGreaterThan(size.intValue, 144 * 1024 * 1024)
        // Darwin reports ru_maxrss in bytes. Allow framework overhead, but
        // reject retaining even one 144 MiB multipart body.
        XCTAssertLessThan(after.ru_maxrss - before.ru_maxrss, 64 * 1024 * 1024)
    }

    @MainActor
    func testLoadRebasesRelocatedContainerWithoutRewritingMetadata() throws {
        let oldDocuments = root.appendingPathComponent("old/Documents", isDirectory: true)
        let currentDocuments = root.appendingPathComponent("current/Documents", isDirectory: true)
        var old = try Scan.makeNew(base: oldDocuments, name: "preserve name")
        old.modelURL = old.folder.appendingPathComponent("models/sub folder/模型.usdz")
        try FileManager.default.createDirectory(at: old.modelURL!.deletingLastPathComponent(), withIntermediateDirectories: true)
        try Data([9]).write(to: old.modelURL!)
        try Data([4]).write(to: old.rawFolder.appendingPathComponent("capture.jpg"))
        let metadata = try JSONEncoder.scanEncoder.encode(old)
        try metadata.write(to: old.metaURL)
        let currentFolder = currentDocuments.appendingPathComponent("Scans/\(old.id.uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: currentFolder.deletingLastPathComponent(), withIntermediateDirectories: true)
        try FileManager.default.moveItem(at: old.folder, to: currentFolder)

        let store = ScanStore(base: currentDocuments)
        let loaded = try XCTUnwrap(store.scans.first)
        XCTAssertEqual(loaded.folder.standardizedFileURL, currentFolder.standardizedFileURL)
        XCTAssertEqual(loaded.id, old.id)
        XCTAssertEqual(loaded.name, old.name)
        XCTAssertEqual(try FileManager.default.imageFileURLs(in: loaded.rawFolder).count, 1)
        XCTAssertEqual(try Data(contentsOf: loaded.modelURL!), Data([9]))
        XCTAssertEqual(try Data(contentsOf: loaded.metaURL), metadata)
        store.save(loaded)
        store.load()
        XCTAssertEqual(store.scans, [loaded])
    }

    func testRebasePreservesExternalURLsAndDoesNotMatchSiblingPrefix() throws {
        var scan = try Scan.makeNew(base: root, name: "scan")
        let current = root.appendingPathComponent("new/Scans/current", isDirectory: true)
        let siblings = [URL(string: "https://example.invalid/model.usdz")!,
                        URL(fileURLWithPath: scan.folder.path + "-sibling/model.usdz"),
                        scan.folder.appendingPathComponent("../other/model.usdz")]
        for external in siblings {
            scan.modelURL = external
            XCTAssertEqual(scan.rebased(to: current).modelURL, external)
        }
        scan.modelURL = nil
        XCTAssertNil(scan.rebased(to: current).modelURL)
        XCTAssertEqual(scan.rebased(to: scan.folder), scan)
    }
}
