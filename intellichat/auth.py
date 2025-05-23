import streamlit as st
import re
from database import create_user, verify_user, get_user_by_id

def init_session_state():
    """Initialize session state variables if they don't exist."""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'current_chat_id' not in st.session_state:
        st.session_state.current_chat_id = None
    if 'use_context' not in st.session_state:
        st.session_state.use_context = False

def is_valid_email(email):
    """Validate email format."""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))

def is_valid_username(username):
    """Validate username format."""
    # Alphanumeric and underscore, 3-20 characters
    username_pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return bool(re.match(username_pattern, username))

def is_valid_password(password):
    """Validate password strength."""
    # At least 8 characters
    # return len(password) >= 3
    return True

def login_form():
    """Display and process the login form."""
    st.subheader("Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if not username or not password:
                st.error("Please fill in all fields.")
                return
            
            user_id = verify_user(username, password)
            
            if user_id:
                st.session_state.logged_in = True
                st.session_state.user_id = user_id
                st.session_state.username = username
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password.")

def signup_form():
    """Display and process the signup form."""
    st.subheader("Sign Up")
    
    with st.form("signup_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        password_confirm = st.text_input("Confirm Password", type="password")
        submit = st.form_submit_button("Sign Up")
        
        if submit:
            # Validate inputs
            if not all([username, email, password, password_confirm]):
                st.error("Please fill in all fields.")
                return
            
            if not is_valid_username(username):
                st.error("Username must be 3-20 characters and contain only letters, numbers, and underscores.")
                return
                
            if not is_valid_email(email):
                st.error("Please enter a valid email address.")
                return
                
            if not is_valid_password(password):
                st.error("Password must be at least 8 characters.")
                return
                
            if password != password_confirm:
                st.error("Passwords do not match.")
                return
            
            # Create user
            user_id = create_user(username, email, password)
            
            if user_id:
                st.success("Account created successfully! Please log in.")
                st.session_state.show_login = True
                st.rerun()
            else:
                st.error("Username or email already exists.")

def logout():
    """Log the user out and reset session state."""
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.current_chat_id = None
    st.rerun()

def auth_page():
    """Display the authentication page (login/signup)."""
    init_session_state()
    
    st.title("Chat Application")
    
    if st.session_state.logged_in:
        return True
    
    # Toggle between login and signup
    if 'show_login' not in st.session_state:
        st.session_state.show_login = True
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login", use_container_width=True, 
                    type="primary" if st.session_state.show_login else "secondary"):
            st.session_state.show_login = True
    
    with col2:
        if st.button("Sign Up", use_container_width=True,
                    type="primary" if not st.session_state.show_login else "secondary"):
            st.session_state.show_login = False
    
    if st.session_state.show_login:
        login_form()
    else:
        signup_form()
    
    return False