import streamlit as st
import database as db
from datetime import datetime, timedelta
import theme_manager

theme_manager.apply_user_theme()

# Page config
st.set_page_config(
    page_title="Meal Plan - Recipes For Success",
    page_icon="📅",
    layout="wide"
)

# Session check
if 'user_id' not in st.session_state or st.session_state.user_id is None:
    st.warning("⚠️ Please sign in first")
    st.stop()

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.title("📅 Meal Plan")
with col2:
    if st.button("🏠 Dashboard", use_container_width=True):
        st.switch_page("pages/1_Dashboard.py")

st.markdown("---")

# Initialize session state for week navigation
if 'current_week_offset' not in st.session_state:
    st.session_state.current_week_offset = 0

# View toggle
view_mode = st.radio("View Mode", ["📅 Calendar View", "📋 List View"], horizontal=True, label_visibility="collapsed")

st.markdown("---")

# Add New Meal Plan Section
with st.expander("➕ Add Meal to Plan", expanded=False):
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    
    # Get user's recipes for dropdown
    user_recipes = db.get_user_cookbook(st.session_state.user_id)
    saved_recipes = db.get_saved_public_recipes(st.session_state.user_id)
    all_available_recipes = user_recipes + saved_recipes
    
    if not all_available_recipes:
        st.info("📚 You don't have any recipes yet. Create or save recipes to add them to your meal plan!")
    else:
        with st.form("add_meal_plan", clear_on_submit=True):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                recipe_options = {f"{r['title']}": r['recipe_id'] for r in all_available_recipes}
                selected_recipe_name = st.selectbox("Recipe*", options=list(recipe_options.keys()))
            
            with col2:
                meal_date_str = st.text_input("Date* (YYYY-MM-DD)", value=datetime.now().strftime("%Y-%m-%d"), placeholder="YYYY-MM-DD")
            
            with col3:
                meal_type = st.selectbox("Meal Type*", options=["Breakfast", "Lunch", "Dinner", "Snack"])
            
            if st.form_submit_button("➕ Add to Plan", type="primary", use_container_width=True):
                try:
                    meal_date = datetime.strptime(meal_date_str, "%Y-%m-%d").date()
                    selected_recipe_id = recipe_options[selected_recipe_name]
                    result = db.create_meal_plan(
                        user_id=st.session_state.user_id,
                        date=meal_date.strftime('%Y-%m-%d'),
                        recipe_id=selected_recipe_id,
                        meal_type=meal_type
                    )
                    
                    if isinstance(result, dict) and 'error' in result:
                        st.error(f"❌ {result['error']}")
                    else:
                        st.success(f"✅ Added {selected_recipe_name} to {meal_type} on {meal_date}!")
                        st.rerun()
                except ValueError:
                    st.error("Invalid date format. Please use YYYY-MM-DD")
    
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# Fetch meal plan
meal_plans = db.get_user_meal_plan(st.session_state.user_id)

# Create a dictionary to organize meals by date
meals_by_date = {}
for plan in meal_plans:
    date = plan['date']
    if date not in meals_by_date:
        meals_by_date[date] = []
    
    # Get recipe details
    recipe = db.get_recipe(plan['recipe_id'])
    if recipe:
        meals_by_date[date].append({
            'plan_id': plan['plan_id'],
            'meal_type': plan['meal_type'],
            'recipe_title': recipe['title'],
            'recipe_id': recipe['recipe_id']
        })

# === CALENDAR VIEW ===
if view_mode == "📅 Calendar View":
    # Custom CSS for card styling
    st.markdown("""
    <style>
    .day-card-wrapper {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 12px;
        min-height: 280px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 8px;
        position: relative;
    }
    .day-card-wrapper.is-today {
        border: 2px solid #4CAF50;
        box-shadow: 0 0 15px rgba(76, 175, 80, 0.3);
    }
    .day-header-section {
        text-align: center;
        padding-bottom: 10px;
        margin-bottom: 10px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    .day-name-label {
        font-size: 0.85em;
        font-weight: 600;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .day-number-label {
        font-size: 1.6em;
        font-weight: bold;
        color: #fff;
        margin-top: 2px;
    }
    .meal-card {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        padding: 8px 10px;
        margin-bottom: 6px;
        transition: all 0.2s ease;
        border-left: 3px solid transparent;
    }
    .meal-card:hover {
        background: rgba(255, 255, 255, 0.12);
        transform: translateX(3px);
    }
    .meal-card.Breakfast { border-left-color: #FF9800; }
    .meal-card.Lunch { border-left-color: #2196F3; }
    .meal-card.Dinner { border-left-color: #9C27B0; }
    .meal-card.Snack { border-left-color: #4CAF50; }
    .meal-type-label {
        font-size: 0.65em;
        font-weight: 700;
        text-transform: uppercase;
        padding: 2px 6px;
        border-radius: 3px;
        display: inline-block;
        margin-bottom: 4px;
        letter-spacing: 0.5px;
    }
    .meal-type-label.Breakfast { background: #FF9800; color: #000; }
    .meal-type-label.Lunch { background: #2196F3; color: #fff; }
    .meal-type-label.Dinner { background: #9C27B0; color: #fff; }
    .meal-type-label.Snack { background: #4CAF50; color: #fff; }
    .meal-recipe-title {
        font-size: 0.8em;
        color: #e0e0e0;
        line-height: 1.3;
        word-wrap: break-word;
    }
    .empty-day-message {
        color: #666;
        font-size: 0.75em;
        text-align: center;
        padding: 15px 5px;
        font-style: italic;
    }
    .week-navigation {
        text-align: center;
        font-size: 1.1em;
        font-weight: 500;
        padding: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Week navigation
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday()) + timedelta(weeks=st.session_state.current_week_offset)
    week_end = week_start + timedelta(days=6)
    
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("⬅️ Previous Week", use_container_width=True):
            st.session_state.current_week_offset -= 1
            st.rerun()
    with col2:
        if st.session_state.current_week_offset == 0:
            st.markdown(f'<div class="week-navigation">This Week: {week_start.strftime("%b %d")} - {week_end.strftime("%b %d, %Y")}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="week-navigation">{week_start.strftime("%b %d")} - {week_end.strftime("%b %d, %Y")}</div>', unsafe_allow_html=True)
    with col3:
        if st.button("➡️ Next Week", use_container_width=True):
            st.session_state.current_week_offset += 1
            st.rerun()
    
    if st.session_state.current_week_offset != 0:
        col_center = st.columns([2, 1, 2])[1]
        with col_center:
            if st.button("📍 Today", use_container_width=True):
                st.session_state.current_week_offset = 0
                st.rerun()
    
    st.markdown("---")
    
    # Create 7-day calendar grid
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    cols = st.columns(7)
    
    for i, day_name in enumerate(days_of_week):
        current_date = week_start + timedelta(days=i)
        date_str = current_date.strftime('%Y-%m-%d')
        is_today = current_date == today
        
        with cols[i]:
            # Build the entire card as one HTML block
            card_class = "day-card-wrapper is-today" if is_today else "day-card-wrapper"
            
            card_html = '<div class="' + card_class + '">'
            
            # Header
            card_html += '<div class="day-header-section">'
            card_html += '<div class="day-name-label">' + day_name[:3] + '</div>'
            card_html += '<div class="day-number-label">' + str(current_date.day) + '</div>'
            card_html += '</div>'
            
            # Meals content
            if date_str in meals_by_date:
                meal_order = {'Breakfast': 0, 'Lunch': 1, 'Dinner': 2, 'Snack': 3}
                sorted_meals = sorted(meals_by_date[date_str], key=lambda x: meal_order.get(x['meal_type'], 4))
                
                for meal in sorted_meals:
                    truncated_title = meal['recipe_title'][:22] + ('...' if len(meal['recipe_title']) > 22 else '')
                    meal_type = meal['meal_type']
                    card_html += '<div class="meal-card ' + meal_type + '">'
                    card_html += '<div class="meal-type-label ' + meal_type + '">' + meal_type + '</div>'
                    card_html += '<div class="meal-recipe-title">' + truncated_title + '</div>'
                    card_html += '</div>'
            else:
                card_html += '<div class="empty-day-message">No meals planned</div>'
            
            card_html += '</div>'
            
            # Render the complete card
            st.markdown(card_html, unsafe_allow_html=True)
            
            # Interactive buttons below card (Streamlit requirement)
            if date_str in meals_by_date:
                meal_order = {'Breakfast': 0, 'Lunch': 1, 'Dinner': 2, 'Snack': 3}
                sorted_meals = sorted(meals_by_date[date_str], key=lambda x: meal_order.get(x['meal_type'], 4))
                
                for meal in sorted_meals:
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("👁️", key=f"view_{meal['plan_id']}", use_container_width=True, help=f"View {meal['recipe_title']}"):
                            st.session_state.selected_recipe_id = meal['recipe_id']
                            st.switch_page("pages/8_View_Recipe.py")
                    with btn_col2:
                        if st.button("🗑️", key=f"del_{meal['plan_id']}", use_container_width=True, help="Remove from plan"):
                            st.session_state.delete_plan_id = meal['plan_id']
                            st.rerun()
            
            # Add meal button
            if st.button("➕ Add", key=f"add_{date_str}", use_container_width=True):
                st.session_state.quick_add_date = date_str
                st.rerun()

# === LIST VIEW ===
else:
    st.subheader("📋 Meal Plan List")
    
    if meals_by_date:
        # Sort dates
        sorted_dates = sorted(meals_by_date.keys())
        
        for date_str in sorted_dates:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            is_today = date_obj == datetime.now().date()
            
            # Date section
            st.markdown('<div class="list-view-container">', unsafe_allow_html=True)
            
            day_name = date_obj.strftime('%A')
            formatted_date = date_obj.strftime('%B %d, %Y')
            today_badge = " 🔥 TODAY" if is_today else ""
            
            st.markdown(f'<div class="date-title">{day_name}, {formatted_date}{today_badge}</div>', unsafe_allow_html=True)
            
            # Sort meals
            meal_order = {'Breakfast': 0, 'Lunch': 1, 'Dinner': 2, 'Snack': 3}
            sorted_meals = sorted(meals_by_date[date_str], key=lambda x: meal_order.get(x['meal_type'], 4))
            
            for meal in sorted_meals:
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"""
                    <div class="meal-entry">
                        <div class="meal-type {meal['meal_type']}">{meal['meal_type']}</div>
                        <div class="meal-title">{meal['recipe_title']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.button("👁️ View", key=f"view_list_{meal['plan_id']}", use_container_width=True):
                        st.session_state.selected_recipe_id = meal['recipe_id']
                        st.switch_page("pages/8_View_Recipe.py")
                
                with col3:
                    if st.button("🗑️ Remove", key=f"del_list_{meal['plan_id']}", use_container_width=True):
                        st.session_state.delete_plan_id = meal['plan_id']
                        st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.info("📅 Your meal plan is empty. Add meals to get started!")

# Quick Add Modal
if 'quick_add_date' in st.session_state:
    st.markdown("---")
    st.subheader(f"➕ Add Meal for {st.session_state.quick_add_date}")
    
    user_recipes = db.get_user_cookbook(st.session_state.user_id)
    saved_recipes = db.get_saved_public_recipes(st.session_state.user_id)
    all_available_recipes = user_recipes + saved_recipes
    
    if all_available_recipes:
        with st.form("quick_add_meal"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                recipe_options = {f"{r['title']}": r['recipe_id'] for r in all_available_recipes}
                selected_recipe_name = st.selectbox("Recipe*", options=list(recipe_options.keys()), key="quick_add_recipe")
            
            with col2:
                meal_type_quick = st.selectbox("Meal Type*", options=["Breakfast", "Lunch", "Dinner", "Snack"], key="quick_add_meal_type")
            
            col_add, col_cancel = st.columns(2)
            with col_add:
                if st.form_submit_button("➕ Add", type="primary", use_container_width=True):
                    selected_recipe_id = recipe_options[selected_recipe_name]
                    result = db.create_meal_plan(
                        user_id=st.session_state.user_id,
                        date=st.session_state.quick_add_date,
                        recipe_id=selected_recipe_id,
                        meal_type=meal_type_quick
                    )
                    
                    if isinstance(result, dict) and 'error' in result:
                        st.error(f"❌ {result['error']}")
                    else:
                        del st.session_state.quick_add_date
                        st.success(f"✅ Added {selected_recipe_name}!")
                        st.rerun()
            
            with col_cancel:
                if st.form_submit_button("❌ Cancel", use_container_width=True):
                    del st.session_state.quick_add_date
                    st.rerun()

# Delete Confirmation
if 'delete_plan_id' in st.session_state:
    st.markdown("---")
    st.warning("⚠️ Remove this meal from your plan?")
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("🗑️ Yes, Remove", type="primary", use_container_width=True):
            db.delete_recipe_from_meal_plan(st.session_state.delete_plan_id)
            del st.session_state.delete_plan_id
            st.success("✅ Meal removed from plan!")
            st.rerun()
    with col_no:
        if st.button("❌ Cancel", use_container_width=True):
            del st.session_state.delete_plan_id
            st.rerun()

# Footer
st.markdown("---")
st.caption("Recipes For Success © 2025 • Made with ❤️ and a pinch of code")