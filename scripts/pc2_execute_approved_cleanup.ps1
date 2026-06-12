param(
    [string]$ReportDir = "D:\fit_transfer\reports"
)

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

$Now = Get-Date
$GiB = [double]1GB

$SafeCsv = Join-Path $ReportDir "pc2_full_safe_delete_candidates.csv"
$ReviewCsv = Join-Path $ReportDir "pc2_full_review_delete_candidates.csv"
$NeverCsv = Join-Path $ReportDir "pc2_full_never_delete_candidates.csv"

$OutMd = Join-Path $ReportDir "pc2_cleanup_executed_full.md"
$OutJson = Join-Path $ReportDir "pc2_cleanup_executed_full.json"
$OutFailures = Join-Path $ReportDir "pc2_cleanup_executed_failures.csv"
$OutRemainingReview = Join-Path $ReportDir "pc2_remaining_review_delete_top50.csv"
$OutFeasibility = Join-Path $ReportDir "pc2_workspace_feasibility_after_cleanup.md"

$ApprovedReviewPaths = @(
    "D:\projects\fit-reasoning-vton\backend\datasets\lora_pilot_aihub_10k_full_split.7z.001",
    "D:\projects\fit-reasoning-vton\backend\datasets\lora_pilot_aihub_10k_full_split.7z.002",
    "D:\projects\fit-reasoning-vton\backend\datasets\lora_pilot_aihub_10k_full_split.7z.003",
    "D:\projects\fit-reasoning-vton\backend\datasets\lora_pilot_aihub_10k_full_split.7z.004",
    "D:\projects\fit-reasoning-vton\backend\datasets\lora_pilot_aihub_10k_full_split.7z.005",
    "D:\projects\fit-reasoning-vton\backend\datasets\lora_pilot_aihub_10k_full_split.7z.006",
    "D:\projects\fit-reasoning-vton\backend\datasets\lora_pilot_aihub_10k_full_split.7z.007",
    "D:\projects\fit-reasoning-vton\backend\datasets\lora_pilot_aihub_10k_full_split.7z.008",
    "D:\projects\fit-reasoning-vton\backend\datasets\lora_pilot_aihub_10k_full_split.7z.009",
    "D:\projects\fit-reasoning-vton\backend\datasets\lora_pilot_aihub_10k_full_split.7z.010",
    "D:\projects\fit-reasoning-vton\backend\datasets\lora_pilot_aihub_10k_full_split.7z.011",
    "D:\projects\fit-reasoning-vton\backend\datasets\lora_pilot_aihub_10k_full_split.7z.012",
    "D:\fit_transfer\densepose_smoke100_norm",
    "D:\fit_transfer\densepose_smoke100",
    "D:\fit_transfer\agnostic_smoke100"
)

$ExplicitProtectedRoots = @(
    "D:\projects\fit-reasoning-vton\.git",
    "D:\projects\fit-reasoning-vton.git",
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
    "C:\Users\user\miniconda3\envs\vton",
    "D:\fit_transfer\external\detectron2"
)

function Format-Gb([double]$Bytes) {
    [math]::Round(($Bytes / $GiB), 6)
}

function Get-FreeSnapshot {
    $Rows = foreach ($Letter in @("C", "D")) {
        try {
            $Drive = [System.IO.DriveInfo]::new("$Letter`:\")
            [pscustomobject]@{
                drive = $Letter
                free_bytes = [int64]$Drive.AvailableFreeSpace
                total_bytes = [int64]$Drive.TotalSize
                free_gb = Format-Gb $Drive.AvailableFreeSpace
                total_gb = Format-Gb $Drive.TotalSize
            }
        }
        catch {
            [pscustomobject]@{
                drive = $Letter
                free_bytes = 0
                total_bytes = 0
                free_gb = 0
                total_gb = 0
            }
        }
    }
    @($Rows)
}

function Test-SameOrUnderPath([string]$Path, [string[]]$Roots) {
    if ([string]::IsNullOrWhiteSpace($Path)) { return $false }
    $CleanPath = $Path.TrimEnd("\")
    foreach ($Root in $Roots) {
        if ([string]::IsNullOrWhiteSpace($Root)) { continue }
        $CleanRoot = $Root.TrimEnd("\")
        if ($CleanPath.Equals($CleanRoot, [System.StringComparison]::OrdinalIgnoreCase)) { return $true }
        if ($CleanPath.StartsWith($CleanRoot + "\", [System.StringComparison]::OrdinalIgnoreCase)) { return $true }
    }
    return $false
}

function Test-PathContainsProtectedRoot([string]$Path, [string[]]$Roots) {
    if ([string]::IsNullOrWhiteSpace($Path)) { return $false }
    $CleanPath = $Path.TrimEnd("\")
    foreach ($Root in $Roots) {
        if ([string]::IsNullOrWhiteSpace($Root)) { continue }
        $CleanRoot = $Root.TrimEnd("\")
        if ($CleanPath.Equals($CleanRoot, [System.StringComparison]::OrdinalIgnoreCase)) { continue }
        if ($CleanRoot.StartsWith($CleanPath + "\", [System.StringComparison]::OrdinalIgnoreCase)) { return $true }
    }
    return $false
}

function Get-DriveName([string]$Path) {
    if ($Path -match "^[A-Za-z]:") { return $Path.Substring(0, 1).ToUpperInvariant() }
    return ""
}

function Get-PathKind([string]$Path) {
    if (Test-Path -LiteralPath $Path -PathType Container) { return "directory" }
    if (Test-Path -LiteralPath $Path -PathType Leaf) { return "file" }
    return "missing"
}

function Get-PathSizeBytes([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return [int64]0 }
    if (Test-Path -LiteralPath $Path -PathType Leaf) {
        try { return [int64]([System.IO.FileInfo]::new($Path)).Length } catch { return [int64]0 }
    }
    $Total = [int64]0
    $Stack = New-Object System.Collections.Generic.Stack[string]
    $Stack.Push($Path)
    while ($Stack.Count -gt 0) {
        $Current = $Stack.Pop()
        try {
            foreach ($File in [System.IO.Directory]::EnumerateFiles($Current)) {
                try { $Total += [int64]([System.IO.FileInfo]::new($File)).Length } catch {}
            }
            foreach ($Dir in [System.IO.Directory]::EnumerateDirectories($Current)) {
                try {
                    $DirInfo = [System.IO.DirectoryInfo]::new($Dir)
                    if (($DirInfo.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { continue }
                    $Stack.Push($Dir)
                }
                catch {}
            }
        }
        catch {}
    }
    return $Total
}

function New-TargetRow(
    [string]$Path,
    [string]$Source,
    [string]$Classification,
    [string]$Type,
    [string]$Reason,
    [double]$ReportSizeGb
) {
    $Kind = Get-PathKind $Path
    $ActualBytes = Get-PathSizeBytes $Path
    [pscustomobject]@{
        path = $Path
        drive = Get-DriveName $Path
        kind = $Kind
        source = $Source
        classification = $Classification
        type = $Type
        reason = $Reason
        report_size_gb = $ReportSizeGb
        actual_size_bytes_before = $ActualBytes
        actual_size_gb_before = Format-Gb $ActualBytes
    }
}

New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null

$BeforeFree = Get-FreeSnapshot

$NeverRows = if (Test-Path -LiteralPath $NeverCsv) { @(Import-Csv -LiteralPath $NeverCsv) } else { @() }
$NeverPaths = @($NeverRows | ForEach-Object { $_.path })
$ProtectedRoots = @($ExplicitProtectedRoots + $NeverPaths | Where-Object { $_ } | Select-Object -Unique)

$SafeRows = if (Test-Path -LiteralPath $SafeCsv) { @(Import-Csv -LiteralPath $SafeCsv) } else { @() }
$ReviewRows = if (Test-Path -LiteralPath $ReviewCsv) { @(Import-Csv -LiteralPath $ReviewCsv) } else { @() }

$SafeDeleteTargets = @(
    $SafeRows |
        Where-Object {
            $_.classification -eq "safe_delete" -and
            $_.requires_user_approval -eq "false" -and
            -not (Test-SameOrUnderPath $_.path $ProtectedRoots) -and
            -not (Test-PathContainsProtectedRoot $_.path $ProtectedRoots)
        } |
        ForEach-Object {
            New-TargetRow $_.path "safe_delete_requires_user_approval_false" $_.classification $_.type $_.reason ([double]$_.size_gb)
        }
)

$ReviewLookup = @{}
foreach ($Row in $ReviewRows) {
    if ($Row.path) { $ReviewLookup[$Row.path.ToLowerInvariant()] = $Row }
}

$ApprovedReviewTargets = foreach ($Path in $ApprovedReviewPaths) {
    $Meta = $ReviewLookup[$Path.ToLowerInvariant()]
    $Type = if ($Meta) { $Meta.type } else { "approved_review_path" }
    $Reason = if ($Meta) { $Meta.reason } else { "Explicitly approved review_delete path." }
    $SizeGb = if ($Meta -and $Meta.size_gb) { [double]$Meta.size_gb } else { 0 }
    New-TargetRow $Path "approved_review_delete" "review_delete" $Type $Reason $SizeGb
}

$RawTargets = @($SafeDeleteTargets + $ApprovedReviewTargets)
$TargetMap = @{}
foreach ($Target in $RawTargets) {
    if (-not $Target.path) { continue }
    $TargetMap[$Target.path.ToLowerInvariant()] = $Target
}
$Targets = @($TargetMap.Values | Sort-Object path)

$ExcludedRows = New-Object System.Collections.Generic.List[object]
$DeleteRows = New-Object System.Collections.Generic.List[object]
foreach ($Target in $Targets) {
    $BlockReason = $null
    if ($Target.kind -eq "missing") {
        $BlockReason = "missing_before_delete"
    }
    elseif (Test-SameOrUnderPath $Target.path $ProtectedRoots) {
        $BlockReason = "blocked_protected_or_never_delete_root"
    }
    elseif (Test-PathContainsProtectedRoot $Target.path $ProtectedRoots) {
        $BlockReason = "blocked_contains_protected_or_never_delete_root"
    }

    if ($BlockReason) {
        $ExcludedRows.Add([pscustomobject]@{
            path = $Target.path
            source = $Target.source
            classification = $Target.classification
            reason = $BlockReason
            size_gb = $Target.actual_size_gb_before
        }) | Out-Null
    }
    else {
        $DeleteRows.Add($Target) | Out-Null
    }
}

$EstimatedDeleteBytes = [int64](($DeleteRows | Measure-Object -Property actual_size_bytes_before -Sum).Sum)

$Results = New-Object System.Collections.Generic.List[object]
foreach ($Target in $DeleteRows) {
    $Status = "unknown"
    $ErrorMessage = ""
    try {
        if ($Target.kind -eq "directory") {
            Remove-Item -LiteralPath $Target.path -Recurse -Force -ErrorAction Stop
        }
        elseif ($Target.kind -eq "file") {
            Remove-Item -LiteralPath $Target.path -Force -ErrorAction Stop
        }
        else {
            $Status = "missing_before_delete"
        }

        if ($Status -ne "missing_before_delete") {
            if (Test-Path -LiteralPath $Target.path) {
                $Status = "failed_still_exists_after_delete"
                $ErrorMessage = "Path still exists after Remove-Item returned."
            }
            else {
                $Status = "deleted"
            }
        }
    }
    catch {
        $Status = "failed"
        $ErrorMessage = $_.Exception.Message
    }

    $Results.Add([pscustomobject]@{
        path = $Target.path
        drive = $Target.drive
        kind = $Target.kind
        source = $Target.source
        classification = $Target.classification
        type = $Target.type
        expected_size_gb = $Target.actual_size_gb_before
        status = $Status
        error = $ErrorMessage
    }) | Out-Null
}

$AfterFree = Get-FreeSnapshot

$BeforeCombinedBytes = [int64](($BeforeFree | Measure-Object -Property free_bytes -Sum).Sum)
$AfterCombinedBytes = [int64](($AfterFree | Measure-Object -Property free_bytes -Sum).Sum)
$FreedBytes = [int64]($AfterCombinedBytes - $BeforeCombinedBytes)

$SuccessRows = @($Results | Where-Object { $_.status -eq "deleted" })
$FailureRows = @($Results | Where-Object { $_.status -notin @("deleted") })

$FailureExport = @(
    $FailureRows |
        Select-Object path,drive,kind,source,classification,type,expected_size_gb,status,error
)
$FailureExport | Export-Csv -LiteralPath $OutFailures -NoTypeInformation -Encoding UTF8

$DeletedPathSet = @{}
foreach ($Row in $SuccessRows) { $DeletedPathSet[$Row.path.ToLowerInvariant()] = $true }

$RemainingReview = @(
    $ReviewRows |
        Where-Object {
            $_.path -and -not $DeletedPathSet.ContainsKey($_.path.ToLowerInvariant())
        } |
        Sort-Object { [double]$_.size_gb } -Descending |
        Select-Object -First 50
)
$RemainingReview | Export-Csv -LiteralPath $OutRemainingReview -NoTypeInformation -Encoding UTF8

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

$AfterCBytes = [int64](($AfterFree | Where-Object { $_.drive -eq "C" }).free_bytes)
$AfterDBytes = [int64](($AfterFree | Where-Object { $_.drive -eq "D" }).free_bytes)
$AfterCombinedBytes = [int64]($AfterCBytes + $AfterDBytes)
$FeasibilityRows = foreach ($Key in $FeasibilityTargets.Keys) {
    $RequiredGb = [double]$FeasibilityTargets[$Key]
    $RequiredBytes = [int64]($RequiredGb * $GiB)
    [pscustomobject]@{
        scenario = $Key
        required_gb = [math]::Round($RequiredGb, 3)
        combined_free_gb = Format-Gb $AfterCombinedBytes
        possible_with_combined_c_d = ($AfterCombinedBytes -ge $RequiredBytes)
        shortage_gb = [math]::Max(0, [math]::Round((($RequiredBytes - $AfterCombinedBytes) / $GiB), 3))
        c_only_possible = ($AfterCBytes -ge $RequiredBytes)
        d_only_possible = ($AfterDBytes -ge $RequiredBytes)
    }
}

$FeasibilityMd = New-Object System.Text.StringBuilder
[void]$FeasibilityMd.AppendLine("# PC2 Workspace Feasibility After Cleanup")
[void]$FeasibilityMd.AppendLine("")
[void]$FeasibilityMd.AppendLine(("C free: {0} GB" -f (Format-Gb $AfterCBytes)))
[void]$FeasibilityMd.AppendLine(("D free: {0} GB" -f (Format-Gb $AfterDBytes)))
[void]$FeasibilityMd.AppendLine(("C+D combined free: {0} GB" -f (Format-Gb $AfterCombinedBytes)))
[void]$FeasibilityMd.AppendLine("")
[void]$FeasibilityMd.AppendLine("| Scenario | Required GB | Combined Possible | Shortage GB | C Only | D Only |")
[void]$FeasibilityMd.AppendLine("|---|---:|---:|---:|---:|---:|")
foreach ($Row in $FeasibilityRows) {
    [void]$FeasibilityMd.AppendLine(("| {0} | {1} | {2} | {3} | {4} | {5} |" -f $Row.scenario, $Row.required_gb, $Row.possible_with_combined_c_d, $Row.shortage_gb, $Row.c_only_possible, $Row.d_only_possible))
}
$FeasibilityMd.ToString() | Set-Content -LiteralPath $OutFeasibility -Encoding UTF8

$Summary = [pscustomobject]@{
    generated_at = $Now.ToString("o")
    report_dir = $ReportDir
    inputs = [pscustomobject]@{
        safe_csv = $SafeCsv
        review_csv = $ReviewCsv
        never_csv = $NeverCsv
    }
    free_space_before = $BeforeFree
    free_space_after = $AfterFree
    freed_bytes = $FreedBytes
    freed_gb = Format-Gb $FreedBytes
    estimated_delete_bytes = $EstimatedDeleteBytes
    estimated_delete_gb = Format-Gb $EstimatedDeleteBytes
    safe_delete_requires_false_count = $SafeDeleteTargets.Count
    approved_review_count = $ApprovedReviewTargets.Count
    delete_target_count = $DeleteRows.Count
    excluded_target_count = $ExcludedRows.Count
    deleted_success_count = $SuccessRows.Count
    delete_failure_count = $FailureRows.Count
    excluded_targets = $ExcludedRows
    delete_results = $Results
    remaining_review_top50 = $RemainingReview
    feasibility_after_cleanup = $FeasibilityRows
}
$Summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutJson -Encoding UTF8

$Md = New-Object System.Text.StringBuilder
[void]$Md.AppendLine("# PC2 Cleanup Executed Full")
[void]$Md.AppendLine("")
[void]$Md.AppendLine(("Generated: {0}" -f $Now.ToString("yyyy-MM-dd HH:mm:ss zzz")))
[void]$Md.AppendLine("")
[void]$Md.AppendLine("## Guardrails")
[void]$Md.AppendLine("- safe_delete was executed only when `requires_user_approval=false`.")
[void]$Md.AppendLine("- approved review_delete was limited to the 12 split parts and 3 smoke100 paths explicitly listed by the user.")
[void]$Md.AppendLine("- never_delete, move_to_external_or_keep, source code, raw/processed master, active env, external detectron2 source, and current final artifacts were protected.")
[void]$Md.AppendLine("")
[void]$Md.AppendLine("## Free Space Before")
foreach ($Drive in $BeforeFree) {
    [void]$Md.AppendLine(("- {0}: {1} GB free" -f $Drive.drive, $Drive.free_gb))
}
[void]$Md.AppendLine("")
[void]$Md.AppendLine("## Delete Targets")
[void]$Md.AppendLine(("- safe_delete requires_user_approval=false: {0}" -f $SafeDeleteTargets.Count))
[void]$Md.AppendLine(("- approved review_delete: {0}" -f $ApprovedReviewTargets.Count))
[void]$Md.AppendLine(("- final delete target count after guardrails: {0}" -f $DeleteRows.Count))
[void]$Md.AppendLine(("- excluded target count: {0}" -f $ExcludedRows.Count))
[void]$Md.AppendLine(("- expected delete size: {0} GB" -f (Format-Gb $EstimatedDeleteBytes)))
[void]$Md.AppendLine("")
[void]$Md.AppendLine("### Target List")
foreach ($Target in $DeleteRows) {
    [void]$Md.AppendLine(('- {0} GB | {1} | {2} | `{3}`' -f $Target.actual_size_gb_before, $Target.kind, $Target.source, $Target.path))
}
[void]$Md.AppendLine("")
[void]$Md.AppendLine("## Results")
[void]$Md.AppendLine(("- deleted success count: {0}" -f $SuccessRows.Count))
[void]$Md.AppendLine(("- delete failure count: {0}" -f $FailureRows.Count))
[void]$Md.AppendLine(("- actual free-space delta: {0} GB" -f (Format-Gb $FreedBytes)))
[void]$Md.AppendLine("")
[void]$Md.AppendLine("## Free Space After")
foreach ($Drive in $AfterFree) {
    [void]$Md.AppendLine(("- {0}: {1} GB free" -f $Drive.drive, $Drive.free_gb))
}
[void]$Md.AppendLine("")
[void]$Md.AppendLine("## Failures")
if ($FailureRows.Count -eq 0) {
    [void]$Md.AppendLine("- None")
}
else {
    foreach ($Row in $FailureRows) {
        [void]$Md.AppendLine(("- {0} | `{1}` | {2}" -f $Row.status, $Row.path, $Row.error))
    }
}
[void]$Md.AppendLine("")
[void]$Md.AppendLine("## Remaining Review Delete Top 50")
foreach ($Row in $RemainingReview) {
    [void]$Md.AppendLine(("- {0} GB | {1} | `{2}` | {3}" -f $Row.size_gb, $Row.type, $Row.path, $Row.reason))
}
[void]$Md.AppendLine("")
[void]$Md.AppendLine("## Workspace Feasibility After Cleanup")
[void]$Md.AppendLine("| Scenario | Required GB | Combined Possible | Shortage GB |")
[void]$Md.AppendLine("|---|---:|---:|---:|")
foreach ($Row in $FeasibilityRows) {
    [void]$Md.AppendLine(("| {0} | {1} | {2} | {3} |" -f $Row.scenario, $Row.required_gb, $Row.possible_with_combined_c_d, $Row.shortage_gb))
}
$Md.ToString() | Set-Content -LiteralPath $OutMd -Encoding UTF8

$Console = [pscustomobject]@{
    reports = @($OutMd, $OutJson, $OutFailures, $OutRemainingReview, $OutFeasibility)
    free_space_before = $BeforeFree
    free_space_after = $AfterFree
    freed_gb = Format-Gb $FreedBytes
    estimated_delete_gb = Format-Gb $EstimatedDeleteBytes
    safe_delete_requires_false_count = $SafeDeleteTargets.Count
    approved_review_count = $ApprovedReviewTargets.Count
    delete_target_count = $DeleteRows.Count
    excluded_target_count = $ExcludedRows.Count
    deleted_success_count = $SuccessRows.Count
    delete_failure_count = $FailureRows.Count
    failures = $FailureRows
    feasibility_after_cleanup = $FeasibilityRows
}
$Console | ConvertTo-Json -Depth 8
