"""Main entry point for the coder agent server."""

import os
import logging
import click
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from src.common.server import A2AServer
from src.common.types import (
    AgentCard,
    AgentCapabilities,
    AgentSkill,
    HTTPAuthSecurityScheme,
    MissingAPIKeyError,
    AgentConstraints
)
from src.common.utils.push_notification_auth import PushNotificationSenderAuth
from .task_manager import AgentTaskManager
from .agent import CoderAgent
from config import get_model_config, get_prompt_templates


# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    filemode="a", 
    filename="app.log", 
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s"
)
logger = logging.getLogger(__name__)


@click.command()
@click.option("--host", "host", default="0.0.0.0", help="Host address to bind the server.")
@click.option("--port", "port", default=None, help="Port to bind the server.")
def main(host, port):
    """
    Entry point for starting the Code Generation Agent server.

    This function sets up the agent card, authentication, and server,
    then starts the server to listen for incoming requests.
    """
    try:
        # Load configuration
        model_config = get_model_config()
        prompt_config = get_prompt_templates()
        
        # Set default port from config if not provided
        if port is None:
            port = int(os.getenv("CODER_PORT", model_config["server"]["port"]))

        # Define agent capabilities
        capabilities = AgentCapabilities(
            streaming=model_config["capabilities"]["streaming"],
            push_notifications=model_config["capabilities"]["push_notifications"]
        )

        # Construct the agent card with metadata, skills, and security schema
        agent_card = AgentCard(
            name="Code Helper",
            description="This is a Code Generation Automation Agent that specializes in generating, and delivering high-quality code in multiple programming languages",
            url=f"http://{os.getenv('HOST', host)}:{port}/",
            version="1.0.0",
            defaultInputModes=CoderAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=CoderAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            agent_constraints=AgentConstraints(
                max_file_size=model_config["constraints"]["max_file_size"],
                supported_file_types=model_config["constraints"]["supported_file_types"],
                max_files=model_config["constraints"]["max_files"],
                prompt_template=prompt_config["prompt_templates"],
                prompt_template_variable_name=prompt_config["template_variables"]
            ),
            skills=[
                AgentSkill(
                    id="multi-agent-code-generator",
                    name="Multi-Agent Code Generator",
                    description=(
                        "Generate production-ready code in multiple programming languages "
                        "using a CrewAI agent workflow (Developer). "
                        "This agent transforms natural language requirements into validated, dependency-documented and syntactically correct code."
                    ),
                    tags=["Code Generation", "Multi-Agent", "CrewAI", "MCP"],
                    examples=prompt_config["examples"],            
                )
            ],
            customAgentMetaData="CODE_GENERATOR_AGENT"
        )
        
        # Set up push notification sender authentication and generate JWK
        notification_sender_auth = PushNotificationSenderAuth()
        notification_sender_auth.generate_jwk()

        # Initialize the server with the agent card and task manager
        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(
                agent=CoderAgent(),
                notification_sender_auth=notification_sender_auth
            ),
            host=host,
            port=port,
        )

        # Add endpoint for serving the JWKs (for push notification verification)
        server.app.add_route(
            "/.well-known/jwks.json",
            notification_sender_auth.handle_jwks_endpoint,
            methods=["GET"],
        )

        logger.info(f"Starting Code Generation Agent server on {host}:{port}")
        server.start()

    except MissingAPIKeyError as e:
        logger.error(f"Missing API Key Error: {e}")
        exit(1)
    except Exception as e:
        import traceback
        logger.error(f"An error occurred during server startup: {traceback.format_exc()}")
        exit(1)


if __name__ == "__main__":
    # Run the main function when the script is executed directly
    main()