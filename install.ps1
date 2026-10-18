$ErrorActionPreference = "Stop"

$installDir = "$env:LOCALAPPDATA\Programs\mcp-switch"
if (!(Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
}

$url = "https://github.com/YigitKw/MCP-Switcher/releases/latest/download/mcp-switch-windows-x64.exe"
$target = "$installDir\mcp-switch.exe"

Write-Host "[*] Downloading mcp-switch for Windows..."
Invoke-WebRequest -Uri $url -OutFile $target

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$installDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$installDir", "User")
    Write-Host "[*] Added $installDir to User PATH."
}

Write-Host "[OK] Installation completed: $target"
Write-Host "Restart your terminal and type 'mcp-switch' to start."
