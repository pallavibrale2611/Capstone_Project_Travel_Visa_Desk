import streamlit as st
import os
import json
from typing import Dict, Any, List
from datetime import datetime
import hashlib
import sqlite3
import time
import pandas as pd
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_community.tools.tavily_search import TavilySearchResults

# --- This is a placeholder for your actual tools. ---
# --- Ensure you have a file named 'main_tools.py' in a 'src/api/' directory ---
# --- with your custom tools like Get_Visa_Details, etc. ---
try:
    # This is where you would import your actual, custom tools
    # from src.api.main_tools import Get_Visa_Details, Approve_Visa_Workflow, Create_Visa_Application, rag_visa_query, patch_application
    
    # For demonstration purposes, we will use a generic search tool.
    # Replace this with your actual tool list.
    tools = [TavilySearchResults(max_results=2)]
    
except ImportError:
    st.error("Could not import agent tools. Using a generic web search tool for demonstration.")
    # If your tools are not available, we use a default tool so the app can run.
    tools = [TavilySearchResults(max_results=2)]


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
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 0 !important;
        margin: 0 !important;
    }
    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        max-width: 100% !important;
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
    }
    /* Form & Button Styles */
    .stTextInput>div>div>input {
        background: rgba(255, 255, 255, 0.9);
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        padding: 12px 16px;
        font-size: 16px;
    }
    .stButton>button {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
        padding: 14px 28px;
        font-size: 16px;
        border-radius: 25px;
        font-weight: 600;
        box-shadow: 0 4px 15px 0 rgba(102, 126, 234, 0.3);
        width: 100%;
    }
    /* Chat Message Styles */
    .user-message {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 16px 20px;
        border-radius: 20px 20px 5px 20px;
        margin: 12px 0;
        margin-left: auto;
        max-width: 70%;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    .assistant-message {
        background: white;
        color: #333;
        padding: 16px 20px;
        border-radius: 20px 20px 20px 5px;
        margin: 12px 0;
        margin-right: auto;
        max-width: 70%;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        border: 1px solid #eee;
    }
    /* Card Styles */
    .feature-card {
        background: rgba(255, 255, 255, 0.95);
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05);
        border-left: 5px solid #667eea;
        color: black !important;
    }
    /* Welcome Message */
    .welcome-message {
        background: white;
        color: #333;
        padding: 30px;
        border-radius: 20px;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        border: 1px solid #eee;
    }
    /* Application Status */
    .application-status {
        background: linear-gradient(45deg, #FFA726, #FF9800);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
    }
    /* Role-specific styling */
    .role-user { border-left-color: #4CAF50 !important; }
    .role-hr { border-left-color: #2196F3 !important; }
    .role-legal { border-left-color: #FF9800 !important; }
    .role-manager { border-left-color: #9C27B0 !important; }
</style>
""", unsafe_allow_html=True)

# --- Database setup ---
DB_FILE = "users.db"

def init_db():
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
    default_users = [
        ("manager", "pass123", "MANAGER"),
        ("hr_user", "pass123", "HR"),
        ("legal_user", "pass123", "LEGAL"),
        ("user", "pass123", "USER")
    ]
    for username, password, role in default_users:
        c.execute(
            "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, hash_password(password), role)
        )
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def signup_user(username, password, role):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("SELECT username FROM users WHERE username = ?", (username,))
        if c.fetchone():
            return False, "Username already exists"
        c.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, hash_password(password), role.upper())
        )
        conn.commit()
        return True, "User created successfully"
    except sqlite3.IntegrityError:
        return False, "Username already exists"
    finally:
        conn.close()

def verify_user(username, password, role):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("SELECT password, role FROM users WHERE username = ?", (username,))
        result = c.fetchone()
        if not result:
            return False, "User not found", None
        stored_password, stored_role = result
        if stored_password == hash_password(password) and role.upper() == stored_role.upper():
            return True, "Login successful", stored_role
        elif stored_password != hash_password(password):
            return False, "Invalid password", None
        else:
            return False, f"Role '{role}' does not match your assigned role '{stored_role}'", None
    finally:
        conn.close()

# --- LangChain Agent Initialization ---
def initialize_langchain_agent():
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
    except (FileNotFoundError, KeyError):
        st.error("Google API Key not found. Please create a secrets.toml file with your GOOGLE_API_KEY.")
        return None

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key, convert_system_message_to_human=True)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are VisaBot, a helpful assistant for visa applications. Use the tools provided to assist with user queries. Be friendly and professional."),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # Use your actual tools list here
    # current_tools = [Get_Visa_Details, Approve_Visa_Workflow, Create_Visa_Application, rag_visa_query, patch_application]
    current_tools = tools # Using the placeholder tool
    
    agent = create_tool_calling_agent(llm, current_tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=current_tools, verbose=True)
    
    return agent_executor

# --- Session State Initialization ---
def initialize_session():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'page' not in st.session_state:
        st.session_state.page = "login"
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'agent_executor' not in st.session_state:
        st.session_state.agent_executor = initialize_langchain_agent()

# --- Chat Processing ---
def process_user_input(user_input: str):
    agent_executor = st.session_state.agent_executor
    if not agent_executor:
        return "The AI assistant is not available. Please check the API key configuration."

    try:
        # CORRECT INVOCATION: Pass a dictionary with keys matching the prompt variables
        response = agent_executor.invoke({
            "input": user_input,
            "chat_history": st.session_state.chat_history
        })
        
        bot_response = response.get("output", "I'm sorry, I couldn't process that. Please try again.")
        
        # Update history
        st.session_state.chat_history.append(HumanMessage(content=user_input))
        st.session_state.chat_history.append(AIMessage(content=bot_response))
        
        return bot_response
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        st.error(error_message)
        print(f"Error invoking agent: {e}")
        return "I apologize, but I encountered an error. Please check the logs or try again."

def handle_chat_submission():
    # CORRECT KEY: Read from "user_input_box" which matches the widget's key
    user_input = st.session_state.user_input_box
    if user_input:
        # Add user message to chat history for immediate display
        st.session_state.chat_history.append(HumanMessage(content=user_input))
        
        # Process and get bot response (this will also update the AIMessage part of history)
        with st.spinner("VisaBot is thinking..."):
            process_user_input(user_input) # The function now handles history updates
        
        # Clear the input box
        st.session_state.user_input_box = ""

# --- UI Components ---
def display_chat_message(message):
    if isinstance(message, HumanMessage):
        with st.chat_message("user"):
            st.markdown(message.content)
    elif isinstance(message, AIMessage):
        with st.chat_message("assistant"):
            st.markdown(message.content)

def login_page():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.container(border=True):
            st.markdown('<div class="auth-title">🔐 Welcome Back</div>', unsafe_allow_html=True)
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            role = st.selectbox("Select Your Role", ["USER", "HR", "LEGAL", "MANAGER"])
            
            if st.button("🚀 Sign In", use_container_width=True):
                success, message, user_role = verify_user(username, password, role)
                if success:
                    st.session_state.authenticated = True
                    st.session_state.current_user = username
                    st.session_state.current_role = user_role
                    st.session_state.page = "main"
                    st.success("Login successful! Redirecting...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(message)
            
            st.markdown("<hr style='margin: 2rem 0;'>", unsafe_allow_html=True)
            if st.button("📝 Create New Account", use_container_width=True, type="secondary"):
                st.session_state.page = "signup"
                st.rerun()

def signup_page():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.container(border=True):
            st.markdown('<div class="auth-title">🚀 Create Account</div>', unsafe_allow_html=True)
            username = st.text_input("Username", placeholder="Choose a unique username")
            password = st.text_input("Password", type="password", placeholder="Create a strong password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password")
            role = st.selectbox("Select Your Role", ["USER", "HR", "LEGAL", "MANAGER"])
            
            if st.button("🎉 Create My Account", use_container_width=True):
                if password != confirm_password:
                    st.error("Passwords do not match!")
                else:
                    success, message = signup_user(username, password, role)
                    if success:
                        st.success("Account created! Please log in.")
                        st.session_state.page = "login"
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(message)
            
            st.markdown("<hr style='margin: 2rem 0;'>", unsafe_allow_html=True)
            if st.button("➡️ Sign In Instead", use_container_width=True, type="secondary"):
                st.session_state.page = "login"
                st.rerun()

def get_role_color_class(role):
    return f"role-{role.lower()}"

def view_database():
    if st.session_state.current_role == "MANAGER":
        st.subheader("🔍 Database Viewer (Manager Only)")
        conn = sqlite3.connect(DB_FILE)
        try:
            st.markdown("### 👥 Users Table")
            users_df = pd.read_sql_query("SELECT id, username, role, created_at FROM users", conn)
            st.dataframe(users_df, use_container_width=True)
        finally:
            conn.close()
    else:
        st.warning("⛔ Access denied. Only Managers can view the database.")

def main_app():
    # Header
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
            st.session_state.authenticated = False
            st.session_state.page = "login"
            st.rerun()
            
    # Main Tabs
    tab1, tab2 = st.tabs(["💬 Chat Assistant", "🔍 Database Viewer"])

    with tab1:
        # Chat history display
        chat_container = st.container(height=500, border=False)
        with chat_container:
            for message in st.session_state.chat_history:
                display_chat_message(message)

        # Chat input at the bottom
        st.chat_input(
            "Ask VisaBot anything...", 
            key="user_input_box", # CORRECT KEY
            on_submit=handle_chat_submission
        )

    with tab2:
        view_database()

# --- Main App Router ---
def main():
    init_db()
    initialize_session()
    
    if not st.session_state.authenticated:
        if st.session_state.page == "signup":
            signup_page()
        else:
            login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()