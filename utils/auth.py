import streamlit as st
import hmac
from config import USER_EMAIL, USER_PASSWORD

def check_password():
    """
    Returns True if the user entered the correct password and email
    """
    if 'authenticated' in st.session_state and st.session_state['authenticated']:
        return True

    if 'login_attempts' not in st.session_state:
        st.session_state['login_attempts'] = 0

    authentication_status = False

    with st.form("login_form"):
        st.markdown("<h1 style='text-align: center;'>Welcome to Product Generator</h1>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            email = st.text_input("Email", key="email_input")
            password = st.text_input("Password", type="password", key="password_input")
            
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                # Verify username and password
                if email == USER_EMAIL and password == USER_PASSWORD:
                    st.session_state['authenticated'] = True
                    st.session_state['email'] = email
                    authentication_status = True
                    st.success("Login successful!")
                else:
                    st.session_state['login_attempts'] += 1
                    if st.session_state['login_attempts'] >= 3:
                        st.error("Too many login attempts. Please try again later.")
                    else:
                        st.error("Invalid email or password")

    # If the form was just submitted and the credentials were correct, reload the page
    if authentication_status:
        st.experimental_rerun()

    return False

def logout():
    """
    Logs out the user by resetting the session state
    """
    if 'authenticated' in st.session_state:
        del st.session_state['authenticated']
    if 'email' in st.session_state:
        del st.session_state['email']
    return True
