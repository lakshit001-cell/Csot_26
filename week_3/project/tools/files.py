
import os
import glob
import json

WORKSPACE_ROOT = os.path.abspath(os.environ.get("WORKSPACE_ROOT", "."))

def resolve_path(safe_path: str) -> str:
    
    full_path = os.path.abspath(os.path.join(WORKSPACE_ROOT, safe_path))
    if not full_path.startswith(WORKSPACE_ROOT):
        raise PermissionError("Access denied: Path escapes workspace root.")
    return full_path

def tool_list_files(pattern: str = "*") -> str:
  
    try:
        safe_pattern = os.path.join(WORKSPACE_ROOT, pattern)
        
        if not os.path.abspath(safe_pattern).startswith(WORKSPACE_ROOT):
            return json.dumps({"error": "Path escaping attempt detected."})
            
        matches = glob.glob(safe_pattern, recursive=True)
        
        rel_paths = [os.path.relpath(m, WORKSPACE_ROOT) for m in matches if os.path.isfile(m)]
        return json.dumps({"content": rel_paths})
    except Exception as e:
        return json.dumps({"error": str(e)})

def tool_read_file(path: str, start_line: int = 1, read_lines: int = 200) -> str:
  
    try:
        full_path = resolve_path(path)
        if not os.path.exists(full_path):
            return json.dumps({"error": f"File not found: {path}"})
            
        with open(full_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        total_lines = len(lines)
        start_idx = max(0, start_line - 1)
        end_idx = min(total_lines, start_idx + read_lines)
        
        window = lines[start_idx:end_idx]
        formatted_lines = []
        for i, line_content in enumerate(window):
            line_num = start_idx + i + 1
            formatted_lines.append(f"{line_num:5}| {line_content}")
            
        content_str = "".join(formatted_lines)
        
        # Max character truncation safety net
        max_chars = 12000
        if len(content_str) > max_chars:
            content_str = content_str[:max_chars] + "\n\n[...truncated ]"
            
        has_more = end_idx < total_lines
        
        return json.dumps({
            "content": content_str,
            "metadata": {
                "total_lines": total_lines,
                "start_line": start_line,
                "end_line": end_idx,
                "has_more": has_more
            }
        })
    except Exception as e:
        return json.dumps({"error": str(e)})

def tool_write_file(path: str, content: str) -> str:
   
    try:
        full_path = resolve_path(path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return json.dumps({"content": f"Successfully wrote file to {path}"})
    except Exception as e:
        return json.dumps({"error": str(e)})

def tool_edit_file(path: str, operation: str, start_line: int, end_line: int = None, content: str = "") -> str:
   
    try:
        full_path = resolve_path(path)
        if not os.path.exists(full_path):
            return json.dumps({"error": f"File not found: {path}"})
            
        with open(full_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        new_lines = list(lines)
        diff_preview = []
        
        # Adjust 1-indexed to 0-indexed Python structures safely
        s_idx = start_line - 1
        e_idx = end_line - 1 if end_line is not None else s_idx
        
        input_lines = [l + '\n' if not l.endswith('\n') else l for l in content.splitlines()] if content else []
        
        if operation == "replace":
            if s_idx < 0 or e_idx >= len(lines) or s_idx > e_idx:
                return json.dumps({"error": "Invalid line ranges specified for replacement."})
            
           
            for i in range(s_idx, e_idx + 1):
                diff_preview.append(f"- {lines[i].rstrip()}")
            for l in input_lines:
                diff_preview.append(f"+ {l.rstrip()}")
                
            new_lines[s_idx:e_idx + 1] = input_lines
            
        elif operation == "delete":
            if s_idx < 0 or e_idx >= len(lines) or s_idx > e_idx:
                return json.dumps({"error": "Invalid line ranges specified for deletion."})
                
            for i in range(s_idx, e_idx + 1):
                diff_preview.append(f"- {lines[i].rstrip()}")
                
            del new_lines[s_idx:e_idx + 1]
            
        elif operation == "append":
            
            if start_line == 0:
                for l in input_lines:
                    diff_preview.append(f"+ {l.rstrip()}")
                new_lines = input_lines + new_lines
            else:
                if s_idx < 0 or s_idx >= len(lines):
                    return json.dumps({"error": "Start line out of bounds for append operation."})
                diff_preview.append(f"  [After line {start_line}: {lines[s_idx].strip()}]")
                for l in input_lines:
                    diff_preview.append(f"+ {l.rstrip()}")
                new_lines[s_idx + 1:s_idx + 1] = input_lines
        else:
            return json.dumps({"error": f"Unknown operation: {operation}"})
            
        with open(full_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
            
        return json.dumps({
            "content": f"Successfully updated {path}",
            "diff_preview": "\n".join(diff_preview)
        })
    except Exception as e:
        return json.dumps({"error": str(e)})

FILE_TOOLS_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List existing workspace files matching a standard Unix glob string pattern.",
            "parameters": {
                "type": "object",
                "properties": {"pattern": {"type": "string", "description": "e.g. 'notes/*.md' or '**/*.py'"}},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads a page window of a file containing absolute line numbers. Useful before performing an edit, or when the user prompts to read a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "start_line": {"type": "integer", "default": 1},
                    "read_lines": {"type": "integer", "default": 200}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write or overwrite full files entirely. Best used when setting up new files or major clean rewrites.Whenever any new information comes up save that to a new file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Perform highly focused surgical modifications over line intervals. Returns an absolute preview diff of alterations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "operation": {"type": "string", "enum": ["replace", "delete", "append"]},
                    "start_line": {"type": "integer", "description": "1-indexed target starting line number. (Use 0 only to append at the absolute top of a file)"},
                    "end_line": {"type": "integer", "description": "Inclusive end line (Required for replace and delete)"},
                    "content": {"type": "string", "description": "Text payload to be injected (Required for replace and append)"}
                },
                "required": ["path", "operation", "start_line"]
            }
        }
    }
]