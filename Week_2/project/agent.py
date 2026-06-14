import os
import json
import asyncio
import requests
import webbrowser
import trafilatura
from urllib.parse import parse_qs, urlparse
from openai import AsyncOpenAI
from dotenv import load_dotenv

# MCP & HTTPx Imports
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.client.auth import OAuthClientProvider, TokenStorage
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata, OAuthToken

# Textual Imports
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, Input, RichLog
from textual.containers import Horizontal


load_dotenv()

openai_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)

MODEL = "openrouter/free"
MAX_ITERATIONS = 10


ALPHAXIV_MCP_URL = "https://api.alphaxiv.org/mcp/v1" 
TOKEN_FILE = ".alphaxiv_tokens.json"

#OAUTH

class FileTokenStorage(TokenStorage):
    def __init__(self):
        self.tokens: OAuthToken | None = None
        self.client_info: OAuthClientInformationFull | None = None
        if os.path.exists(TOKEN_FILE):
            try:
                data = json.loads(open(TOKEN_FILE).read())
                if data.get("tokens"):
                    self.tokens = OAuthToken(**data["tokens"])
                if data.get("client_info"):
                    self.client_info = OAuthClientInformationFull(**data["client_info"])
            except Exception:
                pass

    def _save(self):
        data = {}
        if self.tokens:
            data["tokens"] = self.tokens.model_dump(mode="json")
        if self.client_info:
            data["client_info"] = self.client_info.model_dump(mode="json")
        open(TOKEN_FILE, "w").write(json.dumps(data, indent=2))

    async def get_tokens(self) -> OAuthToken | None:
        return self.tokens

    async def set_tokens(self, tokens: OAuthToken) -> None:
        self.tokens = tokens
        self._save()

    async def get_client_info(self) -> OAuthClientInformationFull | None:
        return self.client_info

    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        self.client_info = client_info
        self._save()


# Local Tool Implementations 


def execute_web_search(query: str) -> str:
    
    api_key = os.environ.get("SERPER_API_KEY")
    
    try:
        response = requests.post("https://google.serper.dev/search",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": query, "num": 10},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data.get("organic", []):
            results.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
            })
        return json.dumps(results)
    
    except Exception as e:
        return json.dumps({"error": f"Search failed: {str(e)}"})

def execute_web_fetch(url: str) -> str:
   
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"}
        response = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
        response.raise_for_status()
        
        text = trafilatura.extract(response.text, include_comments=False, include_tables=True)
        if not text:
            return json.dumps({"error": "Cannot extract text from page"})
            
        max_chars = 8000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[...truncated]"
            
        return text
    except Exception as e:
        return json.dumps({"error": f"Fetch failed: {str(e)}"})

LOCAL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web in real time for current and latest information, facts and recent events. Returns titles, URLs, and snippets.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "The search query."}},
                "required": ["query"],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": "Fetch and read the full text content of a web page URL. Use after web_search to read full articles.",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string", "description": "The full URL to read."}},
                "required": ["url"],
            },
        },
    }
]


# Textual TUI Application


class ResearchAgentApp(App):
    CSS = """
    Horizontal { height: 1fr; }
    #chat-panel { width: 60%; border: solid #005f87; margin-right: 1;padding: 1 }
    #tool-panel { width: 40%; border: solid green; }
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
        super().__init__()
        self.system_prompt = {
            "role": "system", 
            "content": "You are the best research assistant. Formulate your answers by searching the web and reading academic papers. Provide references along with the answers"
        }
        self.conversation_history = [self.system_prompt]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            yield RichLog(id="chat-panel", wrap=True, markup=True)
            yield RichLog(id="tool-panel", wrap=True, markup=True)
        yield Input(placeholder="Type a message and press Enter...")
        yield Footer()


    def on_mount(self) -> None:
        
        self.query_one("#chat-panel").write("[bold cyan] Research Engine [/bold cyan]\n")
        self.query_one("#tool-panel").write("[bold yellow]Agentic Activity Log[/bold yellow]\n")

    def action_clear_display(self) -> None:
        self.query_one("#chat-panel", RichLog).clear()
        self.query_one("#tool-panel", RichLog).clear()
        self.query_one("#chat-panel").write("[dim]Display cleared, conversation history is preserved.[/dim]\n")

    def action_clear_history(self) -> None:
        self.conversation_history = [self.system_prompt]
        self.action_clear_display()
        self.query_one("#chat-panel").write("[dim]Conversation history is erased[/dim]\n")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        user_text = event.value.strip()
        if not user_text:
            return
            
        event.input.clear()
        
        chat_log = self.query_one("#chat-panel", RichLog)
        chat_log.write(f"\n[bold cyan][You][/bold cyan] {user_text}")
        
        self.conversation_history.append({"role": "user", "content": user_text})
        self.run_agent_loop()

    # --- Async OAuth Callbacks for the UI ---
    
    async def open_browser(self, auth_url: str) -> None:
        tool_log = self.query_one("#tool-panel", RichLog)
        tool_log.write(f"\n[bold yellow]OAuth Required[/bold yellow]")
        tool_log.write(f"[dim]Opening browser for AlphaXiv login...[/dim]")
        webbrowser.open(auth_url)

    async def wait_for_callback(self) -> tuple[str, str | None]:
        
        tool_log = self.query_one("#tool-panel", RichLog)
        code = state = None
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        async def handler(reader, writer):
            request_line = await reader.readline()
            req = request_line.decode('utf-8')
            try:
                path = req.split(' ')[1]
                params = parse_qs(urlparse(path).query)
                nonlocal code, state
                code = params.get("code", [None])[0]
                state = params.get("state", [None])[0]
                
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<h1>Authorized! You can close this tab and return to the terminal.</h1>"
                writer.write(response.encode('utf-8'))
                await writer.drain()
                writer.close()
                if not future.done():
                    future.set_result((code, state))
            except Exception:
                pass

        server = await asyncio.start_server(handler, 'localhost', 8765)
        tool_log.write("[dim]Waiting for browser callback on port 8765...[/dim]")
        
        async with server:
            code, state = await future
            
        if not code:
            raise RuntimeError("OAuth callback received no authorization code.")
        
        tool_log.write("[bold green]OAuth login successful![/bold green]")
        return code, state

    # --- Core Agent Loop ---

    @work(thread=False)
    async def run_agent_loop(self) -> None:
        chat_log = self.query_one("#chat-panel", RichLog)
        tool_log = self.query_one("#tool-panel", RichLog)
        
        tool_log.write("\n[dim]Initializing MCP connection...[/dim]") 
        
        storage = FileTokenStorage()
        
        # Initialize native OAuth Provider
        auth = OAuthClientProvider(
            server_url=ALPHAXIV_MCP_URL,
            client_metadata=OAuthClientMetadata(
                client_name="AlphaXiv Textual Agent",
                redirect_uris=["http://localhost:8765/callback"],
                grant_types=["authorization_code", "refresh_token"],
                response_types=["code"],
                scope="read",
            ),
            storage=storage,
            redirect_handler=self.open_browser,
            callback_handler=self.wait_for_callback,
        )
        
        try:
            # Connect using Streamable HTTP Transport
            async with httpx.AsyncClient(auth=auth, follow_redirects=True, timeout=60) as http:
                async with streamable_http_client(ALPHAXIV_MCP_URL, http_client=http) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        mcp_tools_req = await session.list_tools()
                        
                        mcp_tools = []
                        for tool in mcp_tools_req.tools:
                            mcp_tools.append({
                                "type": "function",
                                "function": {
                                    "name": tool.name,
                                    "description": tool.description,
                                    "parameters": tool.inputSchema,
                                },
                            })
                        
                        all_tools = LOCAL_TOOLS + mcp_tools
                        tool_log.write(f"[dim]Connected to AlphaXiv via OAuth. {len(all_tools)} tools active.[/dim]\n")

                        for iteration in range(MAX_ITERATIONS):
                            tool_log.write(f"[dim]Iteration {iteration+1}... thinking...[/dim]")
                            
                            response = await openai_client.chat.completions.create(
                                model=MODEL,
                                messages=self.conversation_history,
                                tools=all_tools,
                              
                            )
                            
                            message = response.choices[0].message
                            self.conversation_history.append(message)
                            
                            if not message.tool_calls:
                                final_text = message.content if message.content else "*(API returned a blank response. Please try again.)*"
                                chat_log.write(f"\n[bold cyan]Agent:[/bold cyan]\n{final_text}")
                                return
                                
                            for tool_call in message.tool_calls:
                                name = tool_call.function.name
                                args = json.loads(tool_call.function.arguments)
                                
                                tool_log.write(f"[bold magenta]Executing:[/bold magenta] {name}")
                                tool_log.write(f"[dim]{json.dumps(args, indent=2)}[/dim]")
                                
                                content = ""
                                if name == "web_search":
                                    content = execute_web_search(args.get("query", ""))
                                elif name == "web_fetch":
                                    content = execute_web_fetch(args.get("url", ""))
                                else:
                                    
                                    try:
                                        result = await session.call_tool(name, args)
                                        content = result.content[0].text if result.content else ""
                                    except Exception as e:
                                        content = json.dumps({"error": f"MCP execution failed: {str(e)}"})

                                tool_log.write(f"[dim]Result: {len(content)} chars returned.[/dim]\n")

                                
                                self.conversation_history.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "content": content,
                                })

                        chat_log.write("\n[bold red]System:[/bold red] Iteration limit reached without final answer.")
                        
        except Exception as e:
            err = e.exceptions[0] if hasattr(e, "exceptions") else e
            chat_log.write(f"\n[bold red]System Error:[/bold red] Agent loop crashed: {repr(err)}")


if __name__ == "__main__":
    ResearchAgentApp().run()