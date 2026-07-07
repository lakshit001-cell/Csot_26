# project/tools/exec.py
import os
import subprocess
import shlex
import json

WORKSPACE_ROOT = os.path.abspath(os.environ.get("WORKSPACE_ROOT", "."))
READ_ONLY_ALLOWLIST = ["grep", "find", "ls", "cat", "head", "tail", "git", "pytest", "python -m unittest", "findstr", "dir", "type"]

def looks_like_a_path(token: str) -> bool:
    return "/" in token or token.startswith(".") or token.endswith(".py")

def paths_within_sandbox(command: str, workspace_root: str) -> bool:
    try:
        tokens = shlex.split(command)
        for token in tokens:
            if looks_like_a_path(token):
                abs_path = os.path.abspath(os.path.join(workspace_root, token))
                if not abs_path.startswith(os.path.abspath(workspace_root)):
                    return False
        return True
    except Exception:
        return False

def run_command(command: str, timeout: int = 10) -> str:
    if not paths_within_sandbox(command, WORKSPACE_ROOT):
        return json.dumps({"error": "blocked: command references a path outside the workspace"})

    base_cmd = command.split()[0] if command else ""
    is_read_only = any(command.startswith(ro) for ro in READ_ONLY_ALLOWLIST)

    if not is_read_only:
        print(f"\n[WARNING] The agent wants to run a command that may write, delete, or install files on the target repo:\n    {command}")
        approved = input("Allow this command? [y/N]: ").strip().lower() == "y"
        if not approved:
            return json.dumps({"error": "blocked: user did not approve this command"})

    try:
        result = subprocess.run(
            command, cwd=WORKSPACE_ROOT, shell=True, capture_output=True, text=True, timeout=timeout
        )
        stdout = result.stdout
        
        truncated = False
        if len(stdout) > 6000:
            stdout = stdout[:4000] + "\n...[truncated]"
            truncated = True

        return json.dumps({
            "stdout": stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
            "truncated": truncated
        })
    except subprocess.TimeoutExpired:
        return json.dumps({"error": f"Command timed out after {timeout} seconds."})
    except Exception as e:
        return json.dumps({"error": str(e)})

EXEC_TOOLS = [{
    "type": "function",
    "function": {
        "name": "run_command",
        "description": "Run a shell command in the workspace and return its output. Use this to search, inspect history, run tests, or execute scripts. Read-only commands run immediately. Commands that write, delete, or install will pause for approval.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to run."},
                "timeout": {"type": "integer", "description": "Seconds before the command is killed, default: 10."}
            },
            "required": ["command"]
        }
    }
}]