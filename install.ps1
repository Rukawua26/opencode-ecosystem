# PowerShell Installer for OpenCode Ecosystem
# Usage: Set-Location (git clone https://github.com/Rukawua26/opencode-ecosystem); .\install.ps1

param(
    [switch]$Verbose,
    [switch]$Force,
    [switch]$Sync,
    [switch]$DryRun,
    [switch]$SkipMemory
)

$ErrorActionPreference = "Stop"
if ($Force -and $Sync) { throw "-Force and -Sync cannot be used together" }
$RepoUrl = "https://github.com/Rukawua26/opencode-ecosystem.git"
$InstallTag = if ($env:INSTALL_TAG) { $env:INSTALL_TAG } else { "v1.9.0" }

function Write-Log { param($Message) Write-Host "[opencode-ecosystem] $Message" -ForegroundColor Green }
function Write-Warn { param($Message) Write-Host "[warn] $Message" -ForegroundColor Yellow }
function Write-Info { param($Message) if ($Verbose) { Write-Host "[debug] $Message" -ForegroundColor Blue } }
function Write-Err { param($Message) Write-Host "[error] $Message" -ForegroundColor Red }
function Write-Plan { param($Action, $Target) Write-Host "[dry-run] ${Action}: $Target" }

function Test-Command { param($Cmd) return [bool](Get-Command $Cmd -ErrorAction SilentlyContinue) }

# Check dependencies
Write-Log "Checking dependencies..."
$PreviousNodeDisableCompileCache = $env:NODE_DISABLE_COMPILE_CACHE
if ($DryRun) { $env:NODE_DISABLE_COMPILE_CACHE = "1" }
function Restore-NodeCompileCacheEnvironment {
    if ($null -eq $PreviousNodeDisableCompileCache) {
        Remove-Item Env:NODE_DISABLE_COMPILE_CACHE -ErrorAction SilentlyContinue
    } else {
        $env:NODE_DISABLE_COMPILE_CACHE = $PreviousNodeDisableCompileCache
    }
}
$missing = @()
if (-not (Test-Command "node")) { $missing += "nodejs" }
if (-not (Test-Command "npm")) { $missing += "npm" }
if (-not (Test-Command "git")) { $missing += "git" }

if ($missing.Count -gt 0) {
    Restore-NodeCompileCacheEnvironment
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
Restore-NodeCompileCacheEnvironment

# Set paths
$OpenCodeDir = Join-Path $env:USERPROFILE ".config\opencode"
$OpenCodeBinDir = Join-Path $env:USERPROFILE ".opencode\bin"
$DataDir = Join-Path $env:LOCALAPPDATA "opencode\plugins-data"
$ToolsDir = Join-Path $OpenCodeDir "tools"
$SkillsDir = Join-Path $env:USERPROFILE "opencode-custom\skills"
$ManifestFile = Join-Path $OpenCodeDir ".ecosystem-managed-files"
$CurrentManifest = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
$PreviousManifest = if (Test-Path $ManifestFile) { @(Get-Content $ManifestFile | Where-Object { $_ }) } else { @() }
$SyncBackupDir = $null
$MaxInstallBackups = 10

Write-Log "Creating directories..."
$InstallDirectories = @(
    $OpenCodeDir,
    (Join-Path $OpenCodeDir "plugins"),
    (Join-Path $OpenCodeDir "lib"),
    (Join-Path $OpenCodeDir "mcp"),
    (Join-Path $OpenCodeDir "agents"),
    (Join-Path $OpenCodeDir "profiles"),
    $ToolsDir,
    $OpenCodeBinDir,
    $DataDir
)
foreach ($Directory in $InstallDirectories) {
    if ($DryRun) {
        if (-not (Test-Path -LiteralPath $Directory -PathType Container)) { Write-Plan "create directory" $Directory }
    } else {
        $null = New-Item -ItemType Directory -Force -Path $Directory
    }
}
Write-Info "Directories created at $OpenCodeDir"

# Determine script location
$ScriptDir = if ($MyInvocation.MyCommand.Path) { Split-Path $MyInvocation.MyCommand.Path } else { Get-Location }
if ((Test-Path (Join-Path $ScriptDir "config\opencode.jsonc")) -and (Test-Path (Join-Path $ScriptDir "skills"))) {
    $RepoDir = $ScriptDir
    Write-Info "Using local distribution files"
} else {
    if ($DryRun) {
        Write-Plan "clone $RepoUrl at tag $InstallTag" "distribution sources"
        Write-Plan "defer-verification" "detailed plan requires distribution contents"
        Write-Host ""
        Write-Log "Dry run complete; no changes made."
        return
    }
    $TempDir = [System.IO.Path]::GetTempFileName() | ForEach-Object { [System.IO.Path]::ChangeExtension($_, '') }
    New-Item -ItemType Directory -Force -Path $TempDir | Out-Null
    Write-Log "Cloning repo (tag $InstallTag) to $TempDir..."
    git clone --depth 1 --branch $InstallTag $RepoUrl $TempDir
    $RepoDir = $TempDir
    Write-Info "Repo cloned at tag $InstallTag"
}

function Get-ManagedPath { param($Path)
    $FullPath = [System.IO.Path]::GetFullPath($Path)
    $OpenCodePrefix = [System.IO.Path]::GetFullPath($OpenCodeDir) + [System.IO.Path]::DirectorySeparatorChar
    $SkillsPrefix = [System.IO.Path]::GetFullPath($SkillsDir) + [System.IO.Path]::DirectorySeparatorChar
    $BinPrefix = [System.IO.Path]::GetFullPath($OpenCodeBinDir) + [System.IO.Path]::DirectorySeparatorChar
    if ($FullPath.StartsWith($OpenCodePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        return "opencode/" + $FullPath.Substring($OpenCodePrefix.Length).Replace("\", "/")
    }
    if ($FullPath.StartsWith($SkillsPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        return "skills/" + $FullPath.Substring($SkillsPrefix.Length).Replace("\", "/")
    }
    if ($FullPath.StartsWith($BinPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        return "bin/" + $FullPath.Substring($BinPrefix.Length).Replace("\", "/")
    }
    return $null
}

function Get-ManagedDestination { param($Logical)
    if ($Logical.StartsWith("opencode/")) { return Join-Path $OpenCodeDir $Logical.Substring(9) }
    if ($Logical.StartsWith("skills/")) { return Join-Path $SkillsDir $Logical.Substring(7) }
    if ($Logical.StartsWith("bin/")) { return Join-Path $OpenCodeBinDir $Logical.Substring(4) }
    return $null
}

function Test-SafeManagedPath { param($Logical)
    if ($Logical -notmatch '^(opencode|skills|bin)/') { return $false }
    if ($Logical -match '[:\\]' -or $Logical.Contains('//')) { return $false }
    return -not ($Logical.Split('/') -contains '..')
}

function Test-ProtectedManagedPath { param($Logical)
    return $Logical -in @("opencode/opencode.jsonc", "opencode/.ecosystem-managed-files")
}

function Register-Managed { param($Path)
    $Logical = Get-ManagedPath $Path
    if ($Logical) { [void]$CurrentManifest.Add($Logical) }
}

function Assert-NoReparseComponents { param($Path, $Root)
    $FullPath = [System.IO.Path]::GetFullPath($Path)
    $FullRoot = [System.IO.Path]::GetFullPath($Root)
    $Separator = [System.IO.Path]::DirectorySeparatorChar
    $Prefix = $FullRoot.TrimEnd([char[]]@('\', '/')) + $Separator
    if (-not $FullPath.StartsWith($Prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Managed path is outside its root: $Path"
    }
    $Current = $FullRoot
    $Relative = $FullPath.Substring($Prefix.Length)
    foreach ($Segment in $Relative.Split($Separator, [System.StringSplitOptions]::RemoveEmptyEntries)) {
        $Current = Join-Path $Current $Segment
        $Item = Get-Item -LiteralPath $Current -Force -ErrorAction SilentlyContinue
        if ($Item -and ($Item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
            throw "Refusing managed path with symbolic-link component: $Current"
        }
    }
}

function Assert-ManagedPathSafe { param($Path)
    $Logical = Get-ManagedPath $Path
    if (-not $Logical) { throw "Managed path is outside allowed roots: $Path" }
    if ($Logical.StartsWith("opencode/")) { Assert-NoReparseComponents $Path $OpenCodeDir; return }
    if ($Logical.StartsWith("skills/")) { Assert-NoReparseComponents $Path $SkillsDir; return }
    if ($Logical.StartsWith("bin/")) { Assert-NoReparseComponents $Path $OpenCodeBinDir; return }
    throw "Managed path is outside allowed roots: $Path"
}

function Backup-SyncFile { param($Path)
    if (-not $Sync -or -not (Test-Path -LiteralPath $Path -PathType Leaf)) { return }
    Assert-ManagedPathSafe $Path
    $Logical = Get-ManagedPath $Path
    if (-not $Logical) { return }
    if ($DryRun) { Write-Plan "backup" $Logical; return }
    if (-not $script:SyncBackupDir) {
        $Stamp = "{0}-{1}" -f [DateTimeOffset]::UtcNow.ToUnixTimeSeconds(), $PID
        $script:SyncBackupDir = Join-Path $env:USERPROFILE ".local\share\opencode\install-backups\$Stamp"
        New-Item -ItemType Directory -Force -Path $script:SyncBackupDir | Out-Null
        $BackupRoot = Split-Path $script:SyncBackupDir -Parent
        $OldBackups = @(Get-ChildItem $BackupRoot -Directory -ErrorAction SilentlyContinue | Sort-Object Name -Descending | Select-Object -Skip $MaxInstallBackups)
        foreach ($OldBackup in $OldBackups) { Remove-Item $OldBackup.FullName -Recurse -Force }
    }
    $Backup = Join-Path $script:SyncBackupDir $Logical
    New-Item -ItemType Directory -Force -Path (Split-Path $Backup -Parent) | Out-Null
    Copy-Item -LiteralPath $Path -Destination $Backup -Force
}

function Preserve-ManifestPrefix { param($Prefix)
    foreach ($Logical in $PreviousManifest) {
        if ($Logical.StartsWith($Prefix, [System.StringComparison]::Ordinal)) {
            [void]$CurrentManifest.Add($Logical)
        }
    }
}

# Copy file only if it does not exist, Force is set, or Sync is active.
function Copy-IfOk { param($Src, $Dst, [bool]$Managed = $true)
    if ($Managed) { Register-Managed $Dst }
    if ($Sync) { Assert-ManagedPathSafe $Dst }
    if ((Test-Path $Dst) -and -not $Force -and -not $Sync) {
        if ($DryRun) { Write-Plan "preserve" $Dst } else { Write-Info "Skipping (exists): $Dst" }
        return
    }
    if ($Sync) { Backup-SyncFile $Dst }
    if ($DryRun) {
        if ((Test-Path -LiteralPath $Dst) -or (Get-Item -LiteralPath $Dst -Force -ErrorAction SilentlyContinue)) {
            Write-Plan "update" $Dst
        } else {
            Write-Plan "create" $Dst
        }
        return
    }
    New-Item -ItemType Directory -Force -Path (Split-Path $Dst -Parent) | Out-Null
    Copy-Item $Src $Dst -Force
    Write-Info "Installed: $Dst"
}

# Copy dir with backup on Force
function Copy-DirIfOk { param($SrcDir, $DstDir, $Label)
    $ExistingFiles = @(Get-ChildItem $DstDir -ErrorAction SilentlyContinue)
    if ($Force -and $ExistingFiles.Count -gt 0) {
        if ($DryRun) {
            Write-Plan "backup" "$Label directory $DstDir"
        } else {
            $ts = [int][double]::Parse((Get-Date -UFormat %s))
            $BakDir = "$DstDir.bak-$ts"
            Copy-Item $DstDir $BakDir -Recurse -Force
            Write-Info "$Label backed up to $(Split-Path $BakDir -Leaf)"
        }
    }
    $Files = Get-ChildItem $SrcDir -ErrorAction SilentlyContinue
    foreach ($f in $Files) { Copy-IfOk $f.FullName (Join-Path $DstDir $f.Name) }
}

function Copy-TreeIfOk { param($SrcDir, $DstDir, $Label)
    if ((Test-Path $DstDir) -and -not $Force -and -not $Sync) {
        if ($DryRun) { Write-Plan "preserve" "$Label tree $DstDir" } else { Write-Info "Skipping $Label (exists): $DstDir" }
        return $false
    }
    if ((Test-Path $DstDir) -and $Force) {
        if ($DryRun) {
            Write-Plan "backup" "$Label tree $DstDir"
        } else {
            $ts = [int][double]::Parse((Get-Date -UFormat %s))
            $BakDir = "$DstDir.bak-$ts"
            Copy-Item $DstDir $BakDir -Recurse -Force
            Remove-Item $DstDir -Recurse -Force
            Write-Info "$Label backed up to $(Split-Path $BakDir -Leaf)"
        }
    }
    if ($DryRun) {
        foreach ($File in Get-ChildItem $SrcDir -Recurse -File -ErrorAction SilentlyContinue) {
            $Relative = [System.IO.Path]::GetRelativePath($SrcDir, $File.FullName)
            Copy-IfOk $File.FullName (Join-Path $DstDir $Relative)
        }
        return $true
    }
    New-Item -ItemType Directory -Force -Path $DstDir | Out-Null
    foreach ($File in Get-ChildItem $SrcDir -Recurse -File -ErrorAction SilentlyContinue) {
        $Relative = [System.IO.Path]::GetRelativePath($SrcDir, $File.FullName)
        Copy-IfOk $File.FullName (Join-Path $DstDir $Relative)
    }
    Write-Info "$Label $(if ($Sync) { 'synchronized' } else { 'installed' }): $DstDir"
    return $true
}

# Copy config
Write-Log "Installing config..."

# opencode.jsonc
$ConfigPath = Join-Path $OpenCodeDir "opencode.jsonc"
if ((Test-Path $ConfigPath) -and -not $Force) {
    if ($DryRun) { Write-Plan "preserve" $ConfigPath }
    Write-Warn "opencode.jsonc already exists; preserving it (use -Force to replace)"
} else {
    if ((Test-Path $ConfigPath) -and $Force) {
        if ($DryRun) { Write-Plan "backup" "opencode/opencode.jsonc" } else {
            Copy-Item $ConfigPath "$ConfigPath.bak" -Force
            Write-Info "Backed up opencode.jsonc"
        }
    }
    Copy-IfOk (Join-Path $RepoDir "config\opencode.jsonc") $ConfigPath $false
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
    if ($DryRun) {
        Write-Plan "install-dependencies" (Join-Path $OpenCodeDir "mcp")
    } else {
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
}

# Profiles
Write-Log "Installing profiles..."
$ProfileDirs = Get-ChildItem (Join-Path $RepoDir "config\profiles") -Directory -ErrorAction SilentlyContinue
foreach ($d in $ProfileDirs) {
    $dest = Join-Path $OpenCodeDir "profiles" $d.Name
    if (Copy-TreeIfOk $d.FullName $dest "Profile $($d.Name)") {
        $ProfileConfig = Join-Path $dest "opencode.jsonc"
        if ((Test-Path $ProfileConfig) -and -not $DryRun) {
            (Get-Content $ProfileConfig -Raw).Replace("__OPENCODE_DIR__", $OpenCodeDir.Replace("\", "/")) | Set-Content $ProfileConfig -Encoding UTF8
        } elseif ($DryRun -and (Test-Path (Join-Path $d.FullName "opencode.jsonc"))) {
            Write-Plan "update template" $ProfileConfig
        }
    }
}
Write-Info "Profiles copied: $($ProfileDirs.Count)"

# Skills
Write-Log "Installing skills..."
$SkillDirs = Get-ChildItem (Join-Path $RepoDir "skills") -Directory -ErrorAction SilentlyContinue
foreach ($d in $SkillDirs) {
    $dest = Join-Path $SkillsDir $d.Name
    $null = Copy-TreeIfOk $d.FullName $dest "Skill $($d.Name)"
}

# .env.example
$EnvExample = Join-Path $OpenCodeDir ".env.example"
if (Test-Path (Join-Path $RepoDir ".env.example")) {
    Copy-IfOk (Join-Path $RepoDir ".env.example") $EnvExample
    Write-Info ".env.example copied (configure your API keys manually)"
}

# Global doctor command
$DoctorSource = Join-Path $RepoDir "tools\scripts\doctor.js"
if (Test-Path $DoctorSource) {
    Copy-IfOk $DoctorSource (Join-Path $ToolsDir "doctor.js")
    $DoctorCommand = Join-Path $OpenCodeBinDir "opencode-doctor.cmd"
    Register-Managed $DoctorCommand
    if ($Force -or $Sync -or -not (Test-Path $DoctorCommand)) {
        if ($Sync) { Backup-SyncFile $DoctorCommand }
        if ($DryRun) { Write-Plan $(if (Test-Path $DoctorCommand) { "update" } else { "create" }) $DoctorCommand } else {
            @(
                '@set "NODE_DISABLE_COMPILE_CACHE=1"'
                '@node "%USERPROFILE%\.config\opencode\tools\doctor.js" %*'
            ) | Set-Content $DoctorCommand -Encoding Ascii
        }
    }
    Write-Info "opencode-doctor installed at $OpenCodeBinDir\opencode-doctor.cmd"
}
$MetricsSource = Join-Path $RepoDir "tools\scripts\opencode-metrics.js"
if (Test-Path $MetricsSource) {
    Copy-IfOk $MetricsSource (Join-Path $ToolsDir "opencode-metrics.js")
    $MetricsCommand = Join-Path $OpenCodeBinDir "opencode-metrics.cmd"
    Register-Managed $MetricsCommand
    if ($Force -or $Sync -or -not (Test-Path $MetricsCommand)) {
        if ($Sync) { Backup-SyncFile $MetricsCommand }
        if ($DryRun) { Write-Plan $(if (Test-Path $MetricsCommand) { "update" } else { "create" }) $MetricsCommand } else {
            '@node "%USERPROFILE%\.config\opencode\tools\opencode-metrics.js" %*' | Set-Content $MetricsCommand -Encoding Ascii
        }
    }
    Write-Info "opencode-metrics installed at $OpenCodeBinDir\opencode-metrics.cmd"
}

# Memory adapter
if (-not $SkipMemory) {
    Write-Log "Installing memory adapter..."
    $MemDir = Join-Path $OpenCodeDir "mcp\memory-adapter"
    $null = Copy-TreeIfOk (Join-Path $RepoDir "packages\memory-adapter") $MemDir "Memory adapter"
    $PkgPath = Join-Path $MemDir "package.json"
    if (Test-Path $PkgPath) {
        Write-Info "Memory adapter installed at $MemDir"
    }
    $MemoryCommand = Join-Path $OpenCodeBinDir "memory-adapter.cmd"
    Register-Managed $MemoryCommand
    if ($Force -or $Sync -or -not (Test-Path $MemoryCommand)) {
        if ($Sync) { Backup-SyncFile $MemoryCommand }
        if ($DryRun) { Write-Plan $(if (Test-Path $MemoryCommand) { "update" } else { "create" }) $MemoryCommand } else {
            '@node "%USERPROFILE%\.config\opencode\mcp\memory-adapter\src\cli.js" %*' | Set-Content $MemoryCommand -Encoding Ascii
        }
    }
} else {
    Preserve-ManifestPrefix "opencode/mcp/memory-adapter/"
    Preserve-ManifestPrefix "bin/memory-adapter"
    Write-Warn "Skipping memory adapter (--skip-memory)"
}

function Finalize-Manifest {
    if ($Sync -and (Test-Path $ManifestFile)) {
        foreach ($Logical in $PreviousManifest) {
            if (-not (Test-SafeManagedPath $Logical)) {
                Write-Warn "Ignoring unsafe managed path in manifest: $Logical"
                continue
            }
            if (Test-ProtectedManagedPath $Logical) {
                Write-Warn "Ignoring protected path in manifest: $Logical"
                continue
            }
            if ($CurrentManifest.Contains($Logical)) { continue }
            $Destination = Get-ManagedDestination $Logical
            if ($Destination -and (Test-Path -LiteralPath $Destination -PathType Leaf)) {
                Assert-ManagedPathSafe $Destination
                Backup-SyncFile $Destination
                if ($DryRun) { Write-Plan "remove" $Logical } else {
                    Remove-Item -LiteralPath $Destination -Force
                    Write-Info "Removed stale managed file: $Logical"
                }
            }
        }
    }
    if (-not $Sync -and -not $Force -and (Test-Path $ManifestFile)) {
        foreach ($Logical in $PreviousManifest) {
            if ((Test-SafeManagedPath $Logical) -and -not (Test-ProtectedManagedPath $Logical)) {
                [void]$CurrentManifest.Add($Logical)
            }
        }
    }
    if ($DryRun) { Write-Plan "update manifest" $ManifestFile; return }
    $NextManifest = "$ManifestFile.next"
    @($CurrentManifest | Sort-Object) | Set-Content $NextManifest -Encoding utf8
    Move-Item $NextManifest $ManifestFile -Force
    Write-Info "Managed manifest updated: $ManifestFile"
}

# Verify installation
if ($DryRun) {
    Write-Plan "defer-verification" "runtime installation checks"
    Finalize-Manifest
    Write-Host ""
    Write-Log "Dry run complete; no changes made."
    return
}

Write-Log "Verifying installation..."

$checks = 0; $passed = 0
function Assert-Path($Path, $Desc) {
    $script:checks++
    if (Test-Path $Path) { $script:passed++; Write-Host "[OK] $Desc" -ForegroundColor Green }
    else { Write-Warn "[MISSING] ${Desc}: $Path" }
}

Assert-Path $ConfigPath "opencode.jsonc"
Assert-Path (Join-Path $OpenCodeDir "agents") "agents dir"
Assert-Path (Join-Path $OpenCodeDir "plugins") "plugins dir"
Assert-Path (Join-Path $OpenCodeDir "mcp") "mcp dir"
Assert-Path (Join-Path $OpenCodeDir "profiles") "profiles dir"
Assert-Path $SkillsDir "skills dir"
Assert-Path $EnvExample ".env.example"
Assert-Path (Join-Path $ToolsDir "doctor.js") "doctor.js"
Assert-Path (Join-Path $OpenCodeBinDir "opencode-doctor.cmd") "opencode-doctor command"
Assert-Path (Join-Path $OpenCodeDir "lib\session-metrics.js") "session-metrics library"
Assert-Path (Join-Path $OpenCodeBinDir "opencode-metrics.cmd") "opencode-metrics command"
if (-not $SkipMemory) { Assert-Path (Join-Path $OpenCodeBinDir "memory-adapter.cmd") "memory-adapter command" }

$agentCount = (Get-ChildItem (Join-Path $OpenCodeDir "agents") -Filter "*.md" -ErrorAction SilentlyContinue).Count
$pluginCount = (Get-ChildItem (Join-Path $OpenCodeDir "plugins") -Filter "*.js" -ErrorAction SilentlyContinue | Where-Object { $_.Name -notlike "*-helpers.js" }).Count
$skillCount = (Get-ChildItem $SkillsDir -Directory -ErrorAction SilentlyContinue | Measure-Object).Count
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

Finalize-Manifest

Write-Host ""
Write-Log "Installation successful!"
Write-Log "Next steps:"
Write-Host "  1. Copy: Copy-Item $EnvExample (Join-Path $OpenCodeDir '.env')"
Write-Host "  2. Edit: $env:USERPROFILE\.config\opencode\.env with your API keys"
Write-Host "  3. Run: opencode"

Write-Host ""
Write-Log "Done. Happy coding!"
