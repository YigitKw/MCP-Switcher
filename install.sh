#!/usr/bin/env sh
set -e

INSTALL_DIR="${HOME}/.local/bin"
mkdir -p "$INSTALL_DIR"

OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

if [ "$OS" = "darwin" ]; then
    ASSET="mcp-switch-macos-universal"
elif [ "$OS" = "linux" ]; then
    case "$ARCH" in
        x86_64|amd64)
            ASSET="mcp-switch-linux-x64"
            ;;
        aarch64|arm64)
            ASSET="mcp-switch-linux-arm64"
            ;;
        *)
            echo "[WARN] Unsupported Linux architecture: $ARCH. Attempting fallback via pip..."
            pip3 install --user mcp-switch || pipx install mcp-switch
            exit 0
            ;;
    esac
else
    echo "[ERROR] Unsupported operating system: $OS"
    exit 1
fi

URL="https://github.com/YigitKw/MCP-Switcher/releases/latest/download/${ASSET}"
TARGET="${INSTALL_DIR}/mcp-switch"

echo "[*] Downloading ${ASSET}..."
if curl -fsSL "$URL" -o "$TARGET"; then
    chmod 755 "$TARGET"
    if [ "$OS" = "darwin" ]; then
        xattr -d com.apple.quarantine "$TARGET" 2>/dev/null || true
    fi
    echo "[OK] Installed successfully to ${TARGET}"
else
    echo "[WARN] Prebuilt binary not available for ${ASSET}. Falling back to pip/pipx installation..."
    pip3 install --user mcp-switch || pipx install mcp-switch
fi

case ":$PATH:" in
    *":$INSTALL_DIR:"*) ;;
    *) echo "[INFO] Add ${INSTALL_DIR} to your PATH in ~/.zshrc or ~/.bashrc" ;;
esac
