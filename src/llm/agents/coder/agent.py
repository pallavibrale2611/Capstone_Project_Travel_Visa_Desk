"""Code generation agent implementation."""

from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, ToolMessage
from typing import Any, Dict, AsyncIterable, List, Literal, Optional
import os
import tempfile
from pydantic import BaseModel
import asyncio
import logging

from src.llm.utils import create_gemini_client
from src.prompt_engineering.templates import get_system_instruction
from src.utils.obs import TokenTracker
from .tools import get_coder_tools

memory = MemorySaver()


class ResponseFormat(BaseModel):
    """Respond to the user in this format.
        Args: 
            status: status of the request
            message: Text message to output from the LLM
            files: List of file paths that are provided by the Tools which are available to transfer, not included the files provided by the user
       """
    status: Literal["input_required", "completed", "error"] = "input_required"
    message: str
    files: List[str]


class CoderAgent:
    """Code generation agent using LangGraph and Gemini."""

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain", "application/zip"]

    def __init__(self):
        self.model = create_gemini_client()
        self.tools = get_coder_tools()
        self.system_instruction = get_system_instruction("code_generator")
        
        logging.info(f"Tools: {self.tools}")
        
        self.graph = create_react_agent(
            self.model, 
            tools=self.tools, 
            checkpointer=memory, 
            prompt=self.system_instruction, 
            response_format=ResponseFormat
        )

    def _extract_auth_token(self, query) -> Optional[str]:
        """Extract auth token from query structure."""
        if 'auth_token' in query:
            return query['auth_token']
        return None
    
    async def invoke(self, query, sessionId) -> str:
        """Invoke the agent with a query."""
        token_tracker = TokenTracker()
        config = {"configurable": {"thread_id": sessionId}, "callbacks": [token_tracker]}
        
        auth_token = self._extract_auth_token(query)
        auth_file_path = None
        
        if auth_token:
            try:
                temp_fd, auth_file_path = tempfile.mkstemp(suffix='.txt', prefix='auth_')
                with os.fdopen(temp_fd, 'w') as f:
                    f.write(auth_token)
                logging.info(f"Auth token stored in temporary file: {auth_file_path}")
            except Exception as e:
                logging.error(f"Failed to create or write to auth temp file: {e}", exc_info=True)
                if 'temp_fd' in locals() and temp_fd is not None:
                    os.close(temp_fd)
                if auth_file_path and os.path.exists(auth_file_path):
                    os.remove(auth_file_path)
                auth_file_path = None

        file_paths_query = ""
        if len(query['files']) > 0:
            file_paths_query = "File Paths:\n" + "\n".join(
                f"- {file['uri']} ({file['mimeType']})" for file in query['files']
            )
        
        # Include auth file path in query if present
        auth_info = ""
        if auth_file_path:
            auth_info = f"\nAuth File Path: {auth_file_path}"
        
        full_query = query['text'] + "\n\n" + file_paths_query + auth_info
        logging.info(f"agent: {await self.graph.ainvoke({'messages': [('user', full_query)]}, config)}")  
        logging.info(f"Auth file path used: {auth_file_path}")
        
        return self.get_agent_response(config)

    async def stream(self, query, sessionId) -> AsyncIterable[Dict[str, Any]]:
        """Stream responses from the agent."""
        inputs = {"messages": [("user", query)]}
        config = {"configurable": {"thread_id": sessionId}}

        for item in self.graph.stream(inputs, config, stream_mode="values"):
            message = item["messages"][-1]
            if (
                isinstance(message, AIMessage)
                and message.tool_calls
                and len(message.tool_calls) > 0
            ):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": "Looking up the exchange rates...",
                }
            elif isinstance(message, ToolMessage):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": "Processing the exchange rates..",
                }            
        
        yield self.get_agent_response(config)

    def get_agent_response(self, config):
        """Get the final agent response."""
        current_state = self.graph.get_state(config)
        messages = current_state.values.get('messages', [])
        logging.info(f"Number of messages found: {len(messages)}")
        
        if messages:
            last_message = messages[-1]
            if isinstance(last_message, AIMessage):
                content = last_message.content
                if isinstance(content, list):
                    content = "\n".join(str(item) for item in content)
                elif not isinstance(content, str):
                    content = str(content)
                return {
                    "is_task_complete": True,
                    "require_user_input": False,
                    "content": content
                }

        return {
            "is_task_complete": False,
            "require_user_input": True,
            "content": "We are unable to process your request at the moment. Please try again.",
        }