import json
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)




with open("part_c_star_thresholds.json") as f:
    part_c_thresholds = json.load(f)

with open("part_d_star_calculator.json") as f:
    part_d_thresholds = json.load(f)

with open("contract_measure_scores.json") as f:
    contract_scores = json.load(f)


target_measures = [
    "C14: Medication Reconciliation Post-Discharge",
    "C19: Getting Needed Care",
    "D05: Rating of Drug Plan",
    "D06: Getting Needed Prescription Drugs",
    "D08: Medication Adherence for Diabetes Medications",
    "D09: Medication Adherence for Hypertension (RAS antagonists)",
    "D10: Medication Adherence for Cholesterol (Statins)",
    "D11: MTM Program Completion Rate for CMR"
]
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

    for i in range(4, -1, -1):  # Check from 5 stars down to 1
        if reverse:
            if value <= thresholds[i]:
                return i + 1
        else:
            if value >= thresholds[i]:
                return i + 1
    return 1

def compute_summary_star_ratings(contract_measures, plan_type="MA-PD"):
    part_c_stars = []
    part_d_stars = []

    for measure_name, value in contract_measures.items():
        if isinstance(value, str) or value in ["N/A", None]:
            continue

        base_code = measure_name.split(":")[0]
        is_part_d = base_code.startswith("D")

        thresholds = part_d_thresholds if is_part_d else part_c_thresholds
        if base_code not in thresholds:
            continue

        star = get_star_rating(value, measure_name, is_part_d, plan_type)
        if isinstance(star, int):
            (part_d_stars if is_part_d else part_c_stars).append(star)

    part_c_avg = round(sum(part_c_stars) / len(part_c_stars), 2) if part_c_stars else "N/A"
    part_d_avg = round(sum(part_d_stars) / len(part_d_stars), 2) if part_d_stars else "N/A"

    all_stars = part_c_stars + part_d_stars
    total_avg = round(sum(all_stars) / len(all_stars), 2) if all_stars else "N/A"

    return part_c_avg, part_d_avg, total_avg



#contract_id = "H1994"
#contract = contract_scores.get(contract_id)
all_contract_outputs = []  # Stores summary + detail rows for every contract

for contract_id, contract in contract_scores.items():
    measures = contract["measures"]

    # Summary ratings across all measures
    part_c_avg, part_d_avg, total_avg = compute_summary_star_ratings(measures)

    rows = []
    for measure in target_measures:
        value = contract["measures"].get(measure, "N/A")
        base_code = measure.split(":")[0]
        is_part_d = base_code.startswith("D")

        star_rating = get_star_rating(value, measure, is_part_d=is_part_d, plan_type="MA-PD")

        if value != "N/A" and not isinstance(value, str):
            new_value = round(min(value + 0.05, 1.0), 4)
        else:
            new_value = "N/A"

        new_star_rating = get_star_rating(new_value, measure, is_part_d=is_part_d, plan_type="MA-PD")

        rows.append({
            "Contract ID": contract_id,
            "Contract Name": contract["contract_name"],
            "Measure": measure,
            "Baseline Value": (
                f"{int(value * 100)}%" 
                if isinstance(value, (int, float)) 
                else "N/A"
            ),
            "Star Rating": star_rating,
            "New % with GXSONE": (
                f"{int(new_value * 100)}%" 
                if isinstance(new_value, (int, float)) 
                else "N/A"
            ),
            "New Star Rating": new_star_rating,
            "% Difference": (
                f"{round((new_value - value) * 100)}%" 
                if isinstance(value, (int, float)) and isinstance(new_value, (int, float)) 
                else "N/A"
            ),
            "Part C Avg Star Rating": part_c_avg,
            "Part D Avg Star Rating": part_d_avg,
            "Overall Avg Star Rating": total_avg
        })

    all_contract_outputs.extend(rows)

# Convert all results into a single DataFrame
df_all = pd.DataFrame(all_contract_outputs)

print(df_all)