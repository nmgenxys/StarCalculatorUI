import streamlit as st
import json
import pandas as pd

st.set_page_config(layout="wide")

# =========== header =============
col1, col2 = st.columns([1, 5])
with col1:
    st.image("1Asset 49GenXysHD.png", width=1200)
with col2:
    st.title("Star Rating Calculator")
    st.markdown(
        "<div style='margin-top: -10px; font-size:20px; font-style: italic;'>Understand how GenXys One can impact your star rating</div>",
        unsafe_allow_html=True
    )
# ===== Logic and code ======
# Load JSON files
@st.cache_data
def load_json(filename):
    with open(filename) as f:
        return json.load(f)

part_c_thresholds = load_json("part_c_star_thresholds.json")
part_d_thresholds = load_json("part_d_star_calculator.json")
contract_scores = load_json("contract_measure_scores.json")

# To compute star rating:
def get_star_rating(value, code, is_part_d=False, plan_type="MA-PD"):
    if value == "N/A" or isinstance(value, str):
        return "N/A"

    thresholds_data = part_d_thresholds if is_part_d else part_c_thresholds
    base_code = code.split(":")[0]

    if base_code not in thresholds_data:
        return "N/A"

    entry = thresholds_data[base_code]
    reverse = entry.get("reverse", False)

    thresholds = entry["thresholds"][plan_type] if is_part_d else entry["thresholds"]

    for i in range(4, -1, -1):
        if reverse:
            if value <= thresholds[i]:
                return i + 1
        else:
            if value >= thresholds[i]:
                return i + 1
    return 1

# Summary star computation
def compute_summary_star_ratings(scores_dict, plan_type="MA-PD"):
    part_c_stars = []
    part_d_stars = []

    for measure_code, value in scores_dict.items():
        if isinstance(value, str) or value in ["N/A", None]:
            continue

        base_code = measure_code.split(":")[0]
        is_part_d = base_code.startswith("D")

        thresholds = part_d_thresholds if is_part_d else part_c_thresholds
        if base_code not in thresholds:
            continue

        star = get_star_rating(value, measure_code, is_part_d, plan_type)
        if isinstance(star, int):
            if is_part_d:
                part_d_stars.append(star)
            else:
                part_c_stars.append(star)

    part_c_avg = round(sum(part_c_stars) / len(part_c_stars), 2) if part_c_stars else "N/A"
    part_d_avg = round(sum(part_d_stars) / len(part_d_stars), 2) if part_d_stars else "N/A"
    all_stars = part_c_stars + part_d_stars
    total_avg = round(sum(all_stars) / len(all_stars), 2) if all_stars else "N/A"

    return part_c_avg, part_d_avg, total_avg


# Measures of interest
measures_of_interest = [
    "C14: Medication Reconciliation Post-Discharge",
    "C19: Getting Needed Care",
    "D05: Rating of Drug Plan",
    "D06: Getting Needed Prescription Drugs",
    "D08: Medication Adherence for Diabetes Medications",
    "D09: Medication Adherence for Hypertension (RAS antagonists)",
    "D10: Medication Adherence for Cholesterol (Statins)",
    "D11: MTM Program Completion Rate for CMR"
]

# UI Begins

# ======== Contract name dropdown and Plan Drop Down ========= 
contract_name_to_id = {
    data["contract_name"]: cid
    for cid, data in contract_scores.items() if "contract_name" in data
}

col1, col2 = st.columns(2)

with col1:
    selected_name = st.selectbox("Select a Contract", sorted(contract_name_to_id.keys()))
    contract_id = contract_name_to_id[selected_name]
    contract = contract_scores[contract_id]
    measures = contract["measures"]

with col2:
    selected_plan_type = st.selectbox("Select Plan Type", ["MA-PD", "PDP"])

# ==================== Table ====================
# Title, Spacer, Boost Input, Apply, Reset — all in one row
title_col, spacer_col, boost_input_col, boost_btn_col, reset_col = st.columns([5.5, 1.5, 0.6, 1.1, 1])

# Title
with title_col:
    st.markdown(f"## {selected_name.title()}'s *Projected* Star Gains")

# Spacer (just to nudge input right)
with spacer_col:
    st.markdown("")  # empty

# Boost Input
with boost_input_col:
    st.markdown("""
        <style>
        div[data-testid="stNumberInput"] {
            margin-top: 1px !important;
        }
        </style>
    """, unsafe_allow_html=True)
    boost_amount = st.number_input(
        "Apply % to all", min_value=0, max_value=100, step=1,
        key="boost_input", label_visibility="collapsed"
    )

# Apply Button
with boost_btn_col:
    st.markdown("""
        <style>
        div[data-testid="base-button-apply"] button {
            background-color: #f0f0f0 !important;
            color: black !important;
            margin-top: 6px !important;
        }
        </style>
    """, unsafe_allow_html=True)
    if st.button("Apply New % to All", key="base-button-apply"):
        for measure in measures_of_interest:
            val = st.session_state.get(measure, None)
            if isinstance(val, int):
                st.session_state[measure] = min(val + boost_amount, 100)
        st.rerun()

# Reset Button
with reset_col:
    st.markdown("""
        <style>
        div[data-testid="base-button-reset"] button {
            background-color: #f0f0f0 !important;
            color: black !important;
            margin-top: 6px !important;
        }
        </style>
    """, unsafe_allow_html=True)
    if st.button("Reset New %", key="base-button-reset"):
        for measure in measures_of_interest:
            baseline = measures.get(measure, 0.0)
            st.session_state[f"{measure}_reset"] = int(baseline * 100) if isinstance(baseline, (int, float)) else baseline
        st.rerun()





# style cell for ease
def style_cell(content, align="center"):
    return f"<div style='line-height: 1.2; padding: 0.05rem 0; text-align: {align}; font-size:18px;'>{content}</div>"

rows = []
gxsim_values = {}

# TABLE Header row
header = st.columns([4, 2, 2, 3, 2, 2])
header[0].markdown("<div style='text-align: left; font-size:18px;'><strong>Measure</strong></div>", unsafe_allow_html=True)
header[1].markdown("<div style='text-align: center; font-size:18px;'><strong>Baseline</strong></div>", unsafe_allow_html=True)
header[2].markdown("<div style='text-align: center; font-size:18px;'><strong>Star Rating</strong></div>", unsafe_allow_html=True)
header[3].markdown("<div style='text-align: center; font-size:18px;'><strong>New %</strong></div>", unsafe_allow_html=True)
header[4].markdown("<div style='text-align: center; font-size:18px;'><strong>New Star</strong></div>", unsafe_allow_html=True)
header[5].markdown("<div style='text-align: center; font-size:18px;'><strong>% ∆</strong></div>", unsafe_allow_html=True)

# Style input box alignment
st.markdown("""
    <style>
        div[data-testid="stNumberInput"] input {
            text-align: center !important;
        }
        div[data-testid="stNumberInput"] {
            display: flex;
            justify-content: center;
        }
    </style>
""", unsafe_allow_html=True)

# Reset session init
if "gxsim_reset" not in st.session_state:
    st.session_state.gxsim_reset = {}

# Track contract change
if "prev_contract" not in st.session_state:
    st.session_state.prev_contract = contract_id

# If user selects a different contract, reset values
# If user selects a different contract, reset values
if st.session_state.prev_contract != contract_id:
    for measure in measures_of_interest:
        baseline = measures.get(measure, "N/A")
        
        # If it's a number, convert to int percentage
        if isinstance(baseline, (int, float)):
            st.session_state[measure] = int(baseline * 100)
        else:
            # Store the string message (like "Plan too new to be measured")
            st.session_state[measure] = baseline
            
    # Update contract tracker
    st.session_state.prev_contract = contract_id

# ======== PRE-APPLY PENDING BOOST/RESET UPDATES =========
for measure in measures_of_interest:
    reset_key = f"{measure}_reset"
    boost_key = f"{measure}_boost"

    if reset_key in st.session_state:
        st.session_state[measure] = st.session_state[reset_key]
        del st.session_state[reset_key]

    elif boost_key in st.session_state:
        st.session_state[measure] = st.session_state[boost_key]
        del st.session_state[boost_key]


# Dynamic rows
for measure in measures_of_interest:
    value = measures.get(measure, "N/A")
    base_code = measure.split(":")[0]
    is_part_d = base_code.startswith("D")
    star_rating = get_star_rating(value, measure, is_part_d, selected_plan_type)

    baseline = value if isinstance(value, float) else 0.0
    default = int(min(baseline + 0.05, 1.0) * 100)
    # Initialize only if not set
    if measure not in st.session_state:
        st.session_state[measure] = int(measures.get(measure, 0.0) * 100)

    col1, col2, col3, col4, col5, col6 = st.columns([4, 2, 2, 3, 2, 2])
    col1.markdown(style_cell(measure, align="left"), unsafe_allow_html=True)
    col2.markdown(style_cell(f"{int(baseline*100)}%" if isinstance(baseline, float) else "N/A"), unsafe_allow_html=True)
    col3.markdown(style_cell(f"{star_rating}"), unsafe_allow_html=True)

    gx_val = None  # default
    new_star = "N/A"
    delta = "N/A"

    with col4:
        if isinstance(st.session_state[measure], (int, float)):
            current_val = st.session_state.get(f"{measure}_reset", st.session_state[measure])

            gx_val_pct = st.number_input(
                "", min_value=0, max_value=100, step=1,
                key=measure, value=current_val,
                label_visibility="collapsed", format="%d"
            )
            gx_val = gx_val_pct / 100.0

            # add this line to capture the value for summary calculation
            gxsim_values[measure] = gx_val

            if f"{measure}_reset" in st.session_state:
                del st.session_state[f"{measure}_reset"]
            
            new_star = get_star_rating(gx_val, measure, is_part_d, selected_plan_type)
            delta = round((gx_val - value) * 100) if isinstance(value, float) else "N/A"



    col5.markdown(style_cell(f"{new_star}"), unsafe_allow_html=True)
    col6.markdown(style_cell(f"{delta}%" if delta != "N/A" else "N/A"), unsafe_allow_html=True)










# Summary
baseline_part_c, baseline_part_d, baseline_overall = compute_summary_star_ratings(measures, plan_type=selected_plan_type)

# Build a combined dictionary of baseline + edited GenXys values
gx_combined = {}

for m, v in measures.items():
    if m in gxsim_values:
        gx_combined[m] = gxsim_values[m]  # edited value
    else:
        gx_combined[m] = v  # original baseline

# Now compute summary star ratings using all measures (Part C and D)
gx_part_c, gx_part_d, gx_overall = compute_summary_star_ratings(gx_combined, plan_type=selected_plan_type)

def styled_metric(label, projected, baseline):
    if not isinstance(projected, float) or not isinstance(baseline, float):
        return st.markdown("N/A")

    delta = projected - baseline
    delta_text = f"{delta:+.2f}"
    delta_color = "green" if delta > 0 else "red" if delta < 0 else "gray"
    arrow = "↑" if delta > 0 else "↓" if delta < 0 else "→"

    st.markdown(f"""
    <div style="text-align: center; line-height: 1.3;">
<div style="font-size: 1.1rem; font-weight: 600; color: #4a90f7; margin-bottom: 0.25rem;">{label}</div>
        <div style="display: flex; justify-content: center; align-items: baseline; gap: 0.5rem;">
            <div style="font-size: 2rem; color: grey;">{baseline:.2f}</div>
            <div style="font-size: 3rem; font-weight: bold;">{projected:.2f}</div>
        </div>
        <div style="font-size: 1.8rem; font-weight: bold; color: {delta_color}; margin-top: 0.2rem;">
            {arrow} <span style="font-size: rem;">{delta_text}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


st.markdown("---")
st.markdown("### Summary Star Ratings (Baseline vs. GenXysOne)")

col1, col2, col3 = st.columns(3)
with col1:
    styled_metric("Part C Avg", gx_part_c, baseline_part_c)
with col2:
    styled_metric("Part D Avg", gx_part_d, baseline_part_d)
with col3:
    styled_metric("Overall Avg", gx_overall, baseline_overall)




