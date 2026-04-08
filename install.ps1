# 1. Define Paths
$ConfigDir = "$env:APPDATA\blacklist"
$BinaryPath = "$ConfigDir\blacklist.exe"
$ListPath = "$ConfigDir\blocklist.txt"

# URLs
$BinaryUrl = "https://github.com/Langelozzi/blacklist/releases/download/v0.1.0/blacklist-windows.exe"
$ListUrl = "https://raw.githubusercontent.com/Langelozzi/blacklist/main/lists/blocklist.txt"

# 2. Create Folder
if (!(Test-Path $ConfigDir)) {
    Write-Host "[+] Creating Directory: $ConfigDir" -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $ConfigDir | Out-Null
}

# 3. Download Binary
Write-Host "[+] Downloading binary to $ConfigDir..." -ForegroundColor Cyan
Invoke-WebRequest -Uri $BinaryUrl -OutFile $BinaryPath

# 4. Download Blocklist
Write-Host "[+] Downloading blocklist to $ConfigDir..." -ForegroundColor Cyan
Invoke-WebRequest -Uri $ListUrl -OutFile $ListPath

# 5. Add to PATH (User Level - No Admin required for this part)
Write-Host "[+] Ensuring $ConfigDir is in your PATH..." -ForegroundColor Cyan
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")

if ($UserPath -notlike "*$ConfigDir*") {
    $NewPath = "$UserPath;$ConfigDir"
    [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
    # Update current session PATH
    $env:Path += ";$ConfigDir"
    Write-Host "[+] PATH updated successfully." -ForegroundColor Green
} else {
    Write-Host "[i] Directory already in PATH." -ForegroundColor Yellow
}

Write-Host "`n[!] Success! Restart your terminal and type 'blacklist' to begin." -ForegroundColor Green
Write-Host "[i] Note: You will still need to run your terminal as Administrator to block sites." -ForegroundColor Gray
