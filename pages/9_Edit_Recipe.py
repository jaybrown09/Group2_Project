import streamlit as st
import database as db
import os
import base64
import theme_manager
import json

theme_manager.apply_user_theme()

# Page config
st.set_page_config(
    page_title="Edit Recipe - Recipes For Success",
    page_icon="✏️",
    layout="wide"
)

# Session checks
if 'user_id' not in st.session_state or st.session_state.user_id is None:
    st.warning("⚠️ Please sign in first")
    st.stop()

if 'edit_recipe_id' not in st.session_state:
    st.error("❌ No recipe selected for editing")
    if st.button("🏠 Go to Dashboard"):
        st.switch_page("pages/1_Dashboard.py")
    st.stop()

# Fetch recipe
recipe = db.get_recipe(st.session_state.edit_recipe_id)
if not recipe:
    st.error("❌ Recipe not found")
    if st.button("🏠 Go to Dashboard"):
        st.switch_page("pages/1_Dashboard.py")
    st.stop()

# Check if user owns this recipe
if recipe['user_id'] != st.session_state.user_id:
    st.error("🚫 You don't have permission to edit this recipe")
    if st.button("🏠 Go to Dashboard"):
        st.switch_page("pages/1_Dashboard.py")
    st.stop()

# Initialize ingredients list in session state if not exists or if editing a new recipe
if 'edit_recipe_ingredients' not in st.session_state or st.session_state.get('editing_recipe_id') != recipe['recipe_id']:
    # Load existing ingredients
    # First try to get structured ingredients from the new table
    structured_ingredients = db.get_recipe_ingredients(recipe['recipe_id'])
    
    if structured_ingredients:
        # Use structured ingredients from database
        st.session_state.edit_recipe_ingredients = [
            {
                'quantity': ing['quantity'],
                'unit': ing['unit'],
                'name': ing['name']
            }
            for ing in structured_ingredients
        ]
    else:
        # Try to parse from JSON (new format stored in recipes table)
        try:
            ingredients_data = json.loads(recipe['ingredients'])
            if isinstance(ingredients_data, list):
                st.session_state.edit_recipe_ingredients = ingredients_data
            else:
                raise ValueError("Not a list")
        except (json.JSONDecodeError, ValueError, TypeError):
            # Old format - parse text into structured format
            st.session_state.edit_recipe_ingredients = []
            for line in recipe['ingredients'].split('\n'):
                line = line.strip()
                if line:
                    # Simple parsing - just put the whole line as the name
                    # User can edit to add proper structure
                    st.session_state.edit_recipe_ingredients.append({
                        'quantity': None,
                        'unit': None,
                        'name': line
                    })
    
    st.session_state.editing_recipe_id = recipe['recipe_id']

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.title("✏️ Edit Recipe")
with col2:
    if st.button("📖 Back to Cookbook", use_container_width=True):
        st.switch_page("pages/2_Cookbook.py")

st.markdown("---")

# Form container
st.markdown('<div class="form-container">', unsafe_allow_html=True)

# Recipe Title
st.markdown('<h3 class="section-header">📝 Recipe Details</h3>', unsafe_allow_html=True)
title = st.text_input("Recipe Title*", value=recipe['title'])

# Public/Private Toggle
is_public = st.checkbox("🌍 Make this recipe public (share with the community)", value=recipe['is_public'])

st.markdown("---")

# Ingredients Section
st.markdown('<h3 class="section-header">🥦 Ingredients</h3>', unsafe_allow_html=True)
st.caption("Edit ingredients with quantity and unit for better organization and unit conversion support")

# Add ingredient form
with st.expander("➕ Add New Ingredient", expanded=False):
    col_qty, col_unit, col_name = st.columns([1, 1, 3])
    with col_qty:
        ing_quantity = st.number_input(
            "Quantity", 
            min_value=0.0, 
            step=0.25, 
            value=1.0,
            key="edit_ing_qty_input",
            help="Leave at 0 for ingredients without quantity"
        )
    with col_unit:
        unit_options = [
            "", "cups", "tbsp", "tsp", "oz", "lbs", "g", "kg", 
            "ml", "l", "gallon", "quart", "pint", "fl oz",
            "count", "dozen", "pinch", "dash", "clove", "slice", "piece"
        ]
        ing_unit = st.selectbox(
            "Unit",
            options=unit_options,
            key="edit_ing_unit_input"
        )
    with col_name:
        ing_name = st.text_input(
            "Ingredient Name",
            key="edit_ing_name_input"
        )
    
    if st.button("➕ Add to Recipe", use_container_width=True, type="primary"):
        if ing_name.strip():
            new_ingredient = {
                'quantity': ing_quantity if ing_quantity > 0 else None,
                'unit': ing_unit if ing_unit else None,
                'name': ing_name.strip()
            }
            st.session_state.edit_recipe_ingredients.append(new_ingredient)
            st.success(f"Added: {ing_name}")
            st.rerun()
        else:
            st.error("Please enter an ingredient name")

# Display current ingredients with edit capability
if st.session_state.edit_recipe_ingredients:
    st.markdown("**Current Ingredients:**")
    
    for idx, ing in enumerate(st.session_state.edit_recipe_ingredients):
        with st.expander(f"Ingredient {idx + 1}: {ing['name']}", expanded=False):
            col_qty, col_unit, col_name, col_actions = st.columns([1, 1, 2, 1])
            
            with col_qty:
                new_qty = st.number_input(
                    "Qty",
                    min_value=0.0,
                    step=0.25,
                    value=float(ing['quantity']) if ing['quantity'] else 0.0,
                    key=f"edit_qty_{idx}"
                )
            
            with col_unit:
                current_unit_idx = 0
                if ing['unit'] in unit_options:
                    current_unit_idx = unit_options.index(ing['unit'])
                new_unit = st.selectbox(
                    "Unit",
                    options=unit_options,
                    index=current_unit_idx,
                    key=f"edit_unit_{idx}"
                )
            
            with col_name:
                new_name = st.text_input(
                    "Name",
                    value=ing['name'],
                    key=f"edit_name_{idx}"
                )
            
            with col_actions:
                st.write("")  # Spacer
                if st.button("💾 Update", key=f"update_ing_{idx}", use_container_width=True):
                    if new_name.strip():
                        st.session_state.edit_recipe_ingredients[idx] = {
                            'quantity': new_qty if new_qty > 0 else None,
                            'unit': new_unit if new_unit else None,
                            'name': new_name.strip()
                        }
                        st.success(f"Updated ingredient {idx + 1}")
                        st.rerun()
                    else:
                        st.error("Name cannot be empty")
                
                if st.button("🗑️ Remove", key=f"remove_ing_{idx}", use_container_width=True):
                    st.session_state.edit_recipe_ingredients.pop(idx)
                    st.rerun()
    
    # Show summary
    st.markdown("**Summary:**")
    for idx, ing in enumerate(st.session_state.edit_recipe_ingredients):
        if ing['quantity']:
            qty_str = f"{ing['quantity']:.2f}".rstrip("0").rstrip(".")
            unit_str = ing['unit'] or ""
            display = f"{idx + 1}. {qty_str} {unit_str} {ing['name']}".strip()
        else:
            display = f"{idx + 1}. {ing['name']}"
        st.markdown(display)
else:
    st.warning("No ingredients. Add at least one ingredient.")

st.markdown("---")

# Instructions Section
st.markdown('<h3 class="section-header">📋 Instructions</h3>', unsafe_allow_html=True)
st.markdown('<div class="info-box">💡 <strong>Tip:</strong> Enter one step per line for clear instructions</div>', unsafe_allow_html=True)
instructions = st.text_area(
    "Instructions*",
    value=recipe['instructions'],
    height=250,
)

st.markdown("---")

# Image Section
st.markdown('<h3 class="section-header">📸 Recipe Image</h3>', unsafe_allow_html=True)

# Show current image if exists
if recipe['image_path'] and os.path.exists(recipe['image_path']):
    st.markdown("**Current Image:**")
    with open(recipe['image_path'], "rb") as f:
        img_data = base64.b64encode(f.read()).decode()
    img_uri = f"data:image/jpeg;base64,{img_data}"
    st.markdown(f'<div class="img-preview"><img src="{img_uri}"></div>', unsafe_allow_html=True)
    
    remove_image = st.checkbox("❌ Remove current image")
else:
    remove_image = False
    st.info("📷 No image currently uploaded")

# Upload new image
uploaded_file = st.file_uploader(
    "Upload New Image (optional)",
    type=['png', 'jpg', 'jpeg'],
    help="Upload a new image to replace the current one"
)

# Preview new upload
if uploaded_file:
    st.markdown("**New Image Preview:**")
    st.image(uploaded_file, use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)  # end form-container

st.markdown("---")

# Action Buttons
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if st.button("💾 Save Changes", use_container_width=True, type="primary"):
        # Validation
        if not title or not title.strip():
            st.error("❌ Recipe title cannot be empty")
        elif not st.session_state.edit_recipe_ingredients:
            st.error("❌ Please add at least one ingredient")
        elif not instructions or not instructions.strip():
            st.error("❌ Instructions cannot be empty")
        else:
            # Handle image
            image_path = recipe['image_path']
            
            # Remove old image if requested
            if remove_image and image_path and os.path.exists(image_path):
                try:
                    os.remove(image_path)
                    image_path = None
                except:
                    pass
            
            # Save new image
            if uploaded_file:
                os.makedirs('data/images', exist_ok=True)
                # Generate unique filename
                import time
                filename = f"recipe_{st.session_state.user_id}_{int(time.time())}_{uploaded_file.name}"
                image_path = os.path.join('data/images', filename)
                
                # Remove old image if exists
                if recipe['image_path'] and os.path.exists(recipe['image_path']):
                    try:
                        os.remove(recipe['image_path'])
                    except:
                        pass
                
                # Save new image
                with open(image_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
            
            # Update recipe in database with structured ingredients
            result = db.update_user_recipes(
                recipe_id=recipe['recipe_id'],
                title=title.strip(),
                ingredients=st.session_state.edit_recipe_ingredients,  # Pass list of dicts
                instructions=instructions.strip(),
                image_path=image_path,
                is_public=is_public
            )
            
            if result:
                st.success("✅ Recipe updated successfully!")
                st.balloons()
                # Clear edit session state
                del st.session_state.edit_recipe_id
                del st.session_state.edit_recipe_ingredients
                del st.session_state.editing_recipe_id
                # Navigate to view page
                st.session_state.selected_recipe_id = recipe['recipe_id']
                import time
                time.sleep(1)
                st.switch_page("pages/8_View_Recipe.py")
            else:
                st.error("❌ Failed to update recipe. Please try again.")

with col2:
    if st.button("👁️ Preview Recipe", use_container_width=True):
        st.session_state.selected_recipe_id = recipe['recipe_id']
        st.switch_page("pages/8_View_Recipe.py")

with col3:
    if st.button("❌ Cancel", use_container_width=True):
        del st.session_state.edit_recipe_id
        if 'edit_recipe_ingredients' in st.session_state:
            del st.session_state.edit_recipe_ingredients
        if 'editing_recipe_id' in st.session_state:
            del st.session_state.editing_recipe_id
        st.switch_page("pages/2_Cookbook.py")

# Footer
st.markdown("---")
st.caption("Recipes For Success © 2025 • Made with ❤️ and a pinch of code")