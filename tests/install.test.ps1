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

    Write-Host "[PASS] PowerShell install, preserve, SDK, and rollback checks passed"
} finally {
    $env:USERPROFILE = $OriginalUserProfile
    $env:LOCALAPPDATA = $OriginalLocalAppData
    Remove-Item $TestHome -Recurse -Force -ErrorAction SilentlyContinue
}
