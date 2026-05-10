# Blacklist

A simple CLI tool to block and unblock websites by modifying your system's `hosts` file. Supports optional password protection to prevent unauthorized changes.

The Python CLI lives in `cli/`, and the Chrome extension scaffold lives in `extension/`.

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

**Block sites** using the default `blocklist.txt`:
```bash
sudo blacklist
```

**Block sites** from a custom file:
```bash
sudo blacklist my_sites.txt
```

**Unblock sites** (revert changes):
```bash
sudo blacklist --revert
sudo blacklist my_sites.txt --revert
```

**Redirect to a custom IP** instead of `127.0.0.1`:
```bash
sudo blacklist --ip-address 0.0.0.0
```

**Set or change a password** (to protect the tool from unauthorized use):
```bash
blacklist --set-password
```

**Remove password protection:**
```bash
blacklist --remove-password
```

### Blocklist file format

`blocklist.txt` should contain one domain per line. `www.` variants are added automatically.

```
facebook.com
reddit.com
twitter.com
```
