#requires -Version 5.1
<#
.SYNOPSIS
Stages the verified official Qdrant Windows archive in a new directory on D:.
.DESCRIPTION
origin_signature: MrLiouWord
Download/extract only. Never starts a process, installs a service, opens a port,
changes a running Qdrant configuration, or claims storage/runtime acceptance.
The fixed source was verified against GitHub release asset 612861224.
Every run creates a unique child directory and refuses overwrites.
#>
[CmdletBinding()]
param(
    [string]$StageRoot = 'D:\MRL_Mother\Dependencies\Qdrant',
    [string]$ExpectedClientHost
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$Stage = 'preflight'
$RunDirectory = $null
$SourceUrl = 'https://github.com/qdrant/qdrant/releases/download/v1.19.2/qdrant-x86_64-pc-windows-msvc.zip'
$ExpectedArchiveSha256 = '7d86596f16c6e85d45a50312f5e16ccb51e059b62e3d7308110cb65b4c799a4d'
$ExpectedArchiveBytes = [long]30243552
$AllowedDownloadHosts = @(
    'github.com',
    'release-assets.githubusercontent.com',
    'objects.githubusercontent.com',
    'github-releases.githubusercontent.com'
)

function Assert-LocalDPath {
    param([Parameter(Mandatory = $true)][string]$Value)
    if (-not [System.IO.Path]::IsPathRooted($Value)) {
        throw 'absolute_d_path_required'
    }
    $Full = [System.IO.Path]::GetFullPath($Value)
    if (-not $Full.StartsWith('D:\', [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'local_d_path_required'
    }
    $Probe = $Full.TrimEnd('\')
    while ($Probe) {
        if (Test-Path -LiteralPath $Probe) {
            $Item = Get-Item -LiteralPath $Probe -Force
            if (($Item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw 'reparse_point_not_allowed_in_stage_path'
            }
        }
        $Parent = [System.IO.Path]::GetDirectoryName($Probe)
        if ($Parent -eq $Probe) { break }
        $Probe = $Parent
    }
    return $Full
}

function Write-ExclusiveUtf8 {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Text
    )
    $Final = Assert-LocalDPath -Value $Path
    $Temporary = $Final + '.' + [guid]::NewGuid().ToString('N') + '.tmp'
    $Bytes = (New-Object System.Text.UTF8Encoding($false)).GetBytes($Text + [Environment]::NewLine)
    $Stream = $null
    try {
        $Stream = New-Object System.IO.FileStream(
            $Temporary, [System.IO.FileMode]::CreateNew,
            [System.IO.FileAccess]::Write, [System.IO.FileShare]::None
        )
        $Stream.Write($Bytes, 0, $Bytes.Length)
        $Stream.Flush($true)
        $Stream.Dispose()
        $Stream = $null
        # Same-directory atomic move; File.Move does not replace an existing file.
        [System.IO.File]::Move($Temporary, $Final)
    }
    finally {
        if ($null -ne $Stream) { $Stream.Dispose() }
        if (Test-Path -LiteralPath $Temporary) {
            Remove-Item -LiteralPath $Temporary -Force
        }
    }
}

try {
    if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
        throw 'windows_required'
    }
    if (-not [Environment]::Is64BitOperatingSystem) {
        throw 'windows_x64_required'
    }
    if ($ExpectedClientHost -and
        -not [string]::Equals([Environment]::MachineName, $ExpectedClientHost,
                            [StringComparison]::OrdinalIgnoreCase)) {
        throw 'client_hostname_mismatch'
    }
    $Drive = New-Object System.IO.DriveInfo('D:\')
    if (-not $Drive.IsReady -or $Drive.DriveType -ne [System.IO.DriveType]::Fixed) {
        throw 'local_fixed_d_drive_required'
    }
    $ResolvedStageRoot = Assert-LocalDPath -Value $StageRoot
    if (-not (Test-Path -LiteralPath $ResolvedStageRoot)) {
        New-Item -ItemType Directory -Path $ResolvedStageRoot | Out-Null
    }
    $ResolvedStageRoot = Assert-LocalDPath -Value $ResolvedStageRoot
    $RunName = 'qdrant-v1.19.2-' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ') +
        '-' + [guid]::NewGuid().ToString('N')
    $RunDirectory = Join-Path $ResolvedStageRoot $RunName
    New-Item -ItemType Directory -Path $RunDirectory | Out-Null
    $RunDirectory = Assert-LocalDPath -Value $RunDirectory
    $ArchivePath = Join-Path $RunDirectory 'qdrant-x86_64-pc-windows-msvc.zip'
    $ArchivePartial = $ArchivePath + '.partial'

    $Stage = 'download'
    Add-Type -AssemblyName System.Net.Http
    $OldSecurityProtocol = [Net.ServicePointManager]::SecurityProtocol
    [Net.ServicePointManager]::SecurityProtocol =
        $OldSecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
    $Handler = New-Object System.Net.Http.HttpClientHandler
    $Handler.AllowAutoRedirect = $false
    $Client = New-Object System.Net.Http.HttpClient($Handler)
    $Client.DefaultRequestHeaders.UserAgent.ParseAdd('MRL-Recovery-Validator/1.0')
    $Cancellation = New-Object System.Threading.CancellationTokenSource
    $Cancellation.CancelAfter([TimeSpan]::FromSeconds(180))
    $Response = $null
    $NetworkStream = $null
    $FileStream = $null
    try {
        $CurrentUri = [Uri]$SourceUrl
        for ($RedirectCount = 0; $RedirectCount -le 5; $RedirectCount++) {
            if ($CurrentUri.Scheme -ne 'https' -or
                $AllowedDownloadHosts -notcontains $CurrentUri.Host.ToLowerInvariant() -or
                $CurrentUri.UserInfo) {
                throw 'download_redirect_origin_not_allowed'
            }
            $Response = $Client.GetAsync(
                $CurrentUri, [Net.Http.HttpCompletionOption]::ResponseHeadersRead,
                $Cancellation.Token
            ).GetAwaiter().GetResult()
            $HttpStatus = [int]$Response.StatusCode
            if ($HttpStatus -in @(301, 302, 303, 307, 308)) {
                $Location = $Response.Headers.Location
                if ($null -eq $Location -or $RedirectCount -eq 5) {
                    throw 'download_redirect_limit_or_missing_location'
                }
                $CurrentUri = New-Object System.Uri($CurrentUri, $Location)
                $Response.Dispose()
                $Response = $null
                continue
            }
            if ($HttpStatus -ne 200) { throw 'download_http_status_not_200' }
            break
        }
        if ($null -eq $Response) { throw 'download_response_missing' }
        $ContentLength = $Response.Content.Headers.ContentLength
        if ($null -ne $ContentLength -and [long]$ContentLength -ne $ExpectedArchiveBytes) {
            throw 'download_content_length_mismatch'
        }
        $NetworkStream = $Response.Content.ReadAsStreamAsync().GetAwaiter().GetResult()
        $FileStream = New-Object System.IO.FileStream(
            $ArchivePartial, [System.IO.FileMode]::CreateNew,
            [System.IO.FileAccess]::Write, [System.IO.FileShare]::None
        )
        $Buffer = New-Object byte[] 81920
        $Total = [long]0
        while ($true) {
            $Read = $NetworkStream.ReadAsync(
                $Buffer, 0, $Buffer.Length, $Cancellation.Token
            ).GetAwaiter().GetResult()
            if ($Read -eq 0) { break }
            $Total += $Read
            if ($Total -gt $ExpectedArchiveBytes) { throw 'download_exceeds_expected_size' }
            $FileStream.Write($Buffer, 0, $Read)
        }
        $FileStream.Flush($true)
        if ($Total -ne $ExpectedArchiveBytes) { throw 'download_size_mismatch' }
    }
    finally {
        if ($null -ne $FileStream) { $FileStream.Dispose() }
        if ($null -ne $NetworkStream) { $NetworkStream.Dispose() }
        if ($null -ne $Response) { $Response.Dispose() }
        $Cancellation.Dispose()
        $Client.Dispose()
        $Handler.Dispose()
        [Net.ServicePointManager]::SecurityProtocol = $OldSecurityProtocol
    }

    $Stage = 'archive_hash'
    $ActualArchiveSha256 = (Get-FileHash -LiteralPath $ArchivePartial -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($ActualArchiveSha256 -ne $ExpectedArchiveSha256) { throw 'archive_sha256_mismatch' }
    [System.IO.File]::Move($ArchivePartial, $ArchivePath)

    $Stage = 'archive_validation_and_extraction'
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $Expanded = Join-Path $RunDirectory 'expanded'
    New-Item -ItemType Directory -Path $Expanded | Out-Null
    $Boundary = $Expanded.TrimEnd('\') + '\'
    $Zip = [IO.Compression.ZipFile]::OpenRead($ArchivePath)
    $Planned = New-Object 'System.Collections.Generic.List[object]'
    $Destinations = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
    $UncompressedBytes = [long]0
    try {
        if ($Zip.Entries.Count -eq 0 -or $Zip.Entries.Count -gt 512) {
            throw 'archive_entry_count_invalid'
        }
        foreach ($Entry in $Zip.Entries) {
            $Relative = $Entry.FullName.Replace('/', '\')
            if ([string]::IsNullOrWhiteSpace($Relative) -or
                [IO.Path]::IsPathRooted($Relative) -or $Relative.Contains(':') -or
                $Relative -match '(^|\\)\.\.(\\|$)') {
                throw 'archive_entry_path_invalid'
            }
            $UnixType = (($Entry.ExternalAttributes -shr 16) -band 61440)
            if ($UnixType -eq 40960) { throw 'archive_symlink_not_allowed' }
            $Destination = [IO.Path]::GetFullPath((Join-Path $Expanded $Relative))
            if (-not $Destination.StartsWith($Boundary, [StringComparison]::OrdinalIgnoreCase)) {
                throw 'archive_entry_escapes_stage'
            }
            $IsDirectory = $Entry.FullName.EndsWith('/') -or $Entry.FullName.EndsWith('\')
            if (-not $Destinations.Add($Destination.TrimEnd('\'))) {
                throw 'archive_duplicate_destination'
            }
            if (-not $IsDirectory -and $Entry.Length -le 0) {
                throw 'archive_empty_file'
            }
            $UncompressedBytes += $Entry.Length
            if ($UncompressedBytes -gt [long]1073741824) { throw 'archive_expanded_size_limit' }
            $Planned.Add([pscustomobject]@{
                Entry = $Entry; Destination = $Destination; IsDirectory = $IsDirectory
            })
        }
        foreach ($Plan in $Planned) {
            if ($Plan.IsDirectory) {
                [IO.Directory]::CreateDirectory($Plan.Destination) | Out-Null
            }
            else {
                [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($Plan.Destination)) | Out-Null
                [IO.Compression.ZipFileExtensions]::ExtractToFile(
                    $Plan.Entry, $Plan.Destination, $false
                )
                if ((Get-Item -LiteralPath $Plan.Destination).Length -ne $Plan.Entry.Length) {
                    throw 'extracted_file_size_mismatch'
                }
            }
        }
    }
    finally {
        $Zip.Dispose()
    }

    $Stage = 'executable_and_package_verification'
    $Executables = @(Get-ChildItem -LiteralPath $Expanded -File -Recurse -Filter 'qdrant.exe')
    if ($Executables.Count -ne 1) { throw 'exactly_one_qdrant_executable_required' }
    $PeStream = [IO.File]::OpenRead($Executables[0].FullName)
    try {
        if ($PeStream.ReadByte() -ne 77 -or $PeStream.ReadByte() -ne 90) {
            throw 'qdrant_executable_missing_pe_signature'
        }
    }
    finally { $PeStream.Dispose() }
    $Files = @(Get-ChildItem -LiteralPath $Expanded -File -Recurse)
    $PlannedFileCount = @($Planned | Where-Object { -not $_.IsDirectory }).Count
    if ($Files.Count -ne $PlannedFileCount) { throw 'extracted_package_count_mismatch' }
    $FileEvidence = @($Files | Sort-Object FullName | ForEach-Object {
        [ordered]@{
            relative_path = $_.FullName.Substring($Boundary.Length)
            bytes = $_.Length
            sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    })
    $ExecutablePath = $Executables[0].FullName
    $ExecutableHash = (Get-FileHash -LiteralPath $ExecutablePath -Algorithm SHA256).Hash.ToLowerInvariant()
    $Receipt = [ordered]@{
        schema = 'MRL_Qdrant_Stage_v1'
        origin_signature = 'MrLiouWord'
        recorded_at_utc = [DateTime]::UtcNow.ToString('o')
        status = 'STAGED_VERIFIED'
        source_url = $SourceUrl
        source_release = 'v1.19.2'
        github_release_asset_id = 612861224
        archive_bytes = $ExpectedArchiveBytes
        archive_sha256 = $ActualArchiveSha256
        stage_directory = $RunDirectory
        executable_path = $ExecutablePath
        executable_sha256 = $ExecutableHash
        extracted_file_count = $Files.Count
        extracted_files = $FileEvidence
        observed_client_host = [Environment]::MachineName
        powershell_version = $PSVersionTable.PSVersion.ToString()
        server_started = $false
        service_installed = $false
        runtime_acceptance = 'NOT_RUN'
        storage_write_read_delete_acceptance = 'NOT_RUN'
    }
    $ReceiptPath = Join-Path $RunDirectory 'stage-receipt.json'
    Write-ExclusiveUtf8 -Path $ReceiptPath -Text ($Receipt | ConvertTo-Json -Depth 8)
    $Receipt['receipt_path'] = $ReceiptPath
    $Receipt['receipt_sha256'] = (Get-FileHash -LiteralPath $ReceiptPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $Receipt | ConvertTo-Json -Depth 8 -Compress
    exit 0
}
catch {
    [ordered]@{
        schema = 'MRL_Qdrant_Stage_v1'
        origin_signature = 'MrLiouWord'
        status = 'STAGING_FAILED'
        failed_stage = $Stage
        error_type = $_.Exception.GetType().FullName
        stage_directory = $RunDirectory
        observed_client_host = [Environment]::MachineName
        server_started = $false
        service_installed = $false
        runtime_acceptance = 'NOT_RUN'
    } | ConvertTo-Json -Depth 5 -Compress
    exit 2
}
