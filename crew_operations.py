import os
import requests
from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task, LLM
from crewai.tools import tool
from concurrent.futures import ThreadPoolExecutor
import streamlit as st

os.environ["LITELLM_DROP_PARAMS"] = "True"
os.environ["LITELLM_DISABLE_PROMPT_CACHING"] = "True"

script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, '.env')
load_dotenv(dotenv_path=env_path)

NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
NOTION_API_TOKEN = os.environ.get("NOTION_API_TOKEN")

@st.cache_data(ttl=600)
def _fetch_notion_database():
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, json={})
    response.raise_for_status()
    return response.json()

@tool("Notion connection")
def notion_connection(dummy_input: str = ""):
    """Queries your Notion database to retrieve a list of page titles and IDs.
    Does not require arguments, but accepts an optional dummy string if needed."""
    try:
        data = _fetch_notion_database()
        results = data.get("results", [])
        complied = ""
        for result in results:
            properties = result.get("properties", {})
            page_id = result.get("id", "")
            title_prop = next((prop for prop in properties.values() if prop.get("type") == "title"), None)
            title_text = title_prop["title"][0].get("plain_text", "No Title") if (title_prop and title_prop.get("title")) else "No Title"
            complied += f"Title: {title_text}, Page ID: {page_id}\n"
        return {"results": complied}
    except Exception as e:
        return {"error": str(e)}

@tool("Notion page content")
def notion_page_content(page_id: str):
    """
    Retrieves the content of a specific Notion page given its exact Page ID.
    
    IMPORTANT: You MUST pass a valid 36-character Notion UUID (e.g. '37bd802e-23e0-81f5-9b15-e119b247dbae') 
    obtained from the 'Notion connection' tool. NEVER pass page title names or plain text strings as the page_id."""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {NOTION_API_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        complied_content = ""
        for block in data.get("results", []):
            block_type = block.get("type", "")
            block_content = block.get(block_type, {})
            if block_type == "paragraph":
                for item in block_content.get("text", []):
                    complied_content += item.get("plain_text", "") + "\n"
        return {"content": complied_content}
    except Exception as e:
        return {"error": str(e)}

def crew_operations(query):
    query_lower = query.lower()
    
    llm_config = LLM(
        model="llama-3.3-70b-versatile",
        api_key=os.environ.get("OPENROUTER_API_KEY"),
        base_url=os.environ.get("OPENAI_API_BASE"),
        temperature=0.1,
        max_tokens=1000,
        timeout=20
    )

    coding_agent = Agent(
        role="Coding Help Agent",
        goal="To assist in coding, algorithms, and data structures by guiding the user interactively.",
        backstory="An EX-FAANG senior developer training the user for coding exams.",
        tools=[],
        llm=llm_config,
            verbose=True,
            max_iter=2,
            allow_delegation=False
        )

    academic_agent = Agent(
            role="Notion Academic Agent",
            goal="To assist in academic preparation using Notion classnotes.",
            backstory="You are an academic assistant. Your ONLY source of truth is the user's Notion database. "
            "CRITICAL INSTRUCTION: Always run 'Notion connection' first to check the available pages. "
            "If the exact page or class requested (such as CICS 160) is not listed in your Notion workspace, "
            "you MUST inform the user honestly that the notes do not exist in Notion. DO NOT search the internet or hallucinate notes.",
            tools=[notion_connection, notion_page_content],
            llm=llm_config,
            verbose=True,
            max_iter=2,
            allow_delegation=False
        )
   

    task = Task(
        description=f"Analyze and fulfill the user request: '{query}'\n ROUTING RULE:\n - If it is about coding, algorithms, or programming languages (e.g., Java, Python), delegate strictly to the 'Coding Help Agent'.\n"
            "- If it is about university notes, class material, or study prep, delegate to the 'Notion Academic Agent' and use the Notion tools.\n"
            "Return the final answer immediately once the agent completes it.",
        expected_output="A well-formatted Markdown response with clear code snippets or explanations."
    )

    crew = Crew(
        agents=[coding_agent, academic_agent],
        tasks=[task],
        process=Process.hierarchical,
        manager_llm=llm_config,
        verbose=True
    )

    with ThreadPoolExecutor() as executor:
        future = executor.submit(crew.kickoff, inputs={"query": query})
        result = future.result()
        
        if hasattr(result, 'output') and result.output:
            return result.output
        return str(result)