import streamlit as st
import database as db
import theme_manager
import json

theme_manager.apply_user_theme()

# Helper function to parse ingredients
def parse_ingredients_preview(ingredients_data):
    """Parse ingredients and return a preview string"""
    try:
        # Try to parse as JSON
        ingredients_list = json.loads(ingredients_data)
        if isinstance(ingredients_list, list):
            # Extract ingredient names
            ingredient_names = [ing.get('name', '') for ing in ingredients_list[:3] if ing.get('name')]
            preview = ', '.join(ingredient_names)
            if len(ingredients_list) > 3:
                preview += " ..."
            return preview
    except (json.JSONDecodeError, TypeError):
        # Fallback: treat as newline-separated text
        ingredients_list = ingredients_data.split('\n')
        ingredients_preview = ', '.join([ing.strip() for ing in ingredients_list[:3] if ing.strip()])
        if len(ingredients_list) > 3:
            ingredients_preview += " ..."
        return ingredients_preview
    return ""

# Page config
st.set_page_config(
    page_title="Cookbook - Recipes For Success",
    page_icon="📖",
    layout="wide"
)

# Check if user is logged in
if 'user_id' not in st.session_state or st.session_state.user_id is None:
    st.warning("⚠️ Please sign in first")
    st.stop()

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.title("📖 My Cookbook")
with col2:
    if st.button("🏠 Dashboard", use_container_width=True):
        st.switch_page("pages/1_Dashboard.py")

st.markdown("---")

# Tabs
tab1, tab2, tab3 = st.tabs(["My Recipes", "Saved Recipes", "Public Recipes"])

# === TAB 1: My Recipes ===
with tab1:
    st.subheader("My Personal Recipes")
    
    col_button1, col_button2 = st.columns([1, 4])
    with col_button1:
        if st.button("➕ Create New Recipe", use_container_width=True, type="primary"):
            st.switch_page("pages/6_Create_Recipe.py")
    
    st.markdown("---")
    
    user_recipes = db.get_user_cookbook(st.session_state.user_id)
    
    if user_recipes:
        # Use columns for grid layout
        cols_per_row = 3
        for i in range(0, len(user_recipes), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i + j < len(user_recipes):
                    recipe = user_recipes[i + j]
                    with col:
                        # Recipe card container
                        ingredients_preview = parse_ingredients_preview(recipe['ingredients'])
                        created_date = recipe['created_at'][:10] if recipe['created_at'] else "Unknown"
                        
                        status_class = "status-public" if recipe['is_public'] else "status-private"
                        status_text = "Public" if recipe['is_public'] else "Private"
                        
                        card_html = f"""
                        <div class="recipe-card">
                            <div class="recipe-title">{recipe['title']}</div>
                            <span class="status-tag {status_class}">{status_text}</span>
                            <p class="recipe-ingredients"><em>Ingredients:</em> {ingredients_preview}</p>
                            <div class="recipe-date">Created: {created_date}</div>
                        </div>
                        """
                        st.markdown(card_html, unsafe_allow_html=True)
                        
                        # Streamlit buttons below the card
                        btn_col1, btn_col2, btn_col3 = st.columns(3)
                        with btn_col1:
                            if st.button("👁️ View", key=f"view_my_{recipe['recipe_id']}", use_container_width=True):
                                st.session_state.selected_recipe_id = recipe['recipe_id']
                                st.switch_page("pages/8_View_Recipe.py")
                        with btn_col2:
                            if st.button("✏️ Edit", key=f"edit_{recipe['recipe_id']}", use_container_width=True):
                                st.session_state.edit_recipe_id = recipe['recipe_id']
                                st.switch_page("pages/9_Edit_Recipe.py")
                        with btn_col3:
                            if st.button("🗑️ Delete", key=f"delete_{recipe['recipe_id']}", use_container_width=True):
                                st.session_state.delete_recipe_id = recipe['recipe_id']
                                st.rerun()
        
        # Delete Confirmation
        if 'delete_recipe_id' in st.session_state:
            st.markdown("<br>", unsafe_allow_html=True)
            st.warning("⚠️ Are you sure you want to permanently delete this recipe?")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("🗑️ Yes, Delete Forever", type="primary", use_container_width=True):
                    db.delete_user_recipe(st.session_state.delete_recipe_id, st.session_state.user_id)
                    del st.session_state.delete_recipe_id
                    st.success("Recipe deleted successfully!")
                    st.rerun()
            with col_no:
                if st.button("❌ Cancel", use_container_width=True):
                    del st.session_state.delete_recipe_id
                    st.rerun()
    else:
        st.info("🍳 You haven't created any recipes yet. Click **Create New Recipe** to start cooking up success!")

# === TAB 2: Saved Recipes ===
with tab2:
    st.subheader("Saved Public Recipes")
    st.markdown("---")
    
    saved_recipes = db.get_saved_public_recipes(st.session_state.user_id)
    
    if saved_recipes:
        # Use columns for grid layout
        cols_per_row = 3
        for i in range(0, len(saved_recipes), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i + j < len(saved_recipes):
                    recipe = saved_recipes[i + j]
                    with col:
                        ingredients_preview = parse_ingredients_preview(recipe['ingredients'])
                        saved_date = recipe['created_at'][:10] if recipe['created_at'] else "Recently"
                        
                        card_html = f"""
                        <div class="recipe-card">
                            <div class="recipe-title">{recipe['title']}</div>
                            <p class="recipe-ingredients"><em>Ingredients:</em> {ingredients_preview}</p>
                            <div class="recipe-date">Saved: {saved_date}</div>
                        </div>
                        """
                        st.markdown(card_html, unsafe_allow_html=True)
                        
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            if st.button("👁️ View", key=f"view_saved_{recipe['recipe_id']}", use_container_width=True):
                                st.session_state.selected_recipe_id = recipe['recipe_id']
                                st.switch_page("pages/8_View_Recipe.py")
                        with btn_col2:
                            if st.button("❌ Remove", key=f"remove_saved_{recipe['recipe_id']}", use_container_width=True):
                                db.unsave_recipe_from_cookbook(st.session_state.user_id, recipe['recipe_id'])
                                st.success("✅ Recipe removed from your cookbook!")
                                st.rerun()
    else:
        st.info("💾 You haven't saved any public recipes yet. Browse the **Public Recipes** tab to find inspiration!")

# === TAB 3: Public Recipes ===
with tab3:
    st.subheader("Browse Public Recipes")
    st.markdown("---")
    
    public_recipes = db.get_all_public_recipes()
    
    if public_recipes:
        search_term = st.text_input("🔍 Search recipes", key="public_search")
        
        filtered_recipes = public_recipes
        if search_term:
            filtered_recipes = [r for r in public_recipes if search_term.lower() in r['title'].lower()]
        
        if filtered_recipes:
            # Use columns for grid layout
            cols_per_row = 3
            for i in range(0, len(filtered_recipes), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, col in enumerate(cols):
                    if i + j < len(filtered_recipes):
                        recipe = filtered_recipes[i + j]
                        with col:
                            ingredients_preview = parse_ingredients_preview(recipe['ingredients'])
                            created_date = recipe['created_at'][:10] if recipe['created_at'] else "Recently"
                            
                            card_html = f"""
                            <div class="recipe-card">
                                <div class="recipe-title">{recipe['title']}</div>
                                <p class="recipe-ingredients"><em>Ingredients:</em> {ingredients_preview}</p>
                                <div class="recipe-date">Created: {created_date}</div>
                            </div>
                            """
                            st.markdown(card_html, unsafe_allow_html=True)
                            
                            btn_col1, btn_col2 = st.columns(2)
                            with btn_col1:
                                if st.button("👁️ View", key=f"view_public_{recipe['recipe_id']}", use_container_width=True):
                                    st.session_state.selected_recipe_id = recipe['recipe_id']
                                    st.switch_page("pages/8_View_Recipe.py")
                            with btn_col2:
                                if st.button("💾 Save", key=f"save_{recipe['recipe_id']}", use_container_width=True):
                                    result = db.save_recipe_to_cookbook(st.session_state.user_id, recipe['recipe_id'])
                                    if result:
                                        st.success("✅ Recipe saved to your cookbook!")
                                        st.rerun()
                                    else:
                                        st.error("Already saved!")
        else:
            st.warning(f"😕 No recipes found for '{search_term}'.")
    else:
        st.info("🌟 No public recipes yet. Be the first to share one!")

# Footer
st.markdown("---")
st.caption("Recipes For Success © 2025 • Made with ❤️ and a pinch of code")