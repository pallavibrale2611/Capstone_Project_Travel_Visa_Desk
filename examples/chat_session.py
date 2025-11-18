"""Chat session example with the code generator."""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.llm.agents.coder.agent import CoderAgent


async def chat_session_example():
    """Example of a chat session with multiple interactions."""
    
    # Initialize the agent
    agent = CoderAgent()
    session_id = "chat_session_001"
    
    # Multiple queries in a session
    queries = [
        {
            "text": "Generate a Python class for a simple calculator with basic operations",
            "files": [],
            "auth_token": None
        },
        {
            "text": "Now add error handling to the calculator class",
            "files": [],
            "auth_token": None
        },
        {
            "text": "Add unit tests for the calculator class",
            "files": [],
            "auth_token": None
        }
    ]
    
    print("🚀 Starting chat session...")
    print(f"Session ID: {session_id}")
    print("=" * 60)
    
    for i, query in enumerate(queries, 1):
        print(f"\n💬 Query {i}: {query['text']}")
        print("-" * 50)
        
        try:
            result = await agent.invoke(query, session_id)
            
            print(f"✅ Response {i} completed!")
            print(f"Task Complete: {result['is_task_complete']}")
            print(f"Requires Input: {result['require_user_input']}")
            print("\n📝 Generated Content:")
            print(result['content'][:500] + "..." if len(result['content']) > 500 else result['content'])
            
        except Exception as e:
            print(f"❌ Error in query {i}: {e}")
        
        print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(chat_session_example())