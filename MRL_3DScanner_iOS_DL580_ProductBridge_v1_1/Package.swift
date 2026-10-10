// swift-tools-version: 5.9
import PackageDescription

// Compiles the actual client/model sources for regression tests. This is not
// an iOS application target and does not activate the NavigationStack view.
let package = Package(
    name: "MRLScannerHardening",
    platforms: [.macOS(.v12), .iOS(.v15)],
    targets: [
        .target(
            name: "MRLScannerCore",
            path: "ios/MRL_3DScanner_iOS",
            exclude: ["L10n.swift", "PhotogramApp.swift", "Views", "Utilities/ShareSheet.swift", "en.lproj", "zh-Hant.lproj"],
            sources: ["Models/Scan.swift", "Reconstruction/MRLReconstructionClient.swift",
                      "Reconstruction/MRLReconstructionJob.swift", "Utilities/FileManager+Tools.swift"]
        ),
        .testTarget(name: "HardeningTests", dependencies: ["MRLScannerCore"], path: "Tests/HardeningTests",
                    resources: [.copy("Fixtures")])
    ],
    swiftLanguageVersions: [.v5]
)
