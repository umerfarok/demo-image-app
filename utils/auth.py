import streamlit as st
import hmac
from config import USER_EMAIL, USER_PASSWORD
import uuid

# Add this function to check localStorage auth and redirect if needed
def require_auth():
    """
    Checks if a user is authenticated, either via session state or localStorage.
    - If authenticated via session state: returns True
    - If authenticated via localStorage only: triggers a page reload to restore session
    - If not authenticated: redirects to login page and returns False
    
    Call this at the beginning of any page that requires authentication.
    """
    # If authenticated in session state, we're good
    if 'authenticated' in st.session_state and st.session_state['authenticated']:
        return True
    
    # Add a random parameter to avoid caching issues
    reload_id = str(uuid.uuid4())[:8]
    
    # Try to authenticate from localStorage or redirect to login
    js_code = f"""
    <script>
        // Check localStorage for auth
        const authenticated = localStorage.getItem('authenticated');
        const userEmail = localStorage.getItem('user_email');
        
        // If authenticated in localStorage but not in session state
        if (authenticated === 'true' && userEmail) {{
            // Reload the page to trigger a session state update via check_password
            if (!window.location.search.includes('auth_reload')) {{
                const url = new URL(window.location.href);
                url.searchParams.set('auth_reload', '{reload_id}');
                url.searchParams.set('user_email', userEmail);
                window.location.href = url.toString();
            }}
        }} 
        // If not authenticated at all, go to login page
        else if (!window.location.pathname.endsWith('/')) {{
            window.location.href = '/';
        }}
    </script>
    """
    st.components.v1.html(js_code, height=0)
    
    # Check if we're in the middle of an auth reload
    query_params = st.experimental_get_query_params()
    if 'auth_reload' in query_params and 'user_email' in query_params:
        # Verify the email matches our expected user
        if query_params['user_email'][0] == USER_EMAIL:
            # Set session state based on localStorage (trust localStorage on reload)
            st.session_state['authenticated'] = True
            st.session_state['email'] = query_params['user_email'][0]
            
            # Clear the auth_reload parameter
            st.experimental_set_query_params()
            
            # Ensure sidebar is shown now that we're authenticated
            show_sidebar()
            return True
    
    return False

def check_password():
    """
    Returns True if the user entered the correct password and email
    """
    # Check if we're already authenticated
    if 'authenticated' in st.session_state and st.session_state['authenticated']:
        return True

    # Check if there's authentication info in query parameters from localStorage
    query_params = st.experimental_get_query_params()
    if 'auth_reload' in query_params and 'user_email' in query_params:
        if query_params['user_email'][0] == USER_EMAIL:
            st.session_state['authenticated'] = True
            st.session_state['email'] = query_params['user_email'][0]
            st.experimental_set_query_params()
            show_sidebar()
            return True

    if 'login_attempts' not in st.session_state:
        st.session_state['login_attempts'] = 0

    authentication_status = False

    # Hide sidebar when not authenticated
    hide_sidebar()

    with st.form("login_form"):
        st.markdown("<h3 style='text-align: left;'>Login</h3>", unsafe_allow_html=True)
        
        st.markdown("<label>Email</label>", unsafe_allow_html=True)
        email = st.text_input("", placeholder="Value", key="email_input", label_visibility="collapsed")
        
        st.markdown("<label>Password</label>", unsafe_allow_html=True)
        password = st.text_input("", placeholder="Value", type="password", key="password_input", label_visibility="collapsed")
        
        submit = st.form_submit_button("Sign In", use_container_width=True)
        
        if submit:
            # Verify username and password
            if email == USER_EMAIL and password == USER_PASSWORD:
                st.session_state['authenticated'] = True
                st.session_state['email'] = email
                authentication_status = True
                
                # Save user data to localStorage
                save_to_local_storage(email)
                
                st.success("Login successful!")
            else:
                st.session_state['login_attempts'] += 1
                if st.session_state['login_attempts'] >= 3:
                    st.error("Too many login attempts. Please try again later.")
                else:
                    st.error("Invalid email or password")

    # If the form was just submitted and the credentials were correct, reload the page
    if authentication_status:
        show_sidebar()
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
    
    # Clear localStorage on logout
    clear_local_storage()
    
    # Hide sidebar when logging out
    hide_sidebar()
    
    return True

def save_to_local_storage(email):
    """
    Saves user email to localStorage using JavaScript
    """
    js_code = f"""
    <script>
        localStorage.setItem('user_email', '{email}');
        localStorage.setItem('authenticated', 'true');
    </script>
    """
    st.markdown(js_code, unsafe_allow_html=True)

def clear_local_storage():
    """
    Clears user data from localStorage using JavaScript
    """
    js_code = """
    <script>
        localStorage.removeItem('user_email');
        localStorage.removeItem('authenticated');
    </script>
    """
    st.markdown(js_code, unsafe_allow_html=True)

def hide_sidebar():
    """
    Hides the sidebar using CSS
    """
    st.markdown("""
    <style>
        [data-testid="stSidebar"] {display: none;}
    </style>
    """, unsafe_allow_html=True)

def show_sidebar():
    """
    Shows the sidebar using CSS
    """
    st.markdown("""
    <style>
        [data-testid="stSidebar"] {display: block;}
    </style>
    """, unsafe_allow_html=True)
