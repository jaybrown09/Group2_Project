import streamlit as st
import database as db
from datetime import datetime, timedelta
import theme_manager

theme_manager.apply_user_theme()

# Page config
st.set_page_config(
    page_title="Pantry - Recipes For Success",
    page_icon="Pantry",
    layout="wide"
)

# Session check
if 'user_id' not in st.session_state or st.session_state.user_id is None:
    st.warning("Please sign in first")
    st.stop()

# Get user's preferred unit system
user_settings = db.get_user_settings(st.session_state.user_id)
user_unit_system = user_settings['units'] if user_settings else 'imperial'

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.title("My Pantry")
with col2:
    if st.button("🏠 Dashboard", use_container_width=True):
        st.switch_page("pages/1_Dashboard.py")

st.markdown("---")

# Add New Item
with st.expander("Add New Pantry Item", expanded=False):
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    with st.form("add_item", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Item Name*")
            qty = st.number_input("Quantity*", min_value=0.0, step=0.1, value=1.0)
            unit = st.text_input("Unit")
        with c2:
            exp = st.date_input("Expiration Date*", value=datetime.now().date() + timedelta(days=30))
            low = st.number_input("Low Stock Alert", min_value=0.0, step=0.1, value=1.0)
        
        if st.form_submit_button("Add Item", type="primary", use_container_width=True):
            if not name.strip():
                st.error("Name is required")
            else:
                db.create_pantry_item(
                    user_id=st.session_state.user_id,
                    name=name.strip(),
                    quantity=qty,
                    unit=unit.strip() or None,
                    expiration_date=exp.strftime("%Y-%m-%d"),
                    low_threshold=low
                )
                st.success("Item added!")
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# Filters
c1, c2, c3 = st.columns([2,1,1])
with c1:
    search = st.text_input("Search")
with c2:
    filter_by = st.selectbox("Filter", ["All Items", "Expired", "Expiring Soon", "Low Stock", "Good"])
with c3:
    sort_by = st.selectbox("Sort", ["Expiration Date", "Name", "Quantity"])

# Fetch & process items
items = db.get_user_pantry(st.session_state.user_id)
today = datetime.now().date()
processed = []

for item in items:
    exp_date = datetime.strptime(item["expiration_date"], "%Y-%m-%d").date()
    days_left = (exp_date - today).days
    qty = item["quantity"]
    low_thresh = item["low_threshold"]
    unit = item["unit"] or ""

    # Determine statuses independently
    is_expired = days_left < 0
    is_expiring = 0 <= days_left <= 7
    is_low = qty <= low_thresh

    # Build status badges (can have multiple)
    badges = []
    if is_expired:
        badges.append('<span class="status-badge status-expired">Expired</span>')
    if is_expiring:
        if days_left == 0:
            badges.append('<span class="status-badge status-expiring">Expires today</span>')
        elif days_left == 1:
            badges.append('<span class="status-badge status-expiring">Expires tomorrow</span>')
        else:
            badges.append(f'<span class="status-badge status-expiring">Expires in {days_left} days</span>')
    if is_low:
        qty_display = f"{qty:.2f}".rstrip("0").rstrip(".") if "." in str(qty) else str(qty)
        badges.append(f'<span class="status-badge status-low">Low Stock ({qty_display} {unit})</span>')
    if not badges:
        badges.append('<span class="status-badge status-good">Good</span>')

    # For filtering: primary status
    if is_expired:
        primary_status = "expired"
    elif is_expiring:
        primary_status = "expiring"
    elif is_low:
        primary_status = "low"
    else:
        primary_status = "good"

    # Format quantity to 2 decimal places and strip trailing zeros
    formatted_qty = f"{qty:.2f}".rstrip("0").rstrip(".") if "." in str(qty) else str(qty)
    
    # Check if unit is convertible
    converted_qty, converted_unit = db.convert_unit(qty, unit, to_system="metric" if user_unit_system == "imperial" else "imperial")
    is_convertible = (converted_unit != unit) and (unit is not None and unit != "")
    
    processed.append({
        **item,
        "days_left": days_left,
        "badges_html": " ".join(badges),
        "primary_status": primary_status,
        "qty_text": f"{formatted_qty} {unit}".strip(),
        "is_convertible": is_convertible,
        "converted_qty": converted_qty,
        "converted_unit": converted_unit
    })

# Apply search
filtered = [i for i in processed if search.lower() in i["name"].lower()]

# Apply filter
if filter_by == "Expired":
    filtered = [i for i in filtered if i["primary_status"] == "expired"]
elif filter_by == "Expiring Soon":
    filtered = [i for i in filtered if i["primary_status"] == "expiring"]
elif filter_by == "Low Stock":
    filtered = [i for i in filtered if i["primary_status"] == "low"]
elif filter_by == "Good":
    filtered = [i for i in filtered if i["primary_status"] == "good"]

# Sort
if sort_by == "Expiration Date":
    filtered.sort(key=lambda x: x["days_left"])
elif sort_by == "Name":
    filtered.sort(key=lambda x: x["name"].lower())
elif sort_by == "Quantity":
    filtered.sort(key=lambda x: x["quantity"], reverse=True)

st.markdown("---")

# Summary
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Total", len(items))
with c2: st.metric("Expired", len([i for i in processed if i["primary_status"] == "expired"]))
with c3: st.metric("Expiring Soon", len([i for i in processed if i["primary_status"] == "expiring"]))
with c4: st.metric("Low Stock", len([i for i in processed if i["primary_status"] == "low"]))

st.markdown("---")

# Initialize conversion toggle states if not exists
if 'conversion_toggles' not in st.session_state:
    st.session_state.conversion_toggles = {}

# Display cards
if filtered:
    for i in range(0, len(filtered), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(filtered):
                item = filtered[i + j]
                with cols[j]:
                    # Determine which quantity to show based on toggle state
                    toggle_key = f"toggle_{item['pantry_id']}"
                    show_converted = st.session_state.conversion_toggles.get(toggle_key, False)
                    
                    if show_converted and item['is_convertible']:
                        display_qty = f"{item['converted_qty']:.2f}".rstrip("0").rstrip(".")
                        display_unit = item['converted_unit']
                        quantity_text = f"{display_qty} {display_unit}"
                    else:
                        quantity_text = item['qty_text']
                    
                    st.markdown(f"""
                    <div class="pantry-card">
                        <div class="item-name">{item['name']}</div>
                        <div class="item-quantity">Quantity: {quantity_text}</div>
                        <div class="item-date">Expires: {item['expiration_date']}</div>
                        <div>{item['badges_html']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Action buttons row
                    if item['is_convertible']:
                        spacer, b1, b2, b3 = st.columns([0.25, 1, 1, 1]) # extra spacer for conversion button
                        with b1:
                            if st.button("Edit", key=f"edit_{item['pantry_id']}"):
                                st.session_state.edit_id = item['pantry_id']
                                st.rerun()
                        with b2:
                            if st.button("Delete", key=f"del_{item['pantry_id']}"):
                                st.session_state.delete_id = item['pantry_id']
                                st.rerun()
                        with b3:
                            # Conversion toggle button
                            if st.button("🔄 Convert", key=f"conv_{item['pantry_id']}", help="Toggle unit conversion"):
                                st.session_state.conversion_toggles[toggle_key] = not show_converted
                                st.rerun()
                    else:
                        spacer, b1, b2 = st.columns([0.5, 1, 1]) # no conversion button spacer
                        with b1:
                            if st.button("Edit", key=f"edit_{item['pantry_id']}"):
                                st.session_state.edit_id = item['pantry_id']
                                st.rerun()
                        with b2:
                            if st.button("Delete", key=f"del_{item['pantry_id']}"):
                                st.session_state.delete_id = item['pantry_id']
                                st.rerun()
else:
    st.info("No items match your filters.")

# Edit form
if "edit_id" in st.session_state:
    item = next((x for x in items if x["pantry_id"] == st.session_state.edit_id), None)
    if item:
        with st.form("edit_form"):
            st.subheader(f"Edit {item['name']}")
            c1, c2 = st.columns(2)
            with c1:
                n = st.text_input("Name", item["name"])
                q = st.number_input("Quantity", value=float(item["quantity"]), step=0.1)
                u = st.text_input("Unit", item["unit"] or "")
            with c2:
                e = st.date_input("Expiration", datetime.strptime(item["expiration_date"], "%Y-%m-%d"))
                l = st.number_input("Low Threshold", value=float(item["low_threshold"]), step=0.1)
            
            s, c = st.columns(2)
            if s.form_submit_button("Save", type="primary"):
                db.update_pantry_item(item["pantry_id"], n, q, u or None, e.strftime("%Y-%m-%d"), l)
                del st.session_state.edit_id
                st.success("Updated!")
                st.rerun()
            if c.form_submit_button("Cancel"):
                del st.session_state.edit_id
                st.rerun()

# Delete confirm
if "delete_id" in st.session_state:
    item = next((x for x in items if x["pantry_id"] == st.session_state.delete_id), None)
    if item:
        st.warning(f"Delete **{item['name']}**?")
        y, n = st.columns(2)
        if y.button("Yes, Delete", type="primary"):
            db.delete_pantry_item(st.session_state.delete_id)
            del st.session_state.delete_id
            st.success("Deleted!")
            st.rerun()
        if n.button("Cancel"):
            del st.session_state.delete_id
            st.rerun()

st.markdown("---")
st.caption("Recipes For Success © 2025 • Made with ❤️ and a pinch of code")