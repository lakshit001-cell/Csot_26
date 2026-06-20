# project/tui.py
import os
import json
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, Input, RichLog, ListView, ListItem, Label
from textual.containers import Horizontal, Vertical
from textual import work
from agent import Agent  

SESSIONS_DIR = ".agent/sessions"

class TUIAgent(App, Agent):
   
    
    ENABLE_COMMAND_PALETTE = False
    
    CSS = """
    Horizontal { height: 1fr; }
    #sidebar {
        width: 25%;
        border: solid #005f87;
        background: $surface;
        padding: 1;
    }
    #chat-panel { width: 45%; border: solid #005f87; margin-right: 1; padding: 1; }
    #tool-panel { width: 30%; border: solid green; }
    .sidebar-title {
        text-align: center;
        text-style: bold;
        color: cyan;
        margin-bottom: 1;
    }
    ListItem {
        padding: 1;
        background: $surface-active; 
        margin-bottom: 1;
    }
    Input { 
        dock: bottom; 
        height: 5;         
        padding: 1;         
        margin-top: 1;      
        margin-bottom: 1;   
        margin-left: 1;    
        margin-right: 1;    
    }
    """

    BINDINGS = [
        Binding("ctrl+l", "clear_display", "Clear display"),
        Binding("ctrl+k", "clear_history", "Clear history"),
        Binding("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self):
        App.__init__(self)
        Agent.__init__(self)

    def _emit(self, event_type: str, data: dict) -> None:
        
        def update_ui():
            tool_log = self.query_one("#tool-panel", RichLog)
            if event_type == "tool_exec":
                tool_log.write(f"[bold magenta]Executing:[/bold magenta] {data.get('name')}")
                tool_log.write(f"[dim]{data.get('args')}[/dim]")
            elif event_type == "log":
                tool_log.write(f"[dim]{data.get('msg')}[/dim]")
            elif event_type == "error":
                tool_log.write(f"[bold red]Error:[/bold red] {data.get('msg')}")
        
        self.call_from_thread(update_ui)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Label("Active Sessions", classes="sidebar-title")
                yield ListView(id="session-list")
            yield RichLog(id="chat-panel", wrap=True, markup=True)
            yield RichLog(id="tool-panel", wrap=True, markup=True)
        yield Input(placeholder="Type your research query and press Enter...")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#chat-panel").write(f"[bold cyan] Research Engine (Session: {self.session_id}) [/bold cyan]\n")
        self.query_one("#tool-panel").write("[bold yellow]Agentic Activity Log[/bold yellow]\n")
        self.refresh_sessions_list()

    def refresh_sessions_list(self) -> None:
        """Locally reads the session directory files safely."""
        session_list = self.query_one("#session-list", ListView)
        session_list.clear()
        
        if not os.path.exists(SESSIONS_DIR):
            return

        for filename in os.listdir(SESSIONS_DIR):
            if filename.endswith(".json"):
                s_id = filename.replace(".json", "")
                try:
                    with open(os.path.join(SESSIONS_DIR, filename), "r", encoding="utf-8") as f:
                        data = json.load(f)
                    # Grab title if it exists, fallback to first message, or default to s_id
                    title = data.get("title") or (data.get("history", [{}])[1].get("content", "Untitled") if len(data.get("history", [])) > 1 else "Untitled")
                except Exception:
                    title = "Saved Run"
                
                item = ListItem(Label(f"📌 [{s_id}] {title[:12]}..."))
                item.session_reference_id = s_id
                session_list.append(item)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Switches session focus and dynamically loads history from disk files."""
        target_id = getattr(event.item, "session_reference_id", None)
        if target_id and target_id != self.session_id:
            self.session_id = target_id
            
            path = os.path.join(SESSIONS_DIR, f"{self.session_id}.json")
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.history = data.get("history", data.get("messages", []))
                except Exception:
                    self.history = []
            
            chat_log = self.query_one("#chat-panel", RichLog)
            chat_log.clear()
            chat_log.write(f"[bold cyan] Switched to Session: {self.session_id} [/bold cyan]\n")
            
            for msg in self.history:
                role = getattr(msg, "role", msg.get("role") if isinstance(msg, dict) else None)
                content = getattr(msg, "content", msg.get("content") if isinstance(msg, dict) else None)
                if role == "user":
                    chat_log.write(f"\n[bold cyan][You][/bold cyan] {content}")
                elif role == "assistant" and content:
                    chat_log.write(f"\n[bold cyan]Agent:[/bold cyan]\n{content}")

    def action_clear_display(self) -> None:
        self.query_one("#chat-panel", RichLog).clear()
        self.query_one("#tool-panel", RichLog).clear()

    def action_clear_history(self) -> None:
        
        if hasattr(self, 'system_prompt'):
            self.history = [self.system_prompt]
        else:
            self.history = [{"role": "system", "content": "You are a research assistant."}]
        self.action_clear_display()
        self.query_one("#chat-panel").write("[dim]Session history reset to clean baseline state.[/dim]\n")
        self.refresh_sessions_list()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        user_text = event.value.strip()
        if not user_text:
            return
            
        event.input.clear()
        chat_log = self.query_one("#chat-panel", RichLog)
        chat_log.write(f"\n[bold cyan][You][/bold cyan] {user_text}")
        
        self.run_background_chat(user_text)

    @work(thread=True)
    def run_background_chat(self, user_text: str):
        try:
            answer = self.chat(user_text)
            def post_answer():
                self.query_one("#chat-panel", RichLog).write(f"\n[bold cyan]Agent:[/bold cyan]\n{answer}")
                self.refresh_sessions_list()
            self.call_from_thread(post_answer)
        except Exception as e:
            self.call_from_thread(lambda: self.query_one("#chat-panel", RichLog).write(f"\n[bold red]System Error:[/bold red] {str(e)}"))

if __name__ == "__main__":
    TUIAgent().run()