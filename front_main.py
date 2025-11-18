import streamlit as st
import os
import json
from typing import Dict, Any, List
from datetime import datetime
import hashlib
import sqlite3
import time
import pandas as pd  # Add this import
import base64
from src.api.models.visa_models import Document 
import requests

# Set page configuration
st.set_page_config(
    page_title="Visa Assistant Chatbot",
    page_icon="🛂",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern CSS with gradient backgrounds and animations
st.markdown("""
<style>
    /* Global Styles */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0 !important;
        margin: 0 !important;
    }
    
    .main .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        max-width: 100% !important;
    }
    
    /* Remove all Streamlit default padding and margins */
    .css-18e3th9 {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
    }
    
    .css-1d391kg {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
    }
    
    .css-1v0mbdj {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Header Styles */
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4, #45B7D1, #96CEB4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        text-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Auth Container Styles */
    .auth-container {
        max-width: 450px;
        margin: 2rem auto;
        padding: 2rem 3rem;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.3);
        animation: slideUp 0.6s ease-out;
    }
    
    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .auth-title {
        text-align: center;
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(45deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 2rem;
        margin-top: 0;
        padding-top: 0;
    }
    
    /* Form Styles */
    .stTextInput>div>div>input, .stTextInput>div>div>input:focus {
        background: rgba(255, 255, 255, 0.9);
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        padding: 12px 16px;
        font-size: 16px;
        transition: all 0.3s ease;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    .stSelectbox>div>div>select {
        background: rgba(255, 255, 255, 0.9);
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        padding: 12px 16px;
        font-size: 16px;
    }
    
    /* Button Styles */
    .stButton>button {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
        padding: 14px 28px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 25px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px 0 rgba(102, 126, 234, 0.3);
        width: 100%;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px 0 rgba(102, 126, 234, 0.4);
    }
    
    /* Chat Message Styles */
    .user-message {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 16px 20px;
        border-radius: 20px 20px 5px 20px;
        margin: 12px 0;
        margin-left: 60px;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        border: none;
        animation: messageSlide 0.3s ease-out;
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #f093fb, #f5576c);
        color: white;
        padding: 16px 20px;
        border-radius: 20px 20px 20px 5px;
        margin: 12px 0;
        margin-right: 60px;
        box-shadow: 0 4px 15px rgba(245, 87, 108, 0.3);
        border: none;
        animation: messageSlide 0.3s ease-out;
    }
    
    @keyframes messageSlide {
        from {
            opacity: 0;
            transform: translateX(-10px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    .tool-call {
        background: linear-gradient(135deg, #ffd89b, #19547b);
        color: white;
        padding: 12px 16px;
        border-radius: 15px;
        margin: 8px 0;
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        box-shadow: 0 3px 10px rgba(255, 216, 155, 0.3);
        animation: toolCall 0.4s ease-out;
    }
    
    @keyframes toolCall {
        from {
            opacity: 0;
            transform: scale(0.9);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }
    
    /* Sidebar Styles */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #2c3e50, #34495e);
        color: white;
    }
    
    /* Card Styles */
    .feature-card {
        background: rgba(255, 255, 255, 0.95);
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #667eea;
        transition: transform 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-3px);
    }
    
    /* Welcome Message */
    .welcome-message {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 30px;
        border-radius: 20px;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        animation: welcomeSlide 0.8s ease-out;
    }
    
    @keyframes welcomeSlide {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Country Flags */
    .country-flag {
        font-size: 1.5rem;
        margin-right: 10px;
    }
    
    /* Quick Action Buttons */
    .quick-action {
        background: linear-gradient(45deg, #4CAF50, #45a049);
        color: white;
        border: none;
        padding: 12px 20px;
        border-radius: 15px;
        margin: 5px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
    }
    
    .quick-action:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
    }
    
    /* Application Status */
    .application-status {
        background: linear-gradient(45deg, #FFA726, #FF9800);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        box-shadow: 0 5px 15px rgba(255, 167, 38, 0.3);
    }
    
    /* Input Field Enhancement */
    .stTextInput>div>div>input::placeholder {
        color: #999;
        font-style: italic;
    }
    
    /* Tab Styles */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 10px 10px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #667eea;
        color: white;
    }
            
    .feature-card {
        background: rgba(255, 255, 255, 0.95);
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #667eea;
        transition: transform 0.3s ease;
        color: black !important;
    }

    .feature-card:hover {
        transform: translateY(-3px);
    }

    .feature-card strong,
    .feature-card p {
        color: black !important;
    }
    
    /* Role-specific styling */
    .role-user {
        border-left: 5px solid #4CAF50 !important;
    }
    
    .role-hr {
        border-left: 5px solid #2196F3 !important;
    }
    
    .role-legal {
        border-left: 5px solid #FF9800 !important;
    }
    
    .role-manager {
        border-left: 5px solid #9C27B0 !important;
    }
            
</style>
""", unsafe_allow_html=True)

# Database setup
DB_FILE = "users.db"

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         username TEXT UNIQUE NOT NULL,
         password TEXT NOT NULL,
         role TEXT NOT NULL,
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    ''')
    
    # Create default users for testing with UPPERCASE roles
    default_users = [
        ("pallavi", "password123", "MANAGEMENT_TEAM"),
        ("hr_user", "password123", "HR_TEAM"),
        ("legal_user", "password123", "LEGAL_TEAM"),
        ("user1", "password123", "USER")
    ]
    
    for username, password, role in default_users:
        try:
            c.execute(
                "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, hash_password(password), role)
            )
        except:
            pass
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def signup_user(username, password, role):
    """Register a new user with selected role."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    try:
        # Check if username already exists
        c.execute("SELECT username FROM users WHERE username = ?", (username,))
        if c.fetchone():
            return False, "Username already exists"
        
        # Insert new user with selected role (UPPERCASE)
        c.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, hash_password(password), role.upper())
        )
        conn.commit()
        return True, "User created successfully"
    except sqlite3.IntegrityError:
        return False, "Username already exists"
    except Exception as e:
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def verify_user(username, password, role):
    """Verify user credentials."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    try:
        c.execute(
            "SELECT password, role FROM users WHERE username = ?",
            (username,)
        )
        result = c.fetchone()
        
        if not result:
            return False, "User not found", None
        
        stored_password, stored_role = result
        if stored_password == hash_password(password):
            # Allow login if role matches (both in uppercase for comparison)
            if role.upper() == stored_role.upper():
                return True, "Login successful", stored_role
            else:
                return False, f"Selected role '{role}' does not match your assigned role '{stored_role}'", None
        else:
            return False, "Invalid password", None
    except Exception as e:
        return False, f"Error: {str(e)}", None
    finally:
        conn.close()

def view_database():
    """Display database contents in Streamlit"""
    if st.session_state.current_role == "MANAGEMENT_TEAM":  # Only managers can view DB
        st.subheader("🔍 Database Viewer (Manager Only)")
        
        conn = sqlite3.connect(DB_FILE)
        
        # Show users table
        st.markdown("### 👥 Users Table")
        users_df = pd.read_sql_query("SELECT * FROM users", conn)
        st.dataframe(users_df, use_container_width=True)
        
        # Show table schema
        st.markdown("### 📊 Table Schema")
        schema_df = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
        st.dataframe(schema_df, use_container_width=True)
        
        # Show row count
        st.markdown("### 📈 Statistics")
        row_count = pd.read_sql_query("SELECT COUNT(*) as user_count FROM users", conn)
        st.metric("Total Users", row_count['user_count'].iloc[0])
        
        # Download database
        st.markdown("### 💾 Download Database")
        with open(DB_FILE, 'rb') as f:
            st.download_button(
                label="Download Database File",
                data=f,
                file_name="users.db",
                mime="application/octet-stream"
            )
        
        conn.close()
    else:
        st.warning("⛔ Only MANAGER role can access database viewer")

def signup_page():
    """Display modern signup page with role selection."""
    # Remove all default padding and margins
    st.markdown("""
    <style>
    .main .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
    }
    .css-18e3th9 {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
    }
    .css-1d391kg {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Center the auth container
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Create the auth container with heading at the top
        st.markdown("""
        <div class="auth-container">
            <div class="auth-title">🚀 Create Account</div>
        """, unsafe_allow_html=True)
        
        # Signup form
        with st.form("signup_form"):
            st.markdown("### 👤 Personal Information")
            username = st.text_input("**Username**", placeholder="Choose a unique username")
            
            st.markdown("### 🔒 Security")
            password = st.text_input("**Password**", type="password", placeholder="Create a strong password")
            confirm_password = st.text_input("**Confirm Password**", type="password", placeholder="Re-enter your password")
            
            st.markdown("### 👥 Access Level")
            role = st.selectbox("**Select Your Role**", ["USER", "HR_TEAM", "LEGAL_TEAM", "MANAGEMENT_TEAM", "CEO"])
            
            submitted = st.form_submit_button("🎉 Create My Account", use_container_width=True)
            
            if submitted:
                if not username or not password:
                    st.error("❌ Please fill in all required fields")
                elif len(password) < 6:
                    st.error("❌ Password must be at least 6 characters long")
                elif password != confirm_password:
                    st.error("❌ Passwords do not match")
                else:
                    success, message = signup_user(username, password, role)
                    if success:
                        st.success(f"✅ {message}")
                        st.balloons()
                        st.info("🔄 Redirecting to login page...")
                        time.sleep(2)
                        st.session_state.page = "login"
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
        
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #666;'>
        Already have an account? 
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("➡️ Sign In Instead", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

def login_page():
    """Display modern login page."""
    # Remove all default padding and margins
    st.markdown("""
    <style>
    .main .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
    }
    .css-18e3th9 {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
    }
    .css-1d391kg {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Center the auth container
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Create the auth container with heading at the top
        st.markdown("""
        <div class="auth-container">
            <div class="auth-title">🔐 Welcome Back</div>
        """, unsafe_allow_html=True)
        
        # Login form
        with st.form("login_form"):
            st.markdown("### 👤 Account Details")
            username = st.text_input("**Username**", placeholder="Enter your username")
            password = st.text_input("**Password**", type="password", placeholder="Enter your password")
            
            st.markdown("### 👥 Access Level")
            role = st.selectbox("**Select Your Role**", ["USER", "HR_TEAM", "LEGAL_TEAM", "MANAGEMENT_TEAM", "CEO"])
            
            submitted = st.form_submit_button("🚀 Sign In to VisaBot", use_container_width=True)
            
            if submitted:
                if not username or not password:
                    st.error("❌ Please fill in all fields")
                else:
                    success, message, user_role = verify_user(username, password, role)
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.current_user = username
                        st.session_state.current_role = user_role  # Use the stored role from database
                        st.session_state.page = "main"
                        st.success(f"✅ {message}")
                        st.balloons()
                        st.info(f"👋 Welcome back {username}! | Role: {user_role}")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
        
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #666;'>
        New to VisaBot? 
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📝 Create New Account", use_container_width=True):
            st.session_state.page = "signup"
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent # THE LATEST AND SIMPLEST IMPORT

# --- Make sure your tools can be imported ---
try:
    from src.api.main_tools import Get_Visa_Details, Approve_Visa_Workflow, Create_Visa_Application, rag_visa_query, patch_application , get_embassy_status, validate_document_content, get_pending_approvals
except ImportError:
    st.error("Could not import agent tools. Make sure 'src/api/main_tools.py' is accessible.")
    # Dummy functions for app loading
    def Get_Visa_Details(): pass
    def Approve_Visa_Workflow(): pass
    def Create_Visa_Application(): pass
    def rag_visa_query(): pass
    def patch_application(): pass

def initialize_langchain_agent():
    """
    Initializes the LangChain agent executor using the high-level `create_agent` factory function.
    """
    # Use the GOOGLE_API_KEY from st.secrets if deployed, otherwise from environment
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        st.error("Google API Key not found in secrets.toml. Please add it.")
        return None
    
    if not api_key:
        st.error("Google API Key is not set. Please add it to your secrets or environment variables.")
        return None

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key, convert_system_message_to_human=True)
    
    tools = [Get_Visa_Details, Approve_Visa_Workflow, Create_Visa_Application, rag_visa_query, patch_application  , get_embassy_status , validate_document_content,get_pending_approvals]
    
   
    # --- START: REFINED PROMPT ---

    # Get user details from session state for clarity in the prompt.
    # Using .get() provides a fallback if the keys are missing for any reason.
    current_user = st.session_state.current_user or 'Unknown User'
    current_role = st.session_state.current_role or 'Unknown Role'
    print(f"Initializing agent for user: {current_user}, role: {current_role}")  # Debug log
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", f"""You are VisaBot, a professional and secure visa application assistant.

            ---
            **USER CONTEXT (Strict & Pre-Verified):**
            - **User Name:** {current_user}
            - **User Role:** {current_role}
            ---

            **CRITICAL INSTRUCTIONS:**
            1. **Strict Role Enforcement:** Your actions are strictly governed by the **User Role** provided above. You will only perform actions that the user's role is explicitly authorized to do.
            2. **Approval Authority is Absolute:** The only roles permitted to approve visa applications are 'hr_team', 'legal_team', 'management_team', and 'ceo'. There are no exceptions.
            3. **Direct and Final Denial:** If a user with any role other than an authorized approver role attempts to approve an application, you MUST bluntly and directly deny the request.
                - Your response must clearly state that their role of '{current_role}' does not have the required permissions.
                - **DO NOT** ask if they are acting on behalf of someone else.
                - **DO NOT** suggest any workarounds or alternative paths to approval. The denial is final.
            4. **User Identity is Pre-Verified:** The user's name and role are definitive and not to be questioned. Do not ask the user for this information. All actions are performed on behalf of '{current_user}' as '{current_role}'.
            5. **Maintain a Professional Tone:** Your communication should be direct, secure, and professional at all times.
            """),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")

        ]
    )
    
    st.session_state.prompt = prompt
    # --- THIS IS THE NEW, SIMPLIFIED LOGIC ---
    # create_agent handles creating the agent AND the AgentExecutor in one step.
    # The returned object is the agent executor runnable itself.
    agent_executor = create_agent(llm, tools)
    
    return agent_executor

def initialize_session_state():
    """Initialize session state variables."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_user' not in st.session_state:
        print("Initializing current_user in session state")  # Debug log
        st.session_state.current_user = None
    if 'current_role' not in st.session_state:
        st.session_state.current_role = None
    if 'page' not in st.session_state:
        st.session_state.page = "login"
        
    # LangChain agent chat history (stores message objects)
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
        
    # History for display purposes (stores simple dicts)
    if 'display_history' not in st.session_state:
        st.session_state.display_history = []
        
    if 'conversation_started' not in st.session_state:
        st.session_state.conversation_started = False
    if 'application_id' not in st.session_state:
        st.session_state.application_id = None
    if 'applicant_name' not in st.session_state:
        st.session_state.applicant_name = ""

    if "user_input_box" not in st.session_state:
        st.session_state.user_input_box = ""
    # Initialize the LangChain agent and store it in the session state
    # if 'agent_executor' not in st.session_state:
    #     st.session_state.agent_executor = initialize_langchain_agent()


def process_user_input(user_input: str) -> str:
    """
    Processes user input using the LangChain agent, manages history,
    and returns the bot's final response.
    
    Args:
        user_input: The question or command from the user.

    Returns:
        The text response from the chatbot.
    """
    # Retrieve the initialized agent executor from the session state

    if 'agent_executor' not in st.session_state:
        st.session_state.agent_executor = initialize_langchain_agent()
    agent_executor = st.session_state.agent_executor

     # Retrieve the prompt template from session state
    prompt = st.session_state.prompt
    pi = prompt.invoke({"input": user_input, "chat_history": st.session_state.chat_history})
    # This prompt structure remains the same. It's the standard for conversational agents.
    
    if agent_executor is None:
        return "The AI assistant is not available at the moment. Please check the API key configuration."

    try:
        # Invoke the agent. The agent needs the input, and the chat history for context.
        # The agent will decide if it needs to call a tool or just respond.
        print(f"Invoking agent with input:{pi}")  # Debug log
        response = agent_executor.invoke(pi)
        print(f"Agent response: {response}")  # Debug log
        # The final answer from the agent is in the 'output' key

 # --- START OF CORRECTED LOGIC ---
        # The new `create_agent` returns the full message history in the 'messages' key.
        # We need to extract the content from the last AIMessage.
        bot_response = ""
        if 'messages' in response and isinstance(response['messages'], list) and response['messages']:
            # Get the last message from the list
            last_message = response['messages'][-1]
            print(f"Last message from agent: {last_message}")  # Debug log
            # Check if it's an AIMessage and get its content
            if isinstance(last_message, AIMessage):
                bot_response = last_message.content
        
        # Fallback if the expected structure isn't found, or if another agent type returns 'output'
        if not bot_response:
             bot_response = response.get("output", "I'm sorry, I couldn't process the response correctly.")
             # Add a debug message in the terminal if parsing fails
             print(f"DEBUG: Could not parse AIMessage from agent response: {response}")

        # --- END OF CORRECTED LOGIC ---
        # Append the interaction to the LangChain history
        st.session_state.chat_history.append(HumanMessage(content=user_input))
        st.session_state.chat_history.append(AIMessage(content=bot_response))
        print(f"Updated chat history: {st.session_state.chat_history}")  # Debug log
        return bot_response

    except Exception as e:
        # Provide a user-friendly error message
        error_message = f"I apologize, but I encountered an error. This could be due to a tool issue or a network problem. Please try again. (Details: {str(e)})"
        
        # Also log the full error to the console for debugging
        print(f"Error invoking agent: {e}") 
        
        return error_message




from typing import Any # Make sure this import is at the top of your file

def display_chat_message(role: str, content: Any):
    """
    Display a chat message with appropriate styling. This function is designed to
    robustly parse the AIMessage.content, which can be a string or a list
    containing dictionaries with a 'text' key, and extract only the human-readable text.
    """
    
    # --- START OF NEW, MORE INTELLIGENT PARSING LOGIC ---
    
    final_text_to_display = ""

    if isinstance(content, list):
        # If content is a list, iterate through its parts to find the text.
        text_parts = []
        for part in content:
            if isinstance(part, dict) and 'text' in part:
                # This is the most common structure: a dictionary with a 'text' key.
                text_parts.append(part['text'])
            elif isinstance(part, str):
                # Sometimes, simple text parts can also be in the list.
                text_parts.append(part)
        
        # Join all the collected text parts together.
        final_text_to_display = "\n".join(text_parts)

    elif isinstance(content, str):
        # If the content is already a simple string, just use it.
        final_text_to_display = content
        
    else:
        # As a fallback, convert any other type to its string representation.
        final_text_to_display = str(content)
        
    # --- END OF NEW LOGIC ---

    if role == "user":
        # User messages are always simple strings.
        st.markdown(f'<div class="user-message"><strong>👤 You:</strong> {final_text_to_display}</div>', unsafe_allow_html=True)
    else:
        # For assistant messages, perform the final HTML formatting on the clean text.
        import re
        # Format **bold** text
        formatted_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', final_text_to_display)
        # Convert markdown-style lists (* item) to HTML lists
        formatted_content = re.sub(r'^\* (.*)', r'<li>\1</li>', formatted_content, flags=re.MULTILINE)
        if '<li>' in formatted_content:
            formatted_content = f'<ul>{formatted_content}</ul>'
        # Convert newlines to <br> tags
        formatted_content = formatted_content.replace('\n', '<br>')

        st.markdown(f'<div class="assistant-message"><strong>🤖 VisaBot:</strong> {formatted_content}</div>', unsafe_allow_html=True)

def get_role_color_class(role):
    """Get CSS class for role-specific styling"""
    role_lower = role.lower()
    if role_lower == "user":
        return "role-user"
    elif role_lower == "hr_team":
        return "role-hr"
    elif role_lower == "legal_team":
        return "role-legal"
    elif role_lower == "management_team" or role_lower == "ceo":
        return "role-manager"
    else:
        return ""

# Place this function BEFORE your main_app() function
def handle_chat_submission():
    """
    This function is called when the user clicks the 'Send Message' button.
    It processes the user input, calls the agent, and updates the chat history.
    """
    # Get the current user input from the session_state
    user_input = st.session_state.user_input_box
    if not user_input:
        return # Do nothing if the input is empty

    # Add user message to the display list immediately
    st.session_state.display_history.append({"role": "user", "content": user_input})
    st.session_state.conversation_started = True
    
    # Get the bot's response
    with st.spinner("🔍 VisaBot is thinking..."):
        bot_response = process_user_input(user_input)
    
    # Add the bot's response to the display list
    st.session_state.display_history.append({"role": "assistant", "content": bot_response})
    
    # IMPORTANT: Clear the input box for the next message after processing
    st.session_state.user_input_box = ""
    st.session_state.user_input = ""

def main_app():
    """Main visa assistant application with modern UI"""
    # Custom background for main app
    st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header with user info
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    with col1:
        st.markdown('<div class="main-header">🌍 Visa Assistant Pro</div>', unsafe_allow_html=True)
    with col2:
        role_class = get_role_color_class(st.session_state.current_role)
        st.markdown(f'<div class="feature-card {role_class}" style="text-align: center;"><strong>👤 User</strong><br>{st.session_state.current_user}</div>', unsafe_allow_html=True)
    with col3:
        role_class = get_role_color_class(st.session_state.current_role)
        st.markdown(f'<div class="feature-card {role_class}" style="text-align: center;"><strong>👥 Role</strong><br>{st.session_state.current_role}</div>', unsafe_allow_html=True)
    with col4:
        if st.button("🚪 Logout", use_container_width=True):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.session_state.current_role = None
            st.session_state.page = "login"
            st.rerun()
    
    # Main content with tabs - UPDATED: REMOVED "MY APPLICATION" TAB
    tab1, tab2, tab3 = st.tabs(["💬 Chat Assistant", "🌍 Visa Info", "🔍 Database"])
    
    with tab1:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("💬 Chat with VisaBot")
            
            # Chat area
            st.markdown('<div class="chat-area">', unsafe_allow_html=True)
            
            # Display chat history
            for message in st.session_state.display_history:
                display_chat_message(message["role"], message["content"])
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Welcome message for new conversations
            if not st.session_state.conversation_started and not st.session_state.chat_history:
                st.markdown("""
                <div class="welcome-message">
                <h3>👋 Welcome to Visa Assistant Pro!</h3>
                <p>I'm your AI-powered visa expert, here to make your visa application process smooth and stress-free! 🎉</p>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 20px;">
                    <div class="feature-card">
                        <strong>📋 Document Checklists</strong>
                        <p>Get precise requirements for any country</p>
                    </div>
                    <div class="feature-card">
                        <strong>⏰ Processing Times</strong>
                        <p>Know exactly how long it will take</p>
                    </div>
                    <div class="feature-card">
                        <strong>💰 Fee Information</strong>
                        <p>Clear cost breakdowns</p>
                    </div>
                    <div class="feature-card">
                        <strong>📝 Application Help</strong>
                        <p>Step-by-step guidance</p>
                    </div>
                </div>
                
                <p style="margin-top: 20px;"><strong>💡 Try asking me:</strong></p>
                <ul>
                <li>"What do I need for a France tourist visa?" 🇫🇷</li>
                <li>"How to apply for USA business visa?" 🇺🇸</li>
                <li>"Create a new visa application for Japan" 🇯🇵</li>
                <li>"My name is Sarah, I want to apply for UK tourist visa" 🇬🇧</li>
                </ul>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.subheader("🚀 Quick Actions")
            
            # Quick country buttons
            st.markdown("**🌍 Popular Destinations:**")
            countries = [
                ("🇫🇷 France", "France tourist visa requirements"),
                ("🇩🇪 Germany", "Germany visa requirements for tourism"),
                ("🇯🇵 Japan", "What do I need for Japan tourist visa?"),
                ("🇺🇸 USA", "USA tourist visa requirements"),
                ("🇬🇧 UK", "UK tourist visa requirements")
            ]
            
            for country, query in countries:
                if st.button(country, use_container_width=True, key=f"btn_{country}"):
                    st.session_state.user_input = query
                    st.rerun()
            
            st.markdown("---")
            st.markdown("**📝 Application Tools:**")
            if st.button("🆕 Start New Application", use_container_width=True):
                st.session_state.user_input = "I want to create a new tourist visa application"
            
            if st.button("🧹 Clear Chat History", use_container_width=True):
                st.session_state.chat_history = []
                st.session_state.conversation_started = False
                st.session_state.tool_calls = []
                st.rerun()
    
    with tab2:
        st.subheader("🌍 Global Visa Information")
        
        # Country info cards
        countries_info = {
            "France": {"fee": "€80", "processing": "15-20 days", "emoji": "🇫🇷", "popular": "Tourist, Business"},
            "Germany": {"fee": "€75", "processing": "10-15 days", "emoji": "🇩🇪", "popular": "Tourist, Work"},
            "Japan": {"fee": "€25", "processing": "5-7 days", "emoji": "🇯🇵", "popular": "Tourist, Business"},
            "USA": {"fee": "$185", "processing": "3-5 days", "emoji": "🇺🇸", "popular": "Tourist, Business"},
            "UK": {"fee": "£115", "processing": "3 weeks", "emoji": "🇬🇧", "popular": "Tourist, Study"}
        }
        
        cols = st.columns(3)
        for idx, (country, info) in enumerate(countries_info.items()):
            with cols[idx % 3]:
                st.markdown(f"""
                <div class="feature-card">
                    <h4>{info['emoji']} {country}</h4>
                    <p><strong>Fee:</strong> {info['fee']}</p>
                    <p><strong>Processing:</strong> {info['processing']}</p>
                    <p><strong>Popular:</strong> {info['popular']}</p>
                    <p><em>Ask me for detailed requirements!</em></p>
                </div>
                """, unsafe_allow_html=True)
    
    with tab3:  # DATABASE TAB
        view_database()
    
    # Chat input section (always visible)
    st.markdown("---")
    st.markdown("### 💭 Ask VisaBot Anything")
    
    if 'input_processed' not in st.session_state:
        st.session_state.input_processed = False

    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input(
            "Type your question about visas, requirements, or applications...", 
            key="user_input",
            placeholder="e.g., 'What documents do I need for a France tourist visa?' or 'Help me create a new application'",
            label_visibility="collapsed"
        )
        st.session_state.user_input_box = user_input  # Sync with session state
        

    
    with col2:
        st.button("🚀 Send Message", use_container_width=True,on_click=handle_chat_submission)

        # print("Show upload UI state:", st.session_state.show_upload_ui)  # Debug log
 
        appid = st.text_input("Enter Application ID")
        doctype = st.selectbox("type of Document:", ["passport", "passport_photos", "employment_letter", "invitation_letter", "bank_statement", "flight_itinerary", "hotel_booking",
"employment_contract", "qualification_certificates"])
 
        st.markdown("### 📎 Attach Documents")
        uploaded_file = st.file_uploader(
        "Upload your passport, photos, or other documents here.",
        type=['pdf', 'png', 'jpg', 'jpeg'],
        accept_multiple_files=False,  # Set to True to allow multiple files
        key="file_uploader"
    )
        if uploaded_file is not None:
            # Display a confirmation message and a preview
           
            # To display an image preview
            if uploaded_file.type in ["image/jpeg", "image/png"]:
                st.image(uploaded_file, caption="Uploaded Image Preview", width=300)
 
            if st.button("Process Uploaded Document"):
                with st.spinner("Processing document..."):                  
                        # Convert to Base64
                    file_bytes = uploaded_file.read()
                    encoded_string = base64.b64encode(file_bytes).decode("utf-8")
                    doclist = Document(
                        filename=uploaded_file.name,
                        type=doctype,
                        file_path=encoded_string
                    )
                   
 
                   
 
                    print(f"> Prepared Document List: {doclist}")
                    endpoint_url = f"http://localhost:8001/api/visa/applications/{appid}/upload-documents"
                    try:
                        response = requests.post(endpoint_url,json = doclist.model_dump(mode="json")  , timeout=60)
                        response.raise_for_status()
                        print(f"> API Response ({response.status_code}): {response.json()}")
                        st.success("Document(s) processed successfully!")
 
                    except requests.exceptions.RequestException as e:
                        print(f"> Network/API error occurred: {e}")
                        if e.response:
                            print(f"> Server Response Body: {e.response.text}")
def main():
    # Initialize database and session state
    init_db()
    initialize_session_state()
    
    # Route to appropriate page
    if not st.session_state.authenticated:
        if st.session_state.page == "signup":
            signup_page()
        else:
            login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()

    