import streamlit as st
import database as db
import os
import base64
import theme_manager
import json

theme_manager.apply_user_theme()

# Page config
st.set_page_config(page_title="View Recipe - Recipes For Success", page_icon="👀", layout="wide")

# Session checks
if 'user_id' not in st.session_state or st.session_state.user_id is None:
    st.warning("⚠️: Please sign in first")
    st.stop()

if 'selected_recipe_id' not in st.session_state:
    st.error("❌: No recipe selected")
    if st.button("🏠: Go to Dashboard"):
        st.switch_page("pages/1_Dashboard.py")
    st.stop()

# Fetch recipe
recipe = db.get_recipe(st.session_state.selected_recipe_id)
if not recipe:
    st.error("❌: Recipe not found")
    if st.button("🏠: Go to Dashboard"): st.switch_page("pages/1_Dashboard.py")
    st.stop()

# Get structured ingredients
structured_ingredients = db.get_recipe_ingredients(recipe['recipe_id'])

# If no structured ingredients, try to parse from JSON or fall back to text
if not structured_ingredients:
    try:
        ingredients_data = json.loads(recipe['ingredients'])
        if isinstance(ingredients_data, list):
            structured_ingredients = ingredients_data
        else:
            structured_ingredients = None
    except (json.JSONDecodeError, ValueError, TypeError):
        structured_ingredients = None

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("<h1 style='margin: 0; padding: 0;'>👀: View Recipe</h1>", unsafe_allow_html=True)
with col2:
    if st.button("📖: Back to Cookbook", use_container_width=True):
        st.switch_page("pages/2_Cookbook.py")

st.markdown("---")

# === MAIN RECIPE CARD ===
st.markdown('<div class="recipe-card">', unsafe_allow_html=True)

# Title + Status
st.markdown(f'<div class="recipe-title">{recipe["title"]}</div>', unsafe_allow_html=True)
status_class = "status-public" if recipe['is_public'] else "status-private"
status_text = "🌐: Public" if recipe['is_public'] else "🔒: Private"
st.markdown(f'<span class="status-badge {status_class}">{status_text}</span>', unsafe_allow_html=True)

# Metadata
created = recipe['created_at'][:10] if recipe['created_at'] else "Unknown"
if structured_ingredients:
    ing_count = len(structured_ingredients)
else:
    ing_count = len([i for i in recipe['ingredients'].split('\n') if i.strip()])
step_count = len([i for i in recipe['instructions'].split('\n') if i.strip()])

st.markdown(f"""
<div class="metadata-bar">
    <div class="meta-item"><span class="meta-label">Created:</span> {created}</div>
    <div class="meta-item"><span class="meta-label">Ingredients:</span> {ing_count}</div>
    <div class="meta-item"><span class="meta-label">Steps:</span> {step_count}</div>
    <div class="meta-item"><span class="meta-label">Creator ID:</span> {recipe['user_id']}</div>
</div>
""", unsafe_allow_html=True)

# === IMAGE ===
if recipe['image_path'] and os.path.exists(recipe['image_path']):
    with open(recipe['image_path'], "rb") as f:
        img_data = base64.b64encode(f.read()).decode()
    img_uri = f"data:image/jpeg;base64,{img_data}"
    st.markdown(f'<div class="img-container"><img src="{img_uri}"></div>', unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="img-container">
        <div style="background: rgba(255,255,255,0.08); border: 2px dashed rgba(255,255,255,0.2); border-radius: 20px; padding: 4rem; color: #94a3b8;">
            Camera: No image uploaded
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)  # end recipe-card

# === INGREDIENTS ===
st.markdown('<h2 class="section-header">🥦: Ingredients</h2>', unsafe_allow_html=True)

# Initialize conversion state: None = original, 'metric' = show metric, 'imperial' = show imperial
if 'unit_display_mode' not in st.session_state:
    st.session_state.unit_display_mode = None  # None means show original units

# Check if any ingredients are convertible
has_convertible = False
if structured_ingredients:
    for ing in structured_ingredients:
        if isinstance(ing, dict):
            qty = ing.get('quantity')
            unit = ing.get('unit')
            if qty and unit:
                # Check if unit is in our conversion map
                test_metric, _ = db.convert_unit(qty, unit, to_system="metric")
                test_imperial, _ = db.convert_unit(qty, unit, to_system="imperial")
                if test_metric != qty or test_imperial != qty:
                    has_convertible = True
                    break

# Show conversion buttons only if there are convertible ingredients
if has_convertible:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("📏 Show Original", key="show_original", use_container_width=True, 
                     type="primary" if st.session_state.unit_display_mode is None else "secondary"):
            st.session_state.unit_display_mode = None
            st.rerun()
    with col2:
        if st.button("🔄 Convert to Metric", key="convert_metric", use_container_width=True,
                     type="primary" if st.session_state.unit_display_mode == "metric" else "secondary"):
            st.session_state.unit_display_mode = "metric"
            st.rerun()
    with col3:
        if st.button("🔄 Convert to Imperial", key="convert_imperial", use_container_width=True,
                     type="primary" if st.session_state.unit_display_mode == "imperial" else "secondary"):
            st.session_state.unit_display_mode = "imperial"
            st.rerun()

st.markdown('<div class="ingredients-box">', unsafe_allow_html=True)

if structured_ingredients:
    # Use structured ingredients
    for idx, ing in enumerate(structured_ingredients):
        # Get ingredient data (handle both dict formats)
        if isinstance(ing, dict):
            qty = ing.get('quantity')
            unit = ing.get('unit')
            name = ing.get('name', '')
        else:
            # Fallback if somehow not a dict
            qty = None
            unit = None
            name = str(ing)
        
        # Apply conversion based on display mode
        if qty and unit and st.session_state.unit_display_mode is not None:
            converted_qty, converted_unit = db.convert_unit(
                qty, 
                unit, 
                to_system=st.session_state.unit_display_mode
            )
            formatted_qty = f"{converted_qty:.2f}".rstrip("0").rstrip(".")
            display_text = f"{formatted_qty} {converted_unit} {name}"
        elif qty:
            formatted_qty = f"{qty:.2f}".rstrip("0").rstrip(".")
            unit_str = unit or ""
            display_text = f"{formatted_qty} {unit_str} {name}".strip()
        else:
            display_text = name
        
        st.markdown(f'<div class="ingredient-item">{display_text}</div>', unsafe_allow_html=True)
else:
    # Fall back to old text format
    for ing in recipe['ingredients'].split('\n'):
        if ing.strip():
            st.markdown(f'<div class="ingredient-item">{ing.strip()}</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# === INSTRUCTIONS ===
st.markdown('<h2 class="section-header">📝: Instructions</h2>', unsafe_allow_html=True)
st.markdown('<div class="instructions-box">', unsafe_allow_html=True)
for i, step in enumerate(recipe['instructions'].split('\n'), 1):
    if step.strip():
        st.markdown(f'<div class="instruction-step"><span class="step-num">Step {i}:</span> {step.strip()}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# === BUTTONS ===
if recipe['user_id'] == st.session_state.user_id:
    st.markdown("---")
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        if st.button("✏️: Edit Recipe", use_container_width=True, type="primary"):
            st.session_state.edit_recipe_id = recipe['recipe_id']
            st.switch_page("pages/9_Edit_Recipe.py")
    with c2:
        if st.button("🗑️: Delete Recipe", use_container_width=True):
            st.session_state.delete_recipe_id = recipe['recipe_id']
            st.rerun()
    with c3:
        if st.button("🏠: Dashboard", use_container_width=True):
            st.switch_page("pages/1_Dashboard.py")

    if 'delete_recipe_id' in st.session_state and st.session_state.delete_recipe_id == recipe['recipe_id']:
        st.warning("⚠️: Delete forever?")
        cy, cn = st.columns(2)
        with cy:
            if st.button("Yes, Delete", type="primary", use_container_width=True):
                db.delete_user_recipe(recipe['recipe_id'])
                for k in ['delete_recipe_id', 'selected_recipe_id']:
                    st.session_state.pop(k, None)
                st.success("Deleted!")
                st.balloons()
                import time; time.sleep(1)
                st.switch_page("pages/2_Cookbook.py")
        with cn:
            if st.button("Cancel", use_container_width=True):
                st.session_state.pop('delete_recipe_id', None)
                st.rerun()
else:
    st.markdown("---")
    
    # Show save/unsave option for public recipes
    if recipe['is_public']:
        is_saved = db.is_recipe_saved(st.session_state.user_id, recipe['recipe_id'])
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if is_saved:
                if st.button("❌ Remove from Cookbook", use_container_width=True, type="secondary"):
                    db.unsave_public_recipe(st.session_state.user_id, recipe['recipe_id'])
                    st.success("✅ Recipe removed from your cookbook!")
                    import time; time.sleep(1)
                    st.rerun()
            else:
                if st.button("📥 Save to My Cookbook", use_container_width=True, type="primary"):
                    result = db.save_public_recipe(st.session_state.user_id, recipe['recipe_id'])
                    if result:
                        st.success("✅ Recipe saved to your cookbook!")
                        st.balloons()
                        import time; time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Recipe is already in your cookbook!")
        with col2:
            if st.button("🏠: Back to Dashboard", use_container_width=True):
                st.switch_page("pages/1_Dashboard.py")
    else:
        if st.button("🏠: Back to Dashboard", use_container_width=True, type="primary"):
            st.switch_page("pages/1_Dashboard.py")

st.markdown("---")
st.caption("Recipes For Success © 2025 • Made with ❤️ and a pinch of code")