import os
import requests
import json
from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task,LLM
from crewai.project import CrewBase, agent, crew,task
from crewai.tools import tool
os.environ["LITELLM_DROP_PARAMS"] = "True"
os.environ["LITELLM_DISABLE_PROMPT_CACHING"] = "True"
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
NOTION_API_TOKEN = os.environ.get("NOTION_API_TOKEN")
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, '.env')
load_dotenv(dotenv_path=env_path)

# crewai 1.15.2 marks every message with a "cache_breakpoint" flag for
# prompt-caching, but only its Anthropic adapter strips/translates that
# flag before sending. The generic litellm path (used for groq/*,
# openrouter/*, and other non-Anthropic models) forwards it as-is, and
# these providers reject the unknown field. Since we aren't on Anthropic,
# disable the marker entirely rather than patching every call site.
import crewai.llms.cache as _crewai_llm_cache
_crewai_llm_cache.mark_cache_breakpoint = lambda message: dict(message)

@tool("Notion connection")
def notion_connection():
    """
    Queries your Notion database to retrieve a list of page titles and IDs.
    Does not require arguments.
    """
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers, json={})
        response.raise_for_status() # Automatically catches 4xx/5xx errors
        
        data = response.json()
        results = data.get("results", [])
        complied = ""
        
        for result in results:
            properties = result.get("properties", {})
            page_id = result.get("id", "")
            
            # DYNAMIC LOOKUP: Find the property that is of type 'title'
            title_prop = next(
                (prop for prop in properties.values() if prop.get("type") == "title"),
                None
            )
            
            # Extract plain text from the title property
            title_text = "No Title"
            if title_prop and title_prop.get("title"):
                # 'plain_text' is the safest way to get the readable title string
                title_text = title_prop["title"][0].get("plain_text", "No Title")
            
            complied += f"Title: {title_text}, Page ID: {page_id}\n"
            
        return {"results": complied}
        
    except requests.exceptions.HTTPError as http_err:
        return {"error": f"HTTP error occurred: {http_err}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}

   
@CrewBase
class AcademicAgent:
    llm_config = LLM(
        model="gemini/gemini-3.5-flash",
        api_key=os.environ.get("OPENROUTER_API_KEY"),
        temperature=0.1,
        max_tokens=1000,
        top_p=0.2
    )

    @agent
    def academic_agent(self):
        return Agent(
            role= "Notion Academic Agent",
            goal= "To assist in academic preperation by providing information and then generating new resources according to my request using my Notion classnotes.",
            backstory= "I am a student who is preparing for my academic exams. I have a lot of classnotes in my Notion workspace, and I want to use them to generate new resources that can help me in my studies.",
            tools= [notion_connection],
            constraints= [
                "I can only use the information that is available in my Notion workspace.",
                "I cannot access any other information outside of my Notion workspace.",
                "I cannot make any assumptions or guesses about the information in my Notion workspace.",
                "I must always provide accurate and reliable information.",
                "I must always provide sources for the information I provide."
            ],
            llm= self.llm_config,
            verbose= True,
            max_iter=3,
            allow_delegation=False
        )

    @agent
    def coding_help(self):
        return Agent(
            role= "Coding Help Agent",
            goal= "To assist in coding by providing information and then generating new code according to my requests. I am not an expert in coding and I want to focus more on important concepts so, when asking questions, you will ask me questions back for more clarification so you can give the best questions according to the difficulty level and how do I want the concepts presented to me   ",
            backstory= "You are an EX-FAANG senior developer who is preparing me for my coding exams. I need someone helping me to train my brain in understanding code much better for the exams, especially in algorithims and data structures. I want to focus on important concepts and not waste time on unimportant concepts. I want to learn how to think like a senior developer and how to approach problems in a systematic way.",
            tools= [],
            constraints= [
               "I MUST rely entirely on my internal knowledge of Python, algorithms, and data structures.",
                "I MUST NOT use the Notion connection tool under any circumstances.",
                "I will ask clarifying questions if the user's coding request is too vague.",
                "I will focus on system architecture, logical reasoning, and clean code."
            ],
            llm= self.llm_config,
            verbose= True,
            max_iter=3,
            allow_delegation=False
        )


    @task
    def user_request(self):
        return Task(
            name= "User Request",
            description= ("Analyze and fulfill the following user request: '{query}'\n\n"
                "CRITICAL ROUTING INSTRUCTIONS FOR THE MANAGER:\n"
                "1. If '{query}' is related to CODING (e.g., Python, algorithms, scripts, FAANG prep), you MUST assign this to the 'Coding Help Agent'. Do NOT use the Notion tool.\n"
                "2. If '{query}' is related to UNIVERSITY NOTES or CLASS MATERIAL, you MUST assign this to the 'Notion Academic Agent' and allow them to use the Notion connection tool.\n"
                "3. Once the assigned agent returns an answer, you MUST immediately output that exact answer as your Final Output.\n"
                "4. NEVER execute the same tool twice for the same query."
            ),
            expected_output= "A clear, accurate response to the user's request.",
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            name= "Academic Agent Crew",
            description= "This crew is to assist in academic preperation by providing information and then generating new resources according to the user's request.",
            agents= [self.academic_agent(), self.coding_help()],
            tasks= [self.user_request()],
            process= Process.hierarchical,
            manager_llm= self.llm_config,
            manager_config= self.llm_config,
            verbose= True,
            max_iter=3
        )
        


