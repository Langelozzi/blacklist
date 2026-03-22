#!/bin/bash

# 1. Define Paths
INSTALL_SRC="$HOME/.config/blacklist"
BIN_LINK="/usr/local/bin/blacklist"
CONFIG_DIR="$HOME/.config/blacklist"

# 2. Create Folders
mkdir -p "$INSTALL_SRC"
mkdir -p "$CONFIG_DIR"

# 3. Download Binary (Assume we are testing locally or repo is public)
# Replace with your actual curl command
echo "[+] Downloading binary to $INSTALL_SRC..."
curl -L -o "$INSTALL_SRC/blacklist-bin" "https://github.com/Langelozzi/blacklist/releases/download/v0.1.0/blacklist-linux"
chmod +x "$INSTALL_SRC/blacklist-bin"

# 4. Download Blocklist to Config Folder
echo "[+] Downloading blocklist to $CONFIG_DIR..."
curl -L -o "$CONFIG_DIR/blocklist.txt" "https://raw.githubusercontent.com/Langelozzi/blacklist/main/blocklist.txt"

# 5. Create the Symlink (Requires Sudo for /usr/local/bin)
echo "[+] Creating symlink..."
if [ -L "$BIN_LINK" ]; then
    sudo rm "$BIN_LINK"
fi
sudo ln -s "$INSTALL_SRC/blacklist-bin" "$BIN_LINK"

echo "[!] Done! Running 'blacklist' will now trigger the binary at $INSTALL_SRC."
