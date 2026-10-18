#!/usr/bin/env sh
set -e

INSTALL_DIR="${HOME}/.local/bin"
mkdir -p "$INSTALL_DIR"

OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

if [ "$OS" = "darwin" ]; then
    ASSET="mcp-switch-macos-universal"
elif [ "$OS" = "linux" ]; then
    ASSET="mcp-switch-linux-x64"
else
    echo "[ERROR] Unsupported OS: $OS"
    exit 1
fi

URL="https://github.com/YigitKw/MCP-Switcher/releases/latest/download/${ASSET}"
TARGET="${INSTALL_DIR}/mcp-switch"

echo "[*] Downloading ${ASSET}..."
curl -fsSL "$URL" -o "$TARGET"
chmod +x "$TARGET"

if [ "$OS" = "darwin" ]; then
    xattr -d com.apple.quarantine "$TARGET" 2>/dev/null || true
fi

echo "[OK] Installed successfully to ${TARGET}"
case ":$PATH:" in
    *":$INSTALL_DIR:"*) ;;
    *) echo "[INFO] Add ${INSTALL_DIR} to your PATH in ~/.zshrc or ~/.bashrc" ;;
esac
