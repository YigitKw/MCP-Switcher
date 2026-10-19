import sys
import os
import json
import shutil
import re
import time
import shlex
import subprocess
from pathlib import Path
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VERSION = "1.0.0"
BASE_DIR = Path(os.environ.get("MCP_SWITCH_HOME", Path.home()))
CONFIG_DIR = BASE_DIR / ".gemini" / "config"
PROFILES_DIR = CONFIG_DIR / "profiles"
ACTIVE_CONFIG = CONFIG_DIR / "mcp_config.json"
CURRENT_PROFILE_FILE = CONFIG_DIR / "current_profile.txt"
LIBRARY_FILE = PROFILES_DIR / "library.json"
BACKUPS_DIR = PROFILES_DIR / "backups"
TARGETS_FILE = CONFIG_DIR / "active_targets.json"
LANG_FILE = CONFIG_DIR / "lang.txt"

EXIT_OK = 0
EXIT_NOT_FOUND = 1
EXIT_INVALID_DATA = 2
EXIT_IO_ERROR = 3

TEXTS = {
    "en": {
        "ok": "[OK]",
        "err": "[ERROR]",
        "warn": "[WARN]",
        "sync": "[SYNC]",
        "profile_active": "Profile activated",
        "total_servers": "Total servers",
        "tools": "Tools",
        "none": "None",
        "empty": "Empty",
        "active": "[ACTIVE]",
        "installed": "Installed",
        "not_found": "Not found",
        "cmd_missing": "Command not found in PATH or disk",
        "cmd_ready": "Executable found",
        "docker_not_running": "Docker executable found but daemon is not running or responsive",
        "profiles_title": "--- AVAILABLE PROFILES ---",
        "status_title": "--- ACTIVE MCP STATUS ---",
        "sync_clients": "Synchronized Clients",
        "lib_title": "--- MCP LIBRARY ---",
        "add_title": "--- ADD NEW MCP SERVER ---",
        "edit_title": "--- EDIT / CREATE PROFILE ---",
        "delete_p_title": "--- DELETE PROFILE ---",
        "remove_s_title": "--- REMOVE SERVER FROM LIBRARY ---",
        "rollback_title": "--- RESTORE BACKUP (ROLLBACK) ---",
        "targets_title": "--- CLIENT SYNC SETTINGS ---",
        "menu_title": "MCP SWITCHER",
        "menu_1": "1. Switch Profile",
        "menu_2": "2. Add New MCP Server",
        "menu_3": "3. Edit / Create Profile",
        "menu_4": "4. Clone Existing Profile",
        "menu_5": "5. Quick Enable Server in Active Profile",
        "menu_6": "6. Quick Disable Server in Active Profile",
        "menu_7": "7. Delete a Profile",
        "menu_8": "8. Remove Server from Library",
        "menu_9": "9. Rollback to Previous Backup",
        "menu_10": "10. Export Profile (Safe / Clean)",
        "menu_11": "11. Manage Target Clients (Claude, Cursor, Windsurf, OpenCode, Codex, Gemini)",
        "menu_12": "12. View Status and Health Check",
        "menu_13": "13. List All Servers in Library",
        "menu_14": "14. Change Language",
        "menu_15": "15. Exit",
        "choice": "Your choice",
        "prompt_profile_name": "Target profile number or name",
        "prompt_select_servers": "Enter server numbers comma-separated (e.g. 1,3), 'all', or press Enter to keep current",
        "saved": "Saved successfully",
        "deleted": "Deleted successfully",
        "restored": "Restored successfully",
        "cloned": "Cloned successfully",
        "aborted": "Operation cancelled",
        "ask_activate": "Do you want to activate this profile now? (y/n)",
        "ask_assign": "Do you want to assign this server to a profile now? (y/n)",
        "ask_confirm_delete": "Are you sure you want to delete? (y/n)",
        "cmd_warn_add": "Warning: Command is not found in PATH. Continue anyway? (y/n)",
        "auto_imported": "Auto-imported existing configuration into profile",
        "non_interactive_help": "Non-interactive mode detected. Use 'mcp-switch --help' for usage.",
        "paste_json_prompt": "Paste JSON configuration (press Enter on empty line or EOF to finish):",
        "cannot_merge_corrupt": "Cannot merge configuration: existing client file contains invalid JSON. Overwrite aborted to prevent data loss.",
        "no_backups_found": "No backup files available to restore.",
    },
    "tr": {
        "ok": "[OK]",
        "err": "[HATA]",
        "warn": "[UYARI]",
        "sync": "[SENKRON]",
        "profile_active": "Profil aktif edildi",
        "total_servers": "Toplam sunucu sayisi",
        "tools": "Araclar",
        "none": "Yok",
        "empty": "Bos",
        "active": "[AKTIF]",
        "installed": "Kurulu",
        "not_found": "Bulunamadi",
        "cmd_missing": "Komut PATH'te veya diskte bulunamadi",
        "cmd_ready": "Calistirilabilir dosya mevcut",
        "docker_not_running": "Docker kurulu ancak servis (daemon) calismiyor",
        "profiles_title": "--- MEVCUT PROFILLER ---",
        "status_title": "--- MCP AKTIF DURUMU ---",
        "sync_clients": "Senkronize Istemciler",
        "lib_title": "--- MCP GENEL KUTUPHANE ---",
        "add_title": "--- YENI MCP SUNUCUSU EKLE ---",
        "edit_title": "--- PROFIL DUZENLE / OLUSTUR ---",
        "delete_p_title": "--- PROFIL SIL ---",
        "remove_s_title": "--- KUTUPHANEDEN SUNUCU SIL ---",
        "rollback_title": "--- YEDEKTEN GERI YUKLE (ROLLBACK) ---",
        "targets_title": "--- ISTEMCI SENKRONIZASYON AYARLARI ---",
        "menu_title": "MCP SWITCHER",
        "menu_1": "1. Profil Degistir",
        "menu_2": "2. Yeni MCP Sunucusu Ekle",
        "menu_3": "3. Profil Duzenle / Olustur",
        "menu_4": "4. Mevcut Profili Klonla",
        "menu_5": "5. Aktif Profile Hizli Sunucu Ekle (Enable)",
        "menu_6": "6. Aktif Profilde Sunucuyu Kapat (Disable)",
        "menu_7": "7. Profil Sil",
        "menu_8": "8. Kutuphaneden Sunucu Sil",
        "menu_9": "9. Yedekten Geri Yukle (Rollback)",
        "menu_10": "10. Profili Disa Aktar (Export / Guvenli)",
        "menu_11": "11. Hedef Istemcileri Yonet (Claude, Cursor, Windsurf, OpenCode, Codex, Gemini)",
        "menu_12": "12. Durum ve Saglik Raporu",
        "menu_13": "13. Tum Sunucu Kutuphanesini Listele",
        "menu_14": "14. Dil Degistir",
        "menu_15": "15. Cikis",
        "choice": "Seciminiz",
        "prompt_profile_name": "Gecmek istediginiz profil numarasi veya adi",
        "prompt_select_servers": "Aktif olmasini istediginiz numaralari virgul ile girin (orn: 1,3), 'all' yazin veya korumak icin Enter'a basin",
        "saved": "Basariyla kaydedildi",
        "deleted": "Basariyla silindi",
        "restored": "Basariyla geri yuklendi",
        "cloned": "Basariyla klonlandi",
        "aborted": "Islem iptal edildi",
        "ask_activate": "Bu profili simdi aktif etmek ister misiniz? (e/h)",
        "ask_assign": "Bu sunucuyu bir profile simdi eklemek ister misiniz? (e/h)",
        "ask_confirm_delete": "Silmek istediginize emin misiniz? (e/h)",
        "cmd_warn_add": "Uyari: Komut PATH'te bulunamadi. Yine de devam edilsin mi? (e/h)",
        "auto_imported": "Mevcut konfigurasyon profile otomatik aktarildi",
        "non_interactive_help": "Etkilesimsiz ortam algilandi. Kullanim icin 'mcp-switch --help'.",
        "paste_json_prompt": "JSON yapilandirmasini yapistirin (bitirmek icin bos satirda Enter'a basin):",
        "cannot_merge_corrupt": "Birlestirme yapilamadi: istemci dosyasi bozuk JSON iceriyor. Veri kaybi olmamasi icin islem durduruldu.",
        "no_backups_found": "Geri yuklenecek yedek dosyasi bulunamadi.",
    }
}

def get_current_lang():
    if LANG_FILE.exists():
        try:
            val = LANG_FILE.read_text(encoding="utf-8").strip().lower()
            if val in TEXTS:
                return val
        except OSError:
            pass
    system_lang = os.environ.get("LANG", "").lower()
    if "tr" in system_lang:
        return "tr"
    return "en"

def set_lang(lang_code):
    clean = lang_code.strip().lower()
    if clean in TEXTS:
        try:
            LANG_FILE.write_text(clean, encoding="utf-8")
            return True
        except OSError:
            pass
    return False

def t(key):
    lang = get_current_lang()
    return TEXTS.get(lang, TEXTS["en"]).get(key, TEXTS["en"].get(key, key))

def check_command_installed(cmd_str):
    if not cmd_str:
        return False, t("none")
    expanded = os.path.expandvars(os.path.expanduser(cmd_str.strip().strip('"').strip("'")))
    path_obj = Path(expanded)
    base_name = path_obj.name.lower()
    is_docker = (base_name == "docker" or base_name.startswith("docker."))
    if path_obj.is_file() or path_obj.exists():
        if is_docker:
            return probe_docker_daemon(str(path_obj))
        return True, str(path_obj)
    resolved = shutil.which(expanded)
    if resolved:
        if is_docker:
            return probe_docker_daemon(resolved)
        return True, resolved
    if sys.platform != "win32" and (base_name.endswith(".exe") or base_name.endswith(".cmd")):
        clean_name = re.sub(r'\.(exe|cmd|bat)$', '', base_name, flags=re.IGNORECASE)
        fallback_posix = shutil.which(clean_name)
        if fallback_posix:
            return True, fallback_posix
    if sys.platform == "win32" and not expanded.lower().endswith((".exe", ".cmd", ".bat")):
        for ext in (".cmd", ".exe", ".bat"):
            candidate = shutil.which(expanded + ext)
            if candidate:
                if is_docker:
                    return probe_docker_daemon(candidate)
                return True, candidate
    return False, f"{t('cmd_missing')}: '{cmd_str}'"

def probe_docker_daemon(docker_path):
    try:
        res = subprocess.run([docker_path, "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1.5)
        if res.returncode == 0:
            return True, docker_path
        return False, f"{t('docker_not_running')} ({docker_path})"
    except Exception:
        return False, f"{t('docker_not_running')} ({docker_path})"

def get_client_registry():
    home = Path(os.environ.get("MCP_SWITCH_HOME", Path.home()))
    if sys.platform == "win32":
        appdata_base = os.environ.get("MCP_SWITCH_APPDATA")
        appdata = Path(appdata_base) if appdata_base else Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
        claude_path = appdata / "Claude" / "claude_desktop_config.json"
    elif sys.platform == "darwin":
        claude_path = home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    else:
        claude_path = home / ".config" / "Claude" / "claude_desktop_config.json"
    return {
        "gemini": home / ".gemini" / "config" / "mcp_config.json",
        "claude": claude_path,
        "cursor": home / ".cursor" / "mcp.json",
        "windsurf": home / ".codeium" / "windsurf" / "mcp_config.json",
        "opencode": home / ".opencode" / "mcp.json",
        "codex": home / ".codex" / "mcp.json",
    }

def sanitize_name(name):
    clean = re.sub(r'[^a-zA-Z0-9_\-]', '', name.strip())
    if not clean or clean.startswith('.') or '..' in clean:
        return ""
    return clean

def read_json_file(path):
    if not path.exists():
        return None, None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data, None
    except json.JSONDecodeError as e:
        return None, f"JSON Error ({path.name}): {e.msg} (L{e.lineno}, C{e.colno})"
    except PermissionError:
        return None, f"Permission denied: {path}"
    except OSError as e:
        return None, f"File read error: {e}"

def write_json_file(path, data):
    for attempt in range(3):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = path.with_suffix(f".tmp_{os.getpid()}_{attempt}")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            if sys.platform != "win32":
                try:
                    os.chmod(str(tmp_path), 0o600)
                except OSError:
                    pass
            if sys.platform == "win32" and path.exists():
                try:
                    os.replace(str(tmp_path), str(path))
                except OSError:
                    shutil.move(str(tmp_path), str(path))
            else:
                shutil.move(str(tmp_path), str(path))
            if sys.platform != "win32":
                try:
                    os.chmod(str(path), 0o600)
                except OSError:
                    pass
            return True, None
        except PermissionError:
            time.sleep(0.1)
        except OSError as e:
            time.sleep(0.1)
            if attempt == 2:
                return False, f"File write error ({path.name}): {e}"
    return False, f"Permission denied: {path}"

def merge_and_save_client_config(client_path, target_data):
    servers = target_data.get("mcpServers", {})
    if client_path.exists():
        existing_data, err = read_json_file(client_path)
        if err:
            return False, f"{t('cannot_merge_corrupt')} ({err})"
        if isinstance(existing_data, dict):
            merged = dict(existing_data)
            merged["mcpServers"] = servers
        else:
            merged = {"mcpServers": servers}
    else:
        merged = {"mcpServers": servers}
    return write_json_file(client_path, merged)

def validate_mcp_structure(data):
    if not isinstance(data, dict):
        return False, "Root data must be a JSON object"
    servers = data.get("mcpServers")
    if servers is None:
        return True, None
    if not isinstance(servers, dict):
        return False, "'mcpServers' must be an object"
    for name, spec in servers.items():
        if not isinstance(spec, dict):
            return False, f"'{name}' definition must be an object"
        if "command" not in spec:
            return False, f"'{name}' missing required field: 'command'"
        if "env" in spec and isinstance(spec["env"], dict):
            for env_k, env_v in list(spec["env"].items()):
                if not isinstance(env_v, str):
                    spec["env"][env_k] = str(env_v)
    return True, None

def get_enabled_targets():
    reg = get_client_registry()
    if TARGETS_FILE.exists():
        saved, err = read_json_file(TARGETS_FILE)
        if isinstance(saved, list) and saved:
            valid = [t_name for t_name in saved if t_name in reg]
            if valid:
                return valid
    detected = ["gemini"]
    for name, path in reg.items():
        if name != "gemini" and (path.exists() or path.parent.exists()):
            detected.append(name)
    write_json_file(TARGETS_FILE, detected)
    return detected

def get_current_profile_name():
    if CURRENT_PROFILE_FILE.exists():
        try:
            curr = CURRENT_PROFILE_FILE.read_text(encoding="utf-8").strip()
            if (PROFILES_DIR / f"{curr}.json").exists():
                return curr
        except OSError:
            pass
    first_p = next(PROFILES_DIR.glob("*.json"), None)
    if first_p and first_p.name not in ("library.json", "active_targets.json"):
        return first_p.stem
    return "default"

def auto_bootstrap_initial_setup():
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    existing_profiles = [p for p in PROFILES_DIR.glob("*.json") if p.name not in ("library.json", "active_targets.json")]
    if not existing_profiles:
        reg = get_client_registry()
        initial_servers = {}
        for c_name, c_path in reg.items():
            data, err = read_json_file(c_path)
            if isinstance(data, dict) and isinstance(data.get("mcpServers"), dict):
                for s_k, s_v in data["mcpServers"].items():
                    if s_k not in initial_servers:
                        initial_servers[s_k] = s_v
        initial_profile = PROFILES_DIR / "default.json"
        write_json_file(initial_profile, {"mcpServers": initial_servers})
        write_json_file(LIBRARY_FILE, {"mcpServers": initial_servers})
        CURRENT_PROFILE_FILE.write_text("default", encoding="utf-8")

def get_all_servers_from_library():
    lib_data, err = read_json_file(LIBRARY_FILE)
    lib = {}
    if isinstance(lib_data, dict):
        lib = lib_data.get("mcpServers", {})
    if not lib:
        for p in PROFILES_DIR.glob("*.json"):
            if p.name in ("library.json", "active_targets.json"):
                continue
            data, err = read_json_file(p)
            if isinstance(data, dict):
                for k, v in data.get("mcpServers", {}).items():
                    if k not in lib:
                        lib[k] = v
        if lib:
            write_json_file(LIBRARY_FILE, {"mcpServers": lib})
    return lib

def switch_profile(target_name):
    clean_name = sanitize_name(target_name)
    if not clean_name:
        print(f"{t('err')} 1: Invalid profile name '{target_name}'", file=sys.stderr)
        return EXIT_NOT_FOUND
    target_path = PROFILES_DIR / f"{clean_name}.json"
    if not target_path.exists():
        print(f"{t('err')} 1: Profile '{clean_name}' not found", file=sys.stderr)
        return EXIT_NOT_FOUND
    target_data, err = read_json_file(target_path)
    if err:
        print(f"{t('err')} 2: Corrupted file: {err}", file=sys.stderr)
        return EXIT_INVALID_DATA
    is_valid, val_err = validate_mcp_structure(target_data)
    if not is_valid:
        print(f"{t('err')} 2: Invalid schema: {val_err}", file=sys.stderr)
        return EXIT_INVALID_DATA
    if "mcpServers" not in target_data:
        target_data = {"mcpServers": {}}
    servers = target_data.get("mcpServers", {})
    missing_cmds = []
    for s_name, spec in servers.items():
        cmd = spec.get("command", "")
        ok, res = check_command_installed(cmd)
        if not ok:
            missing_cmds.append((s_name, cmd, res))
    reg = get_client_registry()
    active_targets = get_enabled_targets()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    failed_targets = []
    print(f"\n{t('ok')} {t('profile_active')}: {clean_name.upper()}")
    for target in active_targets:
        client_file = reg.get(target)
        if not client_file:
            continue
        if client_file.exists():
            backup_file = BACKUPS_DIR / f"{target}_backup_{timestamp}.json"
            try:
                shutil.copy2(client_file, backup_file)
                if sys.platform != "win32":
                    try:
                        os.chmod(str(backup_file), 0o600)
                    except OSError:
                        pass
            except OSError as e:
                print(f"{t('warn')} {target} backup failed: {e}", file=sys.stderr)
        ok, werr = merge_and_save_client_config(client_file, target_data)
        if ok:
            print(f"  {t('sync')} {target:<10} -> {client_file}")
        else:
            print(f"  {t('err')} 3: {target:<10} write failed: {werr}", file=sys.stderr)
            failed_targets.append(target)
    backups = sorted(BACKUPS_DIR.glob("*_backup_*.json"), key=lambda f: f.stat().st_mtime)
    while len(backups) > 20:
        backups.pop(0).unlink(missing_ok=True)
    try:
        CURRENT_PROFILE_FILE.write_text(clean_name, encoding="utf-8")
    except OSError as e:
        print(f"{t('warn')} Failed to save current profile state: {e}", file=sys.stderr)
    print(f"\n{t('total_servers')} : {len(servers)}")
    print(f"{t('tools')}         : {', '.join(servers.keys()) if servers else t('none')}")
    if missing_cmds:
        print(f"\n{t('warn')} Missing executables found:")
        for s_name, cmd, reason in missing_cmds:
            print(f"  - {s_name} ('{cmd}') -> {reason}")
    print()
    if failed_targets:
        return EXIT_IO_ERROR
    return EXIT_OK

def list_profiles():
    current = get_current_profile_name()
    profiles = sorted([p for p in PROFILES_DIR.glob("*.json") if p.name not in ("library.json", "active_targets.json")])
    print(f"\n{t('profiles_title')}")
    for idx, p in enumerate(profiles, 1):
        name = p.stem
        data, err = read_json_file(p)
        if err:
            print(f"{idx}. {name} [CORRUPTED] -> {err}")
            continue
        servers = list(data.get("mcpServers", {}).keys()) if isinstance(data, dict) else []
        tag = f" {t('active')}" if name == current else ""
        print(f"{idx}. {name}{tag} -> {len(servers)} ({', '.join(servers) if servers else t('empty')})")
    print(f"Active: {current}\n")
    return profiles

def show_status():
    current = get_current_profile_name()
    reg = get_client_registry()
    targets = get_enabled_targets()
    print(f"\n{t('status_title')}")
    print(f"Profile: {current}")
    print(f"\n{t('sync_clients')}:")
    for trg in targets:
        p = reg.get(trg)
        exists = f"[{t('installed').upper()}]" if p and p.exists() else f"[{t('not_found').upper()}]"
        print(f"  - {trg:<10}: {exists} {p}")
    data, err = read_json_file(ACTIVE_CONFIG)
    if err:
        print(f"\n{t('err')} Active config cannot be read: {err}")
        return EXIT_IO_ERROR
    servers = data.get("mcpServers", {}) if isinstance(data, dict) else {}
    print(f"\n{t('total_servers')}: {len(servers)}")
    for name, spec in servers.items():
        cmd = spec.get("command", "") if isinstance(spec, dict) else ""
        args = " ".join(spec.get("args", [])) if isinstance(spec, dict) and isinstance(spec.get("args"), list) else ""
        ok, res = check_command_installed(cmd)
        stat = f"[{t('ok')}]" if ok else f"[{t('warn')}]"
        note = f"-> {res}" if not ok else ""
        print(f"  * {stat} {name}: {cmd} {args} {note}".strip())
    if not servers:
        print(f"  {t('none')}")
    print()
    return EXIT_OK

def manage_targets_interactive():
    reg = get_client_registry()
    targets = get_enabled_targets()
    print(f"\n{t('targets_title')}")
    keys = list(reg.keys())
    for idx, k in enumerate(keys, 1):
        status = "[X]" if k in targets else "[ ]"
        p = reg[k]
        exists = f"({t('installed')})" if p.exists() or p.parent.exists() else f"({t('not_found')})"
        print(f"{idx}. {status} {k:<10} {exists} -> {p}")
    print(f"\n{t('prompt_select_servers')}:")
    choice = input("> ").strip().lower()
    new_targets = []
    if choice == "all":
        new_targets = keys
    elif choice:
        for part in choice.split(","):
            part = part.strip()
            if part.isdigit():
                val = int(part)
                if 1 <= val <= len(keys):
                    new_targets.append(keys[val - 1])
    if new_targets:
        write_json_file(TARGETS_FILE, new_targets)
        print(f"{t('ok')} {t('saved')}: {', '.join(new_targets)}")
    else:
        print(f"{t('warn')} No changes made.")

def add_server_interactive():
    print(f"\n{t('add_title')}")
    print("1. Manuel (Command & Args)")
    print("2. Paste JSON")
    print("3. Cancel")
    choice = input(f"{t('choice')} (1-3): ").strip()
    lib = get_all_servers_from_library()
    server_name = ""
    server_data = {}
    if choice == "1":
        raw_name = input("Server name (e.g. github, postgres): ").strip()
        server_name = sanitize_name(raw_name)
        if not server_name:
            print(f"{t('err')} 1: Invalid server name.")
            return
        cmd = input("Command (e.g. npx, python, uvx): ").strip()
        if not cmd:
            print(f"{t('err')} 1: Command cannot be empty.")
            return
        ok, res = check_command_installed(cmd)
        if not ok:
            print(f"{t('warn')} {res}")
            proceed = input(f"{t('cmd_warn_add')} ").strip().lower()
            if proceed not in ("y", "e"):
                return
        raw_args = input("Args (supports quotes for paths with spaces): ").strip()
        if raw_args:
            try:
                raw_tokens = shlex.split(raw_args, posix=(sys.platform != "win32"))
                args = [tok[1:-1] if len(tok) >= 2 and tok[0] == tok[-1] and tok[0] in ('"', "'") else tok for tok in raw_tokens]
            except ValueError:
                args = raw_args.split()
        else:
            args = []
        env_input = input("Env vars (KEY=VAL separated by comma): ").strip()
        env = {}
        if env_input:
            for item in env_input.split(","):
                if "=" in item:
                    k, v = item.split("=", 1)
                    env[k.strip()] = str(v.strip())
        server_data = {"command": cmd, "args": args}
        if env:
            server_data["env"] = env
    elif choice == "2":
        raw_name = input("Server name: ").strip()
        server_name = sanitize_name(raw_name)
        if not server_name:
            print(f"{t('err')} 1: Invalid server name.")
            return
        print(t("paste_json_prompt"))
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if not line.strip() and lines:
                break
            lines.append(line)
            joined = "\n".join(lines).strip()
            if joined.startswith("{") and joined.endswith("}"):
                try:
                    json.loads(joined)
                    break
                except json.JSONDecodeError:
                    pass
        raw_json = "\n".join(lines).strip()
        try:
            parsed = json.loads(raw_json)
            if isinstance(parsed, dict) and isinstance(parsed.get("mcpServers"), dict):
                parsed = parsed["mcpServers"]
            server_data = parsed.get(server_name, parsed) if isinstance(parsed, dict) else {}
        except json.JSONDecodeError as e:
            print(f"{t('err')} 2: Invalid JSON: {e}")
            return
    else:
        return
    is_valid, err = validate_mcp_structure({"mcpServers": {server_name: server_data}})
    if not is_valid:
        print(f"{t('err')} 2: Schema error: {err}")
        return
    lib[server_name] = server_data
    ok, werr = write_json_file(LIBRARY_FILE, {"mcpServers": lib})
    if not ok:
        print(f"{t('err')} 3: Library write failed: {werr}")
        return
    print(f"\n{t('ok')} '{server_name}' added to library.")
    assign = input(f"{t('ask_assign')} ").strip().lower()
    if assign in ("y", "e"):
        manage_profiles_interactive(preselect_server=server_name)

def manage_profiles_interactive(preselect_server=None):
    lib = get_all_servers_from_library()
    if not lib:
        print(f"\n{t('warn')} No servers in library. Add a server first.")
        return
    profiles = sorted([p for p in PROFILES_DIR.glob("*.json") if p.name not in ("library.json", "active_targets.json")])
    print(f"\n{t('edit_title')}")
    for idx, p in enumerate(profiles, 1):
        print(f"{idx}. {p.stem}")
    print(f"{len(profiles) + 1}. [Create New Profile]")
    p_choice = input(f"{t('choice')} (1-{len(profiles) + 1}): ").strip()
    if not p_choice.isdigit():
        return
    p_num = int(p_choice)
    is_new = (p_num == len(profiles) + 1)
    if is_new:
        raw_name = input("New profile name: ").strip().lower()
        profile_name = sanitize_name(raw_name)
        if not profile_name:
            print(f"{t('err')} 1: Invalid profile name.")
            return
        selected_servers = {}
    elif 1 <= p_num <= len(profiles):
        profile_name = profiles[p_num - 1].stem
        data, err = read_json_file(profiles[p_num - 1])
        selected_servers = data.get("mcpServers", {}) if isinstance(data, dict) else {}
    else:
        return
    if preselect_server and preselect_server in lib:
        selected_servers[preselect_server] = lib[preselect_server]
    server_list = list(lib.keys())
    print(f"\n--- SELECT SERVERS FOR '{profile_name}' ---")
    for idx, s_name in enumerate(server_list, 1):
        active = "[X]" if s_name in selected_servers else "[ ]"
        s_cmd = lib[s_name].get("command", "")
        ok, res = check_command_installed(s_cmd)
        note = "" if ok else f" ({t('cmd_missing')})"
        print(f"{idx}. {active} {s_name}{note}")
    print(f"{t('prompt_select_servers')}:")
    selection = input("> ").strip().lower()
    if not selection:
        if is_new and not selected_servers:
            print(f"{t('warn')} {t('aborted')}")
            return
        new_mcp = selected_servers
    elif selection == "all":
        new_mcp = lib
    else:
        new_mcp = {}
        for part in selection.split(","):
            part = part.strip()
            if part.isdigit():
                val = int(part)
                if 1 <= val <= len(server_list):
                    s_key = server_list[val - 1]
                    new_mcp[s_key] = lib[s_key]
    profile_path = PROFILES_DIR / f"{profile_name}.json"
    ok, werr = write_json_file(profile_path, {"mcpServers": new_mcp})
    if not ok:
        print(f"{t('err')} 3: Failed to save profile: {werr}")
        return
    print(f"\n{t('ok')} {t('saved')}: {profile_path}")
    activate = input(f"{t('ask_activate')} ").strip().lower()
    if activate in ("y", "e"):
        switch_profile(profile_name)

def clone_profile(source_name, target_name):
    clean_src = sanitize_name(source_name)
    clean_dst = sanitize_name(target_name)
    if not clean_src or not clean_dst:
        print(f"{t('err')} 1: Invalid profile name.", file=sys.stderr)
        return EXIT_NOT_FOUND
    src_file = PROFILES_DIR / f"{clean_src}.json"
    dst_file = PROFILES_DIR / f"{clean_dst}.json"
    if not src_file.exists():
        print(f"{t('err')} 1: Source profile '{source_name}' not found.", file=sys.stderr)
        return EXIT_NOT_FOUND
    data, err = read_json_file(src_file)
    if err:
        print(f"{t('err')} 2: Corrupted source profile: {err}", file=sys.stderr)
        return EXIT_INVALID_DATA
    ok, werr = write_json_file(dst_file, data)
    if not ok:
        print(f"{t('err')} 3: Failed to clone profile: {werr}", file=sys.stderr)
        return EXIT_IO_ERROR
    print(f"{t('ok')} {t('cloned')}: '{clean_src}' -> '{clean_dst}'")
    return EXIT_OK

def enable_server_in_active_profile(server_name):
    lib = get_all_servers_from_library()
    clean_s = server_name.strip()
    if clean_s not in lib:
        print(f"{t('err')} 1: Server '{server_name}' not found in library.", file=sys.stderr)
        return EXIT_NOT_FOUND
    curr_name = get_current_profile_name()
    curr_file = PROFILES_DIR / f"{curr_name}.json"
    data, err = read_json_file(curr_file)
    if not isinstance(data, dict):
        data = {"mcpServers": {}}
    if "mcpServers" not in data or not isinstance(data["mcpServers"], dict):
        data["mcpServers"] = {}
    data["mcpServers"][clean_s] = lib[clean_s]
    write_json_file(curr_file, data)
    print(f"{t('ok')} Enabled '{clean_s}' in active profile '{curr_name}'.")
    return switch_profile(curr_name)

def disable_server_in_active_profile(server_name):
    curr_name = get_current_profile_name()
    curr_file = PROFILES_DIR / f"{curr_name}.json"
    data, err = read_json_file(curr_file)
    if not isinstance(data, dict) or "mcpServers" not in data or not isinstance(data["mcpServers"], dict):
        print(f"{t('warn')} Server '{server_name}' not active.")
        return EXIT_OK
    clean_s = server_name.strip()
    if clean_s in data["mcpServers"]:
        del data["mcpServers"][clean_s]
        write_json_file(curr_file, data)
        print(f"{t('ok')} Disabled '{clean_s}' in active profile '{curr_name}'.")
        return switch_profile(curr_name)
    print(f"{t('warn')} Server '{server_name}' was not active in '{curr_name}'.")
    return EXIT_OK

def export_profile(profile_name, safe=False):
    clean_name = sanitize_name(profile_name)
    if not clean_name:
        print(f"{t('err')} 1: Invalid profile name.", file=sys.stderr)
        return EXIT_NOT_FOUND
    p_file = PROFILES_DIR / f"{clean_name}.json"
    if not p_file.exists():
        print(f"{t('err')} 1: Profile '{profile_name}' not found.", file=sys.stderr)
        return EXIT_NOT_FOUND
    data, err = read_json_file(p_file)
    if err or not isinstance(data, dict):
        print(f"{t('err')} 2: Invalid profile data: {err}", file=sys.stderr)
        return EXIT_INVALID_DATA
    export_data = dict(data)
    if safe and "mcpServers" in export_data and isinstance(export_data["mcpServers"], dict):
        safe_servers = {}
        for s_name, s_spec in export_data["mcpServers"].items():
            if isinstance(s_spec, dict):
                spec_copy = dict(s_spec)
                if "env" in spec_copy and isinstance(spec_copy["env"], dict):
                    spec_copy["env"] = {k: "<REDACTED>" for k in spec_copy["env"]}
                safe_servers[s_name] = spec_copy
        export_data["mcpServers"] = safe_servers
    print(json.dumps(export_data, indent=2, ensure_ascii=False))
    return EXIT_OK

def rollback_backup(selected_ts=None):
    backups = sorted(BACKUPS_DIR.glob("*_backup_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not backups:
        print(f"{t('warn')} {t('no_backups_found')}")
        return EXIT_NOT_FOUND
    reg = get_client_registry()
    groups = {}
    for b in backups:
        parts = b.stem.split("_backup_")
        if len(parts) == 2:
            client, ts = parts[0], parts[1]
            if ts not in groups:
                groups[ts] = {}
            groups[ts][client] = b
    timestamps = sorted(groups.keys(), reverse=True)
    if not selected_ts:
        print(f"\n{t('rollback_title')}")
        for idx, ts in enumerate(timestamps, 1):
            cl_list = ", ".join(groups[ts].keys())
            print(f"{idx}. {ts} ({cl_list})")
        c = input(f"{t('choice')} (1-{len(timestamps)}): ").strip()
        if c.isdigit() and 1 <= int(c) <= len(timestamps):
            target_ts = timestamps[int(c) - 1]
        else:
            print(t("aborted"))
            return EXIT_OK
    else:
        target_ts = selected_ts.strip()
        if target_ts not in groups:
            print(f"{t('err')} 1: Backup timestamp '{selected_ts}' not found.", file=sys.stderr)
            return EXIT_NOT_FOUND
    restored_any = False
    for client_name, b_file in groups[target_ts].items():
        dst = reg.get(client_name)
        if dst:
            try:
                shutil.copy2(b_file, dst)
                print(f"  {t('sync')} {client_name:<10} <- {b_file.name}")
                restored_any = True
            except OSError as e:
                print(f"{t('warn')} Failed to restore {client_name}: {e}", file=sys.stderr)
    if restored_any:
        print(f"\n{t('ok')} {t('restored')}: {target_ts}")
        return EXIT_OK
    return EXIT_IO_ERROR

def delete_profile_interactive(name=None):
    if not name:
        profiles = sorted([p for p in PROFILES_DIR.glob("*.json") if p.name not in ("library.json", "active_targets.json")])
        if not profiles:
            print(f"\n{t('warn')} {t('none')}")
            return EXIT_OK
        print(f"\n{t('delete_p_title')}")
        for idx, p in enumerate(profiles, 1):
            print(f"{idx}. {p.stem}")
        c = input(f"{t('choice')} (1-{len(profiles)}): ").strip()
        if c.isdigit() and 1 <= int(c) <= len(profiles):
            target_file = profiles[int(c) - 1]
        else:
            print(t("aborted"))
            return EXIT_OK
    else:
        clean = sanitize_name(name)
        if not clean:
            print(f"{t('err')} 1: Invalid profile name.", file=sys.stderr)
            return EXIT_NOT_FOUND
        target_file = PROFILES_DIR / f"{clean}.json"
        if not target_file.exists():
            print(f"{t('err')} 1: Profile '{name}' not found.", file=sys.stderr)
            return EXIT_NOT_FOUND
    confirm = input(f"'{target_file.stem}': {t('ask_confirm_delete')} ").strip().lower()
    if confirm in ("y", "e"):
        is_active = (target_file.stem == get_current_profile_name())
        target_file.unlink(missing_ok=True)
        print(f"{t('ok')} {t('deleted')}: {target_file.stem}")
        if is_active:
            remaining = [p for p in PROFILES_DIR.glob("*.json") if p.name not in ("library.json", "active_targets.json")]
            fallback = remaining[0].stem if remaining else "default"
            CURRENT_PROFILE_FILE.write_text(fallback, encoding="utf-8")
            if remaining:
                switch_profile(fallback)
        return EXIT_OK
    print(t("aborted"))
    return EXIT_OK

def remove_server_interactive(name=None):
    lib = get_all_servers_from_library()
    if not lib:
        print(f"\n{t('warn')} {t('empty')}")
        return EXIT_OK
    if not name:
        print(f"\n{t('remove_s_title')}")
        s_keys = list(lib.keys())
        for idx, k in enumerate(s_keys, 1):
            print(f"{idx}. {k}")
        c = input(f"{t('choice')} (1-{len(s_keys)}): ").strip()
        if c.isdigit() and 1 <= int(c) <= len(s_keys):
            target_name = s_keys[int(c) - 1]
        else:
            print(t("aborted"))
            return EXIT_OK
    else:
        target_name = name.strip()
        if target_name not in lib:
            print(f"{t('err')} 1: Server '{target_name}' not in library.", file=sys.stderr)
            return EXIT_NOT_FOUND
    confirm = input(f"'{target_name}': {t('ask_confirm_delete')} ").strip().lower()
    if confirm in ("y", "e"):
        del lib[target_name]
        write_json_file(LIBRARY_FILE, {"mcpServers": lib})
        curr_p = get_current_profile_name()
        active_modified = False
        for p in PROFILES_DIR.glob("*.json"):
            if p.name in ("library.json", "active_targets.json"):
                continue
            p_data, err = read_json_file(p)
            if isinstance(p_data, dict) and "mcpServers" in p_data and target_name in p_data["mcpServers"]:
                del p_data["mcpServers"][target_name]
                write_json_file(p, p_data)
                if p.stem == curr_p:
                    active_modified = True
        print(f"{t('ok')} {t('deleted')}: '{target_name}'")
        if active_modified:
            switch_profile(curr_p)
        return EXIT_OK
    print(t("aborted"))
    return EXIT_OK

def change_language_interactive():
    print("\n--- SELECT LANGUAGE / DIL SECIN ---")
    langs = [
        ("en", "English"),
        ("tr", "Turkce"),
    ]
    for idx, (code, label) in enumerate(langs, 1):
        print(f"{idx}. {label} ({code})")
    c = input(f"{t('choice')} (1-{len(langs)}): ").strip()
    if c.isdigit():
        num = int(c)
        if 1 <= num <= len(langs):
            chosen_code = langs[num - 1][0]
            set_lang(chosen_code)
            print(f"[OK] Language set to {langs[num - 1][1]} ({chosen_code}).")

def interactive_menu():
    while True:
        current = get_current_profile_name()
        targets = get_enabled_targets()
        print(f"\n==========================================")
        print(f"  {t('menu_title')} ({t('active')}: {current.upper()})")
        print(f"  Targets: {', '.join(targets)} | Lang: {get_current_lang().upper()}")
        print(f"==========================================")
        print(t("menu_1"))
        print(t("menu_2"))
        print(t("menu_3"))
        print(t("menu_4"))
        print(t("menu_5"))
        print(t("menu_6"))
        print(t("menu_7"))
        print(t("menu_8"))
        print(t("menu_9"))
        print(t("menu_10"))
        print(t("menu_11"))
        print(t("menu_12"))
        print(t("menu_13"))
        print(t("menu_14"))
        print(t("menu_15"))
        try:
            choice = input(f"\n{t('choice')} (1-15): ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{t('non_interactive_help')}")
            return
        if choice == "1":
            profiles = list_profiles()
            if not profiles:
                print(t("none"))
                continue
            sel = input(f"{t('prompt_profile_name')}: ").strip()
            if sel.isdigit():
                idx = int(sel)
                if 1 <= idx <= len(profiles):
                    switch_profile(profiles[idx - 1].stem)
            elif sel:
                switch_profile(sel)
        elif choice == "2":
            add_server_interactive()
        elif choice == "3":
            manage_profiles_interactive()
        elif choice == "4":
            src = input("Source profile: ").strip()
            dst = input("New profile name: ").strip()
            clone_profile(src, dst)
        elif choice == "5":
            srv = input("Server to enable: ").strip()
            enable_server_in_active_profile(srv)
        elif choice == "6":
            srv = input("Server to disable: ").strip()
            disable_server_in_active_profile(srv)
        elif choice == "7":
            delete_profile_interactive()
        elif choice == "8":
            remove_server_interactive()
        elif choice == "9":
            rollback_backup()
        elif choice == "10":
            p = input("Profile to export: ").strip()
            safe_c = input("Mask API tokens? (y/n): ").strip().lower()
            export_profile(p, safe=(safe_c in ("y", "e")))
        elif choice == "11":
            manage_targets_interactive()
        elif choice == "12":
            show_status()
        elif choice == "13":
            lib = get_all_servers_from_library()
            print(f"\n{t('lib_title')}")
            for k, v in lib.items():
                cmd = v.get('command', '')
                ok, res = check_command_installed(cmd)
                note = "" if ok else f" [{t('cmd_missing')}]"
                print(f"- {k}: {cmd} {' '.join(v.get('args', []))}{note}".strip())
            if not lib:
                print(t("empty"))
            print()
        elif choice == "14":
            change_language_interactive()
        elif choice in ("15", "q", "exit"):
            break

def main():
    auto_bootstrap_initial_setup()
    if len(sys.argv) < 2:
        interactive_menu()
        return EXIT_OK
    cmd = sys.argv[1].lower()
    if cmd in ("version", "-v", "--version"):
        print(f"mcp-switch {VERSION}")
        return EXIT_OK
    elif cmd in ("list", "-l", "--list"):
        list_profiles()
        return EXIT_OK
    elif cmd in ("status", "-s", "--status"):
        return show_status()
    elif cmd in ("targets", "-t", "--targets"):
        manage_targets_interactive()
        return EXIT_OK
    elif cmd in ("lang", "--lang"):
        target_lang = sys.argv[2].lower() if len(sys.argv) >= 3 else ""
        if target_lang in TEXTS:
            set_lang(target_lang)
            print(f"{t('ok')} Language set to {target_lang}")
        else:
            change_language_interactive()
        return EXIT_OK
    elif cmd in ("add", "-a", "--add"):
        add_server_interactive()
        return EXIT_OK
    elif cmd in ("edit", "-e", "--edit"):
        manage_profiles_interactive()
        return EXIT_OK
    elif cmd in ("clone", "copy-profile"):
        if len(sys.argv) >= 4:
            return clone_profile(sys.argv[2], sys.argv[3])
        print("Usage: mcp-switch clone <source> <target>")
        return EXIT_NOT_FOUND
    elif cmd in ("enable", "use"):
        if len(sys.argv) >= 3:
            return enable_server_in_active_profile(sys.argv[2])
        print("Usage: mcp-switch enable <server_name>")
        return EXIT_NOT_FOUND
    elif cmd in ("disable", "unuse"):
        if len(sys.argv) >= 3:
            return disable_server_in_active_profile(sys.argv[2])
        print("Usage: mcp-switch disable <server_name>")
        return EXIT_NOT_FOUND
    elif cmd in ("export", "--export"):
        if len(sys.argv) >= 3:
            is_safe = ("--safe" in sys.argv or "-s" in sys.argv)
            return export_profile(sys.argv[2], safe=is_safe)
        print("Usage: mcp-switch export <profile_name> [--safe]")
        return EXIT_NOT_FOUND
    elif cmd in ("rollback", "restore"):
        if len(sys.argv) >= 3:
            return rollback_backup(sys.argv[2])
        return rollback_backup()
    elif cmd in ("delete-profile", "remove-profile"):
        if len(sys.argv) >= 3:
            return delete_profile_interactive(sys.argv[2])
        return delete_profile_interactive()
    elif cmd in ("remove-server", "delete-server"):
        if len(sys.argv) >= 3:
            return remove_server_interactive(sys.argv[2])
        return remove_server_interactive()
    elif cmd in ("help", "-h", "--help"):
        print("Usage:")
        print("  mcp-switch                     : Interactive menu")
        print("  mcp-switch --version           : Show version")
        print("  mcp-switch <profile>           : Switch to specified profile")
        print("  mcp-switch list                : List profiles")
        print("  mcp-switch status              : Show active status & health check")
        print("  mcp-switch targets             : Manage target clients")
        print("  mcp-switch lang [en|tr]        : Set language")
        print("  mcp-switch add                 : Add new server")
        print("  mcp-switch edit                : Edit/create profile")
        print("  mcp-switch clone <src> <dst>   : Clone a profile")
        print("  mcp-switch enable <server>     : Quick enable server in active profile")
        print("  mcp-switch disable <server>    : Quick disable server in active profile")
        print("  mcp-switch export <p> [--safe] : Export profile JSON (safe masks tokens)")
        print("  mcp-switch rollback [ts]       : Restore client configs from backup")
        print("  mcp-switch delete-profile <p>  : Delete a profile")
        print("  mcp-switch remove-server <s>   : Remove server from library and profiles")
        return EXIT_OK
    else:
        return switch_profile(cmd)

if __name__ == "__main__":
    sys.exit(main())
