import streamlit as st
import database as db
import theme_manager

theme_manager.apply_user_theme()

# Page config
st.set_page_config(
    page_title="Settings - Recipes For Success",
    page_icon="⚙️",
    layout="wide"
)

# Session check
if 'user_id' not in st.session_state or st.session_state.user_id is None:
    st.warning("⚠️ Please sign in first")
    st.stop()

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.title("⚙️ Settings")
with col2:
    if st.button("🏠 Dashboard", use_container_width=True):
        st.switch_page("pages/1_Dashboard.py")

st.markdown("---")

# Get current user settings
current_settings = db.get_user_settings(st.session_state.user_id)
if current_settings is None:
    current_settings = {'theme': 'light', 'landing_page': 'dashboard'}

# Ensure landing_page exists in settings (for backward compatibility)
if 'landing_page' not in current_settings:
    current_settings['landing_page'] = 'dashboard'

# === PROFILE SECTION ===
st.markdown('<div class="section-title">👤 Profile Information</div>', unsafe_allow_html=True)
st.markdown('<div class="section-description">View your account details and statistics</div>', unsafe_allow_html=True)

# Profile info
st.markdown(f"""
<div class="profile-info">
    <div class="profile-row">
        <span class="profile-label">Username:</span>
        <span class="profile-value">{st.session_state.username}</span>
    </div>
    <div class="profile-row">
        <span class="profile-label">User ID:</span>
        <span class="profile-value">#{st.session_state.user_id}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Get statistics
user_recipes = db.get_user_cookbook(st.session_state.user_id)
saved_recipes = db.get_saved_public_recipes(st.session_state.user_id)
pantry_items = db.get_user_pantry(st.session_state.user_id)
shopping_items = db.get_user_shopping_list(st.session_state.user_id)
meal_plans = db.get_user_meal_plan(st.session_state.user_id)

# Stats grid
st.markdown(f"""
<div class="stats-grid">
    <div class="stat-card">
        <div class="stat-number">{len(user_recipes)}</div>
        <div class="stat-label">My Recipes</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{len(saved_recipes)}</div>
        <div class="stat-label">Saved Recipes</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{len(pantry_items)}</div>
        <div class="stat-label">Pantry Items</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{len(shopping_items)}</div>
        <div class="stat-label">Shopping Items</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{len(meal_plans)}</div>
        <div class="stat-label">Planned Meals</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="settings-divider"></div>', unsafe_allow_html=True)

# === ACCOUNT MANAGEMENT SECTION ===
st.markdown('<div class="section-title">🔐 Account Management</div>', unsafe_allow_html=True)
st.markdown('<div class="section-description">Change your username or password</div>', unsafe_allow_html=True)

# Initialize session state for account management
if 'show_change_username' not in st.session_state:
    st.session_state.show_change_username = False
if 'show_change_password' not in st.session_state:
    st.session_state.show_change_password = False
if 'username_verified' not in st.session_state:
    st.session_state.username_verified = False
if 'password_verified' not in st.session_state:
    st.session_state.password_verified = False

col1, col2 = st.columns(2)
with col1:
    if st.button("✏️ Change Username", use_container_width=True):
        st.session_state.show_change_username = True
        st.session_state.show_change_password = False
        st.session_state.username_verified = False
        st.rerun()

with col2:
    if st.button("🔑 Change Password", use_container_width=True):
        st.session_state.show_change_password = True
        st.session_state.show_change_username = False
        st.session_state.password_verified = False
        st.rerun()

# Change Username Flow
if st.session_state.show_change_username:
    st.markdown("---")
    st.subheader("✏️ Change Username")
    
    if not st.session_state.username_verified:
        st.markdown("""
        <div class="info-box">
        <strong>🔒 Verification Required</strong><br>
        Please enter your current password to verify your identity.
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("verify_for_username"):
            current_password = st.text_input(
                "Current Password",
                type="password",
                placeholder="Enter your current password"
            )
            
            col_verify, col_cancel = st.columns(2)
            with col_verify:
                verify_btn = st.form_submit_button("🔓 Verify", type="primary", use_container_width=True)
            with col_cancel:
                cancel_btn = st.form_submit_button("❌ Cancel", use_container_width=True)
            
            if verify_btn:
                if current_password:
                    # Verify password
                    verified = db.verify_user(st.session_state.username, current_password)
                    if verified:
                        st.session_state.username_verified = True
                        st.session_state.temp_password = current_password
                        st.rerun()
                    else:
                        st.error("❌ Incorrect password. Please try again.")
                else:
                    st.error("❌ Please enter your current password.")
            
            if cancel_btn:
                st.session_state.show_change_username = False
                st.session_state.username_verified = False
                st.rerun()
    
    else:
        st.markdown("""
        <div class="success-box">
        <strong>✅ Identity Verified</strong><br>
        You can now change your username.
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("change_username_form"):
            new_username = st.text_input(
                "New Username",
                placeholder="Enter your new username (min 3 characters)"
            )
            confirm_username = st.text_input(
                "Confirm New Username",
                placeholder="Re-enter your new username"
            )
            
            col_save, col_cancel = st.columns(2)
            with col_save:
                save_btn = st.form_submit_button("💾 Save New Username", type="primary", use_container_width=True)
            with col_cancel:
                cancel_btn = st.form_submit_button("❌ Cancel", use_container_width=True)
            
            if save_btn:
                if not new_username:
                    st.error("❌ Please enter a new username.")
                elif new_username != confirm_username:
                    st.error("❌ Usernames do not match.")
                elif new_username == st.session_state.username:
                    st.error("❌ New username must be different from current username.")
                else:
                    result = db.change_username(
                        st.session_state.user_id,
                        st.session_state.temp_password,
                        new_username
                    )
                    
                    if isinstance(result, dict) and "error" in result:
                        st.error(f"❌ {result['error']}")
                    else:
                        # Update session state with new username
                        st.session_state.username = new_username
                        st.session_state.show_change_username = False
                        st.session_state.username_verified = False
                        if 'temp_password' in st.session_state:
                            del st.session_state.temp_password
                        st.success("✅ Username changed successfully!")
                        st.balloons()
                        import time
                        time.sleep(2)
                        st.rerun()
            
            if cancel_btn:
                st.session_state.show_change_username = False
                st.session_state.username_verified = False
                if 'temp_password' in st.session_state:
                    del st.session_state.temp_password
                st.rerun()

# Change Password Flow
if st.session_state.show_change_password:
    st.markdown("---")
    st.subheader("🔑 Change Password")
    
    if not st.session_state.password_verified:
        st.markdown("""
        <div class="info-box">
        <strong>🔒 Verification Required</strong><br>
        Please enter your current password to verify your identity.
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("verify_for_password"):
            current_password = st.text_input(
                "Current Password",
                type="password",
                placeholder="Enter your current password"
            )
            
            col_verify, col_cancel = st.columns(2)
            with col_verify:
                verify_btn = st.form_submit_button("🔓 Verify", type="primary", use_container_width=True)
            with col_cancel:
                cancel_btn = st.form_submit_button("❌ Cancel", use_container_width=True)
            
            if verify_btn:
                if current_password:
                    # Verify password
                    verified = db.verify_user(st.session_state.username, current_password)
                    if verified:
                        st.session_state.password_verified = True
                        st.session_state.temp_password = current_password
                        st.rerun()
                    else:
                        st.error("❌ Incorrect password. Please try again.")
                else:
                    st.error("❌ Please enter your current password.")
            
            if cancel_btn:
                st.session_state.show_change_password = False
                st.session_state.password_verified = False
                st.rerun()
    
    else:
        st.markdown("""
        <div class="success-box">
        <strong>✅ Identity Verified</strong><br>
        You can now change your password.
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("change_password_form"):
            new_password = st.text_input(
                "New Password",
                type="password",
                placeholder="Enter your new password (min 8 characters)"
            )
            confirm_password = st.text_input(
                "Confirm New Password",
                type="password",
                placeholder="Re-enter your new password"
            )
            
            # Password strength indicator
            if new_password:
                strength = 0
                feedback = []
                if len(new_password) >= 8:
                    strength += 1
                else:
                    feedback.append("At least 8 characters")
                if any(c.isupper() for c in new_password):
                    strength += 1
                else:
                    feedback.append("At least one uppercase letter")
                if any(c.islower() for c in new_password):
                    strength += 1
                else:
                    feedback.append("At least one lowercase letter")
                if any(c.isdigit() for c in new_password):
                    strength += 1
                else:
                    feedback.append("At least one number")
                if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in new_password):
                    strength += 1
                else:
                    feedback.append("At least one special character")
                
                if strength <= 2:
                    st.warning(f"⚠️ Weak password. Consider adding: {', '.join(feedback)}")
                elif strength <= 4:
                    st.info(f"💪 Good password. To make it stronger, add: {', '.join(feedback)}")
                else:
                    st.success("🔒 Strong password!")
            
            col_save, col_cancel = st.columns(2)
            with col_save:
                save_btn = st.form_submit_button("💾 Save New Password", type="primary", use_container_width=True)
            with col_cancel:
                cancel_btn = st.form_submit_button("❌ Cancel", use_container_width=True)
            
            if save_btn:
                if not new_password:
                    st.error("❌ Please enter a new password.")
                elif new_password != confirm_password:
                    st.error("❌ Passwords do not match.")
                elif len(new_password) < 8:
                    st.error("❌ Password must be at least 8 characters.")
                else:
                    result = db.change_password(
                        st.session_state.user_id,
                        st.session_state.temp_password,
                        new_password
                    )
                    
                    if isinstance(result, dict) and "error" in result:
                        st.error(f"❌ {result['error']}")
                    else:
                        st.session_state.show_change_password = False
                        st.session_state.password_verified = False
                        if 'temp_password' in st.session_state:
                            del st.session_state.temp_password
                        st.success("✅ Password changed successfully!")
                        st.balloons()
                        import time
                        time.sleep(2)
                        st.rerun()
            
            if cancel_btn:
                st.session_state.show_change_password = False
                st.session_state.password_verified = False
                if 'temp_password' in st.session_state:
                    del st.session_state.temp_password
                st.rerun()

st.markdown('<div class="settings-divider"></div>', unsafe_allow_html=True)

# === PREFERENCES SECTION ===
st.markdown('<div class="section-title">🎨 Preferences</div>', unsafe_allow_html=True)
st.markdown('<div class="section-description">Customize your app experience</div>', unsafe_allow_html=True)

# Landing page options mapping
landing_page_options = {
    'dashboard': '🏠 Dashboard',
    'pantry': '🥫 Pantry',
    'shopping_list': '🛒 Shopping List',
    'meal_plan': '📅 Meal Plan'
}

# Get current landing page index
current_landing = current_settings.get('landing_page', 'dashboard')
landing_keys = list(landing_page_options.keys())
current_landing_index = landing_keys.index(current_landing) if current_landing in landing_keys else 0

with st.form("preferences_form"):
    theme = st.selectbox(
        "Theme",
        options=["light", "dark"],
        index=0 if current_settings.get('theme', 'light') == 'light' else 1,
    )
    
    landing_page = st.selectbox(
        "Default Landing Page",
        options=landing_keys,
        format_func=lambda x: landing_page_options[x],
        index=current_landing_index,
        help="Choose which page to show after signing in"
    )
    
    if st.form_submit_button("💾 Save Preferences", type="primary", use_container_width=True):
        db.update_user_settings(st.session_state.user_id, theme, landing_page)
        st.markdown('<div class="success-box">✅ Preferences saved successfully!</div>', unsafe_allow_html=True)
        st.rerun()

st.markdown('<div class="settings-divider"></div>', unsafe_allow_html=True)

# === DATA MANAGEMENT SECTION ===
st.markdown('<div class="section-title">📊 Data Management</div>', unsafe_allow_html=True)
st.markdown('<div class="section-description">Export or manage your data</div>', unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
<strong>📦 Data Export (Coming Soon)</strong><br>
Export your recipes, meal plans, and pantry data to backup or transfer to another device.
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    if st.button("📥 Export My Data", use_container_width=True, disabled=True):
        st.info("Data export feature coming soon!")

with col2:
    if st.button("📊 View Activity Log", use_container_width=True, disabled=True):
        st.info("Activity log feature coming soon!")

st.markdown('<div class="settings-divider"></div>', unsafe_allow_html=True)

# === DANGER ZONE ===
st.markdown('<div class="section-title">⚠️ Danger Zone</div>', unsafe_allow_html=True)
st.markdown('<div class="section-description">Irreversible actions that affect your account</div>', unsafe_allow_html=True)

st.markdown("""
<div class="warning-box">
<strong>⚠️ Warning:</strong> The actions below are permanent and cannot be undone. Please proceed with caution.
</div>
""", unsafe_allow_html=True)

# Reset Data Button
if st.button("🔄 Reset All Data", use_container_width=True, type="secondary"):
    st.session_state.confirm_reset = True

# Reset Confirmation
if 'confirm_reset' in st.session_state and st.session_state.confirm_reset:
    st.markdown("---")
    st.markdown("""
    <div class="warning-box">
    <strong>🚨 FINAL WARNING</strong><br><br>
    This will permanently delete:<br>
    • All your recipes ({} recipes)<br>
    • All saved recipes ({} recipes)<br>
    • Your entire pantry ({} items)<br>
    • Your shopping list ({} items)<br>
    • Your meal plans ({} planned meals)<br>
    • Reset your preferences to default<br><br>
    <strong>This action CANNOT be undone!</strong>
    </div>
    """.format(
        len(user_recipes),
        len(saved_recipes),
        len(pantry_items),
        len(shopping_items),
        len(meal_plans)
    ), unsafe_allow_html=True)
    
    st.text_input(
        "Type 'DELETE ALL MY DATA' to confirm:",
        key="reset_confirmation",
        placeholder="Type here to confirm..."
    )
    
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("🗑️ Yes, Delete Everything", type="primary", use_container_width=True):
            if st.session_state.get('reset_confirmation') == 'DELETE ALL MY DATA':
                db.reset_user_data(st.session_state.user_id)
                st.session_state.confirm_reset = False
                st.success("✅ All data has been reset!")
                st.balloons()
                import time
                time.sleep(2)
                st.rerun()
            else:
                st.error("❌ Please type 'DELETE ALL MY DATA' exactly to confirm")
    
    with col_no:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.confirm_reset = False
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="settings-divider"></div>', unsafe_allow_html=True)

# === ABOUT SECTION ===
st.markdown('<div class="section-title">ℹ️ About</div>', unsafe_allow_html=True)
st.markdown('<div class="section-description">Information about Recipes For Success</div>', unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
<strong>📱 Recipes For Success v1.0</strong><br><br>
A comprehensive recipe management and meal planning application designed to help you organize your culinary journey.
<br><br>
<strong>Features:</strong><br>
• 📖 Personal & Public Recipe Management<br>
• 🥫 Smart Pantry Tracking<br>
• 🛒 Dynamic Shopping Lists<br>
• 📅 Weekly Meal Planning<br>
• 🔒 Secure User Authentication<br>
<br>
<strong>Made with ❤️ using Streamlit and SQLite</strong>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("📚 Documentation", use_container_width=True, disabled=True):
        st.info("Documentation coming soon!")
with col2:
    if st.button("💬 Support", use_container_width=True, disabled=True):
        st.info("Support coming soon!")
with col3:
    if st.button("🐛 Report Bug", use_container_width=True, disabled=True):
        st.info("Bug reporting coming soon!")

st.markdown('</div>', unsafe_allow_html=True)

# === LOGOUT SECTION ===
st.markdown("---")

col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("🚪 Logout", use_container_width=True, type="primary"):
        # Clear session state - store keys first to avoid modification during iteration
        keys_to_clear = list(st.session_state.keys())
        for key in keys_to_clear:
            del st.session_state[key]
        # Redirect immediately without any display operations
        st.switch_page("sign_in.py")

# Footer
st.markdown("---")
st.caption("Recipes For Success © 2025 • Made with ❤️ and a pinch of code")