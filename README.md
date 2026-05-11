# Blacklist

A CLI tool to enable a global content filter using Cloudflare Family DNS. Supports optional password protection to prevent unauthorized changes.

---

## Installation

**macOS / Linux**
```bash
curl -fsSL https://raw.githubusercontent.com/Langelozzi/blacklist/main/install.sh | sudo bash
```

**Windows (PowerShell — run as Administrator)**
```powershell
irm https://raw.githubusercontent.com/Langelozzi/blacklist/main/install.ps1 | iex
```

> **Note:** The tool requires root/Administrator privileges to modify the hosts file.

---

## Usage

All commands should be run with `sudo` on macOS/Linux, or from an Administrator terminal on Windows.

**Enable filter**:
```bash
sudo blacklist on
```

**Disable Filter** (revert changes):
```bash
sudo blacklist off
```

**Set or change a password** (to protect the tool from unauthorized use):
```bash
blacklist --set-password
```

**Remove password protection:**
```bash
blacklist --remove-password
```

**Update blacklist:**
```bash
sudo blacklist --update
```
