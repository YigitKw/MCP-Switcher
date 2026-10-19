import subprocess
import sys
import os
import json
import tempfile
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
    code_inv, out_inv, err_inv = run_isolated_cli(sandbox, "delete-profile", "...")
    assert code_inv == 1, "Expected code 1 for invalid profile deletion"
    code, out, err = run_isolated_cli(sandbox, "delete-profile", "to_delete", stdin_text="y\n")
    assert code == 0, f"Delete failed: {err}"
    assert not dummy_p.exists(), "Profile file was not deleted"

def test_isolated_remove_server(sandbox):
    config_dir = Path(sandbox) / ".gemini" / "config"
    profiles_dir = config_dir / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    lib_file = profiles_dir / "library.json"
    active_cfg = config_dir / "mcp_config.json"
    active_profile_file = config_dir / "current_profile.txt"
    srv_dict = {
        "srv_to_remove": {"command": sys.executable, "args": ["-V"]},
        "srv_to_keep": {"command": sys.executable, "args": ["-V"]}
    }
    lib_file.write_text(json.dumps({"mcpServers": srv_dict}), encoding="utf-8")
    p_file = profiles_dir / "active_p.json"
    p_file.write_text(json.dumps({"mcpServers": srv_dict}), encoding="utf-8")
    active_profile_file.write_text("active_p", encoding="utf-8")
    active_cfg.write_text(json.dumps({"mcpServers": srv_dict}), encoding="utf-8")
    code, out, err = run_isolated_cli(sandbox, "remove-server", "srv_to_remove", stdin_text="y\n")
    assert code == 0, f"Remove server failed: {err}"
    lib_data = json.loads(lib_file.read_text(encoding="utf-8"))
    assert "srv_to_remove" not in lib_data.get("mcpServers", {})
    p_data = json.loads(p_file.read_text(encoding="utf-8"))
    assert "srv_to_remove" not in p_data.get("mcpServers", {})
    active_data = json.loads(active_cfg.read_text(encoding="utf-8"))
    assert "srv_to_remove" not in active_data.get("mcpServers", {}), "Active client config was not resynchronized"

def test_isolated_shlex_spaces_and_quotes(sandbox):
    expected_path = "C:\\Program Files\\app\\tool.js" if sys.platform == "win32" else "C:/Program Files/app/tool.js"
    stdin_input = f'1\nspaced_tool\n{sys.executable}\n"{expected_path}" --flag "value with space"\nPORT=8080\nh\n'
    code, out, err = run_isolated_cli(sandbox, "add", stdin_text=stdin_input)
    assert code == 0, f"Add failed: {err}"
    lib_file = Path(sandbox) / ".gemini" / "config" / "profiles" / "library.json"
    data = json.loads(lib_file.read_text(encoding="utf-8"))
    assert "spaced_tool" in data.get("mcpServers", {})
    args = data["mcpServers"]["spaced_tool"]["args"]
    assert args == [expected_path, "--flag", "value with space"], f"Quotes not stripped cleanly: {args}"

def test_isolated_nested_mcpservers_paste(sandbox):
    nested_json = '{\n  "mcpServers": {\n    "nested_tool": {\n      "command": "node",\n      "args": ["app.js"]\n    }\n  }\n}\n\n'
    stdin_input = f'2\nnested_tool\n{nested_json}h\n'
    code, out, err = run_isolated_cli(sandbox, "add", stdin_text=stdin_input)
    assert code == 0, f"Add with nested json failed: {err}"
    lib_file = Path(sandbox) / ".gemini" / "config" / "profiles" / "library.json"
    data = json.loads(lib_file.read_text(encoding="utf-8"))
    assert "nested_tool" in data.get("mcpServers", {})
    assert data["mcpServers"]["nested_tool"]["command"] == "node"

def test_isolated_lang_case_insensitive(sandbox):
    code, out, err = run_isolated_cli(sandbox, "lang", "TR")
    assert code == 0
    assert "[OK]" in out or "Language set to tr" in out
    lang_file = Path(sandbox) / ".gemini" / "config" / "lang.txt"
    assert lang_file.read_text(encoding="utf-8").strip() == "tr"

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
            ("Isolated Nested mcpServers paste test", test_isolated_nested_mcpservers_paste),
            ("Isolated Lang case-insensitive test", test_isolated_lang_case_insensitive),
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
