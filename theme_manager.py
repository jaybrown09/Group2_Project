import streamlit as st
import database as db
import os
import time

def apply_user_theme():
    # Get the theme that should be applied
    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        target_theme = 'light'
    else:
        settings = db.get_user_settings(st.session_state.user_id)
        target_theme = settings['theme'] if settings else 'light'
    
    # Always apply the CSS, regardless of what's in session_state
    theme_file = os.path.join("themes", f"{target_theme}.css")

    if os.path.exists(theme_file):
        with open(theme_file) as f:
            css = f.read()
        
        # Cache bust with timestamp to ensure latest CSS is loaded
        cache_bust = int(time.time())
        st.markdown(
            f"<style>/* v{cache_bust} */\n{css}</style>", 
            unsafe_allow_html=True
        )
        st.session_state['theme'] = target_theme  # Update after successful load
    else:
        st.warning(f"Theme file not found: {theme_file}")