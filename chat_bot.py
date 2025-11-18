
import os
import json
import requests
from typing import Dict, Any, List


# These imports will now work after you upgrade your packages
# from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
# from langchain_core.pydantic_v1 import BaseModel, Field
from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
import requests
from src.api.models.visa_models import Applicant , TravelDetails ,CreateApplicationRequest
from src.api.main_tools import Get_Visa_Details ,Approve_Visa_Workflow ,Create_Visa_Application , rag_visa_query,patch_application

os.environ["GOOGLE_API_KEY"] = ""

from langchain.messages import HumanMessage, AIMessage

# --- Step 2: Set up the Agent (Corrected and Improved) ---
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", convert_system_message_to_human=True)
tools = [Get_Visa_Details, Create_Visa_Application ,Approve_Visa_Workflow, rag_visa_query,patch_application]
 


# A more robust prompt that includes a place for the agent's intermediate steps
# The `agent_scratchpad` is where the agent "thinks" by putting tool calls and tool outputs.
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant for visa applications. Use the tools provided to assist with visa application creation, status retrieval, approval workflow, querying visa requirements and updating application data.")
        
    ]
)
agent = create_agent(llm, tools)
try:
    while(True):
        ip = input("you: ")
        if ip == "q:":
            break
        
        prompt.append(("human", "{input}"))
        p1 = prompt.invoke({"input": ip})  # Test invocation to ensure prompt is set up correctly
        # `create_agent` is a high-level factory that creates a LangGraph agent.
        # It automatically handles the looping logic (model -> tool -> model).
        


        # --- Step 3: Invoke the Agent ---

        print("\n====================================\n")
        # The input dictionary MUST contain keys that match the variables in your prompt template.
        response1 = agent.invoke(p1)

        # The output of a LangGraph agent is a dictionary representing its final state.
        # The 'messages' key holds the entire conversation history. The last message is the answer.
        print("\nFinal Answer:")
        # print(response1)
        # print(response1.get('messages')[2].content[0]["text"])


        def get_last_ai_message_content(agent_response: dict) -> str:
            messages = agent_response.get('messages', [])
            for message in reversed(messages):
                if isinstance(message, AIMessage):
                    content = message.content
                    # If content is a list of dicts (LangChain v1.x)
                    if isinstance(content, list):
                        # Extract text from all items of type 'text'
                        texts = [item.get("text", "") for item in content if item.get("type") == "text"]
                        return "\n".join(texts) if texts else "No text found in AI message."
                    elif isinstance(content, str) and content:
                        return content
            return "Could not find a final AI response."
        r = get_last_ai_message_content(response1)
        print("formated output :->",r)
        prompt.append(("ai",r))
except Exception as e:
    print("Error occurred:", str(e))    