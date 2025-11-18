#!/usr/bin/env python3
"""
Run script for the Generative AI Code Generator.

This script provides different ways to run the code generator:
- Development mode
- Production mode
- Docker mode
- Example mode
"""

import os
import sys
import argparse
import subprocess
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def check_requirements():
    """Check if all requirements are installed."""
    try:
        import dotenv
        import pydantic
        import langchain_google_genai
        import langgraph
        import fastapi
        import uvicorn
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please run: pip install -r requirements.txt")
        return False


def check_environment():
    """Check if environment variables are set."""
    required_vars = ['GOOGLE_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set them in your .env file or environment")
        return False
    
    print("✅ Environment variables are set")
    return True


def run_development():
    """Run in development mode."""
    print("🚀 Starting Code Generator in Development Mode...")
    
    if not check_requirements() or not check_environment():
        return
    
    try:
        # Run the main agent
        subprocess.run([
            sys.executable, "-m", "src.llm.agents.coder",
            "--host", "0.0.0.0",
            "--port", "8090"
        ], cwd=project_root)
    except KeyboardInterrupt:
        print("\n👋 Shutting down development server...")


def run_production():
    """Run in production mode with optimized settings."""
    print("🏭 Starting Code Generator in Production Mode...")
    
    if not check_requirements() or not check_environment():
        return
    
    try:
        # Run with uvicorn for production
        subprocess.run([
            "uvicorn", "src.llm.agents.coder:app",
            "--host", "0.0.0.0",
            "--port", "8090",
            "--workers", "4",
            "--log-level", "info"
        ], cwd=project_root)
    except KeyboardInterrupt:
        print("\n👋 Shutting down production server...")


def run_docker():
    """Run using Docker."""
    print("🐳 Starting Code Generator with Docker...")
    
    # Check if Docker is available
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker is not installed or not available")
        return
    
    try:
        # Build Docker image
        print("Building Docker image...")
        subprocess.run([
            "docker", "build", "-t", "generative-ai-code-generator", "."
        ], cwd=project_root, check=True)
        
        # Run Docker container
        print("Running Docker container...")
        subprocess.run([
            "docker", "run", "-p", "8090:8090",
            "--env-file", ".env",
            "generative-ai-code-generator"
        ], cwd=project_root)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker command failed: {e}")
    except KeyboardInterrupt:
        print("\n👋 Shutting down Docker container...")


async def run_example():
    """Run example code generation."""
    print("📝 Running Code Generation Example...")
    
    if not check_requirements() or not check_environment():
        return
    
    try:
        # Import and run basic example
        from examples.basic_completion import basic_completion_example
        await basic_completion_example()
    except Exception as e:
        print(f"❌ Example failed: {e}")


def run_tests():
    """Run tests and examples."""
    print("🧪 Running Tests and Examples...")
    
    if not check_requirements():
        return
    
    examples_dir = project_root / "examples"
    
    for example_file in examples_dir.glob("*.py"):
        print(f"\n📋 Running {example_file.name}...")
        try:
            subprocess.run([
                sys.executable, str(example_file)
            ], cwd=project_root, timeout=60)
        except subprocess.TimeoutExpired:
            print(f"⏰ {example_file.name} timed out")
        except Exception as e:
            print(f"❌ {example_file.name} failed: {e}")


def setup_project():
    """Set up the project for first-time use."""
    print("🔧 Setting up Generative AI Code Generator...")
    
    # Create .env file if it doesn't exist
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"
    
    if not env_file.exists() and env_example.exists():
        print("📝 Creating .env file from template...")
        env_file.write_text(env_example.read_text())
        print("⚠️  Please edit .env file with your API keys")
    
    # Create data directories
    data_dirs = ["data/cache", "data/prompts", "data/outputs", "data/embeddings"]
    for dir_path in data_dirs:
        (project_root / dir_path).mkdir(parents=True, exist_ok=True)
    
    # Install requirements
    print("📦 Installing requirements...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], cwd=project_root, check=True)
        print("✅ Requirements installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install requirements")
        return
    
    print("✅ Project setup complete!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your API keys")
    print("2. Run: python run.py --mode development")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run the Generative AI Code Generator")
    parser.add_argument(
        "--mode", 
        choices=["development", "production", "docker", "example", "test", "setup"],
        default="development",
        help="Run mode (default: development)"
    )
    
    args = parser.parse_args()
    
    print("🤖 Generative AI Code Generator")
    print("=" * 50)
    
    if args.mode == "setup":
        setup_project()
    elif args.mode == "development":
        run_development()
    elif args.mode == "production":
        run_production()
    elif args.mode == "docker":
        run_docker()
    elif args.mode == "example":
        asyncio.run(run_example())
    elif args.mode == "test":
        run_tests()


if __name__ == "__main__":
    main()