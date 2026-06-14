Installation and Running Instruction:

```text
pip install -r requirements.txt

python agent.py
```

**Description:** I have built a research agent that can search papers and web and give results real time.

agent loop: I have used oauth to connect to alphaxiv mcp sever. Using list.tools function the agent fetch the tools of alphaxiv mcp such as discover paper and get paper content.a
The all tools variable stores these tools along with the local tools I coded namely web_Search and web_fetch.
I have set the max iterations to be at 10, the agent sends the conversation history to openrouter along with all the tools available and their description of when to use them.
Any tool call is shown in agent log along with total characters returned alongwith.
any tool call made is also appended in conversation history along with content retrieved via the tool call for LLM.
I have used trafilatura for text extraction from the web page and set the limit of max characters at 8000. Additionally include comments have been set to false.
Finally the LLM arrives at the answer with all the above information.

**Design Decision:** The fetched pages are truncate by first 8000 characters that were fetched by trafilatura.
If llm fails to provide any output, it will be reflected that llms has failed to provide the answer, and that will not be appended in the conversation history.
System Prompt: I included that LLM is a top research tool and one of the key points of a research tools is always cite its findings which I included in the system prompt. Additionally also instructed to search the web and read papers.

This tool call pipeline with agentic loop was completely new to me. This week I learnt a lot from this. From debugging web fetch results by printing total characters returned or by understanding how to implement streaming in this complex scenario where agent calls tools as well along with the final answer.

**Things I would like to improve:** Implementing streaming in this case along with the additional bonus function save research note. Also I left llms.txt as it is used for root level page navigation and was not usefull in direct web fetch. In future I would enable check for llms.txt
