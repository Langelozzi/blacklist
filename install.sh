#!/bin/bash

INSTALL_DIR="$HOME/.local/share/blacklist"
BIN_NAME="blacklist"
SYMLINK_PATH="/usr/local/bin/$BIN_NAME"
REPO="Langelozzi/blacklist"

# Logic to match your YAML asset_name
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

mkdir -p "$INSTALL_DIR"
curl -L -o "$INSTALL_DIR/$BIN_NAME" "$DOWNLOAD_URL"
chmod +x "$INSTALL_DIR/$BIN_NAME"

if [ -L "$SYMLINK_PATH" ] || [ -f "$SYMLINK_PATH" ]; then sudo rm "$SYMLINK_PATH"; fi
sudo ln -s "$INSTALL_DIR/$BIN_NAME" "$SYMLINK_PATH"

echo -e "\n[!] Done! Type 'sudo blacklist on' to begin."
