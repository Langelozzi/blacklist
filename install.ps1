# 1. Define Paths
$ConfigDir = "$env:APPDATA\blacklist"
$BinaryPath = "$ConfigDir\blacklist.exe"
$Repo = "Langelozzi/blacklist"

# 2. Get Latest Release URL from GitHub API
Write-Host "[+] Checking GitHub for the latest version..." -ForegroundColor Cyan
$ApiUrl = "https://api.github.com/repos/$Repo/releases/latest"
$ReleaseInfo = Invoke-RestMethod -Uri $ApiUrl

# Filter assets for the Windows binary (adjust "-windows.exe" to match your actual filename)
$DownloadUrl = $ReleaseInfo.assets | Where-Object { $_.name -like "*-windows.exe" } | Select-Object -ExpandProperty browser_download_url

if (!$DownloadUrl) {
    Write-Error "[!] Could not find a Windows binary in the latest GitHub release."
    return
}

# 3. Create Folder
if (!(Test-Path $ConfigDir)) {
    Write-Host "[+] Creating Directory: $ConfigDir" -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $ConfigDir | Out-Null
}

# 4. Download Binary with Lock Handling for Self-Updates
Write-Host "[+] Downloading latest version from: $DownloadUrl" -ForegroundColor Cyan

if (Test-Path $BinaryPath) {
    try {
        Invoke-WebRequest -Uri $DownloadUrl -OutFile $BinaryPath -ErrorAction Stop
    } catch {
        Write-Host "[i] File is in use. Performing hot-swap..." -ForegroundColor Yellow
        $OldFile = "$BinaryPath.old"
        if (Test-Path $OldFile) { Remove-Item $OldFile -Force }

        Move-Item -Path $BinaryPath -Destination $OldFile -Force
        Invoke-WebRequest -Uri $DownloadUrl -OutFile $BinaryPath
    }
} else {
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $BinaryPath
}

# 5. Add to PATH
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$ConfigDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$UserPath;$ConfigDir", "User")
    $env:Path += ";$ConfigDir"
    Write-Host "[+] PATH updated." -ForegroundColor Green
}

Write-Host "`n[!] Success! Restart your terminal to use 'blacklist'." -ForegroundColor Green
