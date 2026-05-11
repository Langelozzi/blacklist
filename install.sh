#!/bin/bash

INSTALL_DIR="$HOME/.local/share/blacklist"
BIN_NAME="blacklist"
SYMLINK_PATH="/usr/local/bin/$BIN_NAME"
REPO="Langelozzi/blacklist"

# 1. Logic to match your YAML asset_name
OS_TYPE=$(uname -s | tr '[:upper:]' '[:lower:]')
if [ "$OS_TYPE" == "darwin" ]; then
    SEARCH_PATTERN="blacklist-macos"
else
    SEARCH_PATTERN="blacklist-linux"
fi

echo "[+] Searching for latest $SEARCH_PATTERN..."
API_URL="https://api.github.com/repos/$REPO/releases/latest"
DOWNLOAD_URL=$(curl -s $API_URL | grep "browser_download_url" | grep "$SEARCH_PATTERN" | cut -d '"' -f 4)

if [ -z "$DOWNLOAD_URL" ]; then
    echo "[-] Error: Asset $SEARCH_PATTERN not found in latest release."
    exit 1
fi

# 2. Ensure directory exists
mkdir -p "$INSTALL_DIR"

# 3. Download to a temporary file (Atomic Swap)
# This prevents "Text file busy" errors when updating while running.
echo "[+] Downloading latest binary..."
TEMP_BIN="$INSTALL_DIR/${BIN_NAME}.tmp"

curl -L -o "$TEMP_BIN" "$DOWNLOAD_URL"
chmod +x "$TEMP_BIN"

# Use 'mv' to overwrite the old binary.
# Linux/macOS allows this even if the old binary is currently executing.
mv -f "$TEMP_BIN" "$INSTALL_DIR/$BIN_NAME"

# 4. Manage Symlink
echo "[+] Updating symlink at $SYMLINK_PATH..."
if [ -L "$SYMLINK_PATH" ] || [ -f "$SYMLINK_PATH" ]; then
    sudo rm "$SYMLINK_PATH"
fi
sudo ln -s "$INSTALL_DIR/$BIN_NAME" "$SYMLINK_PATH"

echo -e "\n[!] Success! Type 'sudo blacklist on' to begin."
