param(
    [string]$Repo = "D:\projects\fit-reasoning-vton",
    [string]$ReportDir = "D:\fit_transfer\reports"
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$Now = Get-Date
$GiB = [double]1GB
$Datasets = Join-Path $Repo "backend\datasets"

New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null

function Format-Gb([double]$Bytes) {
    [math]::Round(($Bytes / $GiB), 3)
}

function Escape-CsvValue([string]$Value) {
    if ($null -eq $Value) { return "" }
    $Escaped = $Value -replace '"', '""'
    if ($Escaped -match '[,"\r\n]') { return '"' + $Escaped + '"' }
    return $Escaped
}

function Escape-ForSingleQuotedPowerShell([string]$Value) {
    return $Value -replace "'", "''"
}

function Test-IsUnderPath([string]$Path, [string[]]$Roots) {
    if ([string]::IsNullOrWhiteSpace($Path)) { return $false }
    $CleanPath = $Path.TrimEnd("\")
    foreach ($Root in $Roots) {
        if ([string]::IsNullOrWhiteSpace($Root)) { continue }
        $CleanRoot = $Root.TrimEnd("\")
        if ($CleanPath.Equals($CleanRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
        if ($CleanPath.StartsWith($CleanRoot + "\", [System.StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }
    return $false
}

function Test-PathContainsRoot([string]$Path, [string[]]$Roots) {
    if ([string]::IsNullOrWhiteSpace($Path)) { return $false }
    foreach ($Root in $Roots) {
        if ([string]::IsNullOrWhiteSpace($Root)) { continue }
        if ($Path.TrimEnd("\").Equals($Root.TrimEnd("\"), [System.StringComparison]::OrdinalIgnoreCase)) {
            continue
        }
        if (Test-IsUnderPath $Root @($Path)) {
            return $true
        }
    }
    return $false
}

function Test-EmptyDirectory([string]$Path) {
    try {
        $Enumerator = [System.IO.Directory]::EnumerateFileSystemEntries($Path).GetEnumerator()
        try {
            return -not $Enumerator.MoveNext()
        }
        finally {
            if ($Enumerator -is [System.IDisposable]) {
                $Enumerator.Dispose()
            }
        }
    }
    catch {
        return $false
    }
}

function Get-DirStats([string]$Path) {
    $Total = [int64]0
    $Files = [int64]0
    $Dirs = [int64]0
    $Errors = New-Object System.Collections.Generic.List[string]

    if (-not (Test-Path -LiteralPath $Path)) {
        return [pscustomobject]@{
            path = $Path
            exists = $false
            size_bytes = 0
            size_gb = 0
            file_count = 0
            dir_count = 0
            error_count = 0
            errors = @()
        }
    }

    $RootPath = (Resolve-Path -LiteralPath $Path).Path
    $Stack = New-Object System.Collections.Generic.Stack[string]
    $Stack.Push($RootPath)

    while ($Stack.Count -gt 0) {
        $Current = $Stack.Pop()
        try {
            foreach ($DirPath in [System.IO.Directory]::EnumerateDirectories($Current)) {
                try {
                    $DirInfo = [System.IO.DirectoryInfo]::new($DirPath)
                    if (($DirInfo.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                        continue
                    }
                    $Dirs++
                    $Stack.Push($DirPath)
                }
                catch {
                    $Errors.Add($DirPath + " :: " + $_.Exception.Message) | Out-Null
                }
            }

            foreach ($FilePath in [System.IO.Directory]::EnumerateFiles($Current)) {
                try {
                    $FileInfo = [System.IO.FileInfo]::new($FilePath)
                    $Total += $FileInfo.Length
                    $Files++
                }
                catch {
                    $Errors.Add($FilePath + " :: " + $_.Exception.Message) | Out-Null
                }
            }
        }
        catch {
            $Errors.Add($Current + " :: " + $_.Exception.Message) | Out-Null
        }
    }

    [pscustomobject]@{
        path = $Path
        exists = $true
        size_bytes = $Total
        size_gb = (Format-Gb $Total)
        file_count = $Files
        dir_count = $Dirs
        error_count = $Errors.Count
        errors = @($Errors)
    }
}

function Get-ImmediateDirStats([string[]]$Roots) {
    $Stats = New-Object System.Collections.Generic.List[object]
    foreach ($Root in $Roots) {
        if (-not (Test-Path -LiteralPath $Root)) { continue }
        $Stats.Add((Get-DirStats $Root)) | Out-Null
        foreach ($Dir in Get-ChildItem -LiteralPath $Root -Directory -Force -ErrorAction SilentlyContinue) {
            $Stats.Add((Get-DirStats $Dir.FullName)) | Out-Null
        }
    }
    $Stats
}

function Get-FileList([string[]]$Roots, [string[]]$SkipRoots = @()) {
    $Items = New-Object System.Collections.Generic.List[object]
    foreach ($Root in $Roots) {
        if (-not (Test-Path -LiteralPath $Root)) { continue }
        $RootPath = (Resolve-Path -LiteralPath $Root).Path
        if (Test-IsUnderPath $RootPath $SkipRoots) { continue }

        $Stack = New-Object System.Collections.Generic.Stack[string]
        $Stack.Push($RootPath)

        while ($Stack.Count -gt 0) {
            $Current = $Stack.Pop()
            if (Test-IsUnderPath $Current $SkipRoots) { continue }

            try {
                foreach ($DirPath in [System.IO.Directory]::EnumerateDirectories($Current)) {
                    if (Test-IsUnderPath $DirPath $SkipRoots) { continue }
                    try {
                        $DirInfo = [System.IO.DirectoryInfo]::new($DirPath)
                        if (($DirInfo.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                            continue
                        }
                        $Stack.Push($DirPath)
                    }
                    catch {}
                }

                foreach ($FilePath in [System.IO.Directory]::EnumerateFiles($Current)) {
                    if (Test-IsUnderPath $FilePath $SkipRoots) { continue }
                    try {
                        $FileInfo = [System.IO.FileInfo]::new($FilePath)
                        $Items.Add([pscustomobject]@{
                            FullName = $FileInfo.FullName
                            Name = $FileInfo.Name
                            Extension = $FileInfo.Extension.ToLowerInvariant()
                            Length = [int64]$FileInfo.Length
                            LastWriteTime = $FileInfo.LastWriteTime
                            DirectoryName = $FileInfo.DirectoryName
                        }) | Out-Null
                    }
                    catch {}
                }
            }
            catch {}
        }
    }
    $Items
}

function Get-DirectoryList([string[]]$Roots, [string[]]$SkipRoots = @()) {
    $Items = New-Object System.Collections.Generic.List[object]
    foreach ($Root in $Roots) {
        if (-not (Test-Path -LiteralPath $Root)) { continue }
        $RootPath = (Resolve-Path -LiteralPath $Root).Path
        if (Test-IsUnderPath $RootPath $SkipRoots) { continue }

        $Stack = New-Object System.Collections.Generic.Stack[string]
        $Stack.Push($RootPath)

        while ($Stack.Count -gt 0) {
            $Current = $Stack.Pop()
            if (Test-IsUnderPath $Current $SkipRoots) { continue }

            try {
                foreach ($DirPath in [System.IO.Directory]::EnumerateDirectories($Current)) {
                    if (Test-IsUnderPath $DirPath $SkipRoots) { continue }
                    try {
                        $DirInfo = [System.IO.DirectoryInfo]::new($DirPath)
                        if (($DirInfo.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                            continue
                        }
                        $Items.Add([pscustomobject]@{
                            FullName = $DirInfo.FullName
                            Name = $DirInfo.Name
                            LastWriteTime = $DirInfo.LastWriteTime
                        }) | Out-Null
                        $Stack.Push($DirPath)
                    }
                    catch {}
                }
            }
            catch {}
        }
    }
    $Items
}

function Count-CsvRows([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    $Count = 0
    $Reader = [System.IO.File]::OpenText($Path)
    try {
        while ($null -ne $Reader.ReadLine()) { $Count++ }
    }
    finally {
        $Reader.Close()
    }
    if ($Count -gt 0) { return ($Count - 1) }
    return 0
}

function Add-Row(
    [System.Collections.Generic.List[object]]$Rows,
    [string]$Path,
    [string]$Type,
    [double]$SizeBytes,
    [string]$Recommendation,
    [string]$Reason,
    [bool]$Safe,
    [bool]$Approval
) {
    $Rows.Add([pscustomobject]@{
        path = $Path
        type = $Type
        size_gb = Format-Gb $SizeBytes
        recommendation = $Recommendation
        reason = $Reason
        safe_to_delete = $Safe
        requires_user_approval = $Approval
    }) | Out-Null
}

function Add-Estimate(
    [System.Collections.Generic.List[object]]$Rows,
    [string]$Name,
    [double]$BaseBytes,
    [string]$Basis,
    [double]$Multiplier
) {
    $Estimate = [int64]($BaseBytes * $Multiplier)
    $Rows.Add([pscustomobject]@{
        component = $Name
        basis = $Basis
        base_10k_gb = Format-Gb $BaseBytes
        multiplier = $Multiplier
        estimate_39k_gb = Format-Gb $Estimate
        estimate_39k_bytes = $Estimate
    }) | Out-Null
}

$DiskInfo = Get-PSDrive -PSProvider FileSystem |
    Where-Object { $_.Name -in @("C", "D") } |
    ForEach-Object {
        [pscustomobject]@{
            drive = $_.Name
            free_bytes = [int64]$_.Free
            used_bytes = [int64]$_.Used
            free_gb = Format-Gb $_.Free
            used_gb = Format-Gb $_.Used
        }
    }

$Specified = @(
    "D:\projects\fit-reasoning-vton\backend\datasets",
    "D:\projects\fit-reasoning-vton\backend\datasets\processed",
    "D:\projects\fit-reasoning-vton\backend\datasets\raw",
    "D:\projects\fit-reasoning-vton\backend\datasets\lora_pilot_aihub_10k",
    "D:\projects\fit-reasoning-vton\backend\datasets\lora_pilot_aihub_10k_artifact",
    "D:\projects\fit-reasoning-vton\backend\datasets\lora_pilot_aihub_30k",
    "D:\fit_transfer",
    "C:\fit_transfer"
)

$DiskUsage = @($Specified | ForEach-Object { Get-DirStats $_ } | Sort-Object size_bytes -Descending)

$TopFolderRoots = @(
    "D:\fit_transfer",
    "C:\fit_transfer",
    $Datasets,
    (Join-Path $Datasets "processed")
)
$TopFolders = @(Get-ImmediateDirStats $TopFolderRoots |
    Sort-Object size_bytes -Descending |
    Group-Object path |
    ForEach-Object { $_.Group | Select-Object -First 1 } |
    Sort-Object size_bytes -Descending |
    Select-Object -First 20)

$ProtectedRoots = @(
    "D:\projects\fit-reasoning-vton\backend\datasets\raw",
    "D:\projects\fit-reasoning-vton\backend\datasets\processed\index",
    "D:\projects\fit-reasoning-vton\backend\datasets\processed\aihub_stableviton_explicit_pending",
    "D:\projects\fit-reasoning-vton\backend\datasets\lora_pilot_aihub_10k_artifact",
    "D:\fit_transfer\lora_pilot_aihub_10k_artifact_patch_v1",
    "D:\fit_transfer\send_10k_artifact_patch",
    "D:\fit_transfer\lora_pilot_aihub_10k_agnostic_v3_full",
    "D:\fit_transfer\lora_pilot_aihub_10k_artifact_patch_v1.zip",
    "D:\fit_transfer\lora_pilot_aihub_10k_agnostic_v3_full.zip",
    (Join-Path $Repo "scripts"),
    (Join-Path $Repo "backend\app"),
    (Join-Path $Repo "backend\training"),
    (Join-Path $Repo "frontend"),
    (Join-Path $Repo "configs"),
    (Join-Path $Repo "docs")
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }

$DoNotDeleteWholePaths = @(
    $Repo,
    $Datasets,
    "D:\projects\fit-reasoning-vton\backend\datasets\processed",
    "D:\fit_transfer",
    "C:\fit_transfer"
) + $ProtectedRoots
$DoNotDeleteWholePaths = @($DoNotDeleteWholePaths | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique)

$CandidateRoots = @($Datasets, "D:\fit_transfer", "C:\fit_transfer") |
    Where-Object { Test-Path -LiteralPath $_ }
$SkipForCandidateScan = @(
    "D:\projects\fit-reasoning-vton\backend\datasets\raw",
    "D:\projects\fit-reasoning-vton\backend\datasets\processed\index",
    "D:\projects\fit-reasoning-vton\backend\datasets\processed\aihub_stableviton_explicit_pending",
    "D:\projects\fit-reasoning-vton\backend\datasets\lora_pilot_aihub_10k_artifact",
    "D:\fit_transfer\lora_pilot_aihub_10k_artifact_patch_v1",
    "D:\fit_transfer\send_10k_artifact_patch",
    "D:\fit_transfer\lora_pilot_aihub_10k_agnostic_v3_full"
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }

$Files = @(Get-FileList $CandidateRoots $SkipForCandidateScan)
$Dirs = @(Get-DirectoryList $CandidateRoots $SkipForCandidateScan)

$Rows = New-Object System.Collections.Generic.List[object]

foreach ($Path in $ProtectedRoots) {
    if (Test-Path -LiteralPath $Path -PathType Container) {
        $Size = (Get-DirStats $Path).size_bytes
    }
    else {
        $Size = ([System.IO.FileInfo]::new($Path)).Length
    }
    Add-Row $Rows $Path "protect" $Size "do_not_delete" "Do not delete: raw/processed master, current 10k artifact/patch, code/config/docs, or source metadata." $false $true
}

foreach ($Path in ($DoNotDeleteWholePaths | Where-Object { -not ($_ -in $ProtectedRoots) })) {
    if (Test-Path -LiteralPath $Path -PathType Container) {
        $Size = (Get-DirStats $Path).size_bytes
    }
    else {
        $Size = ([System.IO.FileInfo]::new($Path)).Length
    }
    Add-Row $Rows $Path "protect_container" $Size "do_not_delete_as_whole" "Container/root path. Review child candidates only; never delete this whole path in cleanup." $false $true
}

$MetadataRows = @($Files | Where-Object {
    ($_.Extension -in @(".csv", ".json", ".jsonl", ".txt", ".md")) -and
    ($_.Name -match "(metadata|manifest|pairs|pair|summary|checksum|features|stats|report|validation|bad_pairs|patch|smoke)")
})
foreach ($File in $MetadataRows) {
    Add-Row $Rows $File.FullName "archive_or_protect_metadata" $File.Length "keep_or_archive" "Metadata/report file that may be needed for 39k generation or audit reproducibility." $false $true
}

$ArchiveFiles = @($Files | Where-Object {
    ($_.Extension -in @(".zip", ".7z", ".rar", ".tar", ".gz", ".md5", ".sha1", ".sha256")) -or
    ($_.Name -match "(contact|sheet|validation|report|summary|checksum|final|package|experiment|doc)")
})
foreach ($File in $ArchiveFiles) {
    Add-Row $Rows $File.FullName "archive_candidate" $File.Length "archive_keep_unless_superseded" "Archive candidate: package, checksum, contact sheet, validation report, or experiment document." $false $true
}

$SplitFiles = @($Files | Where-Object {
    ($_.Name -match "\.(7z|zip|rar)\.\d{3}$") -or ($_.Extension -match "^\.z\d{2}$")
})
foreach ($File in $SplitFiles) {
    Add-Row $Rows $File.FullName "delete_candidate_split_part" $File.Length "dry_run_delete_after_pc3_verified" "Split part file. Delete only after PC3 verification and final package confirmation." $false $true
}

$PartialFiles = @($Files | Where-Object {
    $_.Extension -in @(".crdownload", ".download", ".tmp", ".partial")
})
foreach ($File in $PartialFiles) {
    Add-Row $Rows $File.FullName "delete_candidate_partial_or_temp_file" $File.Length "dry_run_delete" "Failed partial download or temporary file pattern." $true $true
}

$ZeroFiles = @($Files | Where-Object {
    $_.Length -eq 0 -and
    $_.Name -notin @("__init__.py", ".gitkeep", ".keep")
})
foreach ($File in $ZeroFiles) {
    Add-Row $Rows $File.FullName "delete_candidate_zero_byte_file" 0 "dry_run_delete_after_review" "0 byte file. Confirm it is not an intentional placeholder before deletion." $false $true
}

$CacheDirs = @($Dirs | Where-Object { $_.Name -in @("__pycache__", ".pytest_cache") })
foreach ($Dir in $CacheDirs) {
    $Size = (Get-DirStats $Dir.FullName).size_bytes
    Add-Row $Rows $Dir.FullName "delete_candidate_cache_dir" $Size "dry_run_delete" "Python/test cache directory." $true $true
}

$EmptyDirs = @($Dirs | Where-Object { Test-EmptyDirectory $_.FullName })
foreach ($Dir in $EmptyDirs) {
    Add-Row $Rows $Dir.FullName "delete_candidate_empty_dir" 0 "dry_run_delete" "Empty folder." $true $true
}

$OldLogs = @($Files | Where-Object {
    $_.Extension -eq ".log" -and $_.LastWriteTime -lt $Now.AddDays(-30)
})
foreach ($File in $OldLogs) {
    Add-Row $Rows $File.FullName "delete_candidate_old_log" $File.Length "dry_run_delete_after_review" "Log file older than 30 days." $true $true
}

$TempDirs = @($Dirs | Where-Object {
    $_.Name -match "(?i)(^tmp$|^temp$|temp_|_temp|copy|partial|failed)"
})
foreach ($Dir in $TempDirs) {
    $Size = (Get-DirStats $Dir.FullName).size_bytes
    Add-Row $Rows $Dir.FullName "delete_candidate_temp_or_failed_dir" $Size "dry_run_delete_after_review" "Temp/copy/partial/failed directory pattern." $false $true
}

$SmokeDirs = @($Dirs | Where-Object { $_.Name -match "(?i)smoke100" })
foreach ($Dir in $SmokeDirs) {
    $Size = (Get-DirStats $Dir.FullName).size_bytes
    Add-Row $Rows $Dir.FullName "delete_candidate_smoke100_copy" $Size "dry_run_delete_after_final_confirmed" "Smoke100 copy. Confirm it is reflected in final artifact before deletion." $false $true
}

$ArchiveDupGroups = @($Files | Where-Object {
    $_.Extension -in @(".zip", ".7z", ".rar", ".tar", ".gz")
} | Group-Object { $_.Name.ToLowerInvariant() + "|" + $_.Length } | Where-Object { $_.Count -gt 1 })
foreach ($Group in $ArchiveDupGroups) {
    $Ordered = @($Group.Group | Sort-Object LastWriteTime -Descending)
    $Keep = $Ordered[0]
    Add-Row $Rows $Keep.FullName "archive_duplicate_keep_reference" $Keep.Length "keep_one_copy" "Reference copy for same name+size archive group." $false $true
    foreach ($File in ($Ordered | Select-Object -Skip 1)) {
        Add-Row $Rows $File.FullName "delete_candidate_duplicate_archive" $File.Length "dry_run_delete_after_hash_or_manifest_confirm" "Duplicate archive candidate with same name+size. Confirm hash/manifest before deletion." $false $true
    }
}

$DirNameGroups = @($TopFolders |
    Where-Object {
        $_.exists -and
        $_.size_bytes -gt 0 -and
        -not (Test-IsUnderPath $_.path $DoNotDeleteWholePaths) -and
        -not (Test-PathContainsRoot $_.path $DoNotDeleteWholePaths)
    } |
    Group-Object { (Split-Path -Leaf $_.path).ToLowerInvariant() } |
    Where-Object { $_.Count -gt 1 })
foreach ($Group in $DirNameGroups) {
    $Ordered = @($Group.Group | Sort-Object size_bytes -Descending)
    $Keep = $Ordered[0]
    Add-Row $Rows $Keep.path "duplicate_folder_reference" $Keep.size_bytes "keep_pending_compare" "Reference candidate for same leaf-name folder group. Compare manifests/files before deleting any copy." $false $true
    foreach ($Dir in ($Ordered | Select-Object -Skip 1)) {
        Add-Row $Rows $Dir.path "delete_candidate_duplicate_extracted_folder" $Dir.size_bytes "dry_run_delete_after_manifest_compare" "Possible duplicate extracted/copied folder. Compare manifest/file counts first." $false $true
    }
}

$ComponentPaths = [ordered]@{
    basic_10k = "D:\projects\fit-reasoning-vton\backend\datasets\lora_pilot_aihub_10k"
    artifact_10k = "D:\projects\fit-reasoning-vton\backend\datasets\lora_pilot_aihub_10k_artifact"
    agnostic_10k = "D:\fit_transfer\agnostic_10k_v3"
    densepose_10k = "D:\fit_transfer\densepose_10k_norm"
    agnostic_full_10k = "D:\fit_transfer\lora_pilot_aihub_10k_agnostic_v3_full"
    artifact_patch_10k = "D:\fit_transfer\lora_pilot_aihub_10k_artifact_patch_v1"
    artifact_patch_zip_10k = "D:\fit_transfer\lora_pilot_aihub_10k_artifact_patch_v1.zip"
    agnostic_full_zip_10k = "D:\fit_transfer\lora_pilot_aihub_10k_agnostic_v3_full.zip"
}

$ComponentStats = [ordered]@{}
foreach ($Key in $ComponentPaths.Keys) {
    $Path = $ComponentPaths[$Key]
    if (Test-Path -LiteralPath $Path -PathType Container) {
        $ComponentStats[$Key] = Get-DirStats $Path
    }
    elseif (Test-Path -LiteralPath $Path -PathType Leaf) {
        $FileInfo = [System.IO.FileInfo]::new($Path)
        $ComponentStats[$Key] = [pscustomobject]@{
            path = $Path
            exists = $true
            size_bytes = [int64]$FileInfo.Length
            size_gb = Format-Gb $FileInfo.Length
            file_count = 1
            dir_count = 0
            error_count = 0
            errors = @()
        }
    }
    else {
        $ComponentStats[$Key] = [pscustomobject]@{
            path = $Path
            exists = $false
            size_bytes = 0
            size_gb = 0
            file_count = 0
            dir_count = 0
            error_count = 0
            errors = @()
        }
    }
}

$BasicSplitFiles = @(Get-ChildItem -LiteralPath $Datasets -Filter "lora_pilot_aihub_10k_full_split.7z.*" -File -ErrorAction SilentlyContinue)
$BasicSplitBytes = [int64](($BasicSplitFiles | Measure-Object -Property Length -Sum).Sum)
$ComponentStats["basic_10k_split_parts"] = [pscustomobject]@{
    path = "D:\projects\fit-reasoning-vton\backend\datasets\lora_pilot_aihub_10k_full_split.7z.*"
    exists = ($BasicSplitFiles.Count -gt 0)
    size_bytes = $BasicSplitBytes
    size_gb = Format-Gb $BasicSplitBytes
    file_count = $BasicSplitFiles.Count
    dir_count = 0
    error_count = 0
    errors = @()
}

$SubfolderNames = [ordered]@{
    openpose_json = @("openpose-json", "openpose_json", "openpose")
    image_parse = @("image-parse", "image_parse", "parse")
    cloth_mask = @("cloth-mask", "cloth_mask")
    image_densepose = @("image-densepose", "image_densepose", "densepose")
    agnostic_v32 = @("agnostic-v3.2", "agnostic_v3.2", "agnostic", "agnostic-v3", "agnostic_v3")
    agnostic_mask = @("agnostic-mask", "agnostic_mask")
}
$SearchBases = @(
    "D:\fit_transfer\lora_pilot_aihub_10k_artifact_patch_v1",
    "D:\projects\fit-reasoning-vton\backend\datasets\lora_pilot_aihub_10k_artifact",
    "D:\fit_transfer\lora_pilot_aihub_10k_agnostic_v3_full",
    "D:\fit_transfer\agnostic_10k_v3",
    "D:\fit_transfer\densepose_10k_norm"
)

$SubStats = [ordered]@{}
foreach ($ComponentKey in $SubfolderNames.Keys) {
    $Found = $null
    foreach ($Base in $SearchBases) {
        if (-not (Test-Path -LiteralPath $Base -PathType Container)) { continue }
        foreach ($Name in $SubfolderNames[$ComponentKey]) {
            $Candidate = Join-Path $Base $Name
            if (Test-Path -LiteralPath $Candidate -PathType Container) {
                $Found = $Candidate
                break
            }
        }
        if ($Found) { break }
    }

    if (-not $Found -and $ComponentKey -eq "agnostic_v32" -and (Test-Path -LiteralPath "D:\fit_transfer\agnostic_10k_v3" -PathType Container)) {
        $Found = "D:\fit_transfer\agnostic_10k_v3"
    }
    if (-not $Found -and $ComponentKey -eq "image_densepose" -and (Test-Path -LiteralPath "D:\fit_transfer\densepose_10k_norm" -PathType Container)) {
        $Found = "D:\fit_transfer\densepose_10k_norm"
    }

    if ($Found) {
        $SubStats[$ComponentKey] = Get-DirStats $Found
    }
    else {
        $SubStats[$ComponentKey] = [pscustomobject]@{
            path = ""
            exists = $false
            size_bytes = 0
            size_gb = 0
            file_count = 0
            dir_count = 0
            error_count = 0
            errors = @()
        }
    }
}

$Scale = 3.9
$EstimateItems = New-Object System.Collections.Generic.List[object]
$BasicBasisBytes = [math]::Max([double]$ComponentStats["basic_10k"].size_bytes, [double]$ComponentStats["basic_10k_split_parts"].size_bytes)
$BasicBasisText = "max(10k basic directory, 10k basic split archive total) x3.9"
Add-Estimate $EstimateItems "basic image/cloth/worn/fit" $BasicBasisBytes $BasicBasisText $Scale
Add-Estimate $EstimateItems "openpose-json" $SubStats["openpose_json"].size_bytes "10k artifact subfolder measured x3.9; zero means folder not found" $Scale
Add-Estimate $EstimateItems "image-parse" $SubStats["image_parse"].size_bytes "10k artifact subfolder measured x3.9; zero means folder not found" $Scale
Add-Estimate $EstimateItems "cloth-mask" $SubStats["cloth_mask"].size_bytes "10k artifact subfolder measured x3.9; zero means folder not found" $Scale
Add-Estimate $EstimateItems "image-densepose" $SubStats["image_densepose"].size_bytes "10k artifact/densepose folder measured x3.9; zero means folder not found" $Scale
Add-Estimate $EstimateItems "agnostic-v3.2" $SubStats["agnostic_v32"].size_bytes "10k agnostic folder measured x3.9; zero means folder not found" $Scale
Add-Estimate $EstimateItems "agnostic-mask" $SubStats["agnostic_mask"].size_bytes "10k agnostic-mask folder measured x3.9; zero means folder not found" $Scale
$FinalZipBasis = [math]::Max($ComponentStats["artifact_patch_zip_10k"].size_bytes, $ComponentStats["agnostic_full_zip_10k"].size_bytes)
Add-Estimate $EstimateItems "final zip/7z" $FinalZipBasis "max(10k artifact patch zip, 10k agnostic full zip) x3.9" $Scale
Add-Estimate $EstimateItems "split parts" $FinalZipBasis "same payload as final zip/7z; split overhead is negligible" $Scale

$UnpackedArtifactBytes = [int64](($EstimateItems |
    Where-Object { $_.component -notin @("final zip/7z", "split parts") } |
    Measure-Object estimate_39k_bytes -Sum).Sum)
$FinalZipEstimateBytes = [int64](($EstimateItems | Where-Object { $_.component -eq "final zip/7z" } | Select-Object -First 1).estimate_39k_bytes)
$SplitPartsEstimateBytes = [int64](($EstimateItems | Where-Object { $_.component -eq "split parts" } | Select-Object -First 1).estimate_39k_bytes)
$TempBytes = [int64](($UnpackedArtifactBytes + $FinalZipEstimateBytes) * 0.15)
$EstimateItems.Add([pscustomobject]@{
    component = "working temp space"
    basis = "15% overhead of unpacked artifacts plus final package during packaging/splitting"
    base_10k_gb = 0
    multiplier = 1
    estimate_39k_gb = Format-Gb $TempBytes
    estimate_39k_bytes = $TempBytes
}) | Out-Null

$TotalNoTempBytes = [int64](($EstimateItems | Where-Object { $_.component -ne "working temp space" } | Measure-Object estimate_39k_bytes -Sum).Sum)
$MinimumPackageWorkspaceBytes = [int64]($FinalZipEstimateBytes + $SplitPartsEstimateBytes + $TempBytes)
$RecommendedPeakBytes = [int64]($UnpackedArtifactBytes + $FinalZipEstimateBytes + $SplitPartsEstimateBytes + $TempBytes)

$MetadataInputCandidates = @(
    "D:\projects\fit-reasoning-vton\backend\datasets\processed\index\aihub_pairs_explicit_pending.csv",
    "D:\projects\fit-reasoning-vton\backend\datasets\processed\aihub_stableviton_explicit_pending\metadata.csv",
    "D:\projects\fit-reasoning-vton\backend\datasets\processed\aihub_stableviton_explicit_pending\pairs.csv",
    "D:\projects\fit-reasoning-vton\backend\datasets\processed\aihub_stableviton_explicit_pending\manifest.jsonl",
    "D:\projects\fit-reasoning-vton\backend\datasets\features_fit_30k_v3.csv",
    "D:\projects\fit-reasoning-vton\backend\datasets\features_fit_10k_v3.csv"
)
$MetadataSearchRoots = @(
    "D:\projects\fit-reasoning-vton\backend\datasets\processed\index",
    "D:\projects\fit-reasoning-vton\backend\datasets\processed\aihub_stableviton_explicit_pending",
    "D:\projects\fit-reasoning-vton\backend\datasets"
) | Where-Object { Test-Path -LiteralPath $_ }
$MetadataSearchSkip = @(
    "D:\projects\fit-reasoning-vton\backend\datasets\raw",
    "D:\projects\fit-reasoning-vton\backend\datasets\lora_pilot_aihub_10k",
    "D:\projects\fit-reasoning-vton\backend\datasets\lora_pilot_aihub_10k_artifact",
    "D:\projects\fit-reasoning-vton\backend\datasets\lora_pilot_aihub_30k"
) | Where-Object { Test-Path -LiteralPath $_ }
$DiscoveredMetadataCsvs = @(Get-FileList $MetadataSearchRoots $MetadataSearchSkip |
    Where-Object { $_.Extension -eq ".csv" -and ($_.Name -match "(pending|explicit|pair|metadata|features_fit_30k|features_fit_10k)") } |
    Select-Object -ExpandProperty FullName -Unique)
$MetadataInputs = @($MetadataInputCandidates + $DiscoveredMetadataCsvs |
    Select-Object -Unique |
    ForEach-Object {
        [pscustomobject]@{
            path = $_
            exists = (Test-Path -LiteralPath $_)
            row_count = (Count-CsvRows $_)
        }
    })
$KnownBadPairs = @("EP00003620", "EP00003937", "EP00005080", "EP00007279")

$DiskUsageReport = [pscustomobject]@{
    generated_at = $Now.ToString("o")
    current_free_space = $DiskInfo
    specified_folder_usage = $DiskUsage
    top_20_largest_folders = $TopFolders
}
$DiskUsageReport | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $ReportDir "pc2_disk_usage_report.json") -Encoding UTF8

$DiskText = New-Object System.Text.StringBuilder
[void]$DiskText.AppendLine("# PC2 Disk Usage Report")
[void]$DiskText.AppendLine("")
[void]$DiskText.AppendLine(("Generated: {0}" -f $Now.ToString("yyyy-MM-dd HH:mm:ss zzz")))
[void]$DiskText.AppendLine("")
[void]$DiskText.AppendLine("## Free Space")
foreach ($Drive in ($DiskInfo | Sort-Object drive)) {
    [void]$DiskText.AppendLine(("- {0}: {1} GB free / {2} GB used" -f $Drive.drive, $Drive.free_gb, $Drive.used_gb))
}
[void]$DiskText.AppendLine("")
[void]$DiskText.AppendLine("## Specified Folders (Largest First)")
foreach ($Stat in $DiskUsage) {
    [void]$DiskText.AppendLine(("- {0} GB`t{1}`tfiles={2}`tdirs={3}`texists={4}" -f $Stat.size_gb, $Stat.path, $Stat.file_count, $Stat.dir_count, $Stat.exists))
}
[void]$DiskText.AppendLine("")
[void]$DiskText.AppendLine("## Top 20 Largest Folders")
foreach ($Stat in $TopFolders) {
    [void]$DiskText.AppendLine(("- {0} GB`t{1}`tfiles={2}`tdirs={3}" -f $Stat.size_gb, $Stat.path, $Stat.file_count, $Stat.dir_count))
}
$DiskText.ToString() | Set-Content -LiteralPath (Join-Path $ReportDir "pc2_disk_usage_report.txt") -Encoding UTF8

$RowsOut = @($Rows | Sort-Object path, type -Unique | Sort-Object @{Expression = "recommendation"; Ascending = $true}, @{Expression = "size_gb"; Descending = $true})
$CsvPath = Join-Path $ReportDir "pc2_cleanup_candidates.csv"
$CsvLines = New-Object System.Collections.Generic.List[string]
$CsvLines.Add("path,type,size_gb,recommendation,reason,safe_to_delete,requires_user_approval") | Out-Null
foreach ($Row in $RowsOut) {
    $CsvLines.Add((@(
        (Escape-CsvValue $Row.path),
        (Escape-CsvValue $Row.type),
        $Row.size_gb,
        (Escape-CsvValue $Row.recommendation),
        (Escape-CsvValue $Row.reason),
        $Row.safe_to_delete.ToString().ToLowerInvariant(),
        $Row.requires_user_approval.ToString().ToLowerInvariant()
    ) -join ",")) | Out-Null
}
$CsvLines | Set-Content -LiteralPath $CsvPath -Encoding UTF8

$DeleteCandidates = @($RowsOut | Where-Object {
    $_.recommendation -match "^dry_run_delete" -or $_.type -match "^delete_candidate"
} | Sort-Object size_gb -Descending)

$NonOverlapDeleteCandidates = New-Object System.Collections.Generic.List[object]
$SelectedPaths = New-Object System.Collections.Generic.List[string]
foreach ($Row in ($DeleteCandidates | Sort-Object @{Expression = { $_.path.Length }; Ascending = $true})) {
    if (-not (Test-IsUnderPath $Row.path @($SelectedPaths))) {
        $NonOverlapDeleteCandidates.Add($Row) | Out-Null
        $SelectedPaths.Add($Row.path) | Out-Null
    }
}
$EstimatedRecoverableBytes = [int64](($NonOverlapDeleteCandidates | ForEach-Object { [double]$_.size_gb * $GiB } | Measure-Object -Sum).Sum)

$CleanupText = New-Object System.Text.StringBuilder
[void]$CleanupText.AppendLine("# PC2 Cleanup Plan (Dry Run)")
[void]$CleanupText.AppendLine("")
[void]$CleanupText.AppendLine("No delete, move, or compress command has been executed.")
[void]$CleanupText.AppendLine("")
[void]$CleanupText.AppendLine("## Absolute Do Not Delete")
foreach ($Path in ($ProtectedRoots | Sort-Object)) {
    [void]$CleanupText.AppendLine(('- `{0}`' -f $Path))
}
[void]$CleanupText.AppendLine("")
[void]$CleanupText.AppendLine("## Delete Candidate Summary")
[void]$CleanupText.AppendLine(("- Candidate rows: {0}" -f $DeleteCandidates.Count))
[void]$CleanupText.AppendLine(("- Non-overlapping candidate rows used for reclaim estimate: {0}" -f $NonOverlapDeleteCandidates.Count))
[void]$CleanupText.AppendLine(("- Dry-run potential reclaim: {0} GB" -f (Format-Gb $EstimatedRecoverableBytes)))
[void]$CleanupText.AppendLine("")
[void]$CleanupText.AppendLine("## Top 20 Delete Candidates")
foreach ($Row in ($DeleteCandidates | Select-Object -First 20)) {
    [void]$CleanupText.AppendLine(("- {0} GB | {1} | `{2}` | {3}" -f $Row.size_gb, $Row.type, $Row.path, $Row.reason))
}
[void]$CleanupText.AppendLine("")
[void]$CleanupText.AppendLine("## Next Cleanup Commands (Not Executed)")
[void]$CleanupText.AppendLine("These command shapes are generated for review only. Run only an approved subset.")
[void]$CleanupText.AppendLine("")
[void]$CleanupText.AppendLine('```powershell')
foreach ($Row in ($DeleteCandidates | Where-Object { [double]$_.size_gb -gt 0 } | Select-Object -First 50)) {
    $Quoted = Escape-ForSingleQuotedPowerShell $Row.path
    if ((Test-Path -LiteralPath $Row.path -PathType Container) -or $Row.type -match "_dir|folder|copy") {
        [void]$CleanupText.AppendLine(("Remove-Item -LiteralPath '{0}' -Recurse -Force" -f $Quoted))
    }
    else {
        [void]$CleanupText.AppendLine(("Remove-Item -LiteralPath '{0}' -Force" -f $Quoted))
    }
}
$CleanupText.AppendLine('```') | Out-Null
$CleanupText.ToString() | Set-Content -LiteralPath (Join-Path $ReportDir "pc2_cleanup_plan.md") -Encoding UTF8

$EstimateReport = [pscustomobject]@{
    generated_at = $Now.ToString("o")
    scale_factor_from_10k_to_39k = $Scale
    measured_10k_components = $ComponentStats
    measured_subcomponents = $SubStats
    estimates = $EstimateItems
    unpacked_artifacts_gb = Format-Gb $UnpackedArtifactBytes
    total_components_without_working_temp_gb = Format-Gb $TotalNoTempBytes
    minimum_package_workspace_gb = Format-Gb $MinimumPackageWorkspaceBytes
    working_temp_gb = Format-Gb $TempBytes
    recommended_peak_workspace_gb = Format-Gb $RecommendedPeakBytes
    free_space = $DiskInfo
    note = "Subcomponent estimates are measured from available 10k folders when folder names are found. Missing subfolders are zero and should be replaced after artifact layout is finalized."
}
$EstimateReport | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $ReportDir "pc2_39k_storage_estimate.json") -Encoding UTF8

$EstimateText = New-Object System.Text.StringBuilder
[void]$EstimateText.AppendLine("# PC2 39k Storage Estimate")
[void]$EstimateText.AppendLine("")
[void]$EstimateText.AppendLine(("Scale: 10k measured size x {0}" -f $Scale))
[void]$EstimateText.AppendLine("")
[void]$EstimateText.AppendLine("| Component | 10k basis GB | 39k estimate GB | Basis |")
[void]$EstimateText.AppendLine("|---|---:|---:|---|")
foreach ($Item in $EstimateItems) {
    [void]$EstimateText.AppendLine(("| {0} | {1} | {2} | {3} |" -f $Item.component, $Item.base_10k_gb, $Item.estimate_39k_gb, $Item.basis))
}
[void]$EstimateText.AppendLine("")
[void]$EstimateText.AppendLine(("Unpacked artifacts: **{0} GB**" -f (Format-Gb $UnpackedArtifactBytes)))
[void]$EstimateText.AppendLine(("Total listed components without working temp: **{0} GB**" -f (Format-Gb $TotalNoTempBytes)))
[void]$EstimateText.AppendLine(("Minimum package workspace (final package + split parts + temp): **{0} GB**" -f (Format-Gb $MinimumPackageWorkspaceBytes)))
[void]$EstimateText.AppendLine(("Working temp: **{0} GB**" -f (Format-Gb $TempBytes)))
[void]$EstimateText.AppendLine(("Recommended peak workspace (unpacked artifacts + final package + split parts + temp): **{0} GB**" -f (Format-Gb $RecommendedPeakBytes)))
[void]$EstimateText.AppendLine("")
[void]$EstimateText.AppendLine("Subcomponent note: zero values mean the expected 10k subfolder name was not found during this audit.")
$EstimateText.ToString() | Set-Content -LiteralPath (Join-Path $ReportDir "pc2_39k_storage_estimate.md") -Encoding UTF8

$CFree = ($DiskInfo | Where-Object { $_.drive -eq "C" }).free_gb
$DFree = ($DiskInfo | Where-Object { $_.drive -eq "D" }).free_gb
$WorkspaceRecommendation = @"
# PC2 Workspace Recommendation

## Current Drive Free Space
- C: $CFree GB free
- D: $DFree GB free

## Recommendation
- Keep raw and processed masters on D:
  - `D:\projects\fit-reasoning-vton\backend\datasets\raw`
  - `D:\projects\fit-reasoning-vton\backend\datasets\processed\index`
  - `D:\projects\fit-reasoning-vton\backend\datasets\processed\aihub_stableviton_explicit_pending`
- Do not concentrate 39k heavy work under the repo or D drive.
- Prefer `C:\fit_transfer\final_packages` for final zip/7z and split-part work because C has more free space in this audit.
- Use `C:\fit_transfer\work_39k_artifact` for heavy intermediate artifact assembly if the next run confirms C still has more free space.
- Keep `D:\fit_transfer\reports` for audit/summary/report outputs.
- Leave only final summary/report/metadata in the repo; keep large zip/part files outside the repo.
- If an external drive is available, use it for final package duplication after checksum generation, not as the only copy.

## Suggested Layout
```text
C:\fit_transfer\work_39k_artifact\
C:\fit_transfer\final_packages\
D:\fit_transfer\reports\
D:\projects\fit-reasoning-vton\backend\datasets\processed\...
```

## Guardrails
- No delete/move/compress action should run until `pc2_cleanup_candidates.csv` is reviewed and approved.
- Generated 39k metadata should exclude known bad pairs and should be versioned with row-count checks before artifact generation.
"@
$WorkspaceRecommendation | Set-Content -LiteralPath (Join-Path $ReportDir "pc2_workspace_recommendation.md") -Encoding UTF8

$MetadataText = New-Object System.Text.StringBuilder
[void]$MetadataText.AppendLine("# PC2 39k Clean Metadata Plan")
[void]$MetadataText.AppendLine("")
[void]$MetadataText.AppendLine("This is a dry run. No 39k metadata CSV was generated.")
[void]$MetadataText.AppendLine("")
[void]$MetadataText.AppendLine("## Known Bad Pairs To Exclude")
foreach ($PairId in $KnownBadPairs) {
    [void]$MetadataText.AppendLine(('- `{0}`' -f $PairId))
}
[void]$MetadataText.AppendLine("")
[void]$MetadataText.AppendLine("## Input Candidate Existence And Row Counts")
[void]$MetadataText.AppendLine("| Path | Exists | Dry-run rows |")
[void]$MetadataText.AppendLine("|---|---:|---:|")
foreach ($Input in ($MetadataInputs | Sort-Object exists, path -Descending)) {
    $RowCountText = ""
    if ($null -ne $Input.row_count) { $RowCountText = [string]$Input.row_count }
    [void]$MetadataText.AppendLine(("| `{0}` | {1} | {2} |" -f $Input.path, $Input.exists, $RowCountText))
}
[void]$MetadataText.AppendLine("")
[void]$MetadataText.AppendLine("## Planned Outputs")
[void]$MetadataText.AppendLine('- `metadata_39k_clean_candidate.csv`')
[void]$MetadataText.AppendLine('- `metadata_39k_train.csv`')
[void]$MetadataText.AppendLine('- `metadata_39k_val.csv`')
[void]$MetadataText.AppendLine('- `metadata_39k_fixed_eval_100.csv`')
[void]$MetadataText.AppendLine('- `metadata_39k_upper_candidate.csv`')
[void]$MetadataText.AppendLine('- `metadata_39k_upper_highconf_candidate.csv`')
[void]$MetadataText.AppendLine('- `bad_pairs_known.csv`')
[void]$MetadataText.AppendLine("")
[void]$MetadataText.AppendLine("## Dry-run Procedure For Next Approved Step")
[void]$MetadataText.AppendLine("1. Select source priority: `processed/index/aihub_pairs_explicit_pending.csv`, otherwise explicit pending metadata/manifest, otherwise current feature CSV only as auxiliary quality metadata.")
[void]$MetadataText.AppendLine("2. Normalize pair_id column and assert strict uniqueness.")
[void]$MetadataText.AppendLine("3. Drop known bad pair IDs.")
[void]$MetadataText.AppendLine("4. Filter to 39k clean candidates using explicit pending clean metadata and required source image/cloth paths.")
[void]$MetadataText.AppendLine("5. Create deterministic train/val/fixed_eval_100 split with saved seed and row counts.")
[void]$MetadataText.AppendLine("6. Derive upper and upper_highconf candidates from category/confidence columns if present; otherwise emit an audit warning and require manual category mapping.")
$MetadataText.ToString() | Set-Content -LiteralPath (Join-Path $ReportDir "pc2_39k_metadata_plan.md") -Encoding UTF8

$ValidationPlan = @"
# PC2 39k Artifact Validation Plan

## Required Checks
- required file existence for every pair_id and every artifact column
- PIL image load for image/cloth/worn/fit/parse/masks/densepose/agnostic
- 0 byte file detection
- width/height validation and expected alignment across paired artifacts
- openpose keypoint valid count from JSON
- image-parse unique label count and empty/degenerate parse detection
- cloth-mask empty mask detection
- image-densepose empty/invalid image detection
- agnostic-v3.2 image load and size alignment
- agnostic-mask empty mask detection
- manifest line count equals metadata row count
- pair_id strict alignment across metadata, manifest, and artifact paths

## Reuse Or Build
1. Search existing repo scripts for validation helpers before writing new code.
2. Reuse existing PIL/OpenCV/json/CSV utilities where available.
3. If no complete validator exists, create a single 39k validator that streams metadata rows and writes JSONL detail plus summary JSON.
4. Run smoke validation on 100 fixed eval rows first, then 1k, then full 39k.
5. Treat any loader failure, zero-byte file, missing artifact, invalid densepose, empty required mask, or pair_id mismatch as blocking before final packaging.

## Final Required Outputs
- `validation_report_39k_artifact.json`
- `bad_pairs_auto.csv`
- `bad_pairs_manual.csv`
- `metadata_39k_artifact_final.csv`
- `manifest_39k_artifact_final.jsonl`

## Suggested Validator Output Schema
- `pair_id`
- `status`
- `missing_files`
- `zero_byte_files`
- `image_load_errors`
- `width_height_errors`
- `openpose_valid_keypoints`
- `image_parse_unique_labels`
- `cloth_mask_nonzero_pixels`
- `densepose_nonzero_pixels`
- `agnostic_load_ok`
- `agnostic_mask_nonzero_pixels`
- `reason`

## Acceptance Gate
Final package can be transferred only when metadata rows, manifest lines, and all required artifact directories have matching pair_id sets, and when the remaining bad-pair list has been explicitly accepted.
"@
$ValidationPlan | Set-Content -LiteralPath (Join-Path $ReportDir "pc2_39k_validation_plan.md") -Encoding UTF8

$BestDrive = $DiskInfo | Sort-Object free_bytes -Descending | Select-Object -First 1
$DDrive = $DiskInfo | Where-Object { $_.drive -eq "D" }
$AdditionalNeededBest = [math]::Max(0, [math]::Round((($RecommendedPeakBytes - $BestDrive.free_bytes) / $GiB), 3))
$AdditionalNeededD = [math]::Max(0, [math]::Round((($RecommendedPeakBytes - $DDrive.free_bytes) / $GiB), 3))
$AdditionalNeededPackageBest = [math]::Max(0, [math]::Round((($MinimumPackageWorkspaceBytes - $BestDrive.free_bytes) / $GiB), 3))
$AdditionalNeededPackageD = [math]::Max(0, [math]::Round((($MinimumPackageWorkspaceBytes - $DDrive.free_bytes) / $GiB), 3))

$Summary = [pscustomobject]@{
    report_dir = $ReportDir
    generated_files = @(
        "pc2_disk_usage_report.json",
        "pc2_disk_usage_report.txt",
        "pc2_cleanup_candidates.csv",
        "pc2_cleanup_plan.md",
        "pc2_39k_storage_estimate.json",
        "pc2_39k_storage_estimate.md",
        "pc2_workspace_recommendation.md",
        "pc2_39k_metadata_plan.md",
        "pc2_39k_validation_plan.md",
        "pc2_audit_summary.json"
    )
    free_space = $DiskInfo
    specified_folder_usage = $DiskUsage | Select-Object path, exists, size_gb, file_count, dir_count
    top_20_largest_folders = $TopFolders | Select-Object path, size_gb, file_count, dir_count
    top_20_delete_candidates = $DeleteCandidates | Select-Object -First 20
    estimated_reclaim_gb = Format-Gb $EstimatedRecoverableBytes
    protected_roots = $ProtectedRoots
    storage_estimate = [pscustomobject]@{
        unpacked_artifacts_gb = Format-Gb $UnpackedArtifactBytes
        minimum_package_workspace_gb = Format-Gb $MinimumPackageWorkspaceBytes
        recommended_peak_workspace_gb = Format-Gb $RecommendedPeakBytes
        current_best_drive = $BestDrive.drive
        current_best_drive_free_gb = $BestDrive.free_gb
        additional_needed_for_package_on_best_drive_gb = $AdditionalNeededPackageBest
        additional_needed_for_package_on_d_gb = $AdditionalNeededPackageD
        additional_needed_for_recommended_peak_on_best_drive_gb = $AdditionalNeededBest
        additional_needed_for_recommended_peak_on_d_gb = $AdditionalNeededD
    }
    metadata_inputs = $MetadataInputs
    cleanup_commands_preview = @($DeleteCandidates | Where-Object { [double]$_.size_gb -gt 0 } | Select-Object -First 20 | ForEach-Object {
        $Quoted = Escape-ForSingleQuotedPowerShell $_.path
        if ((Test-Path -LiteralPath $_.path -PathType Container) -or $_.type -match "_dir|folder|copy") {
            "Remove-Item -LiteralPath '$Quoted' -Recurse -Force"
        }
        else {
            "Remove-Item -LiteralPath '$Quoted' -Force"
        }
    })
}
$Summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $ReportDir "pc2_audit_summary.json") -Encoding UTF8
$Summary | ConvertTo-Json -Depth 8
