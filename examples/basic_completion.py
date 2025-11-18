"""Basic completion example using the code generator."""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.llm.agents.coder.agent import CoderAgent


async def basic_completion_example():
    """Example of basic code completion."""
    
    # Initialize the agent
    agent = CoderAgent()
    
    # Example query
    query = {
        "text": "Generate a Python function to calculate the factorial of a number using recursion",
        "files": [],
        "auth_token": None
    }
    
    session_id = "example_session_001"
    
    print("🚀 Starting code generation...")
    print(f"Query: {query['text']}")
    print("-" * 50)
    
    try:
        # Invoke the agent
        result = await agent.invoke(query, session_id)
        
        print("✅ Code generation completed!")
        print(f"Task Complete: {result['is_task_complete']}")
        print(f"Requires Input: {result['require_user_input']}")
        print("\n📝 Generated Content:")
        print(result['content'])
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(basic_completion_example())