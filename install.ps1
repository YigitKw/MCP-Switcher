$ErrorActionPreference = "Stop"

$installDir = "$env:LOCALAPPDATA\Programs\mcp-switch"
if (!(Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
}

$url = "https://github.com/YigitKw/MCP-Switcher/releases/latest/download/mcp-switch-windows-x64.exe"
$target = "$installDir\mcp-switch.exe"

try {
    Write-Host "[*] Downloading mcp-switch for Windows..."
    Invoke-WebRequest -Uri $url -OutFile $target
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $currentPaths = @()
    if ($userPath) {
        $currentPaths = ($userPath -split ';') | Where-Object { $_ -ne "" }
    }

    if ($currentPaths -notcontains $installDir) {
        $newPath = ($currentPaths + $installDir) -join ';'
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        Write-Host "[*] Added $installDir to User PATH."
    }

    Write-Host "[OK] Installation completed: $target"
    Write-Host "Restart your terminal and type 'mcp-switch' to start."
} catch {
    Write-Host "[WARN] Prebuilt executable not available. Attempting fallback via pip/pipx..."
    try {
        pipx install mcp-switch
    } catch {
        try {
            pip install mcp-switch
        } catch {
            pip install "git+https://github.com/YigitKw/MCP-Switcher.git"
        }
    }
}
