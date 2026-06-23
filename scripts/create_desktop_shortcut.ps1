param(
    [string]$ShortcutName = "FeintLex Dashboard"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Launcher = Join-Path $RepoRoot "scripts\launch_dashboard.ps1"
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "$ShortcutName.lnk"
$PowerShellExe = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"

if (-not (Test-Path -LiteralPath $Launcher)) {
    throw "Dashboard launcher was not found: $Launcher"
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($ShortcutPath)
$shortcut.TargetPath = $PowerShellExe
$shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$Launcher`""
$shortcut.WorkingDirectory = $RepoRoot
$shortcut.WindowStyle = 7
$shortcut.Description = "Launch the local FeintLex dashboard."
$shortcut.IconLocation = "$PowerShellExe,0"
$shortcut.Save()

Write-Output $ShortcutPath
