# project/agent.py
import os
import sys
import json
import uuid
from openai import OpenAI
from dotenv import load_dotenv
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '.env')
load_dotenv(env_path)


from tools.web import execute_web_search, execute_web_fetch, WEB_TOOLS
from tools.files import tool_list_files, tool_read_file, tool_write_file, tool_edit_file, FILE_TOOLS_SCHEMAS
from tools.papers import tool_paper_search, tool_read_paper, PAPERS_TOOLS_SCHEMAS



class Agent:
    def __init__(self, session_id: str = None):

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ.get("OPENROUTER_API_KEY"),
        )

        self.model = "openai/gpt-oss-120b:free"

        self.max_iterations = 12
        self.sessions_dir = os.path.abspath(".agent/sessions")
        os.makedirs(self.sessions_dir, exist_ok=True)
        
        
        self.system_prompt_content = self._load_procedural_memory_rules()
        self.history = [{"role": "system", "content": self.system_prompt_content}]
        
        
        self.available_tools = WEB_TOOLS + FILE_TOOLS_SCHEMAS + PAPERS_TOOLS_SCHEMAS
        self.session_title = None
        
        
        if session_id:
            self.session_id = session_id
            self._load_session_from_disk()
        else:
            self.session_id = str(uuid.uuid4())[:8]
            
    def _load_procedural_memory_rules(self) -> str:
        base_prompt = "You are the primary Research agent engine. Systematically parse documents, verify facts, and build research archives inside notes/. You have access to tools such as web search web fetch get and read papers etc. utilise them wisely"
        if os.path.exists("AGENTS.md"):
            try:
                with open("AGENTS.md", "r", encoding="utf-8") as f:
                    rules = f.read()
                return f"{base_prompt}\n\nStrict Guidelines (from AGENTS.md):\n{rules}"
            except Exception:
                pass
        return base_prompt

    def _load_session_from_disk(self):
        session_file = os.path.join(self.sessions_dir, f"{self.session_id}.json")
        if os.path.exists(session_file):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    saved_data = json.load(f)
                    self.history = saved_data.get("history", self.history)
                    self.session_title = saved_data.get("title") 
            except Exception as e:
                self._emit("error", {"msg": f"Failed loading session: {str(e)}"})

    def _save_session_to_disk(self):
        session_file = os.path.join(self.sessions_dir, f"{self.session_id}.json")
        try:
            
            safe_history = []
            for msg in self.history:
                if isinstance(msg, dict):
                    safe_history.append(msg)
                else:
                    safe_history.append(msg.model_dump()) # Converts OpenAI object to dict

           
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump({
                    "session_id": self.session_id, 
                    "title": self.session_title, 
                    "history": safe_history
                }, f, indent=2)
        except Exception as e:
            
            self._emit("error", {"msg": f"Failed to save session: {str(e)}"})
    def _emit(self, event_type: str, data: dict):
        
        pass

    def _generate_title(self, first_prompt: str) -> str:
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a title generator. Create a concise 5 word title for a chat session based on the user's prompt. Respond ONLY with the title, no quotes, no punctuation."},
                    {"role": "user", "content": first_prompt}
                ]
            )
            return response.choices[0].message.content.strip(' "')
        except Exception:
            return "Untitled Session"

    def chat(self, user_input: str) -> str:
        
        last_role = None
        if self.history:
            last_msg = self.history[-1]
            # If it's a dictionary, use .get()
            if isinstance(last_msg, dict):
                last_role = last_msg.get("role")
            else:
                last_role = getattr(last_msg, "role", None)

       
        if not self.history or last_role != "user":
            self.history.append({"role": "user", "content": user_input})
            if len(self.history) == 2 and not self.session_title:
                self._emit("log", {"msg": "Generating session title..."})
                self.session_title = self._generate_title(user_input)
            
        for iteration in range(self.max_iterations):
            self._emit("log", {"msg": f"Starting ReAct Iteration Loop Step {iteration + 1}..."})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.history,
                tools=self.available_tools
            )
            
            message = response.choices[0].message
            self.history.append(message)
            
            if not message.tool_calls:
                self._save_session_to_disk()
                return message.content if message.content else "Response empty."
                
            for tool_call in message.tool_calls:
                name = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments)
                except Exception:
                    args = {}
                    
                self._emit("tool_exec", {"name": name, "args": args})
                
               
                content = ""
                if name == "web_search":
                    content = execute_web_search(args.get("query", ""))
                elif name == "web_fetch":
                    content = execute_web_fetch(args.get("url", ""))
                elif name == "list_files":
                    content = tool_list_files(args.get("pattern", "*"))
                elif name == "read_file":
                    content = tool_read_file(
                        path=args.get("path"), 
                        start_line=args.get("start_line", 1), 
                        read_lines=args.get("read_lines", 200)
                    )
                elif name == "write_file":
                    content = tool_write_file(path=args.get("path"), content=args.get("content", ""))
                elif name == "edit_file":
                    content = tool_edit_file(
                        path=args.get("path"),
                        operation=args.get("operation"),
                        start_line=args.get("start_line"),
                        end_line=args.get("end_line"),
                        content=args.get("content", "")
                    )
                elif name == "paper_search":
                    content = tool_paper_search(args.get("query", ""))
                elif name == "read_paper":
                    content = tool_read_paper(args.get("arxiv_id", ""))
                else:
                    content = json.dumps({"error": f"Tool signature matching variant '{name}' not found."})
                    
                self.history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": content
                })
                
        self._save_session_to_disk()
        return "System iteration loop bounds hit limits before establishing final answer."

class REPLAgent(Agent):
    def _emit(self, event_type: str, data: dict):
        if event_type == "tool_exec":
            print(f"   [Tool Call] Executing -> {data['name']} with properties: {data['args']}")
        elif event_type == "error":
            print(f"   [Error Encountered] -> {data['msg']}")

    def run_once(self, query: str):
        print(f"Session Token Assigned: {self.session_id}")
        answer = self.chat(query)
        print(f"\nFinal Response:\n{answer}")

    def run(self):
        print(f"=== Research Desk Terminal REPL Active ===")
        print(f"Working Active Session Identifier: {self.session_id}")
        print("Type '/sessions' to view history records, '/resume <id>' to switch contexts, or 'exit' to log out.\n")
        
        while True:
            try:
                user_input = input("Research >>> ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["exit", "quit"]:
                    break
                    
                
                if user_input.startswith("/sessions"):
                    files = [f for f in os.listdir(self.sessions_dir) if f.endswith(".json")]
                    print("Available History Checkpoint Records:")
                    for f in files:
                        print(f" - {f.replace('.json', '')}")
                    continue
                    
                if user_input.startswith("/resume"):
                    parts = user_input.split()
                    if len(parts) > 1:
                        target_id = parts[1]
                        if os.path.exists(os.path.join(self.sessions_dir, f"{target_id}.json")):
                            self.session_id = target_id
                            self._load_session_from_disk()
                            print(f"Context systematically restored onto session profile: {self.session_id}")
                        else:
                            print("Specified context history save vector not found.")
                    continue
                
                answer = self.chat(user_input)
                print(f"\nResponse:\n{answer}\n")
                
            except (KeyboardInterrupt, EOFError):
                print("\nShutting down session logs...")
                break

if __name__ == "__main__":
    
    if len(sys.argv) > 1 and sys.argv[1] != "--tui":
        repl = REPLAgent()
        repl.run_once(sys.argv[1])
    elif len(sys.argv) > 1 and sys.argv[1] == "--tui":
        from tui import TUIAgent
        TUIAgent().run()
    else:
        repl = REPLAgent()
        repl.run()