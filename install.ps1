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
$InstallTag = if ($env:INSTALL_TAG) { $env:INSTALL_TAG } else { "v1.10.0" }

function Write-Log { param($Message) Write-Host "[opencode-ecosystem] $Message" -ForegroundColor Green }
function Write-Warn { param($Message) Write-Host "[warn] $Message" -ForegroundColor Yellow }
function Write-Info { param($Message) if ($Verbose) { Write-Host "[debug] $Message" -ForegroundColor Blue } }
function Write-Err { param($Message) Write-Host "[error] $Message" -ForegroundColor Red }
function Write-Plan { param($Action, $Target) Write-Host "[dry-run] ${Action}: $Target" }

function Resolve-TrustedCommand { param($Command)
    $CurrentDirectory = [System.IO.Path]::GetFullPath((Get-Location).Path)
    $IsWindowsPlatform = [Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT
    $Extensions = if ($IsWindowsPlatform -and -not [System.IO.Path]::HasExtension($Command)) {
        if ($env:PATHEXT) { @($env:PATHEXT -split ';' | Where-Object { $_ }) } else { @('.COM', '.EXE', '.BAT', '.CMD') }
    } else { @('') }
    foreach ($Entry in ($env:PATH -split [System.IO.Path]::PathSeparator)) {
        $Directory = $Entry.Trim('"')
        if (-not $Directory) { continue }
        try { $FullDirectory = [System.IO.Path]::GetFullPath($Directory) } catch { continue }
        if ($FullDirectory -eq $CurrentDirectory) { continue }
        foreach ($Extension in $Extensions) {
            $Candidate = Join-Path $FullDirectory ($Command + $Extension.ToLowerInvariant())
            $Item = Get-Item -LiteralPath $Candidate -Force -ErrorAction SilentlyContinue
            $SafeItem = $Item -and -not $Item.PSIsContainer -and (-not $IsWindowsPlatform -or -not ($Item.Attributes -band [System.IO.FileAttributes]::ReparsePoint))
            if ($SafeItem) {
                if ($Item.FullName -match '[%\r\n]') { throw "Unsafe command path: $($Item.FullName)" }
                return $Item.FullName
            }
        }
    }
    return $null
}

function Assert-NoReparseBelowHome { param($Path)
    $FullPath = [System.IO.Path]::GetFullPath($Path)
    $FullRoot = [System.IO.Path]::GetFullPath($env:USERPROFILE)
    $Separator = [System.IO.Path]::DirectorySeparatorChar
    $Prefix = $FullRoot.TrimEnd([char[]]@('\', '/')) + $Separator
    if (-not $FullPath.StartsWith($Prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Managed path is outside USERPROFILE: $Path"
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
$NodeCommand = Resolve-TrustedCommand "node"
$NpmCommand = Resolve-TrustedCommand "npm"
$GitCommand = Resolve-TrustedCommand "git"
if (-not $NodeCommand) { $missing += "nodejs" }
if (-not $NpmCommand) { $missing += "npm" }
if (-not $GitCommand) { $missing += "git" }

if ($missing.Count -gt 0) {
    Restore-NodeCompileCacheEnvironment
    Write-Err "Missing dependencies: $($missing -join ', ')"
    Write-Err "Install with: winget install $($missing -join ' ') or choco install $($missing -join ' ')"
    exit 1
}
$NodeMajor = [int]((& $NodeCommand --version).TrimStart('v').Split('.')[0])
if ($NodeMajor -lt 22) {
    Write-Err "Node.js 22 or newer is required for the native node:sqlite module"
    exit 1
}
Write-Info "Dependencies OK: node=$(& $NodeCommand --version), git=$(& $GitCommand --version)"
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
    (Join-Path $OpenCodeDir "plugins.disabled"),
    (Join-Path $OpenCodeDir "lib"),
    (Join-Path $OpenCodeDir "commands"),
    (Join-Path $OpenCodeDir "mcp"),
    (Join-Path $OpenCodeDir "agents"),
    (Join-Path $OpenCodeDir "profiles"),
    $ToolsDir,
    $OpenCodeBinDir,
    $DataDir
)
foreach ($Directory in $InstallDirectories) {
    $FullDirectory = [System.IO.Path]::GetFullPath($Directory)
    $HomePrefix = [System.IO.Path]::GetFullPath($env:USERPROFILE).TrimEnd([char[]]@('\', '/')) + [System.IO.Path]::DirectorySeparatorChar
    if ($FullDirectory.StartsWith($HomePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        Assert-NoReparseBelowHome $Directory
    }
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
    & $GitCommand clone --depth 1 --branch $InstallTag $RepoUrl $TempDir
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

function Assert-ManagedPathSafe { param($Path)
    $Logical = Get-ManagedPath $Path
    if (-not $Logical) { throw "Managed path is outside allowed roots: $Path" }
    if ($Logical.StartsWith("opencode/") -or $Logical.StartsWith("skills/") -or $Logical.StartsWith("bin/")) {
        Assert-NoReparseBelowHome $Path
        return
    }
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
    if ($Force -or $Sync -or -not (Test-Path -LiteralPath $Dst -PathType Leaf)) { Assert-ManagedPathSafe $Dst }
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
        Assert-ManagedPathSafe $DstDir
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
        Assert-ManagedPathSafe $DstDir
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
        Assert-ManagedPathSafe $ConfigPath
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
if (Test-Path (Join-Path $RepoDir "config\plugins.disabled")) {
    Copy-DirIfOk (Join-Path $RepoDir "config\plugins.disabled") (Join-Path $OpenCodeDir "plugins.disabled") "Optional plugins (disabled)"
    Write-Info "Optional plugins stored disabled"
}

if (Test-Path (Join-Path $RepoDir "config\lib")) {
    Copy-DirIfOk (Join-Path $RepoDir "config\lib") (Join-Path $OpenCodeDir "lib") "Plugin libraries"
    Write-Info "Plugin libraries copied"
}

# Commands
if (Test-Path (Join-Path $RepoDir "config\commands")) {
    Copy-DirIfOk (Join-Path $RepoDir "config\commands") (Join-Path $OpenCodeDir "commands") "Commands"
    Write-Info "Commands copied"
}

# Plugin runtime dependencies (@opencode-ai/plugin)
$ConfigPkg = Join-Path $RepoDir "config\package.json"
$ConfigLock = Join-Path $RepoDir "config\package-lock.json"
if ((Test-Path $ConfigPkg) -and (Test-Path $ConfigLock)) {
    $UserManifest = $false
    $ExistingPkg = Join-Path $OpenCodeDir "package.json"
    if (Test-Path $ExistingPkg) {
        $ExistingPkgContent = Get-Content -LiteralPath $ExistingPkg -Raw
        if ($ExistingPkgContent -notmatch '"opencode-config-runtime"') { $UserManifest = $true }
    }
    if ($UserManifest) {
        # Never npm ci over a user-owned manifest: it would delete their deps.
        if ($DryRun) {
            Write-Plan "install @opencode-ai/plugin --no-save" "user-owned manifest"
        } else {
            Push-Location $OpenCodeDir
            & $NpmCommand install --no-save --ignore-scripts "@opencode-ai/plugin@1.18.14"
            if ($LASTEXITCODE -ne 0) {
                Pop-Location
                Write-Err "Failed to install plugin runtime dependency into user manifest"
                exit 1
            }
            Pop-Location
            Write-Info "Plugin runtime dependency installed alongside user manifest"
        }
    } else {
        Copy-IfOk $ConfigPkg (Join-Path $OpenCodeDir "package.json")
        Copy-IfOk $ConfigLock (Join-Path $OpenCodeDir "package-lock.json")
        if ($DryRun) {
            Write-Plan "install-dependencies" "$OpenCodeDir (plugin runtime)"
        } else {
            Push-Location $OpenCodeDir
            & $NpmCommand ci --omit=dev --ignore-scripts
            if ($LASTEXITCODE -ne 0) {
                Pop-Location
                Write-Err "Failed to install plugin runtime dependencies in $OpenCodeDir"
                exit 1
            }
            Pop-Location
            Write-Info "Plugin runtime dependencies installed"
        }
    }
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
        & $NpmCommand ci --omit=dev --ignore-scripts
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
$SddCommon = Join-Path $RepoDir "skills\sdd-phase-common.md"
if (Test-Path $SddCommon) {
    Copy-IfOk $SddCommon (Join-Path $SkillsDir "sdd-phase-common.md")
}

# .env.example
$EnvExample = Join-Path $OpenCodeDir ".env.example"
if (Test-Path (Join-Path $RepoDir ".env.example")) {
    Copy-IfOk (Join-Path $RepoDir ".env.example") $EnvExample
    Write-Info ".env.example copied (configure your API keys manually)"
}

# Shared config inspector
$ConfigInspectorSource = Join-Path $RepoDir "tools\scripts\config-inspect.js"
if (Test-Path $ConfigInspectorSource) {
    Copy-IfOk $ConfigInspectorSource (Join-Path $ToolsDir "config-inspect.js")
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
                "@`"$NodeCommand`" `"%USERPROFILE%\.config\opencode\tools\doctor.js`" %*"
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
            "@`"$NodeCommand`" `"%USERPROFILE%\.config\opencode\tools\opencode-metrics.js`" %*" | Set-Content $MetricsCommand -Encoding Ascii
        }
    }
    Write-Info "opencode-metrics installed at $OpenCodeBinDir\opencode-metrics.cmd"
}

# OpenCode profile launchers
$ProfileSource = Join-Path $RepoDir "tools\scripts\profile.js"
$ProfilePowerShellSource = Join-Path $RepoDir "tools\scripts\opencode-profile.ps1"
if ((Test-Path $ProfileSource) -and (Test-Path $ProfilePowerShellSource)) {
    Copy-IfOk $ProfileSource (Join-Path $ToolsDir "profile.js")
    Copy-IfOk $ProfilePowerShellSource (Join-Path $ToolsDir "opencode-profile.ps1")
    $PowerShellCommand = (Get-Process -Id $PID).Path
    if (-not $PowerShellCommand -or $PowerShellCommand -match '[%\r\n]') { throw "Cannot resolve a safe PowerShell path" }
    $ProfileCommands = @{
        "opencode-profile.cmd" = @(
            '@set "OPENCODE_NODE=' + $NodeCommand + '"'
            "@`"$PowerShellCommand`" -NoProfile -ExecutionPolicy Bypass -File `"%USERPROFILE%\.config\opencode\tools\opencode-profile.ps1`" %*"
        )
        "opencode-work.cmd" = @(
            '@set "OPENCODE_NODE=' + $NodeCommand + '"'
            "@`"$PowerShellCommand`" -NoProfile -ExecutionPolicy Bypass -File `"%USERPROFILE%\.config\opencode\tools\opencode-profile.ps1`" work %*"
        )
        "opencode-personal.cmd" = @(
            '@set "OPENCODE_NODE=' + $NodeCommand + '"'
            "@`"$PowerShellCommand`" -NoProfile -ExecutionPolicy Bypass -File `"%USERPROFILE%\.config\opencode\tools\opencode-profile.ps1`" personal %*"
        )
        "opencode-light.cmd" = @(
            '@set "OPENCODE_NODE=' + $NodeCommand + '"'
            "@`"$PowerShellCommand`" -NoProfile -ExecutionPolicy Bypass -File `"%USERPROFILE%\.config\opencode\tools\opencode-profile.ps1`" light %*"
        )
    }
    foreach ($Name in $ProfileCommands.Keys) {
        $Command = Join-Path $OpenCodeBinDir $Name
        Register-Managed $Command
        if ($Force -or $Sync -or -not (Test-Path $Command)) {
            if ($Sync) { Backup-SyncFile $Command }
            if ($DryRun) { Write-Plan $(if (Test-Path $Command) { "update" } else { "create" }) $Command } else {
                $ProfileCommands[$Name] | Set-Content $Command -Encoding Ascii
            }
        }
    }
    Write-Info "OpenCode profile launchers installed at $OpenCodeBinDir"
}

# Skill registry
$SkillsSource = Join-Path $RepoDir "tools\scripts\skills.js"
if (Test-Path $SkillsSource) {
    Copy-IfOk $SkillsSource (Join-Path $ToolsDir "skills.js")
    $SkillsCommand = Join-Path $OpenCodeBinDir "opencode-skills.cmd"
    Register-Managed $SkillsCommand
    if ($Force -or $Sync -or -not (Test-Path $SkillsCommand)) {
        if ($Sync) { Backup-SyncFile $SkillsCommand }
        if ($DryRun) { Write-Plan $(if (Test-Path $SkillsCommand) { "update" } else { "create" }) $SkillsCommand } else {
            @(
                '@set "NODE_DISABLE_COMPILE_CACHE=1"'
                "@`"$NodeCommand`" `"%USERPROFILE%\.config\opencode\tools\skills.js`" %*"
            ) | Set-Content $SkillsCommand -Encoding Ascii
        }
    }
    Write-Info "opencode-skills installed at $OpenCodeBinDir\opencode-skills.cmd"
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
            "@`"$NodeCommand`" `"%USERPROFILE%\.config\opencode\mcp\memory-adapter\src\cli.js`" %*" | Set-Content $MemoryCommand -Encoding Ascii
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
Assert-Path (Join-Path $ToolsDir "profile.js") "profile inspector"
Assert-Path (Join-Path $OpenCodeBinDir "opencode-profile.cmd") "opencode-profile command"
Assert-Path (Join-Path $OpenCodeBinDir "opencode-light.cmd") "opencode-light command"
Assert-Path (Join-Path $ToolsDir "skills.js") "skill registry"
Assert-Path (Join-Path $OpenCodeBinDir "opencode-skills.cmd") "opencode-skills command"
Assert-Path (Join-Path $OpenCodeDir "plugins\organic-rdd.js") "organic-rdd plugin"
Assert-Path (Join-Path $OpenCodeDir "lib\organic-rdd.js") "organic-rdd library"
Assert-Path (Join-Path $OpenCodeDir "commands\review-start.md") "review commands"
Assert-Path (Join-Path $OpenCodeDir "node_modules\@opencode-ai\plugin\package.json") "plugin runtime dependency"
if (-not $SkipMemory) { Assert-Path (Join-Path $OpenCodeBinDir "memory-adapter.cmd") "memory-adapter command" }

# Verify Organic RDD plugin actually loads with its runtime dependency
if (Test-Path (Join-Path $OpenCodeDir "node_modules\@opencode-ai\plugin\package.json")) {
    $checks++
    $RddImport = 'const { pathToFileURL } = await import("node:url"); const m = await import(pathToFileURL(process.argv[1]).href); const p = await m.default(); process.exit(p.tool && p.tool.review_gate ? 0 : 1);'
    & node --input-type=module -e $RddImport (Join-Path $OpenCodeDir "plugins\organic-rdd.js") 2>$null
    if ($LASTEXITCODE -eq 0) { $passed++; Write-Host "[OK] Organic RDD plugin import" -ForegroundColor Green }
    else { Write-Warn "[FAIL] Organic RDD plugin import" }
}

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
