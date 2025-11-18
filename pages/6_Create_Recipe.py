import streamlit as st
import database as db
import os
import theme_manager

theme_manager.apply_user_theme()

# Page config
st.set_page_config(
    page_title="Create Recipe - Recipes For Success",
    page_icon="➕",
    layout="wide"
)

# Check if user is logged in
if 'user_id' not in st.session_state or st.session_state.user_id is None:
    st.warning("⚠️ Please sign in first")
    st.stop()

# Initialize ingredients list in session state if not exists
if 'new_recipe_ingredients' not in st.session_state:
    st.session_state.new_recipe_ingredients = []

# Initialize widget keys with defaults (only if not already set)
if 'ing_qty_input' not in st.session_state:
    st.session_state.ing_qty_input = 1.0
if 'ing_unit_input' not in st.session_state:
    st.session_state.ing_unit_input = ""
if 'ing_name_input' not in st.session_state:
    st.session_state.ing_name_input = ""

# Callback function to add ingredient and reset fields
def add_ingredient():
    if st.session_state.ing_name_input.strip():
        new_ingredient = {
            'quantity': st.session_state.ing_qty_input if st.session_state.ing_qty_input > 0 else None,
            'unit': st.session_state.ing_unit_input if st.session_state.ing_unit_input else None,
            'name': st.session_state.ing_name_input.strip()
        }
        st.session_state.new_recipe_ingredients.append(new_ingredient)
        # Reset the input fields by directly setting their keys
        st.session_state.ing_qty_input = 1.0
        st.session_state.ing_unit_input = ""
        st.session_state.ing_name_input = ""
        st.session_state.ingredient_added = True
    else:
        st.session_state.ingredient_error = True

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.title("➕ Create New Recipe")
with col2:
    if st.button("🏠 Dashboard", use_container_width=True):
        st.switch_page("pages/1_Dashboard.py")

st.markdown("---")

# Main form container
with st.container():
    # Recipe Title
    st.markdown("<div class='section-header'>Recipe Title</div>", unsafe_allow_html=True)
    recipe_title = st.text_input(
        "Enter recipe name",
        label_visibility="collapsed"
    )
    
    # Ingredients Section
    st.markdown("<div class='section-header'>🥦 Ingredients</div>", unsafe_allow_html=True)
    st.caption("Add ingredients with quantity and unit for better organization and unit conversion support")
    
    # Add ingredient form
    with st.expander("➕ Add Ingredient", expanded=True):
        col_qty, col_unit, col_name = st.columns([1, 1, 3])
        with col_qty:
            ing_quantity = st.number_input(
                "Quantity", 
                min_value=0.0, 
                step=0.25,
                key="ing_qty_input",
                help="Leave at 0 for ingredients without quantity (e.g., 'Salt to taste')"
            )
        with col_unit:
            ing_unit = st.text_input(
                "Unit",
                key="ing_unit_input",
                help="e.g., cups, tbsp, oz, g (leave blank if not needed)"
            )
        with col_name:
            ing_name = st.text_input(
                "Ingredient Name",
                key="ing_name_input"
            )
        
        st.button("➕ Add to Recipe", use_container_width=True, type="primary", on_click=add_ingredient)
        
        # Show success/error messages
        if st.session_state.get('ingredient_added'):
            st.success("✓ Ingredient added!")
            del st.session_state.ingredient_added
        if st.session_state.get('ingredient_error'):
            st.error("Please enter an ingredient name")
            del st.session_state.ingredient_error
    
    # Display current ingredients
    if st.session_state.new_recipe_ingredients:
        st.markdown("**Current Ingredients:**")
        for idx, ing in enumerate(st.session_state.new_recipe_ingredients):
            col_ing, col_remove = st.columns([4, 1])
            with col_ing:
                # Format ingredient display
                if ing['quantity']:
                    qty_str = f"{ing['quantity']:.2f}".rstrip("0").rstrip(".")
                    unit_str = ing['unit'] or ""
                    display = f"{idx + 1}. {qty_str} {unit_str} {ing['name']}".strip()
                else:
                    display = f"{idx + 1}. {ing['name']}"
                st.markdown(display)
            with col_remove:
                if st.button("🗑️", key=f"remove_ing_{idx}", help="Remove ingredient"):
                    st.session_state.new_recipe_ingredients.pop(idx)
                    st.rerun()
        
        # Clear all ingredients button
        if st.button("🗑️ Clear All Ingredients", use_container_width=True):
            st.session_state.new_recipe_ingredients = []
            st.rerun()
    else:
        st.info("No ingredients added yet. Use the form above to add ingredients.")
    
    # Instructions Section
    st.markdown("---")
    st.markdown("<div class='section-header'>📋 Instructions</div>", unsafe_allow_html=True)
    st.caption("Enter step-by-step instructions (one step per line)")
    
    instructions = st.text_area(
        "Instructions",
        height=250,
        label_visibility="collapsed"
    )
    
    # Image Upload Section
    st.markdown("---")
    st.markdown("<div class='section-header'>🖼️ Recipe Image (Optional)</div>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Upload an image of your recipe",
        type=['png', 'jpg', 'jpeg'],
        label_visibility="collapsed"
    )
    
    # Preview uploaded image
    if uploaded_file is not None:
        col_preview, col_info = st.columns([1, 2])
        with col_preview:
            st.image(uploaded_file, caption="Recipe Preview", use_container_width=True)
        with col_info:
            st.success("✔ Image uploaded successfully!")
            st.caption(f"File: {uploaded_file.name}")
            st.caption(f"Size: {uploaded_file.size / 1024:.2f} KB")
    
    # Privacy Toggle
    st.markdown("---")
    st.markdown("<div class='section-header'>🌐 Privacy Settings</div>", unsafe_allow_html=True)
    
    is_public = st.checkbox("🌍 Make this recipe public (share with the community)", value=False)

# Action Buttons
st.markdown("---")
col_cancel, col_preview, col_create = st.columns([1, 1, 1])

with col_cancel:
    if st.button("❌ Cancel", use_container_width=True):
        # Clear ingredients on cancel
        st.session_state.new_recipe_ingredients = []
        st.switch_page("pages/2_Cookbook.py")

with col_preview:
    if st.button("👁️ Preview", use_container_width=True):
        if recipe_title and st.session_state.new_recipe_ingredients and instructions:
            st.session_state.preview_recipe = {
                'title': recipe_title,
                'ingredients': st.session_state.new_recipe_ingredients,
                'instructions': instructions,
                'is_public': is_public
            }
            st.rerun()
        else:
            st.error("Please fill in all required fields to preview (title, at least one ingredient, and instructions)")

with col_create:
    if st.button("✔ Create Recipe", use_container_width=True, type="primary"):
        # Validation
        if not recipe_title or not recipe_title.strip():
            st.error("❌ Please enter a recipe title")
        elif not st.session_state.new_recipe_ingredients:
            st.error("❌ Please add at least one ingredient")
        elif not instructions or not instructions.strip():
            st.error("❌ Please add cooking instructions")
        else:
            # Handle image upload
            image_path = None
            if uploaded_file is not None:
                # Create uploads directory if it doesn't exist
                os.makedirs('data/uploads', exist_ok=True)
                
                # Generate unique filename
                import time
                timestamp = int(time.time())
                file_extension = uploaded_file.name.split('.')[-1]
                image_path = f"data/uploads/{st.session_state.user_id}_{timestamp}.{file_extension}"
                
                # Save the file
                with open(image_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
            
            # Create recipe in database with structured ingredients
            result = db.create_recipe(
                user_id=st.session_state.user_id,
                title=recipe_title.strip(),
                ingredients=st.session_state.new_recipe_ingredients,
                instructions=instructions.strip(),
                image_path=image_path,
                is_public=is_public
            )
            
            if isinstance(result, dict) and 'error' in result:
                st.error(f"❌ {result['error']}")
            else:
                st.success(f"✔ Recipe '{recipe_title}' created successfully!")
                st.balloons()
                # Clear the ingredients list and form
                st.session_state.new_recipe_ingredients = []
                st.session_state.pop('preview_recipe', None)
                import time
                time.sleep(1)
                st.switch_page("pages/2_Cookbook.py")

# Preview Modal
if 'preview_recipe' in st.session_state:
    st.markdown("---")
    st.subheader("👁️ Recipe Preview")
    
    # Title
    st.markdown(f"## {st.session_state.preview_recipe['title']}")
    
    # Privacy status
    if st.session_state.preview_recipe['is_public']:
        st.markdown("**Status:** 🌍 Public")
    else:
        st.markdown("**Status:** 🔒 Private")
    
    st.markdown("---")
    
    # Ingredients
    st.markdown("### 🥦 Ingredients")
    for ing in st.session_state.preview_recipe['ingredients']:
        if ing['quantity']:
            qty_str = f"{ing['quantity']:.2f}".rstrip("0").rstrip(".")
            unit_str = ing['unit'] or ""
            display = f"- {qty_str} {unit_str} {ing['name']}".strip()
        else:
            display = f"- {ing['name']}"
        st.markdown(display)
    
    st.markdown("---")
    
    # Instructions
    st.markdown("### 📋 Instructions")
    instructions_list = st.session_state.preview_recipe['instructions'].split('\n')
    for i, instruction in enumerate(instructions_list, 1):
        if instruction.strip():
            st.markdown(f"{i}. {instruction.strip()}")
    
    if st.button("Close Preview"):
        del st.session_state.preview_recipe
        st.rerun()

# Footer
st.markdown("---")
st.caption("Recipes For Success © 2025 • Made with ❤️ and a pinch of code")