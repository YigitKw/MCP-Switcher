import sys
import os
import json
import shutil
import re
import time
import subprocess
from pathlib import Path
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CONFIG_DIR = Path.home() / ".gemini" / "config"
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
        "targets_title": "--- CLIENT SYNC SETTINGS ---",
        "menu_title": "MCP SWITCHER",
        "menu_1": "1. Switch Profile",
        "menu_2": "2. Add New MCP Server",
        "menu_3": "3. Edit / Create Profile",
        "menu_4": "4. Manage Target Clients (Claude, Cursor, OpenCode, Codex, Gemini)",
        "menu_5": "5. View Status and Health Check",
        "menu_6": "6. List All Servers in Library",
        "menu_7": "7. Change Language",
        "menu_8": "8. Exit",
        "choice": "Your choice",
        "prompt_profile_name": "Target profile number or name",
        "prompt_select_servers": "Enter server numbers comma-separated (e.g. 1,3) or 'all'",
        "saved": "Saved successfully",
        "ask_activate": "Do you want to activate this profile now? (y/n)",
        "ask_assign": "Do you want to assign this server to a profile now? (y/n)",
        "cmd_warn_add": "Warning: Command is not found in PATH. Continue anyway? (y/n)",
        "auto_imported": "Auto-imported existing configuration into profile",
        "non_interactive_help": "Non-interactive mode detected. Use 'mcp-switch --help' for usage.",
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
        "targets_title": "--- ISTEMCI SENKRONIZASYON AYARLARI ---",
        "menu_title": "MCP SWITCHER",
        "menu_1": "1. Profil Degistir",
        "menu_2": "2. Yeni MCP Sunucusu Ekle",
        "menu_3": "3. Profil Duzenle / Olustur",
        "menu_4": "4. Hedef Istemcileri Yonet (Claude, Cursor, OpenCode, Codex, Gemini)",
        "menu_5": "5. Durum ve Saglik Raporu",
        "menu_6": "6. Tum Sunucu Kutuphanesini Listele",
        "menu_7": "7. Dil Degistir",
        "menu_8": "8. Cikis",
        "choice": "Seciminiz",
        "prompt_profile_name": "Gecmek istediginiz profil numarasi veya adi",
        "prompt_select_servers": "Aktif olmasini istediginiz numaralari virgul ile girin (orn: 1,3) veya 'all'",
        "saved": "Basariyla kaydedildi",
        "ask_activate": "Bu profili simdi aktif etmek ister misiniz? (e/h)",
        "ask_assign": "Bu sunucuyu bir profile simdi eklemek ister misiniz? (e/h)",
        "cmd_warn_add": "Uyari: Komut PATH'te bulunamadi. Yine de devam edilsin mi? (e/h)",
        "auto_imported": "Mevcut konfigurasyon profile otomatik aktarildi",
        "non_interactive_help": "Etkilesimsiz ortam algilandi. Kullanim icin 'mcp-switch --help'.",
    },
    "es": {
        "ok": "[OK]",
        "err": "[ERROR]",
        "warn": "[AVISO]",
        "sync": "[SINC]",
        "profile_active": "Perfil activado",
        "total_servers": "Servidores totales",
        "tools": "Herramientas",
        "none": "Ninguno",
        "empty": "Vacio",
        "active": "[ACTIVO]",
        "installed": "Instalado",
        "not_found": "No encontrado",
        "cmd_missing": "Comando no encontrado en PATH o disco",
        "cmd_ready": "Ejecutable encontrado",
        "docker_not_running": "Docker instalado pero el servicio no responde",
        "profiles_title": "--- PERFILES DISPONIBLES ---",
        "status_title": "--- ESTADO MCP ACTIVO ---",
        "sync_clients": "Clientes Sincronizados",
        "lib_title": "--- BIBLIOTECA MCP ---",
        "add_title": "--- ANADIR SERVIDOR MCP ---",
        "edit_title": "--- EDITAR / CREAR PERFIL ---",
        "targets_title": "--- CLIENTES OBJETIVO ---",
        "menu_title": "MCP SWITCHER",
        "menu_1": "1. Cambiar Perfil",
        "menu_2": "2. Anadir Servidor MCP",
        "menu_3": "3. Editar / Crear Perfil",
        "menu_4": "4. Gestionar Clientes (Claude, Cursor, OpenCode, Codex, Gemini)",
        "menu_5": "5. Ver Estado y Diagnostico",
        "menu_6": "6. Listar Biblioteca",
        "menu_7": "7. Cambiar Idioma",
        "menu_8": "8. Salir",
        "choice": "Su eleccion",
        "prompt_profile_name": "Numero o nombre del perfil",
        "prompt_select_servers": "Numeros separados por coma (ej: 1,3) o 'all'",
        "saved": "Guardado exitosamente",
        "ask_activate": "Desea activar este perfil ahora? (s/n)",
        "ask_assign": "Desea asignar a un perfil ahora? (s/n)",
        "cmd_warn_add": "Aviso: Comando no encontrado. Continuar? (s/n)",
        "auto_imported": "Configuracion existente importada al perfil",
        "non_interactive_help": "Modo no interactivo. Use 'mcp-switch --help'.",
    },
    "zh": {
        "ok": "[OK]",
        "err": "[错误]",
        "warn": "[警告]",
        "sync": "[同步]",
        "profile_active": "配置文件已激活",
        "total_servers": "服务器总数",
        "tools": "工具",
        "none": "无",
        "empty": "空",
        "active": "[活动]",
        "installed": "已安装",
        "not_found": "未找到",
        "cmd_missing": "在PATH或磁盘中未找到命令",
        "cmd_ready": "找到可执行文件",
        "docker_not_running": "Docker已安装但守护程序未运行",
        "profiles_title": "--- 可用配置文件 ---",
        "status_title": "--- 活动 MCP 状态 ---",
        "sync_clients": "已同步客户端",
        "lib_title": "--- MCP 库 ---",
        "add_title": "--- 添加新 MCP 服务器 ---",
        "edit_title": "--- 编辑 / 创建配置文件 ---",
        "targets_title": "--- 客户端同步设置 ---",
        "menu_title": "MCP SWITCHER",
        "menu_1": "1. 切换配置文件",
        "menu_2": "2. 添加新 MCP 服务器",
        "menu_3": "3. 编辑 / 创建配置文件",
        "menu_4": "4. 管理目标客户端 (Claude, Cursor, OpenCode, Codex, Gemini)",
        "menu_5": "5. 查看状态与诊断",
        "menu_6": "6. 列出库中所有服务器",
        "menu_7": "7. 更改语言",
        "menu_8": "8. 退出",
        "choice": "您的选择",
        "prompt_profile_name": "目标配置文件编号或名称",
        "prompt_select_servers": "输入逗号分隔的服务器编号 (如 1,3) 或 'all'",
        "saved": "保存成功",
        "ask_activate": "是否立即激活此配置文件? (y/n)",
        "ask_assign": "是否立即分配到配置文件? (y/n)",
        "cmd_warn_add": "警告: 未在PATH中找到命令。仍要继续吗? (y/n)",
        "auto_imported": "已将现有配置自动导入到配置文件",
        "non_interactive_help": "检测到非交互模式。使用 'mcp-switch --help' 查看用法。",
    },
    "ru": {
        "ok": "[OK]",
        "err": "[OSHIBKA]",
        "warn": "[VNIMANIE]",
        "sync": "[SINKH]",
        "profile_active": "Profil aktivirovan",
        "total_servers": "Vsego serverov",
        "tools": "Instrumenty",
        "none": "Net",
        "empty": "Pusto",
        "active": "[AKTIVEN]",
        "installed": "Ustanovlen",
        "not_found": "Ne nayden",
        "cmd_missing": "Komanda ne naydena v PATH ili na diske",
        "cmd_ready": "Fayl nayden",
        "docker_not_running": "Docker ustanovlen, no sluzhba ne zapushchena",
        "profiles_title": "--- DOSTUPNYE PROFILI ---",
        "status_title": "--- STATUS MCP ---",
        "sync_clients": "Sinkhronizirovannye klienty",
        "lib_title": "--- BIBLIOTEKA MCP ---",
        "add_title": "--- DOBAVIT SERVER MCP ---",
        "edit_title": "--- REDAKTIROVAT / SOZDAT PROFIL ---",
        "targets_title": "--- NASTROYKI KLIENTOV ---",
        "menu_title": "MCP SWITCHER",
        "menu_1": "1. Pereklyuchit profil",
        "menu_2": "2. Dobavit novyy MCP server",
        "menu_3": "3. Redaktirovat / Sozdat profil",
        "menu_4": "4. Upravlenie klientami (Claude, Cursor, OpenCode, Codex, Gemini)",
        "menu_5": "5. Proverit status i zdorove",
        "menu_6": "6. Spisok vseh serverov",
        "menu_7": "7. Izmenit yazyk",
        "menu_8": "8. Vyhod",
        "choice": "Vash vybor",
        "prompt_profile_name": "Nomer ili imya profilya",
        "prompt_select_servers": "Nomera cherez zapyatuyu (napr. 1,3) ili 'all'",
        "saved": "Uspeshno sohraneno",
        "ask_activate": "Aktivirovat etot profil seychas? (y/n)",
        "ask_assign": "Naznachit v profil seychas? (y/n)",
        "cmd_warn_add": "Vnimanie: Komanda ne naydena v PATH. Prodolzhit? (y/n)",
        "auto_imported": "Sushchestvuyushchaya konfiguratsiya importirovana v profil",
        "non_interactive_help": "Neinteraktivnyy rezhim. Ispolzuyte 'mcp-switch --help'.",
    },
    "de": {
        "ok": "[OK]",
        "err": "[FEHLER]",
        "warn": "[WARNUNG]",
        "sync": "[SYNC]",
        "profile_active": "Profil aktiviert",
        "total_servers": "Server insgesamt",
        "tools": "Tools",
        "none": "Keine",
        "empty": "Leer",
        "active": "[AKTIV]",
        "installed": "Installiert",
        "not_found": "Nicht gefunden",
        "cmd_missing": "Befehl nicht im PATH oder auf Festplatte gefunden",
        "cmd_ready": "Ausfuehrbare Datei gefunden",
        "docker_not_running": "Docker vorhanden, aber Dienst laeuft nicht",
        "profiles_title": "--- VERFUEGBARE PROFILE ---",
        "status_title": "--- AKTIVER MCP STATUS ---",
        "sync_clients": "Synchronisierte Clients",
        "lib_title": "--- MCP BIBLIOTHEK ---",
        "add_title": "--- NEUEN MCP SERVER HINZUFUEGEN ---",
        "edit_title": "--- PROFIL BEARBEITEN / ERSTELLEN ---",
        "targets_title": "--- CLIENT SYNCHRONISATION ---",
        "menu_title": "MCP SWITCHER",
        "menu_1": "1. Profil wechseln",
        "menu_2": "2. Neuen MCP Server hinzufuegen",
        "menu_3": "3. Profil bearbeiten / erstellen",
        "menu_4": "4. Clients verwalten (Claude, Cursor, OpenCode, Codex, Gemini)",
        "menu_5": "5. Status und Diagnose anzeigen",
        "menu_6": "6. Alle Server auflisten",
        "menu_7": "7. Sprache aendern",
        "menu_8": "8. Beenden",
        "choice": "Ihre Wahl",
        "prompt_profile_name": "Profilnummer oder Name",
        "prompt_select_servers": "Servernummern mit Komma getrennt (z.B. 1,3) oder 'all'",
        "saved": "Erfolgreich gespeichert",
        "ask_activate": "Dieses Profil jetzt aktivieren? (j/n)",
        "ask_assign": "Jetzt einem Profil zuweisen? (j/n)",
        "cmd_warn_add": "Warnung: Befehl nicht im PATH gefunden. Trotzdem fortfahren? (j/n)",
        "auto_imported": "Bestehende Konfiguration in Profil importiert",
        "non_interactive_help": "Nicht-interaktiver Modus. Verwenden Sie 'mcp-switch --help'.",
    },
    "fr": {
        "ok": "[OK]",
        "err": "[ERREUR]",
        "warn": "[ATTENTION]",
        "sync": "[SYNC]",
        "profile_active": "Profil active",
        "total_servers": "Total serveurs",
        "tools": "Outils",
        "none": "Aucun",
        "empty": "Vide",
        "active": "[ACTIF]",
        "installed": "Installe",
        "not_found": "Non trouve",
        "cmd_missing": "Commande introuvable dans PATH ou disque",
        "cmd_ready": "Executable trouve",
        "docker_not_running": "Docker est installe mais le service ne repond pas",
        "profiles_title": "--- PROFILS DISPONIBLES ---",
        "status_title": "--- STATUT MCP ACTIF ---",
        "sync_clients": "Clients synchronises",
        "lib_title": "--- BIBLIOTHEQUE MCP ---",
        "add_title": "--- AJOUTER SERVEUR MCP ---",
        "edit_title": "--- MODIFIER / CREER PROFIL ---",
        "targets_title": "--- CLIENTS CIBLES ---",
        "menu_title": "MCP SWITCHER",
        "menu_1": "1. Changer de profil",
        "menu_2": "2. Ajouter un serveur MCP",
        "menu_3": "3. Modifier / Creer un profil",
        "menu_4": "4. Gerer les clients (Claude, Cursor, OpenCode, Codex, Gemini)",
        "menu_5": "5. Voir le statut et diagnostics",
        "menu_6": "6. Lister la bibliotheque",
        "menu_7": "7. Changer de langue",
        "menu_8": "8. Quitter",
        "choice": "Votre choix",
        "prompt_profile_name": "Numero ou nom du profil",
        "prompt_select_servers": "Numeros separes par virgule (ex: 1,3) ou 'all'",
        "saved": "Enregistre avec succes",
        "ask_activate": "Activer ce profil maintenant? (o/n)",
        "ask_assign": "Assigner a un profil maintenant? (o/n)",
        "cmd_warn_add": "Attention: Commande introuvable dans PATH. Continuer quand meme? (o/n)",
        "auto_imported": "Configuration existante importee dans le profil",
        "non_interactive_help": "Mode non interactif. Utilisez 'mcp-switch --help'.",
    },
    "ar": {
        "ok": "[OK]",
        "err": "[KHATA]",
        "warn": "[TAHDHIR]",
        "sync": "[TADAMUN]",
        "profile_active": "Tamma taf'il al-milaf",
        "total_servers": "Ijmali al-khawadim",
        "tools": "Al-adawat",
        "none": "La yujad",
        "empty": "Farigh",
        "active": "[NASHIT]",
        "installed": "Muthabbat",
        "not_found": "Ghayr mawjud",
        "cmd_missing": "Al-amr ghayr mawjud fi PATH aw al-qurs",
        "cmd_ready": "Al-milaf al-tanfidhi mawjud",
        "docker_not_running": "Docker muthabbat lakin al-khidma la ta'mal",
        "profiles_title": "--- AL-MILAFAT AL-MUTAHAT ---",
        "status_title": "--- HALAT MCP AL-HALIYA ---",
        "sync_clients": "Al-umala al-mutadaminun",
        "lib_title": "--- MAKTABAT MCP ---",
        "add_title": "--- IDAFAT KHADIM MCP JADID ---",
        "edit_title": "--- TA'DIL / INSHA MILAF ---",
        "targets_title": "--- I'DADAT AL-TADAMUN ---",
        "menu_title": "MCP SWITCHER",
        "menu_1": "1. Taghyir al-milaf",
        "menu_2": "2. Idafat khadim MCP jadid",
        "menu_3": "3. Ta'dil / Insha milaf",
        "menu_4": "4. Idarat al-umala (Claude, Cursor, OpenCode, Codex, Gemini)",
        "menu_5": "5. 'Ard al-hala wa al-fahs",
        "menu_6": "6. Qaimat jami' al-khawadim",
        "menu_7": "7. Taghyir al-lugha",
        "menu_8": "8. Khuruj",
        "choice": "Ikhtiyaruka",
        "prompt_profile_name": "Raqm aw ism al-milaf",
        "prompt_select_servers": "Arqam mafsula bifasila (mithl: 1,3) aw 'all'",
        "saved": "Tamma al-hifz binajah",
        "ask_activate": "Hal turid taf'il al-milaf al-an? (y/n)",
        "ask_assign": "Hal turid ta'yin al-khadim li milaf al-an? (y/n)",
        "cmd_warn_add": "Tahdhir: Al-amr ghayr mawjud. Al-istimrar? (y/n)",
        "auto_imported": "Tamma istirad al-i'dadat al-haliya ila al-milaf",
        "non_interactive_help": "Wad' ghayr tafa'uli. Istakhdim 'mcp-switch --help'.",
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
    for code in ("tr", "es", "zh", "ru", "de", "fr", "ar"):
        if code in system_lang:
            return code
    return "en"

def set_lang(lang_code):
    if lang_code in TEXTS:
        try:
            LANG_FILE.write_text(lang_code, encoding="utf-8")
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
    home = Path.home()
    if sys.platform == "win32":
        appdata = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
        claude_path = appdata / "Claude" / "claude_desktop_config.json"
    elif sys.platform == "darwin":
        claude_path = home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    else:
        claude_path = home / ".config" / "Claude" / "claude_desktop_config.json"
    return {
        "gemini": home / ".gemini" / "config" / "mcp_config.json",
        "claude": claude_path,
        "cursor": home / ".cursor" / "mcp.json",
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
            if sys.platform == "win32" and path.exists():
                try:
                    os.replace(str(tmp_path), str(path))
                except OSError:
                    shutil.move(str(tmp_path), str(path))
            else:
                shutil.move(str(tmp_path), str(path))
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
    existing_data, err = read_json_file(client_path)
    if isinstance(existing_data, dict):
        merged = dict(existing_data)
        merged["mcpServers"] = servers
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
        print(f"{t('ok')} {t('auto_imported')}: 'default' ({len(initial_servers)} {t('tools')})")

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
            if proceed not in ("y", "e", "s", "ja", "oui"):
                return
        raw_args = input("Args (space separated): ").strip()
        args = raw_args.split() if raw_args else []
        env_input = input("Env vars (KEY=VAL separated by comma): ").strip()
        env = {}
        if env_input:
            for item in env_input.split(","):
                if "=" in item:
                    k, v = item.split("=", 1)
                    env[k.strip()] = v.strip()
        server_data = {"command": cmd, "args": args}
        if env:
            server_data["env"] = env
    elif choice == "2":
        raw_name = input("Server name: ").strip()
        server_name = sanitize_name(raw_name)
        if not server_name:
            print(f"{t('err')} 1: Invalid server name.")
            return
        print("Paste JSON in a single line:")
        raw_json = input().strip()
        try:
            parsed = json.loads(raw_json)
            server_data = parsed.get(server_name, parsed)
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
    if assign in ("y", "e", "s", "ja", "oui"):
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
    if p_num == len(profiles) + 1:
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
    server_list = list(lib.keys())
    print(f"\n--- SELECT SERVERS FOR '{profile_name}' ---")
    for idx, s_name in enumerate(server_list, 1):
        active = "[X]" if s_name in selected_servers or s_name == preselect_server else "[ ]"
        s_cmd = lib[s_name].get("command", "")
        ok, res = check_command_installed(s_cmd)
        note = "" if ok else f" ({t('cmd_missing')})"
        print(f"{idx}. {active} {s_name}{note}")
    print(f"{t('prompt_select_servers')}:")
    selection = input("> ").strip().lower()
    new_mcp = {}
    if selection == "all":
        new_mcp = lib
    elif selection:
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
    if activate in ("y", "e", "s", "ja", "oui"):
        switch_profile(profile_name)

def change_language_interactive():
    print("\n--- SELECT LANGUAGE / SELECCIONAR IDIOMA / SPRACHE WAEHLEN ---")
    langs = [
        ("en", "English"),
        ("tr", "Turkce"),
        ("es", "Espanol"),
        ("zh", "Zhongwen (Simplified Chinese)"),
        ("ru", "Russkiy"),
        ("de", "Deutsch"),
        ("fr", "Francais"),
        ("ar", "Al-Arabiyya"),
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
        try:
            choice = input(f"\n{t('choice')} (1-8): ").strip()
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
            manage_targets_interactive()
        elif choice == "5":
            show_status()
        elif choice == "6":
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
        elif choice == "7":
            change_language_interactive()
        elif choice in ("8", "q", "exit"):
            break

def main():
    auto_bootstrap_initial_setup()
    if len(sys.argv) < 2:
        interactive_menu()
        return EXIT_OK
    cmd = sys.argv[1].lower()
    if cmd in ("list", "-l", "--list"):
        list_profiles()
        return EXIT_OK
    elif cmd in ("status", "-s", "--status"):
        return show_status()
    elif cmd in ("targets", "-t", "--targets"):
        manage_targets_interactive()
        return EXIT_OK
    elif cmd in ("lang", "--lang"):
        if len(sys.argv) >= 3 and sys.argv[2] in TEXTS:
            set_lang(sys.argv[2])
            print(f"{t('ok')} Language set to {sys.argv[2]}")
        else:
            change_language_interactive()
        return EXIT_OK
    elif cmd in ("add", "-a", "--add"):
        add_server_interactive()
        return EXIT_OK
    elif cmd in ("edit", "-e", "--edit"):
        manage_profiles_interactive()
        return EXIT_OK
    elif cmd in ("help", "-h", "--help"):
        print("Usage:")
        print("  mcp-switch                     : Interactive menu")
        print("  mcp-switch <profile>           : Switch to specified profile")
        print("  mcp-switch list                : List profiles")
        print("  mcp-switch status              : Show active status & health check")
        print("  mcp-switch targets             : Manage target clients")
        print("  mcp-switch lang [en|tr|es|...] : Set language")
        print("  mcp-switch add                 : Add new server")
        print("  mcp-switch edit                : Edit/create profile")
        return EXIT_OK
    else:
        return switch_profile(cmd)

if __name__ == "__main__":
    sys.exit(main())
