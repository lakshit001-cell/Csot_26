import json
TODO_LIST = []

def todo_write(items: list) -> str:
    global TODO_LIST
    for new_item in items:
        if new_item.get("status") == "completed":
            evidence = str(new_item.get("evidence", "")).lower()
            if "0" not in evidence and "pass" not in evidence:
                return json.dumps({"error": f"Cannot mark {new_item.get('id')} completed: verification command failed or missing. Provide an exit code 0."})
            
        existing = next((i for i in TODO_LIST if i["id"] == new_item["id"]), None)
        if existing:
            existing.update(new_item)
        else:
            TODO_LIST.append(new_item)
            
    return json.dumps({"todos": TODO_LIST})

def todo_list_exists() -> bool:
    return len(TODO_LIST) > 0

def all_items_completed() -> bool:
    return all(item.get("status") in ["completed", "blocked"] for item in TODO_LIST)

PLAN_TOOLS = [{
    "type": "function",
    "function": {
        "name": "todo_write",
        "description": "Record or update your task list for this request. Call this before starting multi-step work.",
        "parameters": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "content": {"type": "string", "description": "What this subtask is."},
                            "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "blocked"]},
                            "evidence": {"type": "string", "description": "Exit code evidence required if status is completed."}
                        },
                        "required": ["id", "content", "status"]
                    }
                }
            },
            "required": ["items"]
        }
    }
}]