$ErrorActionPreference = "Stop"

$RepoDir = Split-Path $PSScriptRoot -Parent
$TestHome = Join-Path ($env:RUNNER_TEMP ?? $env:TEMP) "opencode-install-home"
$OriginalUserProfile = $env:USERPROFILE
$OriginalLocalAppData = $env:LOCALAPPDATA

function Assert-Path { param($Path)
    if (-not (Test-Path $Path)) { throw "Expected path: $Path" }
}

try {
    Remove-Item $TestHome -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $TestHome | Out-Null
    $env:USERPROFILE = $TestHome
    $env:LOCALAPPDATA = Join-Path $TestHome "AppData\Local"

    & (Join-Path $RepoDir "install.ps1") -Verbose -SkipMemory -Force
    if ($LASTEXITCODE -ne 0) { throw "Initial install failed" }

    $OpenCodeDir = Join-Path $TestHome ".config\opencode"
    $SkillsDir = Join-Path $TestHome "opencode-custom\skills"
    Assert-Path (Join-Path $OpenCodeDir "opencode.jsonc")
    Assert-Path (Join-Path $OpenCodeDir "mcp\node_modules\@modelcontextprotocol\sdk\package.json")

    Set-Content (Join-Path $OpenCodeDir "agents\ai-matcher.md") "user-agent-marker"
    Set-Content (Join-Path $SkillsDir "defuddle\SKILL.md") "user-skill-marker"
    Set-Content (Join-Path $OpenCodeDir "profiles\work\opencode.jsonc") "user-profile-marker"
    Set-Content (Join-Path $OpenCodeDir "tools\doctor.js") "user-tool-marker"

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
    if (-not ($Backups | Where-Object { $_.FullName -like "*\opencode\plugins\retired-managed.js" })) {
        throw "Sync did not back up a stale managed file"
    }
    if (-not ($Backups | Where-Object { $_.FullName -like "*\opencode\profiles\work\opencode.jsonc" })) {
        throw "Sync did not back up a replaced managed file"
    }

    $SymlinkTarget = Join-Path $TestHome "symlink-target"
    $GuardrailsPath = Join-Path $OpenCodeDir "plugins\guardrails.js"
    Set-Content $SymlinkTarget "symlink-target"
    Remove-Item $GuardrailsPath -Force
    New-Item -ItemType SymbolicLink -Path $GuardrailsPath -Target $SymlinkTarget | Out-Null
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
    Remove-Item $GuardrailsPath -Force
    Copy-Item (Join-Path $RepoDir "config\plugins\guardrails.js") $GuardrailsPath

    $NestedVictim = Join-Path $TestHome "nested-victim"
    $DefuddlePath = Join-Path $SkillsDir "defuddle"
    Remove-Item $DefuddlePath -Recurse -Force
    New-Item -ItemType Directory -Force -Path $NestedVictim | Out-Null
    Set-Content (Join-Path $NestedVictim "SKILL.md") "nested-target"
    New-Item -ItemType SymbolicLink -Path $DefuddlePath -Target $NestedVictim | Out-Null
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
    Remove-Item $TestHome -Recurse -Force -ErrorAction SilentlyContinue
}
