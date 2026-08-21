param(
    [Parameter(Position = 0)]
    [string]$Mode,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$OpenCodeArgs
)

$ProfileJs = Join-Path $env:USERPROFILE ".config\opencode\tools\profile.js"
if (-not (Test-Path -LiteralPath $ProfileJs -PathType Leaf)) {
    Write-Error "profile.js is not installed at $ProfileJs"
    exit 1
}
$NodeCommand = $env:OPENCODE_NODE
if (-not $NodeCommand -or -not (Test-Path -LiteralPath $NodeCommand -PathType Leaf)) {
    Write-Error "OPENCODE_NODE does not point to the installer-verified Node.js executable"
    exit 1
}

if ($Mode -in @("--status", "--json", "--help", "-h")) {
    & $NodeCommand $ProfileJs $Mode
    exit $LASTEXITCODE
}

if (-not $Mode) {
    Write-Host "Available profiles:"
    Write-Host "  1) work     - Full model and plugins"
    Write-Host "  2) personal - Light model and essential plugins"
    Write-Host "  3) light    - Economy model and minimal context"
    Write-Host "  4) default  - Default config without OPENCODE_CONFIG"
    $Choice = Read-Host "Select profile [1-4]"
    $Mode = switch ($Choice) {
        "1" { "work" }
        "2" { "personal" }
        "3" { "light" }
        "4" { "default" }
        default { Write-Error "Invalid option"; exit 1 }
    }
}

if ($Mode -notin @("work", "personal", "light", "default")) {
    Write-Error "Invalid profile: $Mode"
    exit 2
}

& $NodeCommand $ProfileJs --validate $Mode
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

switch ($Mode) {
    "work" {
        $env:OPENCODE_CONFIG = Join-Path $env:USERPROFILE ".config\opencode\profiles\work\opencode.jsonc"
        $env:OPENCODE_EFFORT_MODE = "max"
    }
    "personal" {
        $env:OPENCODE_CONFIG = Join-Path $env:USERPROFILE ".config\opencode\profiles\personal\opencode.jsonc"
        $env:OPENCODE_EFFORT_MODE = "medium"
    }
    "light" {
        $env:OPENCODE_CONFIG = Join-Path $env:USERPROFILE ".config\opencode\profiles\light\opencode.jsonc"
        $env:OPENCODE_EFFORT_MODE = "low"
    }
    "default" {
        Remove-Item Env:OPENCODE_CONFIG -ErrorAction SilentlyContinue
        Remove-Item Env:OPENCODE_EFFORT_MODE -ErrorAction SilentlyContinue
    }
}

$OpenCodeCommand = @(
    (Join-Path $env:USERPROFILE ".opencode\bin\opencode.exe"),
    (Join-Path $env:USERPROFILE ".opencode\bin\opencode.cmd"),
    (Join-Path $env:USERPROFILE ".opencode\bin\opencode")
) | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
if (-not $OpenCodeCommand) {
    Write-Error "OpenCode was not found in $env:USERPROFILE\.opencode\bin"
    exit 1
}
& $OpenCodeCommand @OpenCodeArgs
exit $LASTEXITCODE
