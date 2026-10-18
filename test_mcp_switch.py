import subprocess
import sys
import os
import json
import tempfile
import shutil
from pathlib import Path

SCRIPT_PATH = Path(__file__).parent / "mcp_switch.py"

def run_cli(*args):
    cmd = [sys.executable, str(SCRIPT_PATH)] + list(args)
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return proc.returncode, proc.stdout, proc.stderr

def test_nonexistent_profile():
    code, out, err = run_cli("kesinlikle_yok_profil_xyz")
    assert code == 1, f"Expected 1, got {code}"
    assert "1:" in err, f"Error message missing: {err}"

def test_path_traversal():
    code, out, err = run_cli("../../etc/passwd")
    assert code == 1, f"Expected 1, got {code}"
    assert "1:" in err, f"Error message missing: {err}"

def test_corrupt_json_profile():
    profiles_dir = Path.home() / ".gemini" / "config" / "profiles"
    bad_file = profiles_dir / "test_corrupt.json"
    try:
        bad_file.write_text("{invalid json string}", encoding="utf-8")
        code, out, err = run_cli("test_corrupt")
        assert code == 2, f"Expected 2, got {code}"
        assert "2:" in err, f"Error message missing: {err}"
    finally:
        bad_file.unlink(missing_ok=True)

def test_missing_command_warning():
    profiles_dir = Path.home() / ".gemini" / "config" / "profiles"
    missing_cmd_file = profiles_dir / "test_missing_exec.json"
    try:
        missing_cmd_file.write_text(json.dumps({
            "mcpServers": {
                "ghost_tool": {
                    "command": "this_binary_does_not_exist_anywhere_123",
                    "args": []
                }
            }
        }), encoding="utf-8")
        code, out, err = run_cli("test_missing_exec")
        assert code == 0, f"Expected 0 (switch succeeds with warning), got {code}"
        assert "this_binary_does_not_exist_anywhere_123" in out
    finally:
        missing_cmd_file.unlink(missing_ok=True)

def test_non_destructive_client_config_merge():
    cursor_file = Path.home() / ".cursor" / "mcp.json"
    profiles_dir = Path.home() / ".gemini" / "config" / "profiles"
    test_p = profiles_dir / "test_merge.json"
    try:
        cursor_file.parent.mkdir(parents=True, exist_ok=True)
        cursor_file.write_text(json.dumps({
            "theme": "dark",
            "customSetting": 12345,
            "mcpServers": {}
        }), encoding="utf-8")
        test_p.write_text(json.dumps({
            "mcpServers": {
                "merge_test_srv": {
                    "command": sys.executable,
                    "args": ["-V"]
                }
            }
        }), encoding="utf-8")
        code, out, err = run_cli("test_merge")
        assert code == 0, f"Failed switch: {err}"
        updated_cursor = json.loads(cursor_file.read_text(encoding="utf-8"))
        assert updated_cursor.get("theme") == "dark", "Non-MCP settings were wiped out"
        assert updated_cursor.get("customSetting") == 12345, "Custom setting was wiped out"
        assert "merge_test_srv" in updated_cursor.get("mcpServers", {}), "New MCP server missing"
    finally:
        test_p.unlink(missing_ok=True)

def test_all_languages_toggle():
    langs = ["en", "tr", "es", "zh", "ru", "de", "fr", "ar"]
    for lang in langs:
        code, out, err = run_cli("lang", lang)
        assert code == 0, f"Language switch failed for {lang}: {err}"
        code_s, out_s, err_s = run_cli("status")
        assert code_s == 0, f"Status failed for {lang}: {err_s}"
    run_cli("lang", "tr")

def test_non_interactive_execution():
    cmd = [sys.executable, str(SCRIPT_PATH)]
    proc = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert proc.returncode == 0
    assert "mcp-switch --help" in proc.stdout

def test_valid_profile_switch():
    profiles_dir = Path.home() / ".gemini" / "config" / "profiles"
    valid_file = profiles_dir / "test_valid.json"
    active_file = Path.home() / ".gemini" / "config" / "mcp_config.json"
    try:
        valid_file.write_text(json.dumps({
            "mcpServers": {
                "test-server": {
                    "command": sys.executable,
                    "args": ["-V"],
                    "env": {
                        "PORT": 8080
                    }
                }
            }
        }), encoding="utf-8")
        code, out, err = run_cli("test_valid")
        assert code == 0, f"Expected 0, got {code}"
        data = json.loads(active_file.read_text(encoding="utf-8"))
        assert "test-server" in data["mcpServers"]
        assert data["mcpServers"]["test-server"]["env"]["PORT"] == "8080"
    finally:
        valid_file.unlink(missing_ok=True)

def run_all_tests():
    tests = [
        ("Nonexistent profile test", test_nonexistent_profile),
        ("Path traversal protection test", test_path_traversal),
        ("Corrupt JSON test", test_corrupt_json_profile),
        ("Missing executable health check warning test", test_missing_command_warning),
        ("Non-destructive client config merge test", test_non_destructive_client_config_merge),
        ("All 8 languages toggle test (EN, TR, ES, ZH, RU, DE, FR, AR)", test_all_languages_toggle),
        ("Non-interactive headless execution test", test_non_interactive_execution),
        ("Valid profile switch test with env coercion", test_valid_profile_switch),
    ]
    passed = 0
    failed = 0
    print("\n--- TEST SUITE STARTED ---")
    for name, fn in tests:
        try:
            fn()
            print(f"[PASSED] {name}")
            passed += 1
        except AssertionError as e:
            print(f"[FAILED] {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {name}: {e}")
            failed += 1
    print(f"\nResult: {passed} passed, {failed} failed.")
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_all_tests()
