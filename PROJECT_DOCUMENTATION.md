# Travel Visa Desk - Project Documentation

## Table of Contents
1. Project Overview
2. Project Structure
3. Architecture
4. Installation & Setup
5. Configuration
6. Core Components
7. API Endpoints
8. Frontend Interface
9. Usage Examples
10. Database Schema
11. Development Guide
12. Troubleshooting

---

## Project Overview

**Travel Visa Desk** is a comprehensive Corporate Immigration Visa Application Management System that leverages AI and LLM (Large Language Models) to streamline visa application processes. The system provides both backend API services and interactive frontend interfaces for managing visa applications, tracking statuses, and handling approval workflows.

### Key Features
- **AI-Powered Visa Assistance**: Uses Google Generative AI (Gemini) for intelligent visa guidance
- **RAG (Retrieval-Augmented Generation)**: Queries visa requirements and documentation using Milvus vector store
- **Multi-Channel Interfaces**: Streamlit web application and FastAPI backend
- **Approval Workflow Management**: Multi-stage approval processes with role-based access
- **Document Management**: Upload, validation, and tracking of visa documents
- **Session Management**: Persistent user sessions with auto-save capabilities
- **Rate Limiting**: API rate limiting to prevent abuse
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

### Technology Stack
- **Backend**: FastAPI, Python 3.x
- **Frontend**: Streamlit
- **LLM Integration**: LangChain, Google Generative AI, OpenAI, LiteLLM
- **Vector Store**: Milvus (for semantic search and RAG)
- **Database**: SQLite
- **Cache**: Redis (configured)
- **Message Queue**: Celery + RabbitMQ/Redis
- **Authentication**: JWT-based session management
- **Logging**: Structured logging with configuration files

---

## Project Structure

```
working-cb-tool-3.o/
├── front_main.py                     # Main Streamlit web application
├── chat_bot.py                     # LangChain-based chatbot implementation
├── run.py                          # Application entry point
├── setup.py                        # Package setup configuration
├── requirements.txt                # Python dependencies
├── README.md                       # Basic README
│
├── config/                         # Configuration files
│   ├── __init__.py
│   ├── api_config.yaml            # API configuration (CORS, rate limiting, session)
│   ├── logging_config.yaml        # Logging configuration
│   ├── milvus_config.yaml         # Milvus vector store configuration
│   ├── model_config.yaml          # LLM model configurations
│   ├── prompt_templates.yaml      # AI prompt templates
│   └── visa_requirements.yaml     # Visa requirements reference
│
├── src/                            # Source code directory
│   ├── __init__.py
│   │
│   ├── api/                       # FastAPI application
│   │   ├── main.py               # FastAPI app setup and lifespan management
│   │   ├── main_tools.py         # Tool definitions for AI agents
│   │   ├── models/
│   │   │   ├── approval_models.py    # Approval workflow data models
│   │   │   └── visa_models.py        # Visa application data models
│   │   └── routes/
│   │       ├── visa_application.py   # Visa application endpoints
│   │       ├── approval_workflow.py  # Approval workflow endpoints
│   │       ├── session_management.py # Session management endpoints
│   │       └── rag_routes.py         # RAG query endpoints
│   │
│   ├── llm/                       # LLM integration modules
│   │   ├── base.py               # Base LLM client abstract class
│   │   ├── claude_client.py      # Anthropic Claude integration
│   │   ├── openai_client.py      # OpenAI integration
│   │   ├── litellm_client.py     # LiteLLM wrapper for multiple providers
│   │   ├── utils.py              # LLM utility functions
│   │   └── agents/
│   │       └── coder/            # Coding agent implementation
│   │           ├── agent.py
│   │           ├── task_manager.py
│   │           └── tools.py
│   │
│   ├── services/                 # Business logic services
│   │   ├── visa_service.py       # Visa application management
│   │   ├── approval_service.py   # Approval workflow management
│   │   ├── rag_service.py        # RAG service for knowledge retrieval
│   │   └── *_old.py              # Legacy service implementations
│   │
│   ├── vector_store/             # Vector database integration
│   │   └── milvus_client.py     # Milvus client for semantic search
│   │
│   ├── common/                   # Common utilities
│   │   ├── types.py             # Pydantic data models and enums
│   │   ├── server/
│   │   │   ├── server.py        # Server utilities
│   │   │   ├── task_manager.py  # Task management
│   │   │   └── utils.py         # Server utilities
│   │   └── utils/
│   │       └── push_notification_auth.py
│   │
│   ├── handlers/                # Error and exception handlers
│   │   └── error_handler.py     # Custom exception handling
│   │
│   ├── prompt_engineering/      # Prompt optimization
│   │   ├── chain.py            # Prompt chains
│   │   ├── few_shot.py         # Few-shot prompting
│   │   └── templates.py        # Prompt templates
│   │
│   └── utils/                   # Utility functions
│       ├── logger.py           # Logging setup
│       ├── cache.py            # Caching utilities
│       ├── kafka.py            # Kafka integration
│       ├── obs.py              # Observability utilities
│       ├── rate_limiter.py     # Rate limiting
│       └── token_counter.py    # Token counting for LLMs
│
├── data/                         # Data directories
│   ├── cache/                   # Cached data
│   ├── embeddings/              # Vector embeddings
│   ├── outputs/                 # Generated outputs
│   ├── prompts/                 # Prompt files
│   └── tools/
│       └── coder/
│           └── mcp_server.py   # Model Context Protocol server
│
├── scripts/                      # Utility scripts
│   ├── init_milvus.py          # Milvus initialization
│   ├── load_knowledge_base.py  # Knowledge base loading
│   └── test_api.py             # API testing
│
├── notebooks/                    # Jupyter notebooks
│   ├── model_experimentation.ipynb
│   ├── prompt_testing.ipynb
│   └── response_analysis.ipynb
│
├── examples/                     # Example implementations
│   ├── basic_completion.py
│   ├── chain_prompts.py
│   └── chat_session.py
│
├── logs/                        # Application logs (generated at runtime)
│
└── venv/                        # Python virtual environment

```

---

## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Frontend Layer                                      │
├─────────────────────────────────────────────────────────────────────────┤
│  Streamlit Web App (front_main.py)  │  LangChain Chatbot (chat_bot.py)  |
│  • User Authentication              │  • AI-powered assistance          |
│  • Application Forms                │  • Tool-calling agent             |
│  • Status Tracking                  │  • Multi-turn conversations       |
│  • Dashboard & Analytics            │                                   |
└──────────────────┬──────────────────┬───────────────────────────────────┘
                   │                  │
                   ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (src/api)                    │
├─────────────────────────────────────────────────────────────────┤
│  Routes Layer:                                                  │
│  • /api/visa/applications      (Visa application CRUD)          │
│  • /api/approval               (Approval workflows)             │
│  • /api/session                (Session management)             │
│  • /api/rag                    (RAG queries)                    │
└──────────┬──────────────────────────────────────────────────┬───┘
           │                                                  │
           ▼                                                  ▼
┌──────────────────────────────┐    ┌─────────────────────────────┐
│  Services Layer              │    │  LLM Integration Layer      │
├──────────────────────────────┤    ├─────────────────────────────┤
│ • VisaService                │    │ • Google Generative AI      │
│ • ApprovalService            │    │ • OpenAI                    │
│ • RAGService                 │    │ • Anthropic Claude          │
│ • SessionService             │    │ • LiteLLM (multi-provider)  │
└──────────┬───────────────────┘    └────────────┬────────────────┘
           │                                      │
           └──────────────┬───────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                 │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  ┌─────┐  │
│  │  SQLite DB  │  │  Milvus      │  │  Redis Cache  │  │YAML │  │
│  │ • Visa Apps │  │  • Embeddings│  │  • Sessions   │  │Conf │  │
│  │ • Users     │  │  • Knowledge │  │  • Tokens     │  │Files│  │
│  │ • Approvals │  │    Base      │  │               │  │     │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  └─────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Request** → Frontend (Streamlit/Chatbot)
2. **Authentication** → Session validation
3. **API Call** → FastAPI route handlers
4. **Business Logic** → Service layer processes request
5. **LLM Interaction** → AI processing if needed
6. **Data Persistence** → Database/Vector store updates
7. **Response** → Return to frontend with results

---

## Installation & Setup

### Prerequisites
- Python 3.10 or higher
- pip package manager
- Git
- Virtual environment tool (venv)

### Step 1: Clone and Navigate to Project
```bash
cd "c:\Users\pallavi.brale\Downloads\working-cb-tool-3.o"
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv
```

### Step 3: Activate Virtual Environment

**On Windows (Command Prompt):**
```bash
venv\Scripts\activate
```

**On Windows (PowerShell):**
```bash
.\venv\Scripts\Activate.ps1
```

**On macOS/Linux:**
```bash
source venv/bin/activate
```

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 5: Set Environment Variables
Create a `.env` file in the project root:
```bash
GOOGLE_API_KEY=your_google_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
MILVUS_HOST=localhost
MILVUS_PORT=19530
REDIS_URL=redis://localhost:6379
DATABASE_URL=sqlite:///visa_applications.db
```

### Step 6: Initialize Database and Vector Store
```bash
python scripts/init_milvus.py
python scripts/load_knowledge_base.py
```

### Step 7: Run the Application

**Start FastAPI Backend:**
```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Start Streamlit Frontend (in new terminal):**
```bash
streamlit run front_main.py
```

**Run Chatbot (in new terminal):**
```bash
python chat_bot.py
```

---

## Configuration

### API Configuration (`config/api_config.yaml`)

```yaml
api:
  title: "Travel Visa Desk API"
  description: "Corporate Immigration Visa Application Management System"
  version: "1.0.0"
  contact:
    name: "IT Support"
    email: "support@company.com"

cors:
  allow_origins:
    - "http://localhost:3000"
    - "http://localhost:8080"
    - "http://localhost:8000"
  allow_credentials: true
  allow_methods: ["*"]
  allow_headers: ["*"]

rate_limiting:
  default:
    calls: 100
    window: 60
  visa_application:
    calls: 10
    window: 60
  document_upload:
    calls: 20
    window: 60

session_management:
  timeout_minutes: 30
  max_sessions_per_user: 5
  auto_save_interval: 60
```

### Model Configuration (`config/model_config.yaml`)

Define your LLM model settings including:
- Model name
- API endpoint
- Temperature and other parameters
- Token limits
- Provider configuration

### Logging Configuration (`config/logging_config.yaml`)

Controls application logging levels and output:
- Log level (DEBUG, INFO, WARNING, ERROR)
- Log file locations
- Format specifications
- Module-specific settings

### Milvus Configuration (`config/milvus_config.yaml`)

Vector database settings:
- Host and port
- Collection names
- Embedding dimensions
- Index types

---

## Core Components

### 1. Visa Service (`src/services/visa_service.py`)

Manages visa application lifecycle:

```python
class VisaService:
    def create_application(request: CreateApplicationRequest) -> CreateApplicationResponse
    def get_application(application_id: str) -> VisaApplication
    def update_application(application_id: str, updates: dict) -> VisaApplication
    def list_applications(filters: dict) -> List[VisaApplication]
    def validate_documents(application_id: str) -> DocumentValidationResult
    def submit_application(application_id: str) -> ApplicationStatusResponse
```

**Key Responsibilities:**
- Application creation and management
- Document validation
- Status tracking
- Database persistence

### 2. Approval Service (`src/services/approval_service.py`)

Handles approval workflows:

```python
class ApprovalService:
    def create_approval_task(application_id: str, stage: str) -> ApprovalTask
    def approve(task_id: str, approver_id: str, comments: str) -> ApprovalResult
    def reject(task_id: str, approver_id: str, reason: str) -> ApprovalResult
    def get_pending_approvals(approver_id: str) -> List[ApprovalTask]
    def advance_workflow(application_id: str) -> WorkflowStatus
```

**Key Responsibilities:**
- Multi-stage approval workflows
- Role-based approval routing
- Status updates and notifications

### 3. RAG Service (`src/services/rag_service.py`)

Retrieval-Augmented Generation for visa information:

```python
class RAGService:
    def query_visa_requirements(visa_type: str, country: str) -> str
    def get_required_documents(visa_type: str) -> List[DocumentRequirement]
    def search_knowledge_base(query: str) -> List[SearchResult]
    def get_processing_times(visa_type: str, country: str) -> ProcessingInfo
```

**Key Responsibilities:**
- Semantic search using Milvus vector store
- Retrieval of visa requirements
- Knowledge base querying
- Context-aware responses

### 4. Milvus Client (`src/vector_store/milvus_client.py`)

Vector database operations:

```python
class MilvusClient:
    def connect(host: str, port: int) -> None
    def create_collection(collection_name: str, schema: dict) -> None
    def insert(collection_name: str, data: List[dict]) -> None
    def search(collection_name: str, query_vectors: List, top_k: int) -> List
    def disconnect() -> None
```

**Key Responsibilities:**
- Vector embeddings storage
- Semantic search operations
- Knowledge base management

### 5. LLM Clients

#### Base LLM Client (`src/llm/base.py`)
Abstract interface for all LLM providers:

```python
class BaseLLMClient(ABC):
    async def generate(prompt: str, **kwargs) -> str
    async def stream(prompt: str, **kwargs) -> AsyncIterable[str]
```

#### Google Generative AI (`src/llm/claude_client.py`)
- Uses Google's Gemini 2.5 Flash model
- Supports function calling for tool integration
- Stream and batch generation

#### OpenAI Client (`src/llm/openai_client.py`)
- GPT-4 and GPT-3.5-turbo support
- Tool calling and function integration
- Token management

#### LiteLLM Client (`src/llm/litellm_client.py`)
- Multi-provider abstraction
- Unified interface for Claude, OpenAI, Google, etc.
- Cost tracking and logging

---

## API Endpoints

### Base URL
```
http://localhost:8000
```

### Visa Application Endpoints

#### Create Visa Application
```http
POST /api/visa/applications
Content-Type: application/json

{
  "applicant": {
    "employee_id": "EMP001",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@company.com",
    "nationality": "US",
    "passport_number": "ABC123456",
    "passport_expiry": "2025-12-31",
    "date_of_birth": "1990-01-15"
  },
  "visa_type": "business",
  "travel_details": {
    "destination_country": "Japan",
    "purpose": "Business Meeting",
    "start_date": "2025-02-01",
    "end_date": "2025-02-15"
  }
}
```

**Response (201 Created):**
```json
{
  "application_id": "app_uuid",
  "status": "submitted",
  "created_at": "2025-02-17T10:30:00Z",
  "next_steps": ["Document upload", "Application review"]
}
```

#### Get Application Status
```http
GET /api/visa/applications/{application_id}
```

**Response:**
```json
{
  "application_id": "app_uuid",
  "status": "under_review",
  "approval_status": "pending",
  "current_stage": "document_verification",
  "current_approver": "approver_name",
  "documents": [
    {
      "type": "passport",
      "status": "submitted",
      "uploaded_at": "2025-02-17T10:35:00Z"
    }
  ],
  "updated_at": "2025-02-17T11:00:00Z"
}
```

#### Update Application
```http
PATCH /api/visa/applications/{application_id}
Content-Type: application/json

{
  "notes": "Updated application information",
  "documents": []
}
```

#### List Applications
```http
GET /api/visa/applications?status=submitted&visa_type=business&limit=10&offset=0
```

**Response:**
```json
{
  "applications": [...],
  "total": 45,
  "limit": 10,
  "offset": 0
}
```

### Approval Workflow Endpoints

#### Get Pending Approvals
```http
GET /api/approval/pending?approver_id=approver123
```

#### Approve Application
```http
POST /api/approval/approve
Content-Type: application/json

{
  "application_id": "app_uuid",
  "approver_id": "approver123",
  "comments": "Approved for processing",
  "approval_details": {}
}
```

#### Reject Application
```http
POST /api/approval/reject
Content-Type: application/json

{
  "application_id": "app_uuid",
  "approver_id": "approver123",
  "reason": "Missing required documents"
}
```

### Session Management Endpoints

#### Create Session
```http
POST /api/session
Content-Type: application/json

{
  "user_id": "user123",
  "metadata": {}
}
```

#### Get Session
```http
GET /api/session/{session_id}
```

#### Terminate Session
```http
DELETE /api/session/{session_id}
```

### RAG Query Endpoints

#### Query Visa Requirements
```http
POST /api/rag/query
Content-Type: application/json

{
  "query": "What are requirements for Japan business visa?",
  "visa_type": "business",
  "country": "Japan"
}
```

**Response:**
```json
{
  "query": "What are requirements for Japan business visa?",
  "results": [
    {
      "relevance": 0.95,
      "content": "Japan business visa requires...",
      "source": "visa_requirements.yaml"
    }
  ]
}
```

---

## Frontend Interface

### Main Streamlit Application (`front_main.py`)

#### Features

1. **Authentication Page**
   - User login/registration
   - Session management
   - Password hashing with SQLite backend

2. **Dashboard**
   - Application overview
   - Status tracking
   - Key metrics and statistics

3. **Application Forms**
   - Structured form for visa applications
   - Real-time validation
   - Multi-step form wizard

4. **Document Management**
   - File upload interface
   - Document validation
   - Progress tracking

5. **Status Tracking**
   - Real-time application status
   - Approval workflow visualization
   - Timeline view

6. **Support Chat**
   - AI-powered chatbot integration
   - FAQ retrieval
   - Real-time assistance

#### Styling
- Modern gradient backgrounds
- Responsive design
- Custom CSS animations
- Mobile-friendly layout

### Chatbot Interface (`chat_bot.py`)

#### Features
- Multi-turn conversations
- Tool calling for API integration
- AI-powered visa assistance
- Real-time response generation

#### Supported Operations
- Create visa applications
- Query visa requirements
- Check application status
- Update application details

---

## Usage Examples

### Example 1: Create Visa Application via API

```python
import requests

BASE_URL = "http://localhost:8000"

application_data = {
    "applicant": {
        "employee_id": "EMP001",
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice@company.com",
        "nationality": "UK",
        "passport_number": "ABC123456",
        "passport_expiry": "2026-12-31",
        "date_of_birth": "1992-03-20"
    },
    "visa_type": "work",
    "travel_details": {
        "destination_country": "Canada",
        "purpose": "Employment",
        "start_date": "2025-03-01",
        "end_date": "2026-03-01"
    }
}

response = requests.post(
    f"{BASE_URL}/api/visa/applications",
    json=application_data
)

print(f"Application ID: {response.json()['application_id']}")
print(f"Status: {response.json()['status']}")
```

### Example 2: Query Visa Requirements via Chatbot

```python
from chat_bot import setup_agent

agent = setup_agent()

query = "What documents do I need for a Japan business visa?"
response = agent.invoke({"input": query})

# Extract and display the final answer
for message in response['messages']:
    if message.type == "ai":
        print(message.content)
```

### Example 3: Check Application Status

```python
import requests

BASE_URL = "http://localhost:8000"
app_id = "app_uuid_from_creation"

response = requests.get(f"{BASE_URL}/api/visa/applications/{app_id}")
app_data = response.json()

print(f"Application Status: {app_data['status']}")
print(f"Current Stage: {app_data['current_stage']}")
print(f"Approver: {app_data['current_approver']}")
```

### Example 4: Using the Streamlit Interface

1. Open browser to `http://localhost:8501`
2. Login with credentials
3. Click "New Application"
4. Fill visa type and applicant information
5. Upload required documents
6. Submit application
7. Track status in dashboard

---

## Database Schema

### SQLite Database (`visa_applications.db`)

#### visa_applications Table
```sql
CREATE TABLE visa_applications (
    id VARCHAR(50) PRIMARY KEY,
    visa_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'submitted',
    approval_status VARCHAR(20) DEFAULT 'pending',
    current_stage VARCHAR(50),
    current_approver VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    submitted_at TIMESTAMP,
    notes TEXT,
    session_id VARCHAR(50)
);
```

#### applicants Table
```sql
CREATE TABLE applicants (
    id SERIAL PRIMARY KEY,
    application_id VARCHAR(50) REFERENCES visa_applications(id),
    employee_id VARCHAR(20),
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100),
    department VARCHAR(50),
    position VARCHAR(50),
    nationality VARCHAR(50),
    passport_number VARCHAR(50),
    passport_expiry DATE,
    date_of_birth DATE
);
```

#### documents Table
```sql
CREATE TABLE documents (
    id VARCHAR(50) PRIMARY KEY,
    application_id VARCHAR(50) REFERENCES visa_applications(id),
    document_type VARCHAR(50),
    file_path VARCHAR(255),
    file_size INT,
    status VARCHAR(20),
    validation_errors TEXT,
    uploaded_at TIMESTAMP,
    verified_by VARCHAR(50),
    verified_at TIMESTAMP
);
```

#### approval_tasks Table
```sql
CREATE TABLE approval_tasks (
    id VARCHAR(50) PRIMARY KEY,
    application_id VARCHAR(50) REFERENCES visa_applications(id),
    stage VARCHAR(50),
    approver_id VARCHAR(50),
    status VARCHAR(20),
    comments TEXT,
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

### Milvus Vector Store

#### Collections
- **visa_requirements**: Embeddings of visa requirement documents
- **knowledge_base**: General immigration knowledge base
- **faq_embeddings**: FAQ embeddings for quick retrieval

#### Embedding Dimension
- Default: 384 (using sentence-transformers)
- Configurable in `config/milvus_config.yaml`

---

## Development Guide

### Adding a New LLM Provider

1. Create new file `src/llm/provider_client.py`
2. Inherit from `BaseLLMClient`
3. Implement `generate()` and `stream()` methods
4. Add configuration to `config/model_config.yaml`
5. Register in LLM factory

### Adding New API Endpoints

1. Create route file in `src/api/routes/`
2. Define request/response models in `src/api/models/`
3. Implement business logic in service layer
4. Register router in `src/api/main.py`

### Adding RAG Capability

1. Prepare documents/knowledge base
2. Use `scripts/load_knowledge_base.py` to embed and store
3. Update `RAGService.query()` to search relevant collections
4. Test with `/api/rag/query` endpoint

### Adding Approval Stages

1. Define new stage in visa requirements YAML
2. Update `ApprovalService` workflow logic
3. Create corresponding approval routes
4. Update database with new stage field

### Extending Chatbot Capabilities

1. Create new tool function in `src/api/main_tools.py`
2. Define tool schema (name, description, parameters)
3. Implement tool execution logic
4. Add to tools list in `chat_bot.py`

### Running Tests

```bash
pytest tests/ -v
pytest tests/ -v --cov=src  # With coverage
```

### Code Style and Standards

- Follow PEP 8 conventions
- Use type hints for all functions
- Write docstrings for modules and classes
- Keep functions small and focused
- Use logging for debugging
- Handle errors gracefully

---

## Troubleshooting

### Issue: Milvus Connection Failed

**Symptom:** `Error: Failed to connect to Milvus`

**Solution:**
1. Verify Milvus is running: `docker ps | grep milvus`
2. Check host/port in `config/milvus_config.yaml`
3. Restart Milvus container
4. Check network connectivity

### Issue: API Port Already in Use

**Symptom:** `Address already in use`

**Solution:**
```bash
# Find process using port 8000
netstat -ano | findstr :8000
# Kill process
taskkill /PID <PID> /F
# Or use different port
uvicorn src.api.main:app --port 8001
```

### Issue: LLM API Key Invalid

**Symptom:** `Invalid API key or authorization error`

**Solution:**
1. Verify API key in `.env` file
2. Check API key is correct on provider's dashboard
3. Verify key has required permissions
4. Check key hasn't expired

### Issue: Vector Search Returns No Results

**Symptom:** `Empty results from RAG queries`

**Solution:**
1. Run knowledge base loading: `python scripts/load_knowledge_base.py`
2. Verify data in Milvus: `python scripts/check_milvus.py`
3. Check embedding model is loaded correctly
4. Verify query embeddings are being generated

### Issue: Session Timeout

**Symptom:** `Session expired, please login again`

**Solution:**
1. Check session timeout in `config/api_config.yaml`
2. Verify Redis connection if using Redis for sessions
3. Increase timeout if needed
4. Check session storage database

### Issue: Document Validation Fails

**Symptom:** `Document validation failed`

**Solution:**
1. Check file type is supported
2. Verify file size is within limits
3. Check document format is valid
4. Review validation rules in `VisaService._validate_document()`

### Issue: Rate Limiting Triggered

**Symptom:** `429 Too Many Requests`

**Solution:**
1. Check rate limits in `config/api_config.yaml`
2. Wait for rate limit window to reset
3. Adjust rate limits if needed
4. Implement exponential backoff in client

### Issue: Database Locked

**Symptom:** `SQLite database is locked`

**Solution:**
1. Check if application is running in multiple processes
2. Reduce concurrent database access
3. Increase timeout in connection string
4. Consider using connection pooling

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check logs:
```bash
tail -f logs/application.log
```

---

## Additional Resources

### Configuration Files Reference
- `config/api_config.yaml` - API and session settings
- `config/model_config.yaml` - LLM model configurations
- `config/prompt_templates.yaml` - AI prompt templates
- `config/visa_requirements.yaml` - Visa requirement reference

### Key Python Modules
- FastAPI: https://fastapi.tiangolo.com/
- Streamlit: https://docs.streamlit.io/
- LangChain: https://python.langchain.com/
- Pydantic: https://docs.pydantic.dev/
- Milvus: https://milvus.io/docs/

### Related Scripts
- `scripts/init_milvus.py` - Initialize Milvus vector store
- `scripts/load_knowledge_base.py` - Load visa knowledge
- `scripts/test_api.py` - Test API endpoints

### Contributing
1. Create feature branch from `main`
2. Make changes with descriptive commits
3. Add tests for new features
4. Submit pull request with documentation

---

## Support and Contact

For issues, questions, or suggestions:
- Email: support@company.com
- Documentation: See this file
- Issues: Check troubleshooting section
- Contact: IT Support team

---

**Last Updated:** November 17, 2025
**Version:** 1.0.0
**Status:** Active Development
