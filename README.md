<div align="center">

[🇬🇧 English](README.md) | [🇹🇷 Türkçe](README.tr.md)

# MCP Switcher

**Zero-dependency, cross-platform MCP profile switcher and manager for Gemini, Claude Desktop, Cursor, OpenCode, and Codex.**

</div>

---

## Overview

**MCP Switcher** is a command-line utility and interactive manager for organizing and switching Model Context Protocol (MCP) server profiles across multiple AI clients.

Active tool schemas consume context window capacity and increase inference latency. MCP Switcher partitions server configurations into task-oriented profiles (such as `coding`, `research`, `academic`, or `minimal`) and applies them to connected clients through a single command.

## Key Features

- **Multi-Client Synchronization:** Updates configuration files for Gemini, Claude Desktop, Cursor, OpenCode, and Codex concurrently.
- **Non-Destructive Merge:** Updates the `mcpServers` object while preserving custom editor shortcuts, themes, and application settings.
- **Runtime and Daemon Health Checks:** Verifies executable availability in `PATH` and confirms that the Docker daemon responds before activation.
- **Automatic Bootstrapping:** Discovers existing client configurations on first execution and initializes a default baseline profile.
- **Bilingual Support:** English and Turkish.
- **Zero External Dependencies:** Built entirely with the Python standard library.

---

## Installation

### macOS & Linux (Terminal Script)
```bash
curl -fsSL https://raw.githubusercontent.com/YigitKw/MCP-Switcher/main/install.sh | bash
```
> Installs to `~/.local/bin` without triggering browser quarantine attributes (`com.apple.quarantine`).

### Windows (PowerShell Script)
```powershell
irm https://raw.githubusercontent.com/YigitKw/MCP-Switcher/main/install.ps1 | iex
```

### Universal Package (pip / pipx)
```bash
pipx install mcp-switch
# or
pip install mcp-switch
```

---

## Architecture & Workflow

MCP Switcher maintains a persistent master catalog of all configured servers at `~/.gemini/config/profiles/library.json`. Target profiles select and group subsets of these definitions:

```
                  ┌───────────────────────────────┐
                  │      Central Server Library   │
                  │  (GitHub, Postgres, Memory...)│
                  └───────────────┬───────────────┘
                                  │
         ┌────────────────────────┴────────────────────────┐
         ▼                                                 ▼
┌──────────────────────────────┐          ┌──────────────────────────────┐
│  Profile: "coding"           │          │  Profile: "research"         │
│  - GitHub                    │          │  - Brave Search              │
│  - Postgres                  │          │  - Memory                    │
│  - Filesystem                │          │  - Sequential Thinking       │
└──────────────┬───────────────┘          └──────────────┬───────────────┘
               │ (mcp-switch coding)                     │
               ▼                                         ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Synchronized Clients: Gemini, Claude Desktop, Cursor, OpenCode, Codex  │
└────────────────────────────────────────────────────────────────────────┘
```

### Server Configuration and Authentication

Server definitions can be registered without manual file manipulation:
1. **Interactive Entry:** Execute `mcp-switch` and select `2. Add New MCP Server`. The prompt captures the executable name, arguments, and required environment variables (e.g., `GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxx`).
2. **JSON Import:** Supply raw configuration blocks directly via the `Paste JSON` prompt.
3. **Declarative Storage:** Profiles persist as standard JSON files in `~/.gemini/config/profiles/<profile_name>.json`.

---

## Usage

### Interactive Interface
Launch without arguments to enter the interactive terminal menu:
```bash
mcp-switch
```

### Command-Line Interface
```bash
mcp-switch <profile_name>       # Activate the specified profile (e.g., mcp-switch coding)
mcp-switch status               # Display active clients, profiles, and executable health
mcp-switch list                 # Enumerate all configured profiles
mcp-switch targets              # Select which AI clients participate in synchronization
mcp-switch lang [en|tr]         # Set the interface language
mcp-switch add                  # Register a new MCP server definition
mcp-switch edit                 # Create or update profile assignments
mcp-switch delete-profile <p>   # Remove an existing profile
mcp-switch remove-server <s>    # Remove a server from the library and all profiles
```

## License
MIT License. Open source and free to use.
