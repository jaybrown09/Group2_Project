import streamlit as st
import database as db
import json
import theme_manager

theme_manager.apply_user_theme()

# Page config
st.set_page_config(
    page_title="Dashboard - Recipes For Success",
    page_icon="🏠",
    layout="wide"
)

# Check if user is logged in
if 'user_id' not in st.session_state or st.session_state.user_id is None:
    st.warning("⚠️ Please sign in first")
    st.stop()

# Check for landing page redirect (only on first visit after login)
if 'landing_page_checked' not in st.session_state:
    st.session_state.landing_page_checked = True
    
    # Get user settings to check default landing page
    user_settings = db.get_user_settings(st.session_state.user_id)
    if user_settings:
        landing_page = user_settings.get('landing_page', 'dashboard')
        
        # Redirect to the appropriate page if not dashboard
        if landing_page == 'pantry':
            st.switch_page("pages/3_Pantry.py")
        elif landing_page == 'shopping_list':
            st.switch_page("pages/4_Shopping_List.py")
        elif landing_page == 'meal_plan':
            st.switch_page("pages/5_Meal_Plan.py")
        # If 'dashboard', continue loading this page

# Header
st.title(f"🏠 Welcome back, {st.session_state.username}!")
st.markdown("---")

# Navigation buttons in columns
st.subheader("Quick Navigation")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📖 My Cookbook", use_container_width=True):
        st.switch_page("pages/2_Cookbook.py")
    if st.button("🥫 Pantry", use_container_width=True):
        st.switch_page("pages/3_Pantry.py")

with col2:
    if st.button("🛒 Shopping List", use_container_width=True):
        st.switch_page("pages/4_Shopping_List.py")
    if st.button("📅 Meal Plan", use_container_width=True):
        st.switch_page("pages/5_Meal_Plan.py")

with col3:
    if st.button("➕ Create Recipe", use_container_width=True):
        st.switch_page("pages/6_Create_Recipe.py")
    if st.button("⚙️ Settings", use_container_width=True):
        st.switch_page("pages/7_Settings.py")

st.markdown("---")

# Main content in columns
col_left, col_right = st.columns([2, 1])

with col_left:
    # Recipe of the Day
    st.subheader("🌟 Recipe of the Day")
    
    recipe_of_day = db.get_random_public_recipe()
    
    if recipe_of_day:
        with st.container():
            st.markdown(f"### {recipe_of_day['title']}")
            
        try:
            ingredients_list = json.loads(recipe_of_day['ingredients'])
            # Display first 5 ingredients
            st.markdown("**Ingredients:**")
            for ingredient in ingredients_list[:5]:  # Show first 5 ingredients
                qty = ingredient.get('quantity', '')
                unit = ingredient.get('unit', '')
                name = ingredient.get('name', '')
                st.markdown(f"- {qty} {unit} {name}".strip())
            
            if len(ingredients_list) > 5:
                st.caption(f"... and {len(ingredients_list) - 5} more ingredients")
        except (json.JSONDecodeError, TypeError):
            # Fallback if it's plain text
            ingredients_list = recipe_of_day['ingredients'].split('\n')
            st.markdown("**Ingredients:**")
            for ingredient in ingredients_list[:5]:
                if ingredient.strip():
                    st.markdown(f"- {ingredient.strip()}")
            if len(ingredients_list) > 5:
                st.caption(f"... and {len(ingredients_list) - 5} more ingredients")
        
        # Button to view full recipe
        if st.button("👁️ View Full Recipe", key="view_recipe_of_day"):
            # Store recipe_id in session state and navigate
            st.session_state.selected_recipe_id = recipe_of_day['recipe_id']
            st.switch_page("pages/8_View_Recipe.py")
    else:
        st.info("No public recipes available yet. Be the first to share one!")

with col_right:
    # Pantry Preview
    st.subheader("🥫 Pantry Preview")
    
    pantry_items = db.get_user_pantry(st.session_state.user_id)
    
    if pantry_items:
        # Show first 5 items
        for item in pantry_items[:5]:
            qty = item['quantity']
            formatted_qty = f"{qty:.2f}".rstrip("0").rstrip(".") if "." in str(qty) else str(qty)
            st.markdown(f"- **{item['name']}**: {formatted_qty} {item['unit'] or ''}")
        
        if len(pantry_items) > 5:
            st.caption(f"... and {len(pantry_items) - 5} more items")
        
        if st.button("View Full Pantry", use_container_width=True):
            st.switch_page("pages/3_Pantry.py")
    else:
        st.info("Your pantry is empty. Add some items!")
        if st.button("Go to Pantry", use_container_width=True):
            st.switch_page("pages/3_Pantry.py")
    
    st.markdown("---")
    
    # Shopping List Preview
    st.subheader("🛒 Shopping List Preview")
    
    shopping_items = db.get_user_shopping_list(st.session_state.user_id)
    
    if shopping_items:
        # Show first 5 unchecked items
        unchecked_items = [item for item in shopping_items if not item['is_checked']]
        
        for item in unchecked_items[:5]:
            quantity_str = f"{item['quantity']} {item['unit'] or ''}" if item['quantity'] else ""
            st.markdown(f"- {item['name']} {quantity_str}")
        
        if len(unchecked_items) > 5:
            st.caption(f"... and {len(unchecked_items) - 5} more items")
        
        if st.button("View Full Shopping List", use_container_width=True):
            st.switch_page("pages/4_Shopping_List.py")
    else:
        st.info("Your shopping list is empty.")
        if st.button("Go to Shopping List", use_container_width=True):
            st.switch_page("pages/4_Shopping_List.py")

# Footer
st.markdown("---")
st.caption("Recipes For Success © 2025 • Made with ❤️ and a pinch of code")