$ErrorActionPreference = "Stop"

$RepoDir = Split-Path $PSScriptRoot -Parent
$TempRoot = $env:RUNNER_TEMP ?? $env:TEMP ?? [System.IO.Path]::GetTempPath()
$TestId = [guid]::NewGuid().ToString("N")
$TestHome = Join-Path $TempRoot "opencode-install-home-$TestId"
$OriginalUserProfile = $env:USERPROFILE
$OriginalLocalAppData = $env:LOCALAPPDATA
$OriginalTemp = $env:TEMP

function Assert-Path { param($Path)
    if (-not (Test-Path $Path)) { throw "Expected path: $Path" }
}

try {
    Remove-Item $TestHome -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $TestHome | Out-Null
    $env:USERPROFILE = $TestHome
    $env:LOCALAPPDATA = Join-Path $TestHome "AppData\Local"

    # A clean dry-run must leave the requested HOME absent.
    Remove-Item $TestHome -Recurse -Force -ErrorAction SilentlyContinue
    $DryRunOutput = (& (Join-Path $RepoDir "install.ps1") -DryRun -Verbose *>&1 | Out-String)
    if (Test-Path $TestHome) { throw "Clean DryRun modified USERPROFILE" }
    foreach ($Expected in @("create directory:", "install-dependencies:", "defer-verification:", "Dry run complete; no changes made")) {
        if (-not $DryRunOutput.Contains($Expected)) { throw "DryRun output missing: $Expected" }
    }

    $DetachedDir = Join-Path $TempRoot "opencode-detached-dry-run-$TestId"
    Remove-Item $DetachedDir -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path (Join-Path $DetachedDir "tmp") | Out-Null
    Copy-Item (Join-Path $RepoDir "install.ps1") (Join-Path $DetachedDir "install.ps1")
    $env:TEMP = Join-Path $DetachedDir "tmp"
    $DetachedOutput = (& (Join-Path $DetachedDir "install.ps1") -DryRun *>&1 | Out-String)
    $env:TEMP = $OriginalTemp
    if (Test-Path $TestHome) { throw "Detached DryRun modified USERPROFILE" }
    if (@(Get-ChildItem (Join-Path $DetachedDir "tmp") -Force).Count -ne 0) { throw "Detached DryRun created temporary files" }
    if (-not $DetachedOutput.Contains("clone https://github.com/Rukawua26/opencode-ecosystem.git at tag v1.10.0")) {
        throw "Detached DryRun did not report remote clone"
    }
    Remove-Item $DetachedDir -Recurse -Force
    New-Item -ItemType Directory -Force -Path $TestHome | Out-Null

    & (Join-Path $RepoDir "install.ps1") -Verbose -SkipMemory -Force
    if ($LASTEXITCODE -ne 0) { throw "Initial install failed" }

    $OpenCodeDir = Join-Path $TestHome ".config\opencode"
    $SkillsDir = Join-Path $TestHome "opencode-custom\skills"
    Assert-Path (Join-Path $OpenCodeDir "opencode.jsonc")
    Assert-Path (Join-Path $OpenCodeDir "mcp\node_modules\@modelcontextprotocol\sdk\package.json")
    Assert-Path (Join-Path $OpenCodeDir "tools\profile.js")
    Assert-Path (Join-Path $TestHome ".opencode\bin\opencode-profile.cmd")
    Assert-Path (Join-Path $TestHome ".opencode\bin\opencode-light.cmd")
    Assert-Path (Join-Path $OpenCodeDir "tools\skills.js")
    Assert-Path (Join-Path $TestHome ".opencode\bin\opencode-skills.cmd")

    if ($IsWindows) {
        $LaunchOutput = Join-Path $TestHome "profile-launch.txt"
        $env:PROFILE_TEST_OUTPUT = $LaunchOutput
        Set-Content -LiteralPath (Join-Path $TestHome ".opencode\bin\opencode.cmd") -Encoding ascii -Value @'
@echo off
> "%PROFILE_TEST_OUTPUT%" <nul set /p "=%OPENCODE_CONFIG%|%OPENCODE_EFFORT_MODE%|%*"
exit /b 0
'@
        & (Join-Path $TestHome ".opencode\bin\opencode-light.cmd") --test-arg
        if ($LASTEXITCODE -ne 0) { throw "Light profile launcher failed" }
        $ExpectedLaunch = "$(Join-Path $OpenCodeDir 'profiles\light\opencode.jsonc')|low|--test-arg"
        if ((Get-Content $LaunchOutput -Raw) -ne $ExpectedLaunch) {
            throw "Light profile launcher did not forward config, effort, and arguments"
        }
        Remove-Item Env:PROFILE_TEST_OUTPUT
    }

    Set-Content (Join-Path $OpenCodeDir "agents\ai-matcher.md") "user-agent-marker"
    Set-Content (Join-Path $SkillsDir "defuddle\SKILL.md") "user-skill-marker"
    Set-Content (Join-Path $OpenCodeDir "profiles\work\opencode.jsonc") "user-profile-marker"
    Set-Content (Join-Path $OpenCodeDir "tools\doctor.js") "user-tool-marker"

    $PopulatedBefore = @(Get-ChildItem $TestHome -Recurse -Force | ForEach-Object {
        $Hash = if (-not $_.PSIsContainer -and -not ($_.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) { (Get-FileHash $_.FullName -Algorithm SHA256).Hash } else { "" }
        "$($_.FullName.Substring($TestHome.Length))|$($_.Attributes)|$($_.Length)|$Hash"
    } | Sort-Object)
    $NormalDryRun = (& (Join-Path $RepoDir "install.ps1") -SkipMemory -DryRun *>&1 | Out-String)
    $ForceDryRun = (& (Join-Path $RepoDir "install.ps1") -SkipMemory -Force -DryRun *>&1 | Out-String)
    $PopulatedAfter = @(Get-ChildItem $TestHome -Recurse -Force | ForEach-Object {
        $Hash = if (-not $_.PSIsContainer -and -not ($_.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) { (Get-FileHash $_.FullName -Algorithm SHA256).Hash } else { "" }
        "$($_.FullName.Substring($TestHome.Length))|$($_.Attributes)|$($_.Length)|$Hash"
    } | Sort-Object)
    if (Compare-Object $PopulatedBefore $PopulatedAfter) { throw "Normal or Force DryRun changed populated state" }
    if (-not $NormalDryRun.Contains("preserve:") -or -not $ForceDryRun.Contains("backup:")) {
        throw "Normal/Force DryRun did not reflect mode decisions"
    }

    & (Join-Path $RepoDir "install.ps1") -SkipMemory
    if ($LASTEXITCODE -ne 0) { throw "Preserving reinstall failed" }

    $ExpectedMarkers = @{
        (Join-Path $OpenCodeDir "agents\ai-matcher.md") = "user-agent-marker"
        (Join-Path $SkillsDir "defuddle\SKILL.md") = "user-skill-marker"
        (Join-Path $OpenCodeDir "profiles\work\opencode.jsonc") = "user-profile-marker"
        (Join-Path $OpenCodeDir "tools\doctor.js") = "user-tool-marker"
    }
    foreach ($Entry in $ExpectedMarkers.GetEnumerator()) {
        if ((Get-Content $Entry.Key -Raw).Trim() -ne $Entry.Value) {
            throw "Reinstall overwrote $($Entry.Key)"
        }
    }

    $Manifest = Join-Path $OpenCodeDir ".ecosystem-managed-files"
    Remove-Item $Manifest -Force -ErrorAction SilentlyContinue
    Set-Content (Join-Path $OpenCodeDir "opencode.jsonc") "user-config-marker"
    Set-Content (Join-Path $OpenCodeDir "plugins\user-custom.js") "user-custom-plugin"
    Set-Content (Join-Path $OpenCodeDir "plugins\unknown-old.js") "unknown-old-plugin"

    & (Join-Path $RepoDir "install.ps1") -SkipMemory -Sync
    if ($LASTEXITCODE -ne 0) { throw "First sync failed" }
    if ((Get-Content (Join-Path $OpenCodeDir "opencode.jsonc") -Raw).Trim() -ne "user-config-marker") {
        throw "Sync overwrote opencode.jsonc"
    }
    if ((Get-Content (Join-Path $OpenCodeDir "plugins\user-custom.js") -Raw).Trim() -ne "user-custom-plugin") {
        throw "Sync overwrote an unmanaged custom file"
    }
    Assert-Path (Join-Path $OpenCodeDir "plugins\unknown-old.js")
    if ((Get-Content (Join-Path $OpenCodeDir "agents\ai-matcher.md") -Raw).Trim() -eq "user-agent-marker") {
        throw "Sync did not update a managed agent"
    }
    Assert-Path $Manifest

    Set-Content (Join-Path $OpenCodeDir "plugins\retired-managed.js") "retired-managed-plugin"
    Add-Content $Manifest "opencode/plugins/retired-managed.js"
    Set-Content (Join-Path $TestHome "escape") "do-not-delete"
    Add-Content $Manifest "opencode/../../escape"
    Add-Content $Manifest "opencode/opencode.jsonc"
    Add-Content $Manifest "opencode/.ecosystem-managed-files"
    Set-Content (Join-Path $OpenCodeDir "profiles\work\opencode.jsonc") "sync-profile-marker"
    $BackupRoot = Join-Path $TestHome ".local\share\opencode\install-backups"
    foreach ($Index in 1..12) { New-Item -ItemType Directory -Force -Path (Join-Path $BackupRoot "10000000$Index-1") | Out-Null }

    $BeforeDryRun = @(Get-ChildItem $TestHome -Recurse -Force | ForEach-Object {
        $Hash = if (-not $_.PSIsContainer -and -not ($_.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) { (Get-FileHash $_.FullName -Algorithm SHA256).Hash } else { "" }
        "$($_.FullName.Substring($TestHome.Length))|$($_.Attributes)|$($_.Length)|$Hash"
    } | Sort-Object)
    $SyncDryRunOutput = (& (Join-Path $RepoDir "install.ps1") -SkipMemory -Sync -DryRun *>&1 | Out-String)
    $AfterDryRun = @(Get-ChildItem $TestHome -Recurse -Force | ForEach-Object {
        $Hash = if (-not $_.PSIsContainer -and -not ($_.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) { (Get-FileHash $_.FullName -Algorithm SHA256).Hash } else { "" }
        "$($_.FullName.Substring($TestHome.Length))|$($_.Attributes)|$($_.Length)|$Hash"
    } | Sort-Object)
    if (Compare-Object $BeforeDryRun $AfterDryRun) { throw "Sync DryRun changed the installation" }
    if (-not $SyncDryRunOutput.Contains("backup: opencode/plugins/retired-managed.js") -or -not $SyncDryRunOutput.Contains("remove: opencode/plugins/retired-managed.js")) {
        throw "Sync DryRun did not project stale backup and removal"
    }

    & (Join-Path $RepoDir "install.ps1") -SkipMemory -Sync
    if ($LASTEXITCODE -ne 0) { throw "Managed pruning sync failed" }
    if (Test-Path (Join-Path $OpenCodeDir "plugins\retired-managed.js")) {
        throw "Sync did not prune a stale managed file"
    }
    Assert-Path (Join-Path $OpenCodeDir "plugins\user-custom.js")
    Assert-Path (Join-Path $OpenCodeDir "plugins\unknown-old.js")
    if ((Get-Content (Join-Path $TestHome "escape") -Raw).Trim() -ne "do-not-delete") {
        throw "Sync followed an unsafe manifest path"
    }
    if ((Get-Content (Join-Path $OpenCodeDir "opencode.jsonc") -Raw).Trim() -ne "user-config-marker") {
        throw "Sync pruned protected opencode.jsonc"
    }

    $Backups = @(Get-ChildItem $BackupRoot -Recurse -File -ErrorAction SilentlyContinue)
    if (@(Get-ChildItem $BackupRoot -Directory).Count -gt 10) {
        throw "Sync retained more than 10 install backup directories"
    }
    if (-not ($Backups | Where-Object { $_.FullName.Replace('\', '/') -like "*/opencode/plugins/retired-managed.js" })) {
        throw "Sync did not back up a stale managed file"
    }
    if (-not ($Backups | Where-Object { $_.FullName.Replace('\', '/') -like "*/opencode/profiles/work/opencode.jsonc" })) {
        throw "Sync did not back up a replaced managed file"
    }

    $SymlinkTarget = Join-Path $TestHome "symlink-target"
    $GuardrailsPath = Join-Path $OpenCodeDir "plugins\guardrails.js"
    Set-Content $SymlinkTarget "symlink-target"
    Remove-Item $GuardrailsPath -Force
    New-Item -ItemType SymbolicLink -Path $GuardrailsPath -Target $SymlinkTarget | Out-Null
    $RejectedDryRunSymlink = $false
    try {
        & (Join-Path $RepoDir "install.ps1") -SkipMemory -Sync -DryRun
    } catch {
        $RejectedDryRunSymlink = $_.Exception.Message -like "*symbolic-link component*"
    }
    if (-not $RejectedDryRunSymlink) { throw "Sync DryRun did not reject a managed symbolic link" }
    $RejectedSymlink = $false
    try {
        & (Join-Path $RepoDir "install.ps1") -SkipMemory -Sync
    } catch {
        $RejectedSymlink = $_.Exception.Message -like "*symbolic-link component*"
    }
    if (-not $RejectedSymlink) { throw "Sync did not reject a managed symbolic link" }
    if ((Get-Content $SymlinkTarget -Raw).Trim() -ne "symlink-target") {
        throw "Sync modified a symbolic-link target"
    }

    $RejectedForceDryRunSymlink = $false
    try {
        & (Join-Path $RepoDir "install.ps1") -SkipMemory -Force -DryRun
    } catch {
        $RejectedForceDryRunSymlink = $_.Exception.Message -like "*symbolic-link component*"
    }
    if (-not $RejectedForceDryRunSymlink) { throw "Force DryRun did not reject a managed symbolic link" }
    $RejectedForceSymlink = $false
    try {
        & (Join-Path $RepoDir "install.ps1") -SkipMemory -Force
    } catch {
        $RejectedForceSymlink = $_.Exception.Message -like "*symbolic-link component*"
    }
    if (-not $RejectedForceSymlink) { throw "Force did not reject a managed symbolic link" }
    if ((Get-Content $SymlinkTarget -Raw).Trim() -ne "symlink-target") {
        throw "Force modified a symbolic-link target"
    }
    Remove-Item $GuardrailsPath -Force
    Copy-Item (Join-Path $RepoDir "config\plugins\guardrails.js") $GuardrailsPath

    $NestedVictim = Join-Path $TestHome "nested-victim"
    $DefuddlePath = Join-Path $SkillsDir "defuddle"
    Remove-Item $DefuddlePath -Recurse -Force
    New-Item -ItemType Directory -Force -Path $NestedVictim | Out-Null
    Set-Content (Join-Path $NestedVictim "SKILL.md") "nested-target"
    New-Item -ItemType SymbolicLink -Path $DefuddlePath -Target $NestedVictim | Out-Null
    $RejectedNestedDryRunSymlink = $false
    try {
        & (Join-Path $RepoDir "install.ps1") -SkipMemory -Sync -DryRun
    } catch {
        $RejectedNestedDryRunSymlink = $_.Exception.Message -like "*symbolic-link component*"
    }
    if (-not $RejectedNestedDryRunSymlink) { throw "Sync DryRun did not reject a symbolic-link directory" }
    $RejectedNestedSymlink = $false
    try {
        & (Join-Path $RepoDir "install.ps1") -SkipMemory -Sync
    } catch {
        $RejectedNestedSymlink = $_.Exception.Message -like "*symbolic-link component*"
    }
    if (-not $RejectedNestedSymlink) { throw "Sync did not reject a symbolic-link directory" }
    if ((Get-Content (Join-Path $NestedVictim "SKILL.md") -Raw).Trim() -ne "nested-target") {
        throw "Sync modified a file through a symbolic-link directory"
    }
    Remove-Item $DefuddlePath -Force
    Copy-Item (Join-Path $RepoDir "skills\defuddle") $DefuddlePath -Recurse

    Set-Content (Join-Path $OpenCodeDir "profiles\work\opencode.jsonc") "user-profile-marker"
    & (Join-Path $RepoDir "install.ps1") -SkipMemory -Force
    if ($LASTEXITCODE -ne 0) { throw "Forced reinstall failed" }

    $Backup = Get-ChildItem (Join-Path $OpenCodeDir "profiles") -Directory -Filter "work.bak-*" |
        Sort-Object Name -Descending | Select-Object -First 1
    if (-not $Backup) { throw "Forced reinstall did not create a profile backup" }
    if ((Get-Content (Join-Path $Backup.FullName "opencode.jsonc") -Raw).Trim() -ne "user-profile-marker") {
        throw "Profile backup did not preserve customization"
    }
    if ((Get-Content (Join-Path $OpenCodeDir "profiles\work\opencode.jsonc") -Raw).Trim() -eq "user-profile-marker") {
        throw "Forced reinstall did not replace the managed profile"
    }

    Write-Host "[PASS] PowerShell install, preserve, sync, pruning, SDK, and rollback checks passed"
} finally {
    $env:USERPROFILE = $OriginalUserProfile
    $env:LOCALAPPDATA = $OriginalLocalAppData
    $env:TEMP = $OriginalTemp
    Remove-Item $TestHome -Recurse -Force -ErrorAction SilentlyContinue
}
