import subprocess
import sys
import os
import json
import tempfile
import shutil
from pathlib import Path

SCRIPT_PATH = Path(__file__).parent / "mcp_switch.py"

def run_isolated_cli(sandbox_dir, *args, stdin_text=None):
    env = dict(os.environ)
    env["MCP_SWITCH_HOME"] = str(sandbox_dir)
    env["MCP_SWITCH_APPDATA"] = str(Path(sandbox_dir) / "AppData" / "Roaming")
    cmd = [sys.executable, str(SCRIPT_PATH)] + list(args)
    proc = subprocess.run(
        cmd,
        input=stdin_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env
    )
    return proc.returncode, proc.stdout, proc.stderr

def test_isolated_nonexistent_profile(sandbox):
    code, out, err = run_isolated_cli(sandbox, "nonexistent_profile_xyz")
    assert code == 1, f"Expected code 1, got {code}"
    assert "1:" in err, f"Missing error text: {err}"

def test_isolated_path_traversal(sandbox):
    code, out, err = run_isolated_cli(sandbox, "../../etc/passwd")
    assert code == 1, f"Expected code 1, got {code}"
    assert "1:" in err, f"Missing error text: {err}"

def test_isolated_corrupt_json_profile(sandbox):
    profiles_dir = Path(sandbox) / ".gemini" / "config" / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    bad_file = profiles_dir / "bad_syntax.json"
    bad_file.write_text("{broken: json,", encoding="utf-8")
    code, out, err = run_isolated_cli(sandbox, "bad_syntax")
    assert code == 2, f"Expected code 2, got {code}"
    assert "2:" in err, f"Missing error text: {err}"

def test_isolated_safe_merge_on_corrupt_client_file(sandbox):
    gemini_config = Path(sandbox) / ".gemini" / "config" / "mcp_config.json"
    profiles_dir = Path(sandbox) / ".gemini" / "config" / "profiles"
    gemini_config.parent.mkdir(parents=True, exist_ok=True)
    profiles_dir.mkdir(parents=True, exist_ok=True)
    gemini_config.write_text("{corrupt client json: [", encoding="utf-8")
    valid_p = profiles_dir / "safe_test.json"
    valid_p.write_text(json.dumps({
        "mcpServers": {
            "srv": {"command": sys.executable, "args": ["-V"]}
        }
    }), encoding="utf-8")
    code, out, err = run_isolated_cli(sandbox, "safe_test")
    assert code == 3, f"Expected code 3 on corrupt client config merge, got {code}"
    content = gemini_config.read_text(encoding="utf-8")
    assert content == "{corrupt client json: [", "Corrupt client file was overwritten"

def test_isolated_non_destructive_merge(sandbox):
    gemini_config = Path(sandbox) / ".gemini" / "config" / "mcp_config.json"
    profiles_dir = Path(sandbox) / ".gemini" / "config" / "profiles"
    gemini_config.parent.mkdir(parents=True, exist_ok=True)
    profiles_dir.mkdir(parents=True, exist_ok=True)
    gemini_config.write_text(json.dumps({
        "editorTheme": "dracula",
        "keybindings": [1, 2, 3],
        "mcpServers": {}
    }), encoding="utf-8")
    test_p = profiles_dir / "valid_merge.json"
    test_p.write_text(json.dumps({
        "mcpServers": {
            "node_tool": {"command": sys.executable, "args": ["-V"]}
        }
    }), encoding="utf-8")
    code, out, err = run_isolated_cli(sandbox, "valid_merge")
    assert code == 0, f"Switch failed: {err}"
    data = json.loads(gemini_config.read_text(encoding="utf-8"))
    assert data.get("editorTheme") == "dracula"
    assert data.get("keybindings") == [1, 2, 3]
    assert "node_tool" in data.get("mcpServers", {})

def test_isolated_delete_profile(sandbox):
    profiles_dir = Path(sandbox) / ".gemini" / "config" / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    dummy_p = profiles_dir / "to_delete.json"
    dummy_p.write_text(json.dumps({"mcpServers": {}}), encoding="utf-8")
    code, out, err = run_isolated_cli(sandbox, "delete-profile", "to_delete", stdin_text="y\n")
    assert code == 0, f"Delete failed: {err}"
    assert not dummy_p.exists(), "Profile file was not deleted"

def test_isolated_remove_server(sandbox):
    lib_file = Path(sandbox) / ".gemini" / "config" / "profiles" / "library.json"
    lib_file.parent.mkdir(parents=True, exist_ok=True)
    lib_file.write_text(json.dumps({
        "mcpServers": {
            "srv_to_remove": {"command": "python", "args": []}
        }
    }), encoding="utf-8")
    code, out, err = run_isolated_cli(sandbox, "remove-server", "srv_to_remove", stdin_text="y\n")
    assert code == 0, f"Remove server failed: {err}"
    data = json.loads(lib_file.read_text(encoding="utf-8"))
    assert "srv_to_remove" not in data.get("mcpServers", {})

def test_isolated_shlex_spaces_and_quotes(sandbox):
    code, out, err = run_isolated_cli(
        sandbox,
        "add",
        stdin_text='1\nspaced_tool\npython\n"C:\\Program Files\\app\\tool.js" --flag "value with space"\nPORT=8080\nh\n'
    )
    assert code == 0, f"Add failed: {err}"
    lib_file = Path(sandbox) / ".gemini" / "config" / "profiles" / "library.json"
    data = json.loads(lib_file.read_text(encoding="utf-8"))
    assert "spaced_tool" in data.get("mcpServers", {})
    args = data["mcpServers"]["spaced_tool"]["args"]
    assert "C:\\Program Files\\app\\tool.js" in args or "C:/Program Files/app/tool.js" in args or any("Program Files" in a for a in args)

def run_all_tests():
    with tempfile.TemporaryDirectory() as temp_root:
        tests = [
            ("Isolated Nonexistent profile test", test_isolated_nonexistent_profile),
            ("Isolated Path traversal test", test_isolated_path_traversal),
            ("Isolated Corrupt JSON profile test", test_isolated_corrupt_json_profile),
            ("Isolated Safe merge on corrupt client file test", test_isolated_safe_merge_on_corrupt_client_file),
            ("Isolated Non-destructive merge test", test_isolated_non_destructive_merge),
            ("Isolated Delete profile test", test_isolated_delete_profile),
            ("Isolated Remove server test", test_isolated_remove_server),
            ("Isolated Shlex space handling test", test_isolated_shlex_spaces_and_quotes),
        ]
        passed = 0
        failed = 0
        print("\n--- TEST SUITE STARTED (FULLY ISOLATED) ---")
        for name, fn in tests:
            test_sandbox = Path(temp_root) / f"run_{name.replace(' ', '_')}"
            test_sandbox.mkdir(parents=True, exist_ok=True)
            try:
                fn(test_sandbox)
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
