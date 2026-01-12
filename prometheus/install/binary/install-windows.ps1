#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Prometheus Binary Installer for Windows

.DESCRIPTION
    Downloads and installs Prometheus from official releases on Windows.
    Creates a Windows service for automatic startup.

.PARAMETER Version
    Prometheus version to install (default: 2.54.1)

.PARAMETER DataDir
    Data directory path (default: C:\ProgramData\prometheus)

.PARAMETER Config
    Custom prometheus.yml config file path

.PARAMETER InstallDir
    Installation directory (default: C:\Program Files\prometheus)

.EXAMPLE
    .\install-windows.ps1

.EXAMPLE
    .\install-windows.ps1 -Version 2.54.1

.EXAMPLE
    .\install-windows.ps1 -DataDir D:\prometheus\data -Config C:\config\prometheus.yml

.NOTES
    Requirements: 1.4, 1.8, 1.9
    Requires Administrator privileges
#>

[CmdletBinding()]
param(
    [Parameter()]
    [string]$Version = "2.54.1",

    [Parameter()]
    [string]$DataDir = "C:\ProgramData\prometheus",

    [Parameter()]
    [string]$Config,

    [Parameter()]
    [string]$InstallDir = "C:\Program Files\prometheus"
)

# Strict mode
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Constants
$ServiceName = "prometheus"
$ServiceDisplayName = "Prometheus Monitoring System"
$DownloadUrl = "https://github.com/prometheus/prometheus/releases/download"

# Logging functions
function Write-LogInfo {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-LogWarn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-LogError {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Check if running as Administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Detect architecture
function Get-Architecture {
    $arch = [System.Environment]::GetEnvironmentVariable("PROCESSOR_ARCHITECTURE")
    switch ($arch) {
        "AMD64" { return "amd64" }
        "x86" {
            Write-LogError "32-bit Windows is not supported"
            exit 1
        }
        default {
            Write-LogError "Unsupported architecture: $arch"
            exit 1
        }
    }
}

# Download Prometheus
function Get-Prometheus {
    param(
        [string]$Version,
        [string]$TempDir
    )

    $arch = Get-Architecture
    $filename = "prometheus-$Version.windows-$arch.zip"
    $url = "$DownloadUrl/v$Version/$filename"
    $downloadPath = Join-Path $TempDir $filename

    Write-LogInfo "Downloading Prometheus v$Version for windows-$arch..."
    Write-LogInfo "URL: $url"

    try {
        # Use TLS 1.2
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

        # Download with progress
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($url, $downloadPath)

        Write-LogInfo "Download complete"
        return $downloadPath
    }
    catch {
        Write-LogError "Failed to download Prometheus: $_"
        exit 1
    }
}

# Extract archive
function Expand-PrometheusArchive {
    param(
        [string]$ArchivePath,
        [string]$TempDir
    )

    Write-LogInfo "Extracting archive..."

    try {
        Expand-Archive -Path $ArchivePath -DestinationPath $TempDir -Force

        # Find extracted directory
        $extractedDir = Get-ChildItem -Path $TempDir -Directory |
            Where-Object { $_.Name -like "prometheus-*" } |
            Select-Object -First 1

        if (-not $extractedDir) {
            Write-LogError "Could not find extracted Prometheus directory"
            exit 1
        }

        return $extractedDir.FullName
    }
    catch {
        Write-LogError "Failed to extract archive: $_"
        exit 1
    }
}

# Create directories
function New-PrometheusDirectories {
    param(
        [string]$InstallDir,
        [string]$DataDir
    )

    Write-LogInfo "Creating directories..."

    $directories = @(
        $InstallDir,
        $DataDir,
        (Join-Path $InstallDir "consoles"),
        (Join-Path $InstallDir "console_libraries")
    )

    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-LogInfo "Created: $dir"
        }
    }
}

# Install Prometheus files
function Install-PrometheusFiles {
    param(
        [string]$SourceDir,
        [string]$InstallDir
    )

    Write-LogInfo "Installing Prometheus files to $InstallDir..."

    # Copy binaries
    Copy-Item -Path (Join-Path $SourceDir "prometheus.exe") -Destination $InstallDir -Force
    Copy-Item -Path (Join-Path $SourceDir "promtool.exe") -Destination $InstallDir -Force

    # Copy console templates
    $consolesSource = Join-Path $SourceDir "consoles"
    $consolesTarget = Join-Path $InstallDir "consoles"
    if (Test-Path $consolesSource) {
        Copy-Item -Path "$consolesSource\*" -Destination $consolesTarget -Recurse -Force
    }

    # Copy console libraries
    $consoleLibsSource = Join-Path $SourceDir "console_libraries"
    $consoleLibsTarget = Join-Path $InstallDir "console_libraries"
    if (Test-Path $consoleLibsSource) {
        Copy-Item -Path "$consoleLibsSource\*" -Destination $consoleLibsTarget -Recurse -Force
    }

    Write-LogInfo "Files installed successfully"
}

# Create default configuration
function New-PrometheusConfig {
    param(
        [string]$InstallDir,
        [string]$CustomConfig
    )

    $configPath = Join-Path $InstallDir "prometheus.yml"

    if ($CustomConfig -and (Test-Path $CustomConfig)) {
        Write-LogInfo "Using custom configuration from $CustomConfig"
        Copy-Item -Path $CustomConfig -Destination $configPath -Force
        return
    }

    if (Test-Path $configPath) {
        Write-LogWarn "Configuration file already exists at $configPath, skipping..."
        return
    }

    Write-LogInfo "Creating default prometheus.yml configuration..."

    $configContent = @"
# Prometheus configuration file
# Generated by install-windows.ps1

global:
  scrape_interval: 15s
  evaluation_interval: 15s
  # scrape_timeout is set to the global default (10s)

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
          # - alertmanager:9093

# Rule files
rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

# Scrape configurations
scrape_configs:
  # Prometheus self-monitoring
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]
        labels:
          instance: "prometheus-server"

  # Windows Exporter (uncomment when installed)
  # - job_name: "windows"
  #   static_configs:
  #     - targets: ["localhost:9182"]
"@

    Set-Content -Path $configPath -Value $configContent -Encoding UTF8
    Write-LogInfo "Configuration file created at $configPath"
}

# Create Windows service
function New-PrometheusService {
    param(
        [string]$InstallDir,
        [string]$DataDir
    )

    Write-LogInfo "Creating Windows service..."

    $exePath = Join-Path $InstallDir "prometheus.exe"
    $configPath = Join-Path $InstallDir "prometheus.yml"
    $consolesPath = Join-Path $InstallDir "consoles"
    $consoleLibsPath = Join-Path $InstallDir "console_libraries"

    # Build service arguments
    $serviceArgs = @(
        "--config.file=`"$configPath`"",
        "--storage.tsdb.path=`"$DataDir`"",
        "--web.console.templates=`"$consolesPath`"",
        "--web.console.libraries=`"$consoleLibsPath`"",
        "--web.listen-address=0.0.0.0:9090",
        "--web.enable-lifecycle"
    ) -join " "

    # Check if service exists
    $existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue

    if ($existingService) {
        Write-LogInfo "Service already exists, stopping and removing..."
        Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
        & sc.exe delete $ServiceName | Out-Null
        Start-Sleep -Seconds 2
    }

    # Create service using sc.exe
    $binPath = "`"$exePath`" $serviceArgs"

    Write-LogInfo "Creating service with binary path: $binPath"

    $result = & sc.exe create $ServiceName `
        binPath= $binPath `
        DisplayName= $ServiceDisplayName `
        start= auto `
        obj= "LocalSystem"

    if ($LASTEXITCODE -ne 0) {
        Write-LogError "Failed to create service: $result"
        exit 1
    }

    # Set service description
    & sc.exe description $ServiceName "Prometheus monitoring system and time series database" | Out-Null

    # Configure service recovery options (restart on failure)
    & sc.exe failure $ServiceName reset= 86400 actions= restart/5000/restart/10000/restart/30000 | Out-Null

    Write-LogInfo "Windows service created successfully"
}

# Start service
function Start-PrometheusService {
    Write-LogInfo "Starting Prometheus service..."

    try {
        Start-Service -Name $ServiceName
        Start-Sleep -Seconds 3

        $service = Get-Service -Name $ServiceName
        if ($service.Status -eq "Running") {
            Write-LogInfo "Prometheus service started successfully"
        }
        else {
            Write-LogWarn "Service status: $($service.Status)"
        }
    }
    catch {
        Write-LogError "Failed to start service: $_"
        Write-LogWarn "Check Windows Event Viewer for details"
    }
}

# Add firewall rule
function Add-FirewallRule {
    Write-LogInfo "Adding firewall rule for port 9090..."

    $ruleName = "Prometheus"

    # Remove existing rule if present
    $existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
    if ($existingRule) {
        Remove-NetFirewallRule -DisplayName $ruleName
    }

    # Add new rule
    New-NetFirewallRule -DisplayName $ruleName `
        -Direction Inbound `
        -Protocol TCP `
        -LocalPort 9090 `
        -Action Allow `
        -Profile Any `
        -Description "Allow Prometheus monitoring on port 9090" | Out-Null

    Write-LogInfo "Firewall rule added"
}

# Verify installation
function Test-Installation {
    param(
        [string]$InstallDir
    )

    Write-LogInfo "Verifying installation..."

    $exePath = Join-Path $InstallDir "prometheus.exe"
    $configPath = Join-Path $InstallDir "prometheus.yml"
    $promtoolPath = Join-Path $InstallDir "promtool.exe"

    # Check binary version
    try {
        $versionOutput = & $exePath --version 2>&1 | Select-Object -First 1
        Write-LogInfo "Installed: $versionOutput"
    }
    catch {
        Write-LogError "Failed to get version: $_"
    }

    # Check service status
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($service) {
        Write-LogInfo "Service status: $($service.Status)"
    }
    else {
        Write-LogWarn "Service not found"
    }

    # Check if port 9090 is listening
    $listener = Get-NetTCPConnection -LocalPort 9090 -State Listen -ErrorAction SilentlyContinue
    if ($listener) {
        Write-LogInfo "Prometheus is listening on port 9090"
    }
    else {
        Write-LogWarn "Prometheus is not yet listening on port 9090"
    }

    # Validate configuration
    Write-LogInfo "Validating configuration..."
    try {
        $validateResult = & $promtoolPath check config $configPath 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-LogInfo "Configuration is valid"
        }
        else {
            Write-LogError "Configuration validation failed: $validateResult"
        }
    }
    catch {
        Write-LogWarn "Could not validate configuration: $_"
    }
}

# Print post-installation information
function Write-PostInstallInfo {
    param(
        [string]$Version,
        [string]$InstallDir,
        [string]$DataDir
    )

    $configPath = Join-Path $InstallDir "prometheus.yml"

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Prometheus Installation Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Version:        $Version"
    Write-Host "Install dir:    $InstallDir"
    Write-Host "Config file:    $configPath"
    Write-Host "Data directory: $DataDir"
    Write-Host "Service:        $ServiceName"
    Write-Host ""
    Write-Host "Useful commands:" -ForegroundColor Yellow
    Write-Host "  Check status:     Get-Service $ServiceName"
    Write-Host "  View logs:        Get-EventLog -LogName Application -Source $ServiceName"
    Write-Host "  Stop service:     Stop-Service $ServiceName"
    Write-Host "  Start service:    Start-Service $ServiceName"
    Write-Host "  Restart service:  Restart-Service $ServiceName"
    Write-Host ""
    Write-Host "Access Prometheus:" -ForegroundColor Yellow
    Write-Host "  Web UI:           http://localhost:9090"
    Write-Host "  API:              http://localhost:9090/api/v1/"
    Write-Host ""
    Write-Host "Configuration:" -ForegroundColor Yellow
    Write-Host "  Edit config:      notepad `"$configPath`""
    Write-Host "  Validate config:  & `"$InstallDir\promtool.exe`" check config `"$configPath`""
    Write-Host ""
}

# Main installation function
function Install-Prometheus {
    Write-LogInfo "Starting Prometheus installation for Windows..."

    # Check administrator privileges
    if (-not (Test-Administrator)) {
        Write-LogError "This script must be run as Administrator"
        Write-LogInfo "Right-click PowerShell and select 'Run as Administrator'"
        exit 1
    }

    # Create temp directory
    $tempDir = Join-Path $env:TEMP "prometheus-install-$(Get-Random)"
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

    try {
        # Download Prometheus
        $archivePath = Get-Prometheus -Version $Version -TempDir $tempDir

        # Extract archive
        $extractedDir = Expand-PrometheusArchive -ArchivePath $archivePath -TempDir $tempDir

        # Create directories
        New-PrometheusDirectories -InstallDir $InstallDir -DataDir $DataDir

        # Install files
        Install-PrometheusFiles -SourceDir $extractedDir -InstallDir $InstallDir

        # Create configuration
        New-PrometheusConfig -InstallDir $InstallDir -CustomConfig $Config

        # Create Windows service
        New-PrometheusService -InstallDir $InstallDir -DataDir $DataDir

        # Add firewall rule
        Add-FirewallRule

        # Start service
        Start-PrometheusService

        # Verify installation
        Test-Installation -InstallDir $InstallDir

        # Print info
        Write-PostInstallInfo -Version $Version -InstallDir $InstallDir -DataDir $DataDir

        Write-LogInfo "Installation completed successfully!"
    }
    finally {
        # Cleanup temp directory
        if (Test-Path $tempDir) {
            Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

# Run installation
Install-Prometheus
