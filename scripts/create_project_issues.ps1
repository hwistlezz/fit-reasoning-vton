param(
    [string]$Repo = "hwistlezz/fit-reasoning-vton",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Stop-WithMessage {
    param([string]$Message)

    Write-Error $Message
    exit 1
}

function Resolve-GitHubCli {
    $command = Get-Command gh -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $candidates = @()
    if ($env:ProgramFiles) {
        $candidates += (Join-Path $env:ProgramFiles "GitHub CLI\gh.exe")
    }
    if (${env:ProgramFiles(x86)}) {
        $candidates += (Join-Path ${env:ProgramFiles(x86)} "GitHub CLI\gh.exe")
    }
    if ($env:LOCALAPPDATA) {
        $candidates += (Join-Path $env:LOCALAPPDATA "GitHub CLI\gh.exe")
    }

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    Stop-WithMessage "GitHub CLI 'gh' is not installed or not available on PATH."
}

function Get-IssueTitle {
    param([string]$BodyPath)

    $firstLine = Get-Content -LiteralPath $BodyPath -Encoding UTF8 -TotalCount 1
    if (-not $firstLine -or -not $firstLine.StartsWith("# ")) {
        Stop-WithMessage "Issue body must start with a Markdown H1 title: $BodyPath"
    }

    return $firstLine.Substring(2).Trim()
}

function Get-ExistingIssueUrl {
    param(
        [string]$RepoName,
        [string]$Title
    )

    $json = & $script:Gh issue list `
        --repo $RepoName `
        --state open `
        --search $Title `
        --json title,url 2>$null

    if ($LASTEXITCODE -ne 0 -or -not $json) {
        Write-Warning "Duplicate check failed for '$Title'. Continuing."
        return $null
    }

    $matches = @($json | ConvertFrom-Json | Where-Object { $_.title -eq $Title })
    if ($matches.Count -gt 0) {
        return $matches[0].url
    }

    return $null
}

function Get-AvailableLabels {
    param([string]$RepoName)

    $labels = @{}
    $json = & $script:Gh label list --repo $RepoName --limit 200 --json name 2>$null

    if ($LASTEXITCODE -ne 0 -or -not $json) {
        Write-Warning "Could not read labels from $RepoName. Issues will be created without labels."
        return $labels
    }

    foreach ($label in ($json | ConvertFrom-Json)) {
        $labels[$label.name] = $true
    }

    return $labels
}

$repoRoot = (Get-Location).Path

if (-not (Test-Path -LiteralPath (Join-Path $repoRoot ".git"))) {
    Stop-WithMessage "Run this script from the repository root."
}

if (-not (Test-Path -LiteralPath (Join-Path $repoRoot "docs\issues"))) {
    Stop-WithMessage "Missing docs/issues directory. Run from the expected repository root."
}

$script:Gh = Resolve-GitHubCli

$previousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$authOutput = & $script:Gh auth status --hostname github.com 2>&1
$authExitCode = $LASTEXITCODE
$ErrorActionPreference = $previousErrorActionPreference

if ($authExitCode -ne 0) {
    Stop-WithMessage "GitHub CLI is not authenticated. Run 'gh auth login' first."
}

$issueSpecs = @(
    @{
        BodyFile = "docs/issues/01_stableviton_mvp_plan.md"
        Labels = @("docs", "planning")
    },
    @{
        BodyFile = "docs/issues/02_pc1_stableviton_external_setup.md"
        Labels = @("experiment", "pc1", "planning")
    },
    @{
        BodyFile = "docs/issues/03_pc1_stableviton_cli_smoke_test.md"
        Labels = @("experiment", "pc1")
    },
    @{
        BodyFile = "docs/issues/04_fastapi_backend_skeleton.md"
        Labels = @("feat", "backend", "pc1")
    },
    @{
        BodyFile = "docs/issues/05_tryon_job_api_outputs.md"
        Labels = @("feat", "backend")
    },
    @{
        BodyFile = "docs/issues/06_stableviton_service_wrapper.md"
        Labels = @("feat", "backend", "pc1")
    },
    @{
        BodyFile = "docs/issues/07_pc1_test_job_batch_logging.md"
        Labels = @("experiment", "pc1")
    },
    @{
        BodyFile = "docs/issues/08_pc3_idm_lora_plan.md"
        Labels = @("experiment", "pc3", "planning")
    }
)

$availableLabels = Get-AvailableLabels -RepoName $Repo
$issueUrls = New-Object System.Collections.Generic.List[string]

foreach ($spec in $issueSpecs) {
    $bodyPath = Join-Path $repoRoot $spec.BodyFile
    if (-not (Test-Path -LiteralPath $bodyPath)) {
        Stop-WithMessage "Missing issue body file: $($spec.BodyFile)"
    }

    $title = Get-IssueTitle -BodyPath $bodyPath
    Write-Host ""
    Write-Host "==> $title"

    $existingUrl = Get-ExistingIssueUrl -RepoName $Repo -Title $title
    if ($existingUrl) {
        Write-Host "Already exists: $existingUrl"
        $issueUrls.Add($existingUrl) | Out-Null
        continue
    }

    if ($DryRun) {
        Write-Host "[DryRun] Would create issue from $($spec.BodyFile)"
        continue
    }

    $labelArgs = @()
    foreach ($label in $spec.Labels) {
        if ($availableLabels.ContainsKey($label)) {
            $labelArgs += @("--label", $label)
        }
        else {
            Write-Warning "Label '$label' does not exist. Skipping it."
        }
    }

    $createArgs = @(
        "issue", "create",
        "--repo", $Repo,
        "--title", $title,
        "--body-file", $bodyPath,
        "--assignee", "@me"
    ) + $labelArgs

    $output = & $script:Gh @createArgs 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Issue creation with labels/assignee failed. Retrying without labels and assignee. Details: $output"

        $fallbackArgs = @(
            "issue", "create",
            "--repo", $Repo,
            "--title", $title,
            "--body-file", $bodyPath
        )

        $output = & $script:Gh @fallbackArgs 2>&1
        if ($LASTEXITCODE -ne 0) {
            Stop-WithMessage "Failed to create issue '$title'. Details: $output"
        }
    }

    $url = ($output | Select-Object -Last 1).ToString().Trim()
    Write-Host "Created: $url"
    $issueUrls.Add($url) | Out-Null
}

Write-Host ""
Write-Host "Issue URLs:"
foreach ($url in $issueUrls) {
    Write-Host "- $url"
}
