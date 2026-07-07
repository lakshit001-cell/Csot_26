# Research Desk Rules

## 1. Planning & The Todo Loop (`todo_write`)
- **When to use:** Call `todo_write` before starting *any* multi-step task to outline your plan, and call it again whenever an item's status changes[cite: 5].
- **Rule:** Do not batch updates to the end[cite: 5]. Update the list as you work.
- **Verification:** A todo item that changes code is not "completed" until the relevant verification command (e.g., the test suite) has actually exited `0`. You MUST cite the exit code as evidence in the todo item[cite: 5].
- **Stop Condition:** Once the plan is fully verified and marked `completed`, STOP. Do not re-verify or continue exploring.

## 2. Exploration & Finding Code
- **`list_files`:** Use this FIRST to understand the directory structure or find files matching a pattern (e.g., `*.py`).
 **Never** guess file paths or use raw shell commands like `ls`, `dir`, or custom Python `os.walk` scripts to explore directories. 
- **`run_command` (Search):** Prefer `run_command` (using standard `grep` or `find`) for broad keyword searches across the repository[cite: 5]. If `grep` returns zero results, try a broader term before reporting that something doesn't exist[cite: 5].
- **`read_file`:** Use this ONLY once you know the exact file path and roughly which lines matter[cite: 5]. Do not use this to blindly read a 2,000-line file top-to-bottom. If a test traceback gives you a file and line number, use `read_file` immediately.

## 3. Editing & Verifying Changes
- **`edit_file`:** Prefer `edit_file` over `run_command` for precise, line-level changes[cite: 5]. It is safer and returns a diff preview.
- **`write_file`:** Use this only when creating brand new files or doing major, complete file rewrites. 
- **`run_command` (Execution):** Use this to run test suites (e.g., `pytest`, `python -m unittest`), linters, or check git history[cite: 5]. 
- **Safety Expectations:** Expect destructive commands, unclassified shell commands, and ANY `edit_file`/`write_file` operation to pause for human approval[cite: 5]. That is normal, not an error[cite: 5]. Do not try to bypass the human or apologize for the pause.

again never write ls/dir commands

## Citations
- Include source URLs inline: [title](url)
- For papers: cite as [title](https://arxiv.org/abs/{arxiv_id})
- Prefer primary sources (papers, official docs) over blog posts

## Papers (required tools)
- Use `paper_search` when the user prompts about research paper or you need to see papers, no web search for these tasks.
- Use `read_paper` with the arxiv_id from search results — do not guess IDs
- If `read_paper` returns 404, fall back to `web_fetch` on arxiv.org/abs/...
- Do not use web_search when paper_search is the right tool

## Research notes
- Save new content with `write_file` to `notes/`
- Update existing notes with `read_file` then `edit_file` — do not rewrite whole files unnecessarily
- Use `edit_file` operations: `append` for new sections, `replace` to revise, `delete` to remove stale parts
- Keep edits inside `notes/` unless the user explicitly asks otherwise
- Use lowercase hyphenated filenames: `notes/topic-name.md`

## Web search
- Use `web_search` before `web_fetch` for non-paper questions
- Do not fetch more than 3 pages per question unless the user asks for depth

## Tone
- Be concise in chat; put detail in the note files


exit_code: 0 do not keep continuing.

for an task which requires information, use the web search tool and wait for web fetch results. Do not fill in the details with your outdated data.
NOW YOUR DATA IS OUTDATED SINCE YOUR KNOWLEDGE CUTOFF IS OLD, NEVER GIVE YOUR DATA TO USER, SEARCH THE WEB GET FACTS AND THEN PROVIDE THE RESULTS. DO NOT DO MORE THAN 3 SEARCH AND FETCH FOR THE DATA.
USE SITES LIKE WIKIPIDEA FOR GENERAL INFORMATION.
