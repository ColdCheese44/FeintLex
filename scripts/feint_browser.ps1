function Get-FeintBrowserMode {
    param([string]$Mode = $env:FEINT_BROWSER_MODE)

    if (-not $Mode) {
        $Mode = "fullscreen"
    }

    switch ($Mode.ToLowerInvariant()) {
        "fullscreen" { return "fullscreen" }
        "maximized" { return "maximized" }
        "normal" { return "normal" }
        "kiosk" { return "kiosk" }
        default { return "fullscreen" }
    }
}

function Get-FeintBravePath {
    if ($env:FEINT_BROWSER_PATH -and (Test-Path -LiteralPath $env:FEINT_BROWSER_PATH)) {
        return $env:FEINT_BROWSER_PATH
    }

    $paths = @(
        "C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        "C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
        "$env:LOCALAPPDATA\BraveSoftware\Brave-Browser\Application\brave.exe"
    )

    foreach ($path in $paths) {
        if ($path -and (Test-Path -LiteralPath $path)) {
            return $path
        }
    }

    $commands = @("brave.exe", "brave", "brave-browser")
    foreach ($command in $commands) {
        $candidate = Get-Command $command -ErrorAction SilentlyContinue
        if ($candidate) {
            return $candidate.Source
        }
    }

    return $null
}

function Get-FeintBrowserLaunchArgs {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url,

        [string]$Mode = $env:FEINT_BROWSER_MODE
    )

    $resolvedMode = Get-FeintBrowserMode -Mode $Mode
    $args = @("--new-window")

    switch ($resolvedMode) {
        "fullscreen" { $args += "--start-fullscreen" }
        "maximized" { $args += "--start-maximized" }
        "kiosk" { $args += "--kiosk" }
        "normal" { }
        default { $args += "--start-fullscreen" }
    }

    $args += $Url
    return $args
}

function Get-FeintBrowserLaunchPlan {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url,

        [string]$Mode = $env:FEINT_BROWSER_MODE
    )

    $resolvedMode = Get-FeintBrowserMode -Mode $Mode
    $browserPreference = if ($env:FEINT_BROWSER) { $env:FEINT_BROWSER.ToLowerInvariant() } else { "brave" }

    if ($browserPreference -in @("default", "system", "browser")) {
        return [pscustomobject]@{
            Browser = "default"
            FilePath = $null
            Arguments = @()
            Mode = $resolvedMode
            Url = $Url
            FallbackReason = "FEINT_BROWSER=$browserPreference"
        }
    }

    $brave = Get-FeintBravePath
    if ($brave) {
        return [pscustomobject]@{
            Browser = "brave"
            FilePath = $brave
            Arguments = Get-FeintBrowserLaunchArgs -Url $Url -Mode $resolvedMode
            Mode = $resolvedMode
            Url = $Url
            FallbackReason = $null
        }
    }

    return [pscustomobject]@{
        Browser = "default"
        FilePath = $null
        Arguments = @()
        Mode = $resolvedMode
        Url = $Url
        FallbackReason = "Brave not found"
    }
}

function Open-FeintBrowser {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url,

        [string]$Mode = $env:FEINT_BROWSER_MODE
    )

    $plan = Get-FeintBrowserLaunchPlan -Url $Url -Mode $Mode

    if ($plan.Browser -eq "brave" -and $plan.FilePath) {
        Start-Process -FilePath $plan.FilePath -ArgumentList $plan.Arguments
        return
    }

    Write-Warning "Brave not found or not selected. Falling back to default browser."
    Start-Process $Url
}
