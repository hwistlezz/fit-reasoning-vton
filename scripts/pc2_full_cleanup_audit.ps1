param(
    [string]$ReportDir = "D:\fit_transfer\reports",
    [int]$OldDays = 30,
    [int64]$LargeFileThresholdBytes = 52428800
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$Now = Get-Date
$GiB = [double]1GB
$Cutoff = $Now.AddDays(-1 * $OldDays)
$CsvColumns = @(
    "path",
    "drive",
    "type",
    "size_gb",
    "classification",
    "reason",
    "recommended_action",
    "requires_user_approval",
    "last_write_time"
)

New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null

function Format-Gb([double]$Bytes) {
    [math]::Round(($Bytes / $GiB), 6)
}

function Get-DriveName([string]$Path) {
    if ($Path -match "^[A-Za-z]:") { return $Path.Substring(0, 1).ToUpperInvariant() }
    return ""
}

function Test-SameOrUnderPath([string]$Path, [string[]]$Roots) {
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

function Test-PathExists([string]$Path) {
    if (-not $Path) { return $false }
    try {
        return (Test-Path -LiteralPath $Path -ErrorAction Stop)
    }
    catch {
        return $true
    }
}

function Test-PathContainer([string]$Path) {
    if (-not $Path) { return $false }
    try {
        return (Test-Path -LiteralPath $Path -PathType Container -ErrorAction Stop)
    }
    catch {
        return $false
    }
}

function Test-PathLeaf([string]$Path) {
    if (-not $Path) { return $false }
    try {
        return (Test-Path -LiteralPath $Path -PathType Leaf -ErrorAction Stop)
    }
    catch {
        return $false
    }
}

function Get-ResolvedExistingPaths([string[]]$Paths) {
    $Result = New-Object System.Collections.Generic.List[string]
    foreach ($Path in $Paths) {
        if (Test-PathExists $Path) {
            try {
                $Result.Add((Resolve-Path -LiteralPath $Path).Path) | Out-Null
            }
            catch {
                $Result.Add($Path) | Out-Null
            }
        }
    }
    @($Result | Select-Object -Unique)
}

function Test-EmptyDirectory([string]$Path) {
    try {
        $Enumerator = [System.IO.Directory]::EnumerateFileSystemEntries($Path).GetEnumerator()
        try {
            return -not $Enumerator.MoveNext()
        }
        finally {
            if ($Enumerator -is [System.IDisposable]) { $Enumerator.Dispose() }
        }
    }
    catch {
        return $false
    }
}

$DirSizeCache = @{}
function Get-DirStats([string]$Path, [string[]]$NestedSkipRoots = @()) {
    $Key = $Path.ToLowerInvariant()
    if ($DirSizeCache.ContainsKey($Key)) { return $DirSizeCache[$Key] }

    $Total = [int64]0
    $Files = [int64]0
    $Dirs = [int64]0
    $Errors = [int64]0

    if (-not (Test-PathContainer $Path)) {
        $Result = [pscustomobject]@{
            path = $Path
            exists = $false
            size_bytes = 0
            size_gb = 0
            file_count = 0
            dir_count = 0
            error_count = 0
        }
        $DirSizeCache[$Key] = $Result
        return $Result
    }

    $Stack = New-Object System.Collections.Generic.Stack[string]
    try {
        $Stack.Push((Resolve-Path -LiteralPath $Path).Path)
    }
    catch {
        $Stack.Push($Path)
    }

    while ($Stack.Count -gt 0) {
        $Current = $Stack.Pop()
        if (Test-SameOrUnderPath $Current $NestedSkipRoots) { continue }
        try {
            foreach ($DirPath in [System.IO.Directory]::EnumerateDirectories($Current)) {
                if (Test-SameOrUnderPath $DirPath $NestedSkipRoots) { continue }
                try {
                    $DirInfo = [System.IO.DirectoryInfo]::new($DirPath)
                    if (($DirInfo.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { continue }
                    $Dirs++
                    $Stack.Push($DirPath)
                }
                catch {
                    $Errors++
                }
            }
            foreach ($FilePath in [System.IO.Directory]::EnumerateFiles($Current)) {
                try {
                    $FileInfo = [System.IO.FileInfo]::new($FilePath)
                    $Files++
                    $Total += $FileInfo.Length
                }
                catch {
                    $Errors++
                }
            }
        }
        catch {
            $Errors++
        }
    }

    $Result = [pscustomobject]@{
        path = $Path
        exists = $true
        size_bytes = $Total
        size_gb = Format-Gb $Total
        file_count = $Files
        dir_count = $Dirs
        error_count = $Errors
    }
    $DirSizeCache[$Key] = $Result
    return $Result
}

$CandidateMap = @{}
$Priority = @{
    safe_delete = 1
    review_delete = 2
    move_to_external_or_keep = 3
    never_delete = 4
    skipped_system_or_risky = 5
}

function New-AuditRow(
    [string]$Path,
    [string]$Type,
    [int64]$SizeBytes,
    [string]$Classification,
    [string]$Reason,
    [string]$Action,
    [bool]$RequiresApproval,
    [object]$LastWriteTime
) {
    [pscustomobject]@{
        path = $Path
        drive = Get-DriveName $Path
        type = $Type
        size_gb = Format-Gb $SizeBytes
        classification = $Classification
        reason = $Reason
        recommended_action = $Action
        requires_user_approval = $RequiresApproval.ToString().ToLowerInvariant()
        last_write_time = $(if ($LastWriteTime) { $LastWriteTime.ToString("o") } else { "" })
        size_bytes = $SizeBytes
        last_write_dt = $LastWriteTime
    }
}

function Add-Candidate([pscustomobject]$Row) {
    if (-not $Row.path) { return }
    $Key = $Row.path.ToLowerInvariant()
    if ($CandidateMap.ContainsKey($Key)) {
        $Existing = $CandidateMap[$Key]
        if ($Priority[$Row.classification] -gt $Priority[$Existing.classification]) {
            $CandidateMap[$Key] = $Row
        }
        elseif ($Priority[$Row.classification] -eq $Priority[$Existing.classification] -and $Row.size_bytes -gt $Existing.size_bytes) {
            $CandidateMap[$Key] = $Row
        }
    }
    else {
        $CandidateMap[$Key] = $Row
    }
}

function ConvertTo-ExportRows([object[]]$Rows) {
    $Rows | Select-Object $CsvColumns
}

function Export-AuditCsv([string]$Path, [object[]]$Rows) {
    ConvertTo-ExportRows $Rows | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding UTF8
}

function Test-ArchiveFileName([string]$Name) {
    $Lower = $Name.ToLowerInvariant()
    return ($Lower -match "\.(zip|7z|rar|tar|gz|tgz|bz2|xz)$")
}

function Test-SplitPartName([string]$Name) {
    $Lower = $Name.ToLowerInvariant()
    return ($Lower -match "\.(zip|7z|rar)\.\d{3}$" -or $Lower -match "\.\d{3}$")
}

function Test-PartialFileName([string]$Name) {
    $Lower = $Name.ToLowerInvariant()
    return ($Lower -match "\.(part|partial|crdownload|download|tmp)$")
}

function Test-MetadataOrReportName([string]$Name) {
    $Lower = $Name.ToLowerInvariant()
    return ($Lower -match "(metadata|manifest|pairs?|summary|checksum|validation|report|contact|sheet|patch|smoke|features|stats|bad_pairs)" -and $Lower -match "\.(csv|json|jsonl|md|txt|jpg|jpeg|png)$")
}

function Test-FinalOrPackageName([string]$Name) {
    $Lower = $Name.ToLowerInvariant()
    return ($Lower -match "(final|package|checksum|validated|verification|contact|summary|report|manifest|metadata|artifact_patch|agnostic_v3_full)")
}

function Test-ModelCheckpointName([string]$Name) {
    $Lower = $Name.ToLowerInvariant()
    return ($Lower -match "\.(ckpt|pt|pth|safetensors|onnx|bin)$")
}

function Test-SourceLikeZeroByte([System.IO.FileInfo]$FileInfo) {
    $Name = $FileInfo.Name.ToLowerInvariant()
    $Ext = $FileInfo.Extension.ToLowerInvariant()
    if ($Name -in @("__init__.py", ".gitkeep", ".keep", ".npmignore", ".dockerignore")) { return $true }
    if ($Ext -in @(".py", ".js", ".ts", ".tsx", ".jsx", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".h", ".hpp", ".c", ".cc", ".cpp", ".cs")) { return $true }
    return $false
}

function Get-DirectoryClassification([System.IO.DirectoryInfo]$DirInfo) {
    $Name = $DirInfo.Name
    $Lower = $Name.ToLowerInvariant()
    $PathLower = $DirInfo.FullName.ToLowerInvariant()
    $AgeOld = $DirInfo.LastWriteTime -lt $Cutoff

    if ($Lower -in @("__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".ipynb_checkpoints")) {
        return @{ classification = "safe_delete"; type = "cache_dir"; reason = "Python/notebook/test cache directory."; action = "delete_after_safe_delete_approval"; skip = $true }
    }
    if ($Lower -in @("node_modules", ".next", "coverage", "htmlcov", ".cache", "npm-cache", ".npm", ".pnpm-store")) {
        return @{ classification = "safe_delete"; type = "dev_cache_or_build_dir"; reason = "Development cache/build dependency directory."; action = "delete_after_safe_delete_approval"; skip = $true }
    }
    if ($Lower -in @("dist", "build")) {
        return @{ classification = "safe_delete"; type = "build_output_dir"; reason = "Common build output directory. Rebuildable if source is intact."; action = "delete_after_safe_delete_approval"; skip = $true }
    }
    if ($Lower -in @("temp", "tmp") -or $Lower -match "^(tmp|temp)[-_]") {
        return @{ classification = "safe_delete"; type = "temp_dir"; reason = "Temporary directory pattern."; action = "delete_after_safe_delete_approval"; skip = $true }
    }
    if ($PathLower -match "\\yarn\\cache$" -or $PathLower -match "\\\.yarn\\cache$" -or $PathLower -match "\\pip\\cache$") {
        return @{ classification = "safe_delete"; type = "package_cache_dir"; reason = "Package-manager cache directory."; action = "delete_after_safe_delete_approval"; skip = $true }
    }
    if ($Lower -eq "pkgs" -and $PathLower -match "(conda|anaconda|miniconda|mambaforge|miniforge)") {
        return @{ classification = "safe_delete"; type = "conda_package_cache_dir"; reason = "Conda package cache directory, not an environment directory."; action = "delete_after_safe_delete_approval"; skip = $true }
    }

    if ($Lower -match "(smoke100|tiny100)") {
        return @{ classification = "review_delete"; type = "small_smoke_artifact_dir"; reason = "Smoke/tiny intermediate artifact directory. Confirm reflected in final package first."; action = "review_before_delete"; skip = $true }
    }
    if ($Lower -match "(old|backup|copy|duplicate|partial|failed)") {
        return @{ classification = "review_delete"; type = "old_backup_copy_or_failed_dir"; reason = "Old/backup/copy/duplicate/partial/failed directory pattern."; action = "review_before_delete"; skip = $true }
    }
    if ($Lower -in @("runs", "wandb", "tensorboard", "tb_logs", "checkpoints", "checkpoint", "outputs", "logs")) {
        if ($AgeOld) {
            return @{ classification = "review_delete"; type = "old_experiment_output_dir"; reason = "Old experiment logs/outputs/checkpoints directory."; action = "review_before_delete"; skip = $true }
        }
        return @{ classification = "move_to_external_or_keep"; type = "recent_experiment_output_dir"; reason = "Recent experiment logs/outputs/checkpoints directory."; action = "keep_or_move_external"; skip = $true }
    }
    if ($Lower -match "(final|package|checksum|contact|validation|report|summary|model)") {
        return @{ classification = "move_to_external_or_keep"; type = "important_result_dir"; reason = "Final/package/report/model-like directory. Keep or move to external storage."; action = "keep_or_move_external"; skip = $true }
    }

    return $null
}

$SystemSkipExact = @(
    "C:\Windows",
    "C:\Program Files",
    "C:\Program Files (x86)",
    "C:\ProgramData\Microsoft",
    'C:\$Recycle.Bin',
    'D:\$Recycle.Bin',
    "C:\System Volume Information",
    "D:\System Volume Information",
    "C:\Recovery",
    "C:\PerfLogs",
    'C:\$WinREAgent',
    "C:\ProgramData\USOShared",
    "C:\ProgramData\AhnLab",
    "C:\ProgramData\NVIDIA",
    "C:\ProgramData\NVIDIA Corporation"
)

$SystemSkipDynamic = New-Object System.Collections.Generic.List[string]
if (Test-PathContainer "C:\Users") {
    foreach ($UserDir in Get-ChildItem -LiteralPath "C:\Users" -Directory -Force -ErrorAction SilentlyContinue) {
        $LocalMicrosoft = Join-Path $UserDir.FullName "AppData\Local\Microsoft"
        $LocalPackages = Join-Path $UserDir.FullName "AppData\Local\Packages"
        $LocalPrograms = Join-Path $UserDir.FullName "AppData\Local\Programs"
        $CodexRuntimes = Join-Path $UserDir.FullName "AppData\Local\OpenAI\Codex\runtimes"
        $VsCodeExtensions = Join-Path $UserDir.FullName ".vscode\extensions"
        $CodexPluginCache = Join-Path $UserDir.FullName ".codex\plugins\cache"
        $ChromeUserData = Join-Path $UserDir.FullName "AppData\Local\Google\Chrome\User Data"
        if (Test-PathExists $LocalMicrosoft) { $SystemSkipDynamic.Add($LocalMicrosoft) | Out-Null }
        if (Test-PathExists $LocalPackages) { $SystemSkipDynamic.Add($LocalPackages) | Out-Null }
        if (Test-PathExists $LocalPrograms) { $SystemSkipDynamic.Add($LocalPrograms) | Out-Null }
        if (Test-PathExists $CodexRuntimes) { $SystemSkipDynamic.Add($CodexRuntimes) | Out-Null }
        if (Test-PathExists $VsCodeExtensions) { $SystemSkipDynamic.Add($VsCodeExtensions) | Out-Null }
        if (Test-PathExists $CodexPluginCache) { $SystemSkipDynamic.Add($CodexPluginCache) | Out-Null }
        if (Test-PathExists $ChromeUserData) { $SystemSkipDynamic.Add($ChromeUserData) | Out-Null }
    }
}

$SystemSkipRoots = Get-ResolvedExistingPaths (@($SystemSkipExact) + @($SystemSkipDynamic))

$NeverDeleteRequested = @(
    "D:\projects\fit-reasoning-vton.git",
    "D:\projects\fit-reasoning-vton\.git",
    "D:\projects\fit-reasoning-vton\scripts",
    "D:\projects\fit-reasoning-vton\backend\app",
    "D:\projects\fit-reasoning-vton\backend\training",
    "D:\projects\fit-reasoning-vton\frontend",
    "D:\projects\fit-reasoning-vton\configs",
    "D:\projects\fit-reasoning-vton\docs",
    "D:\projects\fit-reasoning-vton\backend\datasets\raw",
    "D:\projects\fit-reasoning-vton\backend\datasets\processed\index",
    "D:\projects\fit-reasoning-vton\backend\datasets\processed\aihub_stableviton_explicit_pending",
    "D:\projects\fit-reasoning-vton\backend\datasets\lora_pilot_aihub_10k_artifact",
    "D:\fit_transfer\lora_pilot_aihub_10k_artifact_patch_v1",
    "D:\fit_transfer\send_10k_artifact_patch",
    "D:\fit_transfer\lora_pilot_aihub_10k_agnostic_v3_full",
    "D:\fit_transfer\lora_pilot_aihub_10k_artifact_patch_v1.zip",
    "D:\fit_transfer\lora_pilot_aihub_10k_agnostic_v3_full.zip",
    "C:\fit_transfer\lora_pilot_aihub_30k_full",
    "D:\fit_transfer\external\detectron2"
)
if ($env:CONDA_PREFIX -and (Test-PathExists $env:CONDA_PREFIX)) { $NeverDeleteRequested += $env:CONDA_PREFIX }
if ($env:VIRTUAL_ENV -and (Test-PathExists $env:VIRTUAL_ENV)) { $NeverDeleteRequested += $env:VIRTUAL_ENV }
if (Test-PathExists "C:\Users\user\miniconda3\envs\vton") { $NeverDeleteRequested += "C:\Users\user\miniconda3\envs\vton" }
$NeverDeleteRoots = Get-ResolvedExistingPaths $NeverDeleteRequested

$ProtectedSkipRoots = Get-ResolvedExistingPaths @(
    "D:\projects\fit-reasoning-vton\.git",
    "D:\projects\fit-reasoning-vton\backend\datasets\raw",
    "D:\projects\fit-reasoning-vton\backend\datasets\processed\index",
    "D:\projects\fit-reasoning-vton\backend\datasets\processed\aihub_stableviton_explicit_pending",
    "D:\projects\fit-reasoning-vton\backend\datasets\lora_pilot_aihub_10k_artifact",
    "D:\fit_transfer\lora_pilot_aihub_10k_artifact_patch_v1",
    "D:\fit_transfer\send_10k_artifact_patch",
    "D:\fit_transfer\lora_pilot_aihub_10k_agnostic_v3_full",
    "C:\fit_transfer\lora_pilot_aihub_30k_full",
    "C:\Users\user\miniconda3\envs\vton"
)

$ScanSkipRoots = @($SystemSkipRoots + $ProtectedSkipRoots | Select-Object -Unique)

foreach ($SkipPath in $SystemSkipRoots) {
    $SizeBytes = 0
    $LastWrite = $null
    try {
        if (Test-PathContainer $SkipPath) {
            $LastWrite = ([System.IO.DirectoryInfo]::new($SkipPath)).LastWriteTime
        }
    }
    catch {}
    Add-Candidate (New-AuditRow $SkipPath "skipped_system_dir" $SizeBytes "skipped_system_or_risky" "System/risky Windows area skipped and not proposed as deletion candidate." "skip_no_delete_candidate" $true $LastWrite)
}

foreach ($Path in $NeverDeleteRoots) {
    $SizeBytes = [int64]0
    $LastWrite = $null
    $Type = "never_delete_path"
    try {
        if (Test-PathContainer $Path) {
            $Stats = Get-DirStats $Path $SystemSkipRoots
            $SizeBytes = [int64]$Stats.size_bytes
            $LastWrite = ([System.IO.DirectoryInfo]::new($Path)).LastWriteTime
            $Type = "protected_dir"
        }
        elseif (Test-PathLeaf $Path) {
            $FileInfo = [System.IO.FileInfo]::new($Path)
            $SizeBytes = [int64]$FileInfo.Length
            $LastWrite = $FileInfo.LastWriteTime
            $Type = "protected_file"
        }
    }
    catch {}
    Add-Candidate (New-AuditRow $Path $Type $SizeBytes "never_delete" "Explicitly protected path: raw/processed master, source code, active artifact, active env/source, or current final package." "never_delete" $true $LastWrite)
}

$LargeFileRows = New-Object System.Collections.Generic.List[object]
$ArchiveRows = New-Object System.Collections.Generic.List[object]
$ScanErrors = New-Object System.Collections.Generic.List[object]
$VisitedDirs = [int64]0
$VisitedFiles = [int64]0

function Classify-File([System.IO.FileInfo]$FileInfo) {
    $FullName = $FileInfo.FullName
    $Name = $FileInfo.Name
    $LowerPath = $FullName.ToLowerInvariant()
    $LowerName = $Name.ToLowerInvariant()
    $SizeBytes = [int64]$FileInfo.Length
    $LastWrite = $FileInfo.LastWriteTime

    if (Test-SameOrUnderPath $FullName $SystemSkipRoots) { return }
    if (Test-SameOrUnderPath $FullName $NeverDeleteRoots) {
        if ($FileInfo.Length -ge $LargeFileThresholdBytes) {
            $LargeFileRows.Add((New-AuditRow $FullName "large_file_under_protected_path" $SizeBytes "never_delete" "Large file under protected path." "never_delete" $true $LastWrite)) | Out-Null
        }
        return
    }

    if ($FileInfo.Length -ge $LargeFileThresholdBytes) {
        $LargeFileRows.Add((New-AuditRow $FullName "large_file" $SizeBytes "review_delete" "Large scanned file; inspect classification before action." "review_before_delete_or_keep" $true $LastWrite)) | Out-Null
    }

    if (Test-PartialFileName $Name) {
        Add-Candidate (New-AuditRow $FullName "partial_or_tmp_file" $SizeBytes "safe_delete" "Partial download or temporary file extension." "delete_after_safe_delete_approval" $true $LastWrite)
        return
    }

    if ($SizeBytes -eq 0) {
        if (Test-SourceLikeZeroByte $FileInfo) {
            Add-Candidate (New-AuditRow $FullName "zero_byte_placeholder_like_file" 0 "review_delete" "0 byte file, but extension/name can be intentional placeholder/source marker." "review_before_delete" $true $LastWrite)
        }
        else {
            Add-Candidate (New-AuditRow $FullName "zero_byte_file" 0 "safe_delete" "0 byte file outside protected/system areas." "delete_after_safe_delete_approval" $true $LastWrite)
        }
        return
    }

    if (Test-SplitPartName $Name) {
        Add-Candidate (New-AuditRow $FullName "split_part_file" $SizeBytes "review_delete" "Archive split part. Delete only after final package and receiver verification." "review_before_delete" $true $LastWrite)
        return
    }

    if (Test-ArchiveFileName $Name) {
        $ArchiveRow = New-AuditRow $FullName "archive_file" $SizeBytes "review_delete" "Archive file found in full-disk audit." "review_before_delete" $true $LastWrite
        $ArchiveRows.Add($ArchiveRow) | Out-Null
        if (Test-FinalOrPackageName $Name) {
            Add-Candidate (New-AuditRow $FullName "archive_final_or_report_package" $SizeBytes "move_to_external_or_keep" "Final/package/checksum/report-like archive. Keep or move to external storage." "keep_or_move_external" $true $LastWrite)
        }
        else {
            Add-Candidate $ArchiveRow
        }
        return
    }

    if ($LowerName -match "\.(md5|sha1|sha256|sha512|sfv)$") {
        Add-Candidate (New-AuditRow $FullName "checksum_file" $SizeBytes "move_to_external_or_keep" "Checksum file; useful for validating packages." "keep_or_move_external" $true $LastWrite)
        return
    }

    if (Test-MetadataOrReportName $Name) {
        Add-Candidate (New-AuditRow $FullName "metadata_report_or_contact_sheet" $SizeBytes "move_to_external_or_keep" "Metadata/report/contact/summary file. Keep for audit or 39k generation." "keep_or_move_external" $true $LastWrite)
        return
    }

    if (Test-ModelCheckpointName $Name) {
        Add-Candidate (New-AuditRow $FullName "model_checkpoint_file" $SizeBytes "move_to_external_or_keep" "Model/checkpoint-like file. Verify importance before any deletion." "keep_or_move_external" $true $LastWrite)
        return
    }

    if ($LowerName -match "\.log$" -and $LastWrite -lt $Cutoff) {
        Add-Candidate (New-AuditRow $FullName "old_log_file" $SizeBytes "review_delete" "Log file older than cutoff." "review_before_delete" $true $LastWrite)
        return
    }

    if (($LowerPath -match "\\(runs|wandb|tensorboard|tb_logs|outputs|checkpoints|checkpoint|logs)\\" -and $LastWrite -lt $Cutoff) -or $LowerName -match "(old|backup|copy|duplicate)") {
        Add-Candidate (New-AuditRow $FullName "old_output_or_copy_file" $SizeBytes "review_delete" "Old output/checkpoint/log/copy-like file." "review_before_delete" $true $LastWrite)
        return
    }
}

function Scan-Root([string]$RootPath) {
    if (-not (Test-PathContainer $RootPath)) { return }
    $Stack = New-Object System.Collections.Generic.Stack[string]
    $Stack.Push((Resolve-Path -LiteralPath $RootPath).Path)

    while ($Stack.Count -gt 0) {
        $Current = $Stack.Pop()
        if (Test-SameOrUnderPath $Current $ScanSkipRoots) { continue }

        $VisitedDirs++
        try {
            $CurrentInfo = [System.IO.DirectoryInfo]::new($Current)
            if (($CurrentInfo.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { continue }

            if (Test-EmptyDirectory $Current) {
                if (-not (Test-SameOrUnderPath $Current $NeverDeleteRoots)) {
                    Add-Candidate (New-AuditRow $Current "empty_dir" 0 "safe_delete" "Empty directory outside protected/system areas." "delete_after_safe_delete_approval" $true $CurrentInfo.LastWriteTime)
                }
            }

            $DirClass = Get-DirectoryClassification $CurrentInfo
            if ($DirClass -and -not (Test-SameOrUnderPath $Current $NeverDeleteRoots)) {
                $Stats = Get-DirStats $Current $ScanSkipRoots
                Add-Candidate (New-AuditRow $Current $DirClass.type ([int64]$Stats.size_bytes) $DirClass.classification $DirClass.reason $DirClass.action $true $CurrentInfo.LastWriteTime)
                if ($DirClass.skip) { continue }
            }

            foreach ($FilePath in [System.IO.Directory]::EnumerateFiles($Current)) {
                try {
                    $FileInfo = [System.IO.FileInfo]::new($FilePath)
                    $VisitedFiles++
                    Classify-File $FileInfo
                }
                catch {
                    $ScanErrors.Add([pscustomobject]@{ path = $FilePath; error = $_.Exception.Message }) | Out-Null
                }
            }

            foreach ($DirPath in [System.IO.Directory]::EnumerateDirectories($Current)) {
                if (Test-SameOrUnderPath $DirPath $ScanSkipRoots) { continue }
                try {
                    $DirInfo = [System.IO.DirectoryInfo]::new($DirPath)
                    if (($DirInfo.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { continue }
                    $Stack.Push($DirPath)
                }
                catch {
                    $ScanErrors.Add([pscustomobject]@{ path = $DirPath; error = $_.Exception.Message }) | Out-Null
                }
            }
        }
        catch {
            $ScanErrors.Add([pscustomobject]@{ path = $Current; error = $_.Exception.Message }) | Out-Null
        }
    }
}

Scan-Root "C:\"
Scan-Root "D:\"

$DuplicateArchiveRows = New-Object System.Collections.Generic.List[object]
$ArchiveGroups = @($ArchiveRows | Where-Object { $_.size_bytes -gt 0 } | Group-Object { $_.path.Split("\")[-1].ToLowerInvariant() + "|" + $_.size_bytes } | Where-Object { $_.Count -gt 1 })
foreach ($Group in $ArchiveGroups) {
    $Ordered = @($Group.Group | Sort-Object last_write_dt -Descending)
    $Reference = $Ordered[0]
    foreach ($Dup in ($Ordered | Select-Object -Skip 1)) {
        $Reason = "Duplicate archive candidate: same filename and byte size as reference [$($Reference.path)]. Verify hash before deleting."
        $Row = New-AuditRow $Dup.path "duplicate_archive_file" ([int64]$Dup.size_bytes) "review_delete" $Reason "review_before_delete" $true $Dup.last_write_dt
        Add-Candidate $Row
        $DuplicateArchiveRows.Add($Row) | Out-Null
    }
}

$AllCandidates = @($CandidateMap.Values | Sort-Object @{ Expression = "classification"; Ascending = $true }, @{ Expression = "size_bytes"; Descending = $true }, path)
$SafeDelete = @($AllCandidates | Where-Object { $_.classification -eq "safe_delete" } | Sort-Object size_bytes -Descending)
$ReviewDelete = @($AllCandidates | Where-Object { $_.classification -eq "review_delete" } | Sort-Object size_bytes -Descending)
$MoveOrKeep = @($AllCandidates | Where-Object { $_.classification -eq "move_to_external_or_keep" } | Sort-Object size_bytes -Descending)
$NeverDelete = @($AllCandidates | Where-Object { $_.classification -eq "never_delete" } | Sort-Object size_bytes -Descending)
$Skipped = @($AllCandidates | Where-Object { $_.classification -eq "skipped_system_or_risky" } | Sort-Object path)

$LargeDirs = @($AllCandidates | Where-Object { $_.type -match "dir|path" -and $_.size_bytes -gt 0 } | Sort-Object size_bytes -Descending | Select-Object -First 150)
$LargeFiles = @(
    ($LargeFileRows + ($AllCandidates | Where-Object { $_.type -match "file|archive|checkpoint|checksum" -and $_.size_bytes -ge $LargeFileThresholdBytes })) |
    Sort-Object path -Unique |
    Sort-Object size_bytes -Descending |
    Select-Object -First 300
)

function Sum-Bytes([object[]]$Rows) {
    [int64](($Rows | Measure-Object -Property size_bytes -Sum).Sum)
}

$DriveInfo = Get-PSDrive -PSProvider FileSystem |
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

$CFree = [int64](($DriveInfo | Where-Object { $_.drive -eq "C" }).free_bytes)
$DFree = [int64](($DriveInfo | Where-Object { $_.drive -eq "D" }).free_bytes)
$CombinedFree = [int64]($CFree + $DFree)

$FeasibilityTargets = [ordered]@{
    "full_39k_unpacked_artifacts" = 827.537
    "package_only_workspace" = 975.426
    "final_zip_and_split_parts" = 791.904
    "recommended_peak" = 1802.964
    "10k_chunk_recommended_peak" = (1802.964 * 10 / 39)
    "10k_chunk_package_only" = (975.426 * 10 / 39)
    "5k_chunk_recommended_peak" = (1802.964 * 5 / 39)
    "5k_chunk_package_only" = (975.426 * 5 / 39)
}

$FeasibilityRows = foreach ($Key in $FeasibilityTargets.Keys) {
    $NeedGb = [double]$FeasibilityTargets[$Key]
    $NeedBytes = [int64]($NeedGb * $GiB)
    [pscustomobject]@{
        scenario = $Key
        required_gb = [math]::Round($NeedGb, 3)
        combined_free_gb = Format-Gb $CombinedFree
        possible_with_combined_c_d = ($CombinedFree -ge $NeedBytes)
        shortage_gb = [math]::Max(0, [math]::Round((($NeedBytes - $CombinedFree) / $GiB), 3))
        c_only_possible = ($CFree -ge $NeedBytes)
        d_only_possible = ($DFree -ge $NeedBytes)
    }
}

$Summary = [pscustomobject]@{
    generated_at = $Now.ToString("o")
    scan_roots = @("C:\", "D:\")
    report_dir = $ReportDir
    old_days_cutoff = $OldDays
    visited_dirs = $VisitedDirs
    visited_files = $VisitedFiles
    scan_error_count = $ScanErrors.Count
    drive_free_space = $DriveInfo
    combined_free_gb = Format-Gb $CombinedFree
    estimated_reclaim = [pscustomobject]@{
        safe_delete_gb = Format-Gb (Sum-Bytes $SafeDelete)
        review_delete_gb = Format-Gb (Sum-Bytes $ReviewDelete)
        move_to_external_or_keep_gb = Format-Gb (Sum-Bytes $MoveOrKeep)
        never_delete_gb = Format-Gb (Sum-Bytes $NeverDelete)
    }
    counts = [pscustomobject]@{
        all_candidates = $AllCandidates.Count
        safe_delete = $SafeDelete.Count
        review_delete = $ReviewDelete.Count
        move_to_external_or_keep = $MoveOrKeep.Count
        never_delete = $NeverDelete.Count
        skipped_system_or_risky = $Skipped.Count
        duplicate_archive_pairs = $DuplicateArchiveRows.Count
    }
    skipped_system_roots = $SystemSkipRoots
    never_delete_roots = $NeverDeleteRoots
    protected_scan_skip_roots = $ProtectedSkipRoots
    feasibility = $FeasibilityRows
    top_safe_delete = $SafeDelete | Select-Object -First 30
    top_review_delete = $ReviewDelete | Select-Object -First 50
    top_move_or_keep = $MoveOrKeep | Select-Object -First 30
    top_never_delete = $NeverDelete | Select-Object -First 30
    scan_errors_sample = $ScanErrors | Select-Object -First 100
}

Export-AuditCsv (Join-Path $ReportDir "pc2_full_cleanup_candidates.csv") $AllCandidates
Export-AuditCsv (Join-Path $ReportDir "pc2_full_safe_delete_candidates.csv") $SafeDelete
Export-AuditCsv (Join-Path $ReportDir "pc2_full_review_delete_candidates.csv") $ReviewDelete
Export-AuditCsv (Join-Path $ReportDir "pc2_full_move_or_keep_candidates.csv") $MoveOrKeep
Export-AuditCsv (Join-Path $ReportDir "pc2_full_never_delete_candidates.csv") $NeverDelete
Export-AuditCsv (Join-Path $ReportDir "pc2_full_large_files_top300.csv") $LargeFiles
Export-AuditCsv (Join-Path $ReportDir "pc2_full_large_dirs_top150.csv") $LargeDirs
Export-AuditCsv (Join-Path $ReportDir "pc2_full_duplicate_archive_pairs.csv") $DuplicateArchiveRows

$Summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $ReportDir "pc2_full_cleanup_audit.json") -Encoding UTF8

$Md = New-Object System.Text.StringBuilder
[void]$Md.AppendLine("# PC2 Full Cleanup Audit (Dry Run)")
[void]$Md.AppendLine("")
[void]$Md.AppendLine("No delete, move, compression, extraction, or git command was executed.")
[void]$Md.AppendLine("")
[void]$Md.AppendLine("## Free Space")
foreach ($Drive in ($DriveInfo | Sort-Object drive)) {
    [void]$Md.AppendLine(("- {0}: {1} GB free / {2} GB used" -f $Drive.drive, $Drive.free_gb, $Drive.used_gb))
}
[void]$Md.AppendLine(("- C+D combined: {0} GB free" -f (Format-Gb $CombinedFree)))
[void]$Md.AppendLine("")
[void]$Md.AppendLine("## Estimated Capacity By Classification")
[void]$Md.AppendLine(("- safe_delete: {0} GB" -f (Format-Gb (Sum-Bytes $SafeDelete))))
[void]$Md.AppendLine(("- review_delete: {0} GB" -f (Format-Gb (Sum-Bytes $ReviewDelete))))
[void]$Md.AppendLine(("- move_to_external_or_keep: {0} GB" -f (Format-Gb (Sum-Bytes $MoveOrKeep))))
[void]$Md.AppendLine(("- never_delete: {0} GB" -f (Format-Gb (Sum-Bytes $NeverDelete))))
[void]$Md.AppendLine("")
[void]$Md.AppendLine("## Workspace Feasibility")
[void]$Md.AppendLine("| Scenario | Required GB | C+D Possible | Shortage GB | C Only | D Only |")
[void]$Md.AppendLine("|---|---:|---:|---:|---:|---:|")
foreach ($Row in $FeasibilityRows) {
    [void]$Md.AppendLine(("| {0} | {1} | {2} | {3} | {4} | {5} |" -f $Row.scenario, $Row.required_gb, $Row.possible_with_combined_c_d, $Row.shortage_gb, $Row.c_only_possible, $Row.d_only_possible))
}
[void]$Md.AppendLine("")
[void]$Md.AppendLine("## Largest Safe Delete Candidates")
foreach ($Row in ($SafeDelete | Select-Object -First 30)) {
    [void]$Md.AppendLine(("- {0} GB | {1} | `{2}` | {3}" -f $Row.size_gb, $Row.type, $Row.path, $Row.reason))
}
[void]$Md.AppendLine("")
[void]$Md.AppendLine("## Largest Review Delete Candidates")
foreach ($Row in ($ReviewDelete | Select-Object -First 50)) {
    [void]$Md.AppendLine(("- {0} GB | {1} | `{2}` | {3}" -f $Row.size_gb, $Row.type, $Row.path, $Row.reason))
}
[void]$Md.AppendLine("")
[void]$Md.AppendLine("## Largest Move Or Keep Candidates")
foreach ($Row in ($MoveOrKeep | Select-Object -First 30)) {
    [void]$Md.AppendLine(("- {0} GB | {1} | `{2}` | {3}" -f $Row.size_gb, $Row.type, $Row.path, $Row.reason))
}
[void]$Md.AppendLine("")
[void]$Md.AppendLine("## Never Delete Top")
foreach ($Row in ($NeverDelete | Select-Object -First 30)) {
    [void]$Md.AppendLine(("- {0} GB | {1} | `{2}` | {3}" -f $Row.size_gb, $Row.type, $Row.path, $Row.reason))
}
[void]$Md.AppendLine("")
[void]$Md.AppendLine("## Skipped System/Risky Roots")
foreach ($Path in $SystemSkipRoots) {
    [void]$Md.AppendLine(('- `{0}`' -f $Path))
}
[void]$Md.AppendLine("")
[void]$Md.AppendLine("## Safe Delete Command Draft (Not Executed)")
[void]$Md.AppendLine("Only run after explicit approval. Review-delete candidates are intentionally excluded.")
[void]$Md.AppendLine("")
[void]$Md.AppendLine('```powershell')
foreach ($Row in $SafeDelete) {
    $Quoted = $Row.path -replace "'", "''"
    if ($Row.type -match "dir|cache|build|temp") {
        [void]$Md.AppendLine(("Remove-Item -LiteralPath '{0}' -Recurse -Force" -f $Quoted))
    }
    else {
        [void]$Md.AppendLine(("Remove-Item -LiteralPath '{0}' -Force" -f $Quoted))
    }
}
[void]$Md.AppendLine('```')
[void]$Md.AppendLine("")
[void]$Md.AppendLine("## Notes")
[void]$Md.AppendLine("- review_delete is not safe-delete. It requires separate human approval and, for archives/split parts, package verification.")
[void]$Md.AppendLine("- Windows/system/risky roots were skipped and not suggested as direct deletion candidates.")
[void]$Md.AppendLine("- Protected data masters and current 10k artifact/final package paths were classified as never_delete.")

$Md.ToString() | Set-Content -LiteralPath (Join-Path $ReportDir "pc2_full_cleanup_audit.md") -Encoding UTF8

$FeasibilityMd = New-Object System.Text.StringBuilder
[void]$FeasibilityMd.AppendLine("# PC2 Full Workspace Feasibility")
[void]$FeasibilityMd.AppendLine("")
[void]$FeasibilityMd.AppendLine(("C free: {0} GB" -f (Format-Gb $CFree)))
[void]$FeasibilityMd.AppendLine(("D free: {0} GB" -f (Format-Gb $DFree)))
[void]$FeasibilityMd.AppendLine(("C+D combined free: {0} GB" -f (Format-Gb $CombinedFree)))
[void]$FeasibilityMd.AppendLine("")
[void]$FeasibilityMd.AppendLine("| Scenario | Required GB | Combined Possible | Shortage GB |")
[void]$FeasibilityMd.AppendLine("|---|---:|---:|---:|")
foreach ($Row in $FeasibilityRows) {
    [void]$FeasibilityMd.AppendLine(("| {0} | {1} | {2} | {3} |" -f $Row.scenario, $Row.required_gb, $Row.possible_with_combined_c_d, $Row.shortage_gb))
}
[void]$FeasibilityMd.AppendLine("")
[void]$FeasibilityMd.AppendLine("Interpretation:")
[void]$FeasibilityMd.AppendLine("- Full 39k work on C+D combined is possible only when the scenario row says True.")
[void]$FeasibilityMd.AppendLine("- Chunked 10k/5k generation is the practical path when full unpacked/package-only rows are False.")
[void]$FeasibilityMd.AppendLine("- Large archives and review_delete items should not be deleted before explicit package/receiver verification.")
$FeasibilityMd.ToString() | Set-Content -LiteralPath (Join-Path $ReportDir "pc2_full_workspace_feasibility.md") -Encoding UTF8

$ConsoleSummary = [pscustomobject]@{
    report_dir = $ReportDir
    generated_files = @(
        "pc2_full_cleanup_audit.json",
        "pc2_full_cleanup_audit.md",
        "pc2_full_cleanup_candidates.csv",
        "pc2_full_safe_delete_candidates.csv",
        "pc2_full_review_delete_candidates.csv",
        "pc2_full_move_or_keep_candidates.csv",
        "pc2_full_never_delete_candidates.csv",
        "pc2_full_large_files_top300.csv",
        "pc2_full_large_dirs_top150.csv",
        "pc2_full_duplicate_archive_pairs.csv",
        "pc2_full_workspace_feasibility.md"
    )
    free_space = [pscustomobject]@{
        c_free_gb = Format-Gb $CFree
        d_free_gb = Format-Gb $DFree
        combined_free_gb = Format-Gb $CombinedFree
    }
    estimated = $Summary.estimated_reclaim
    counts = $Summary.counts
    feasibility = $FeasibilityRows
    top_safe_delete = $SafeDelete | Select-Object -First 30
    top_review_delete = $ReviewDelete | Select-Object -First 50
    top_move_or_keep = $MoveOrKeep | Select-Object -First 30
    top_never_delete = $NeverDelete | Select-Object -First 30
    safe_delete_command_draft = @($SafeDelete | Select-Object -First 50 | ForEach-Object {
        $Quoted = $_.path -replace "'", "''"
        if ($_.type -match "dir|cache|build|temp") {
            "Remove-Item -LiteralPath '$Quoted' -Recurse -Force"
        }
        else {
            "Remove-Item -LiteralPath '$Quoted' -Force"
        }
    })
}

$ConsoleSummary | ConvertTo-Json -Depth 8
