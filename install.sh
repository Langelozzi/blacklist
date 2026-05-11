#!/bin/bash

# 1. Define Paths
INSTALL_DIR="$HOME/.local/share/blacklist"
BIN_NAME="blacklist"
SYMLINK_PATH="/usr/local/bin/$BIN_NAME"

# Detect OS for correct binary
OS_TYPE=$(uname -s | tr '[:upper:]' '[:lower:]')
BINARY_URL="https://github.com/Langelozzi/blacklist/releases/download/v0.1.0/blacklist-$OS_TYPE"

# 2. Create Installation Directory
mkdir -p "$INSTALL_DIR"

# 3. Download Binary
echo "[+] Downloading $OS_TYPE binary to $INSTALL_DIR..."
curl -L -o "$INSTALL_DIR/$BIN_NAME" "$BINARY_URL"
chmod +x "$INSTALL_DIR/$BIN_NAME"

# 4. Create the Symlink (Requires Sudo for /usr/local/bin)
echo "[+] Creating symlink at $SYMLINK_PATH..."
if [ -L "$SYMLINK_PATH" ] || [ -f "$SYMLINK_PATH" ]; then
    sudo rm "$SYMLINK_PATH"
fi

sudo ln -s "$INSTALL_DIR/$BIN_NAME" "$SYMLINK_PATH"

echo -e "\n[!] Done! Type 'blacklist on' or 'blacklist off' to manage the filter."
echo "[i] Note: You will be prompted for your sudo password to change network settings."
