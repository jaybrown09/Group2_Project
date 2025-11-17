import streamlit as st
import database as db
import theme_manager

theme_manager.apply_user_theme()

#streamlit run sign_in.py

# Initialize database
db.init_DB()

# Page config
st.set_page_config(
    page_title="Recipes For Success - Sign In",
    page_icon="👨‍🍳",
    layout="centered"
)

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None

# Header
st.markdown("# 👨‍🍳 Recipes For Success")
st.markdown("### Your personal recipe manager")
st.markdown("---")

# Check if user is already logged in
if st.session_state.user_id:
    st.success(f"Welcome back, {st.session_state.username}!")
    st.info("You are already logged in. Navigate to other pages using the sidebar.")
    
    if st.button("Sign Out"):
        st.session_state.user_id = None
        st.session_state.username = None
        st.rerun()
else:
    # Toggle between Sign In and Create Account
    mode = st.radio("", ["Sign In", "Create Account"], horizontal=True)
    
    st.markdown("---")
    
    # Use st.form to enable Enter key submission
    with st.form(key="auth_form"):
        # Input fields
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if mode == "Create Account":
            st.caption("Password must be at least 8 characters")
        
        # Submit button (now inside form)
        submitted = st.form_submit_button(mode)
        
        if submitted:
            if not username or not password:
                st.error("⚠️ Please fill in all fields")
            else:
                if mode == "Create Account":
                    # Create new account
                    result = db.create_user(username, password)
                    
                    if isinstance(result, dict) and "error" in result:
                        st.error(f"⚠️ {result['error']}")
                    elif result == "Username Already Exists":
                        st.error("⚠️ Username already exists. Please choose a different username.")
                    else:
                        # Success - user_id returned
                        st.session_state.user_id = result
                        st.session_state.username = username
                        st.success(f"✅ Account created successfully! Welcome, {username}!")
                        st.switch_page("pages/1_Dashboard.py")
                
                else:
                    # Sign in existing user
                    user_id = db.verify_user(username, password)
                    
                    if user_id is None:
                        st.error("⚠️ Invalid username or password")
                    else:
                        # Success
                        st.session_state.user_id = user_id
                        st.session_state.username = username
                        st.success(f"✅ Welcome back, {username}!")
                        st.switch_page("pages/1_Dashboard.py")
    
    # Footer with instructions
    st.markdown("---")
    if mode == "Sign In":
        st.caption("Don't have an account? Select 'Create Account' above")
    else:
        st.caption("Already have an account? Select 'Sign In' above")