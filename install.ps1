# PowerShell Installer for OpenCode Ecosystem
# Usage: Set-Location (git clone https://github.com/Rukawua26/opencode-ecosystem); .\install.ps1

param(
    [switch]$Verbose,
    [switch]$Force,
    [switch]$SkipMemory
)

$ErrorActionPreference = "Stop"
$RepoUrl = "https://github.com/Rukawua26/opencode-ecosystem.git"
$InstallTag = if ($env:INSTALL_TAG) { $env:INSTALL_TAG } else { "v1.8.0" }

function Write-Log { param($Message) Write-Host "[opencode-ecosystem] $Message" -ForegroundColor Green }
function Write-Warn { param($Message) Write-Host "[warn] $Message" -ForegroundColor Yellow }
function Write-Info { param($Message) if ($Verbose) { Write-Host "[debug] $Message" -ForegroundColor Blue } }
function Write-Err { param($Message) Write-Host "[error] $Message" -ForegroundColor Red }

function Test-Command { param($Cmd) return [bool](Get-Command $Cmd -ErrorAction SilentlyContinue) }

# Check dependencies
Write-Log "Checking dependencies..."
$missing = @()
if (-not (Test-Command "node")) { $missing += "nodejs" }
if (-not (Test-Command "git")) { $missing += "git" }

if ($missing.Count -gt 0) {
    Write-Err "Missing dependencies: $($missing -join ', ')"
    Write-Err "Install with: winget install $($missing -join ' ') or choco install $($missing -join ' ')"
    exit 1
}
$NodeMajor = [int]((node --version).TrimStart('v').Split('.')[0])
if ($NodeMajor -lt 22) {
    Write-Err "Node.js 22 or newer is required for the native node:sqlite module"
    exit 1
}
Write-Info "Dependencies OK: node=$(node --version), git=$(git --version)"

# Set paths
$OpenCodeDir = Join-Path $env:USERPROFILE ".config\opencode"
$OpenCodeBinDir = Join-Path $env:USERPROFILE ".opencode\bin"
$DataDir = Join-Path $env:LOCALAPPDATA "opencode\plugins-data"
$ToolsDir = Join-Path $OpenCodeDir "tools"

Write-Log "Creating directories..."
$null = New-Item -ItemType Directory -Force -Path $OpenCodeDir, "$OpenCodeDir\plugins", "$OpenCodeDir\lib", "$OpenCodeDir\mcp", "$OpenCodeDir\agents", "$OpenCodeDir\profiles", $ToolsDir, $OpenCodeBinDir, $DataDir
Write-Info "Directories created at $OpenCodeDir"

# Determine script location
$ScriptDir = if ($MyInvocation.MyCommand.Path) { Split-Path $MyInvocation.MyCommand.Path } else { Get-Location }
if ((Test-Path (Join-Path $ScriptDir "config\opencode.jsonc")) -and (Test-Path (Join-Path $ScriptDir "skills"))) {
    $RepoDir = $ScriptDir
    Write-Info "Using local distribution files"
} else {
    $TempDir = [System.IO.Path]::GetTempFileName() | ForEach-Object { [System.IO.Path]::ChangeExtension($_, '') }
    New-Item -ItemType Directory -Force -Path $TempDir | Out-Null
    Write-Log "Cloning repo (tag $InstallTag) to $TempDir..."
    git clone --depth 1 --branch $InstallTag $RepoUrl $TempDir
    $RepoDir = $TempDir
    Write-Info "Repo cloned at tag $InstallTag"
}

# Copy file only if it does not exist or Force is set
function Copy-IfOk { param($Src, $Dst)
    if ((Test-Path $Dst) -and -not $Force) {
        Write-Info "Skipping (exists): $Dst"
        return
    }
    Copy-Item $Src $Dst -Force
    Write-Info "Installed: $Dst"
}

# Copy dir with backup on Force
function Copy-DirIfOk { param($SrcDir, $DstDir, $Label)
    if ($Force -and (Test-Path $DstDir)) {
        $ts = [int][double]::Parse((Get-Date -UFormat %s))
        $BakDir = "$DstDir.bak-$ts"
        Copy-Item $DstDir $BakDir -Recurse -Force -ErrorAction SilentlyContinue
        Write-Info "$Label backed up to $(Split-Path $BakDir -Leaf)"
    }
    $Files = Get-ChildItem $SrcDir -ErrorAction SilentlyContinue
    foreach ($f in $Files) { Copy-IfOk $f.FullName (Join-Path $DstDir $f.Name) }
}

# Copy config
Write-Log "Installing config..."

# opencode.jsonc
$ConfigPath = Join-Path $OpenCodeDir "opencode.jsonc"
if ((Test-Path $ConfigPath) -and -not $Force) {
    Write-Warn "opencode.jsonc already exists; preserving it (use -Force to replace)"
} else {
    if ((Test-Path $ConfigPath) -and $Force) {
        Copy-Item $ConfigPath "$ConfigPath.bak" -Force
        Write-Info "Backed up opencode.jsonc"
    }
    Copy-Item (Join-Path $RepoDir "config\opencode.jsonc") $ConfigPath -Force
    Write-Info "opencode.jsonc installed"
}

# Agents
Write-Log "Installing agents..."
if (Test-Path (Join-Path $RepoDir "config\agents")) {
    Copy-DirIfOk (Join-Path $RepoDir "config\agents") (Join-Path $OpenCodeDir "agents") "Agents"
    Write-Info "Agents copied"
}

# Plugins
Write-Log "Installing plugins..."
if (Test-Path (Join-Path $RepoDir "config\plugins")) {
    Copy-DirIfOk (Join-Path $RepoDir "config\plugins") (Join-Path $OpenCodeDir "plugins") "Plugins"
    Write-Info "Plugins copied"
}

if (Test-Path (Join-Path $RepoDir "config\lib")) {
    Copy-DirIfOk (Join-Path $RepoDir "config\lib") (Join-Path $OpenCodeDir "lib") "Plugin libraries"
    Write-Info "Plugin libraries copied"
}

# MCP servers
Write-Log "Installing MCP servers..."
if (Test-Path (Join-Path $RepoDir "config\mcp")) {
    $McpFiles = Get-ChildItem (Join-Path $RepoDir "config\mcp") -Filter "*.js" -ErrorAction SilentlyContinue
    foreach ($f in $McpFiles) { Copy-IfOk $f.FullName (Join-Path $OpenCodeDir "mcp" $f.Name) }
    Write-Info "MCP servers copied: $($McpFiles.Count)"
}

# MCP router package.json and lockfile
$McpPkg = Join-Path $RepoDir "config\mcp\package.json"
$McpLock = Join-Path $RepoDir "config\mcp\package-lock.json"
if (Test-Path $McpPkg) {
    Copy-IfOk $McpPkg (Join-Path $OpenCodeDir "mcp\package.json")
    if (Test-Path $McpLock) { Copy-IfOk $McpLock (Join-Path $OpenCodeDir "mcp\package-lock.json") }
    Write-Info "Installing MCP router dependencies..."
    Push-Location (Join-Path $OpenCodeDir "mcp")
    npm ci --omit=dev --ignore-scripts
    if ($LASTEXITCODE -ne 0) {
        Pop-Location
        Write-Err "Failed to install MCP router dependencies"
        Write-Err "Run 'npm ci --omit=dev --ignore-scripts' manually in $(Join-Path $OpenCodeDir 'mcp')"
        exit 1
    }
    Pop-Location
    Write-Info "MCP router dependencies installed"
}

# Profiles
Write-Log "Installing profiles..."
$ProfileDirs = Get-ChildItem (Join-Path $RepoDir "config\profiles") -Directory -ErrorAction SilentlyContinue
foreach ($d in $ProfileDirs) {
    $dest = Join-Path $OpenCodeDir "profiles" $d.Name
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Copy-Item (Join-Path $d.FullName "*") $dest -Recurse -Force
    $ProfileConfig = Join-Path $dest "opencode.jsonc"
    if (Test-Path $ProfileConfig) {
        (Get-Content $ProfileConfig -Raw).Replace("__OPENCODE_DIR__", $OpenCodeDir.Replace("\", "/")) | Set-Content $ProfileConfig -Encoding UTF8
    }
}
Write-Info "Profiles copied: $($ProfileDirs.Count)"

# Skills
Write-Log "Installing skills..."
$SkillsDir = Join-Path $env:USERPROFILE "opencode-custom\skills"
$SkillDirs = Get-ChildItem (Join-Path $RepoDir "skills") -Directory -ErrorAction SilentlyContinue
foreach ($d in $SkillDirs) {
    $dest = Join-Path $SkillsDir $d.Name
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Copy-Item (Join-Path $d.FullName "*") $dest -Recurse -Force
    Write-Info "Skill installed: $($d.Name)"
}

# .env.example
$EnvExample = Join-Path $OpenCodeDir ".env.example"
if (Test-Path (Join-Path $RepoDir ".env.example")) {
    Copy-Item (Join-Path $RepoDir ".env.example") $EnvExample -Force
    Write-Info ".env.example copied (configure your API keys manually)"
}

# Global doctor command
$DoctorSource = Join-Path $RepoDir "tools\scripts\doctor.js"
if (Test-Path $DoctorSource) {
    Copy-Item $DoctorSource (Join-Path $ToolsDir "doctor.js") -Force
    '@node "%USERPROFILE%\.config\opencode\tools\doctor.js" %*' | Set-Content (Join-Path $OpenCodeBinDir "opencode-doctor.cmd") -Encoding Ascii
    Write-Info "opencode-doctor installed at $OpenCodeBinDir\opencode-doctor.cmd"
}
$MetricsSource = Join-Path $RepoDir "tools\scripts\opencode-metrics.js"
if (Test-Path $MetricsSource) {
    Copy-Item $MetricsSource (Join-Path $ToolsDir "opencode-metrics.js") -Force
    '@node "%USERPROFILE%\.config\opencode\tools\opencode-metrics.js" %*' | Set-Content (Join-Path $OpenCodeBinDir "opencode-metrics.cmd") -Encoding Ascii
    Write-Info "opencode-metrics installed at $OpenCodeBinDir\opencode-metrics.cmd"
}

# Memory adapter
if (-not $SkipMemory) {
    Write-Log "Installing memory adapter..."
    $MemDir = Join-Path $OpenCodeDir "mcp\memory-adapter"
    New-Item -ItemType Directory -Force -Path $MemDir | Out-Null
    Copy-Item (Join-Path $RepoDir "packages\memory-adapter\*") $MemDir -Recurse -Force
    $PkgPath = Join-Path $MemDir "package.json"
    if (Test-Path $PkgPath) {
        Write-Info "Installing memory adapter dependencies..."
        Push-Location $MemDir
        npm install --production 2>$null
        Pop-Location
        Write-Info "Memory adapter installed at $MemDir"
    }
    '@node "%USERPROFILE%\.config\opencode\mcp\memory-adapter\src\cli.js" %*' | Set-Content (Join-Path $OpenCodeBinDir "memory-adapter.cmd") -Encoding Ascii
} else {
    Write-Warn "Skipping memory adapter (--skip-memory)"
}

# Verify installation
Write-Log "Verifying installation..."

$checks = 0; $passed = 0
function Assert-Path($Path, $Desc) {
    $script:checks++
    if (Test-Path $Path) { $script:passed++; Write-Host "[OK] $Desc" -ForegroundColor Green }
    else { Write-Warn "[MISSING] $Desc: $Path" }
}

Assert-Path $ConfigPath "opencode.jsonc"
Assert-Path (Join-Path $OpenCodeDir "agents") "agents dir"
Assert-Path (Join-Path $OpenCodeDir "plugins") "plugins dir"
Assert-Path (Join-Path $OpenCodeDir "mcp") "mcp dir"
Assert-Path (Join-Path $OpenCodeDir "profiles") "profiles dir"
Assert-Path (Join-Path $SkillsDir) "skills dir"
Assert-Path $EnvExample ".env.example"
Assert-Path (Join-Path $ToolsDir "doctor.js") "doctor.js"
Assert-Path (Join-Path $OpenCodeBinDir "opencode-doctor.cmd") "opencode-doctor command"
Assert-Path (Join-Path $OpenCodeDir "lib\session-metrics.js") "session-metrics library"
Assert-Path (Join-Path $OpenCodeBinDir "opencode-metrics.cmd") "opencode-metrics command"
if (-not $SkipMemory) { Assert-Path (Join-Path $OpenCodeBinDir "memory-adapter.cmd") "memory-adapter command" }

$agentCount = (Get-ChildItem (Join-Path $OpenCodeDir "agents") -Filter "*.md" -ErrorAction SilentlyContinue).Count
$pluginCount = (Get-ChildItem (Join-Path $OpenCodeDir "plugins") -Filter "*.js" -ErrorAction SilentlyContinue).Count
$skillCount = (Get-ChildItem (Join-Path $SkillsDir) -Directory -ErrorAction SilentlyContinue | Measure-Object).Count
$skillCount = if ($skillCount -gt 0) { $skillCount } else { 0 }

Write-Host ""
Write-Log "Installation summary:"
Write-Host "  Agents:  $agentCount"
Write-Host "  Plugins: $pluginCount"
Write-Host "  Skills:  $skillCount"
Write-Host "  Checks:  $passed/$checks"

if ($passed -ne $checks) {
    Write-Err "Some checks failed. Review the warnings above."
    exit 1
}

Write-Host ""
Write-Log "Installation successful!"
Write-Log "Next steps:"
Write-Host "  1. Copy: Copy-Item $EnvExample (Join-Path $OpenCodeDir '.env')"
Write-Host "  2. Edit: $env:USERPROFILE\.config\opencode\.env with your API keys"
Write-Host "  3. Run: opencode"

Write-Host ""
Write-Log "Done. Happy coding!"
