import streamlit as st
import database as db
import theme_manager

theme_manager.apply_user_theme()

# Page config
st.set_page_config(
    page_title="Shopping List - Recipes For Success",
    page_icon="🛒",
    layout="wide"
)

# Session check
if 'user_id' not in st.session_state or st.session_state.user_id is None:
    st.warning("⚠️ Please sign in first")
    st.stop()

# Get user's preferred unit system
user_settings = db.get_user_settings(st.session_state.user_id)
user_unit_system = user_settings['units'] if user_settings else 'imperial'

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🛒 Shopping List")
with col2:
    if st.button("🏠 Dashboard", use_container_width=True):
        st.switch_page("pages/1_Dashboard.py")

st.markdown("---")

# Add New Item Section
with st.expander("➕ Add New Item", expanded=False):
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    with st.form("add_shopping_item", clear_on_submit=True):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            item_name = st.text_input("Item Name*")
        with col2:
            item_quantity = st.number_input("Quantity", min_value=0.0, step=0.5, value=1.0)
        with col3:
            item_unit = st.text_input("Unit")
        
        if st.form_submit_button("➕ Add to List", type="primary", use_container_width=True):
            if not item_name.strip():
                st.error("❌ Item name is required")
            else:
                result = db.create_shopping_list_item(
                    user_id=st.session_state.user_id,
                    name=item_name.strip(),
                    quantity=item_quantity if item_quantity > 0 else None,
                    unit=item_unit.strip() if item_unit.strip() else None,
                    is_checked=False
                )
                if isinstance(result, dict) and 'error' in result:
                    st.error(f"❌ {result['error']}")
                else:
                    st.success(f"✅ Added {item_name} to shopping list!")
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# Filters and Actions
col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
with col1:
    search_query = st.text_input("Search")
with col2:
    filter_option = st.selectbox("Filter", ["All Items", "Unchecked Only", "Checked Only"])
with col3:
    st.markdown("<div style='height: 29px'></div>", unsafe_allow_html=True)  # Spacer for alignment
    if st.button("🗑️ Clear Checked", use_container_width=True):
        st.session_state.confirm_clear = True
with col4:
    st.markdown("<div style='height: 29px'></div>", unsafe_allow_html=True)  # Spacer for alignment
    if st.button("📦 Add All to Pantry", use_container_width=True):
        st.session_state.add_to_pantry_mode = True

st.markdown("---")

# Fetch shopping list items
shopping_items = db.get_user_shopping_list(st.session_state.user_id)

# Process items to add conversion info
processed_items = []
for item in shopping_items:
    # Check if unit is convertible
    if item['quantity'] and item['unit']:
        converted_qty, converted_unit = db.convert_unit(
            item['quantity'], 
            item['unit'], 
            to_system="metric" if user_unit_system == "imperial" else "imperial"
        )
        is_convertible = (converted_unit != item['unit'])
    else:
        converted_qty = item['quantity']
        converted_unit = item['unit']
        is_convertible = False
    
    processed_items.append({
        **item,
        'is_convertible': is_convertible,
        'converted_qty': converted_qty,
        'converted_unit': converted_unit
    })

# Apply filters
filtered_items = processed_items

# Search filter
if search_query:
    filtered_items = [item for item in filtered_items if search_query.lower() in item['name'].lower()]

# Status filter
if filter_option == "Unchecked Only":
    filtered_items = [item for item in filtered_items if not item['is_checked']]
elif filter_option == "Checked Only":
    filtered_items = [item for item in filtered_items if item['is_checked']]

# Statistics
total_items = len(shopping_items)
checked_items = len([item for item in shopping_items if item['is_checked']])
unchecked_items = total_items - checked_items

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Items", total_items)
with col2:
    st.metric("To Buy", unchecked_items)
with col3:
    st.metric("Checked Off", checked_items)
with col4:
    if total_items > 0:
        progress = int((checked_items / total_items) * 100)
        st.metric("Progress", f"{progress}%")
    else:
        st.metric("Progress", "0%")

st.markdown("---")

# Initialize conversion toggle states if not exists
if 'shopping_conversion_toggles' not in st.session_state:
    st.session_state.shopping_conversion_toggles = {}

# Display shopping items
if filtered_items:
    # Sort: unchecked items first, then checked items
    filtered_items.sort(key=lambda x: (x['is_checked'], x['name'].lower()))
    
    for item in filtered_items:
        checked_class = "checked" if item['is_checked'] else ""
        
        # Determine which quantity to show based on toggle state
        toggle_key = f"shop_toggle_{item['list_id']}"
        show_converted = st.session_state.shopping_conversion_toggles.get(toggle_key, False)
        
        # Build quantity display
        quantity_display = ""
        if item['quantity']:
            if show_converted and item['is_convertible']:
                qty = item['converted_qty']
                formatted_qty = f"{qty:.2f}".rstrip("0").rstrip(".") if "." in str(qty) else str(qty)
                unit = item['converted_unit'] or ""
            else:
                qty = item['quantity']
                formatted_qty = f"{qty:.2f}".rstrip("0").rstrip(".") if "." in str(qty) else str(qty)
                unit = item['unit'] or ""
            quantity_display = f"{formatted_qty} {unit}".strip()
        
        # Display card
        st.markdown(f"""
        <div class="shopping-card {checked_class}">
            <div class="item-name">{item['name']}</div>
            <div class="item-quantity">{quantity_display}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Action buttons
        if item['is_convertible']:
            col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
            with col1:
                checkbox_label = "✅ Uncheck" if item['is_checked'] else "☑️ Check"
                if st.button(checkbox_label, key=f"check_{item['list_id']}", use_container_width=True):
                    db.update_shopping_list_item(
                        list_id=item['list_id'],
                        name=item['name'],
                        quantity=item['quantity'],
                        unit=item['unit'],
                        is_checked=not item['is_checked']
                    )
                    st.rerun()
            with col2:
                if st.button("✏️ Edit", key=f"edit_{item['list_id']}", use_container_width=True):
                    st.session_state.edit_item_id = item['list_id']
                    st.rerun()
            with col3:
                if st.button("🗑️ Delete", key=f"delete_{item['list_id']}", use_container_width=True):
                    st.session_state.delete_item_id = item['list_id']
                    st.rerun()
            with col4:
                if st.button("🔄 Convert", key=f"conv_{item['list_id']}", use_container_width=True, help="Toggle unit conversion"):
                    st.session_state.shopping_conversion_toggles[toggle_key] = not show_converted
                    st.rerun()
            with col5:
                st.write("")  # Spacer
        else:
            col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
            with col1:
                checkbox_label = "✅ Uncheck" if item['is_checked'] else "☑️ Check"
                if st.button(checkbox_label, key=f"check_{item['list_id']}", use_container_width=True):
                    db.update_shopping_list_item(
                        list_id=item['list_id'],
                        name=item['name'],
                        quantity=item['quantity'],
                        unit=item['unit'],
                        is_checked=not item['is_checked']
                    )
                    st.rerun()
            with col2:
                if st.button("✏️ Edit", key=f"edit_{item['list_id']}", use_container_width=True):
                    st.session_state.edit_item_id = item['list_id']
                    st.rerun()
            with col3:
                if st.button("🗑️ Delete", key=f"delete_{item['list_id']}", use_container_width=True):
                    st.session_state.delete_item_id = item['list_id']
                    st.rerun()
            with col4:
                st.write("")  # Spacer
        
        st.markdown("<br>", unsafe_allow_html=True)
else:
    if search_query:
        st.info(f"🔍 No items found matching '{search_query}'")
    elif filter_option == "Checked Only" and checked_items == 0:
        st.info("✨ No checked items yet. Check off items as you shop!")
    elif filter_option == "Unchecked Only" and unchecked_items == 0:
        st.success("🎉 All items checked! You're done shopping!")
    else:
        st.info("📝 Your shopping list is empty. Add items to get started!")

# Edit Item Modal
if 'edit_item_id' in st.session_state:
    item = next((x for x in shopping_items if x['list_id'] == st.session_state.edit_item_id), None)
    if item:
        st.markdown("---")
        st.subheader(f"✏️ Edit: {item['name']}")
        with st.form("edit_shopping_item"):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                edit_name = st.text_input("Item Name", value=item['name'])
            with col2:
                edit_qty = st.number_input("Quantity", value=float(item['quantity']) if item['quantity'] else 0.0, step=0.5)
            with col3:
                edit_unit = st.text_input("Unit", value=item['unit'] or "")
            
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True):
                    if not edit_name.strip():
                        st.error("❌ Item name cannot be empty")
                    else:
                        db.update_shopping_list_item(
                            list_id=item['list_id'],
                            name=edit_name.strip(),
                            quantity=edit_qty if edit_qty > 0 else None,
                            unit=edit_unit.strip() if edit_unit.strip() else None,
                            is_checked=item['is_checked']
                        )
                        del st.session_state.edit_item_id
                        st.success("✅ Item updated!")
                        st.rerun()
            with col_cancel:
                if st.form_submit_button("❌ Cancel", use_container_width=True):
                    del st.session_state.edit_item_id
                    st.rerun()

# Delete Confirmation
if 'delete_item_id' in st.session_state:
    item = next((x for x in shopping_items if x['list_id'] == st.session_state.delete_item_id), None)
    if item:
        st.markdown("---")
        st.warning(f"⚠️ Are you sure you want to delete **{item['name']}**?")
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("🗑️ Yes, Delete", type="primary", use_container_width=True):
                db.delete_shopping_list_item(st.session_state.delete_item_id)
                del st.session_state.delete_item_id
                st.success("✅ Item deleted!")
                st.rerun()
        with col_no:
            if st.button("❌ Cancel", use_container_width=True):
                del st.session_state.delete_item_id
                st.rerun()

# Clear All Checked Items Confirmation
if 'confirm_clear' in st.session_state and st.session_state.confirm_clear:
    checked_to_clear = [item for item in shopping_items if item['is_checked']]
    if checked_to_clear:
        st.markdown("---")
        st.warning(f"⚠️ Delete all {len(checked_to_clear)} checked items?")
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("🗑️ Yes, Clear All Checked", type="primary", use_container_width=True):
                for item in checked_to_clear:
                    db.delete_shopping_list_item(item['list_id'])
                st.session_state.confirm_clear = False
                st.success(f"✅ Cleared {len(checked_to_clear)} items!")
                st.rerun()
        with col_no:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.confirm_clear = False
                st.rerun()
    else:
        st.info("No checked items to clear!")
        st.session_state.confirm_clear = False

# Add to Pantry Mode
if 'add_to_pantry_mode' in st.session_state and st.session_state.add_to_pantry_mode:
    checked_items_list = [item for item in shopping_items if item['is_checked']]
    if checked_items_list:
        st.markdown("---")
        st.info(f"📦 {len(checked_items_list)} checked items will be added to your pantry")
        st.caption("Note: You'll need to set expiration dates in the Pantry page")
        
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("📦 Add to Pantry", type="primary", use_container_width=True):
                from datetime import datetime, timedelta
                added_count = 0
                items_to_delete = []
                
                for item in checked_items_list:
                    # Add to pantry with default 30-day expiration
                    result = db.create_pantry_item(
                        user_id=st.session_state.user_id,
                        name=item['name'],
                        quantity=item['quantity'] if item['quantity'] else 1.0,
                        unit=item['unit'],
                        expiration_date=(datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                        low_threshold=1.0
                    )
                    if not isinstance(result, dict):
                        added_count += 1
                        items_to_delete.append(item['list_id'])
                
                # Delete items from shopping list after successfully adding to pantry
                for list_id in items_to_delete:
                    db.delete_shopping_list_item(list_id)
                
                st.session_state.add_to_pantry_mode = False
                st.success(f"✅ Added {added_count} items to pantry and removed from shopping list!")
                st.info("💡 Don't forget to update expiration dates in your Pantry!")
                st.rerun()
        with col_no:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.add_to_pantry_mode = False
                st.rerun()
    else:
        st.info("No checked items to add to pantry!")
        st.session_state.add_to_pantry_mode = False

# Footer
st.markdown("---")
st.caption("Recipes For Success © 2025 • Made with ❤️ and working code")