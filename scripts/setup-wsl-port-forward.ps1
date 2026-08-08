#Requires -RunAsAdministrator

[CmdletBinding()]
param(
    [ValidateRange(1, 65535)]
    [int]$Port = 8000,

    [string]$Distro = "",

    [System.Net.IPAddress]$ListenAddress = "0.0.0.0",

    [switch]$Remove
)

$ErrorActionPreference = "Stop"
$ruleName = "EffortList-WSL-TCP-$Port"
$listenIp = $ListenAddress.ToString()

if ($Remove) {
    $null = & netsh.exe interface portproxy delete v4tov4 `
        listenaddress=$listenIp listenport=$Port 2>&1

    $existingRule = Get-NetFirewallRule -Name $ruleName -ErrorAction SilentlyContinue
    if ($existingRule) {
        $existingRule | Remove-NetFirewallRule
    }

    Write-Host "Removed the Windows port proxy and firewall rule for TCP port $Port."
    return
}

if ($Distro) {
    $wslAddresses = & wsl.exe --distribution $Distro hostname -I
} else {
    $wslAddresses = & wsl.exe hostname -I
}

if ($LASTEXITCODE -ne 0) {
    throw "Could not query WSL. Confirm that the requested distribution exists and can start."
}

$wslIp = (($wslAddresses -join " ") -split "\s+" | Where-Object {
    $_ -match "^\d{1,3}(\.\d{1,3}){3}$"
} | Select-Object -First 1)

$parsedWslIp = $null
$isValidWslIp = $wslIp -and
    [System.Net.IPAddress]::TryParse($wslIp, [ref]$parsedWslIp) -and
    $parsedWslIp.AddressFamily -eq [System.Net.Sockets.AddressFamily]::InterNetwork

if (-not $isValidWslIp) {
    throw "Could not find an IPv4 address in the WSL output: $wslAddresses"
}

$ipHelper = Get-Service -Name iphlpsvc
if ($ipHelper.Status -ne "Running") {
    Start-Service -Name iphlpsvc
}

# Refresh the mapping because WSL's NAT address can change after a restart.
$null = & netsh.exe interface portproxy delete v4tov4 `
    listenaddress=$listenIp listenport=$Port 2>&1

& netsh.exe interface portproxy add v4tov4 `
    listenaddress=$listenIp listenport=$Port `
    connectaddress=$wslIp connectport=$Port

if ($LASTEXITCODE -ne 0) {
    throw "Windows could not create the TCP port proxy."
}

$existingRule = Get-NetFirewallRule -Name $ruleName -ErrorAction SilentlyContinue
if ($existingRule) {
    $existingRule | Remove-NetFirewallRule
}

New-NetFirewallRule `
    -Name $ruleName `
    -DisplayName "EffortList WSL TCP $Port" `
    -Description "Allow local-network devices to reach EffortList in WSL through TCP port $Port." `
    -Direction Inbound `
    -Action Allow `
    -Protocol TCP `
    -LocalPort $Port `
    -Profile Private `
    -RemoteAddress LocalSubnet | Out-Null

Write-Host ""
Write-Host "EffortList WSL forwarding is ready." -ForegroundColor Green
Write-Host "Windows listener : ${listenIp}:$Port"
Write-Host "WSL destination  : ${wslIp}:$Port"
Write-Host "Firewall scope   : Private networks, LocalSubnet only"
Write-Host ""
Write-Host "Start the server inside WSL with:"
Write-Host ".venv/bin/fastapi dev --host 0.0.0.0 --port $Port" -ForegroundColor Cyan
Write-Host ""
Write-Host "Use the Windows Wi-Fi IPv4 address, followed by :$Port, from another device."
Write-Host "Rerun this script after WSL restarts if its NAT address changes."
