**Instructions**
1.Use standard commands to run from week_3/project directory.
```text
pip install openai python-dotenv requests markdownify trafilatura textual
```
You can navigate to any previous session by clicking on the desired session title box from the side bar.
Title: After user write first prompt, the model is asked to generate a title based on that. The generated title is saved along with the session id.

Design Decisions: Any page of website that is read by agent, max character limit for that is set to 12000 words, increased by 4000 words from week 2.
Tui has 3 panels now, one is for chat, one is activity log and the third one is the panel to show all the previous chats. Clicking on these would go that chat's page.
The code is divided into suggested layout to ensure user readability.
I tried out multiple models from openrouter and have finally used gpt-oss 120 b for best performance.
Max iterations for react loop are 12 and the model is told about it in agents.md
The model whenever reads a paper saves it into notes folder, but it can be prompted to do so in normal web search as well.




Challenges: I tried solving a weird bug where the LLM whose knowledge cutoff is 2024 was prompted to answer queries about ipl 2026. Curiously it was able to answer the final winner and exact scores of the match using the tool web search but that query was not reflected on the serper activity log. 
Tried solving it by modifying code but didn't work, finally created another api key and it works normally.
File tools were difficult to implement but learned a lot of things from them.

