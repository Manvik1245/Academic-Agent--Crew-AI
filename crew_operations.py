import os
import shutil
import requests
from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task, LLM
from crewai.tools import tool
from mcp import StdioServerParameters
from crewai_tools import MCPServerAdapter
from crewai.tools import tool as crewai_tool
import streamlit as st
import time

os.environ["LITELLM_DROP_PARAMS"] = "True"
os.environ["LITELLM_DISABLE_PROMPT_CACHING"] = "True"

script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, '.env')
load_dotenv(dotenv_path=env_path)

NOTION_TOKEN = os.environ.get("NOTION_TOKEN") or os.environ.get("NOTION_API_TOKEN")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")


def get_notion_mcp():
    return None
    """
        url="https://mcp.notion.com/mcp",
        headers={"Authorization": f"Bearer {NOTION_TOKEN}"},
        extra_headers={"Notion-Version": "2022-06-28"}
    )

notion_mcp_server = get_notion_mcp()

    """
notion_mcp_server = StdioServerParameters(
    command="npx",
    args=["-y", "mcp-remote", "https://mcp.notion.com/mcp"],
    env={
        **os.environ,
        "NOTION_TOKEN": NOTION_TOKEN,
    },
)




def _notion_headers():
    if not NOTION_TOKEN:
        raise RuntimeError("NOTION_TOKEN or NOTION_API_TOKEN is not configured.")
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


@crewai_tool("Notion connection")
def notion_connection(_: str = ""):
    """List pages in the configured Notion database."""
    if not NOTION_DATABASE_ID:
        return {"error": "NOTION_DATABASE_ID is not configured."}
    try:
        response = requests.post(
            f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query",
            headers=_notion_headers(), json={}, timeout=20
        )
        response.raise_for_status()
        pages = []
        for page in response.json().get("results", []):
            title_property = next(
                (value for value in page.get("properties", {}).values() if value.get("type") == "title"),
                None,
            )
            title_items = title_property.get("title", []) if title_property else []
            title = title_items[0].get("plain_text", "No Title") if title_items else "No Title"
            pages.append(f"Title: {title}, Page ID: {page.get('id', '')}")
        return {"results": "\n".join(pages) or "No pages found."}
    except (requests.RequestException, RuntimeError) as exc:
        return {"error": f"Notion connection failed: {exc}"}


@crewai_tool("Notion page content")
def notion_page_content(page_id: str):
    """Retrieve paragraph content from a Notion page."""
    try:
        response = requests.get(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=_notion_headers(), timeout=20
        )
        response.raise_for_status()
        content = []
        for block in response.json().get("results", []):
            if block.get("type") == "paragraph":
                content.extend(item.get("plain_text", "") for item in block["paragraph"].get("rich_text", []))
        return {"content": "\n".join(content) or "The page has no paragraph content."}
    except (requests.RequestException, RuntimeError) as exc:
        return {"error": f"Notion page retrieval failed: {exc}"}


llm_config = LLM(
    model="gemini/gemini-3.1-flash-lite",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    temperature=0.1,
    max_tokens=600,
    timeout=15
)




def run_crew(query, chat_history=None):
    history = ""
    for entry in chat_history or []:
        history += (
            f"User: {entry['user']}\n"
            f"Assistant: {entry['response']}\n\n"
        )

    with MCPServerAdapter(notion_mcp_server) as notion_tools:
        print("Available tools:", [t.name for t in notion_tools])
        read = [
            t for t in notion_tools
            if t.name in {
               "notion_search", "notion_fetch"
            }
        ]
        try:
            print("Selected tools:", [t.name for t in read])
        except:
            raise RuntimeError("No Notion Tools are found")
        
        
        coding_agent = Agent(
    role="Coding Help Agent",
    goal="To assist in coding, algorithms, and data structures by guiding the user interactively.",
    backstory="An EX-FAANG senior developer training the user for coding exams.",
    llm=llm_config,
    verbose=True,
    max_iter=3,
    allow_delegation=False
    )

        academic_agent = Agent(
            role="Notion Academic Agent",
            goal="Retrieve relevant notes and study materials from Notion.",
            backstory="You help the user study using their Notion notes. For note requests, search Notion first using the lesson title or course name. Start without date filters and omit unused optional arguments. If no results appear, retry with broader keywords. Fetch matching pages with notion_fetch using the URLs returned by search. Check the lesson date in the fetched content, then summarize it and cite the source. Never summarize search snippets as full notes or invent content when retrieval fails.",
            tools=read,
            llm=llm_config,
            allow_delegation=False,
            max_iter=4,
            verbose=True,
        )

        task = Task(
            description=(
                "Use the previous conversation as context.\n\n"
                f"Previous conversation:\n{history or 'No previous messages.'}\n\n"
                f"Latest user request:\n{query}"
            ),
            expected_output="A helpful and accurate Markdown response.",
        )

        crew = Crew(
            agents=[coding_agent, academic_agent],
            tasks=[task],
            process=Process.hierarchical,
            manager_llm=llm_config,
            max_rpm=15,
            verbose=True,
        )

        for attempt in range(3):
            try:
                result = crew.kickoff(inputs={"query": query})
                if hasattr(result, 'raw') and result.raw:
                    return result.raw
            except Exception as e:
                if "429" in str(e) or "rate_limit" in str(e).lower():
                    time.sleep(8)
                else:
                    raise e
    return "Error: Request rate limit exceeded. Please try again in a few seconds."



