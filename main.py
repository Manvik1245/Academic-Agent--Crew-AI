import os
import sys
from dotenv import load_dotenv
from crew_operations import AcademicAgent

load_dotenv()

def main():
    sys.stdout.reconfigure(line_buffering=True)
    crew = AcademicAgent().crew()
    
    print("==================================================")
    print("🚀 Unified Personal AI Workspace Online (Groq + Python)")
    print("==================================================")
    print("Ask me anything about your university notes or coding practice.")
    print("Type 'exit' or 'quit' to close.")
    print("==================================================")
    history=""
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ['exit', 'quit', 'bye','leave']:
                print("Exiting the application. Goodbye!")
                break
            elif user_input.lower() in ['clear','empty']:
                os.system('cls' if os.name == 'nt' else 'clear')
                history=""
                print("Chat history cleared.")
                continue
            elif user_input.lower()== "":
                print("Enter a query in")
                continue
            
            response = crew.kickoff(inputs={
                "query": user_input,
                "history": history
            })
            final_output = response.raw if hasattr(response, 'raw') else str(response)
            print(f"Academic Agent: {final_output}")
            history += f"You: {user_input}\nAcademic Agent: {final_output}\n"
        except:
            print("An error occurred while processing your request.")
            break

if __name__ == "__main__":
    main()
    
    