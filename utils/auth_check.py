import streamlit as st

def check_authentication():
    """
    Simple authentication check to be used at the top of each page.
    Redirects to the main page if not authenticated.
    
    Returns:
        bool: True if authenticated, otherwise redirects
    """
    # Check if the user is authenticated
    if st.session_state.get("authentication_status") is not True:
        # Redirect to main page if not authenticated
        st.warning("You must be logged in to access this page.")
        st.info("Redirecting to login page...")
        
        # Add JavaScript for redirection
        redirect_js = """
        <script>
            setTimeout(function() {
                window.location.href = "/";
            }, 2000);  // Redirect after 2 seconds
        </script>
        """
        st.markdown(redirect_js, unsafe_allow_html=True)
        
        # Stop execution of the rest of the page
        st.stop()
        
    return True
