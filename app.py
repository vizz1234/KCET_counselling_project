import streamlit as st
import json
import pandas as pd
import numpy as np

# --- Login section ---
def login():
    st.title("Manyu's Classes College Finder")
    password = st.text_input("Enter password:", type="password")

    if password != st.secrets["app_password"]:
        st.warning("Incorrect password")
        st.stop()  # Halts the app if wrong password

# Call login function first
login()

# --- Your existing app logic below ---
st.title("Manyu's Classes College Finder Based on CET Rank")
# Load the JSON file
with open("data/category_tables.json", "r") as f:
    category_tables_dict = json.load(f)

# Convert each dict back into a DataFrame
category_tables = {
    category: pd.DataFrame(**df_dict)
    for category, df_dict in category_tables_dict.items()
}

with open("data/category_tables_2ext.json", "r") as f:
    category_tables_2_dict = json.load(f)

category_tables_2 = {
    category: pd.DataFrame(**df_dict)
    for category, df_dict in category_tables_2_dict.items()
}

branches = ['AI Artificial\nIntelligence',
       'CF CS(Artificial\nIntel.)','CS Computers',
       'DL B.TECH IN CS','EC Electronics',
       'EE Electrical',
       'IE Info.Science',]


def get_valid_colleges(category, selected_branches, rank, rank_low=None, rank_high=None):
    if rank_low is None:
        rank_low = max(0, rank - 1000)
    if rank_high is None:
        rank_high = min(rank + 1000, 200000)

    df_cat1 = category_tables.get(category)
    df_cat2 = category_tables_2.get(category)

    all_valid_colleges = set()
    for branch in selected_branches:
        if branch not in df_cat1.index:
            matches = [b for b in df_cat1.index if branch.lower() in b.lower()]
            if not matches:
                continue
            branch = matches[0]

        round1 = pd.to_numeric(df_cat1.loc[branch], errors='coerce')
        round2 = pd.to_numeric(df_cat2.loc[branch], errors='coerce')

        mask1 = (round1 >= rank_low) & (round1 <= rank_high)
        mask2 = (round2 >= rank_low) & (round2 <= rank_high)

        valid_colleges = set(round1[mask1].index).union(set(round2[mask2].index))
        all_valid_colleges.update(valid_colleges)

    return list(all_valid_colleges)


def get_branch_ranks_for_colleges(category, branch, colleges):
    df_cat1 = category_tables.get(category)
    df_cat2 = category_tables_2.get(category)

    if branch not in df_cat1.index:
        matches = [b for b in df_cat1.index if branch.lower() in b.lower()]
        if not matches:
            return pd.DataFrame()
        branch = matches[0]

    round1 = pd.to_numeric(df_cat1.loc[branch], errors='coerce')
    round2 = pd.to_numeric(df_cat2.loc[branch], errors='coerce')

    # Select ranks only for the provided colleges list
    round1_sel = round1.loc[round1.index.intersection(colleges)]
    round2_sel = round2.loc[round2.index.intersection(colleges)]

    result = pd.DataFrame({
        f"{branch} R1": round1_sel,
        f"{branch} R2": round2_sel
    })
    result.index.name = "College"
    return result


# --- Streamlit code ---

category = st.selectbox("Select Category", sorted(category_tables.keys()))
rank = st.number_input("Enter Rank", min_value=1, max_value=200000, value=5000)

selected_branches = st.multiselect(
    "Select up to 4 Branches",
    options=branches,
    default=["CS Computers"],
    max_selections=4

)

custom_range = st.checkbox("Customize Rank Range", value=False)
rank_low = rank_high = None
if custom_range:
    rank_low = st.number_input("Rank Low", min_value=0, max_value=200000, value=max(0, rank - 1000))
    rank_high = st.number_input("Rank High", min_value=0, max_value=200000, value=min(rank + 1000, 200000))

if st.button("Find Colleges"):
    if not selected_branches:
        st.warning("Please select at least one branch.")
    else:
        # Get all colleges that qualify for any branch & any round within rank range
        all_valid_colleges = get_valid_colleges(category, selected_branches, rank, rank_low, rank_high)

        if not all_valid_colleges:
            st.write("No colleges found for the given criteria.")
        else:
            combined_df = pd.DataFrame()

            for branch in selected_branches:
                branch_df = get_branch_ranks_for_colleges(category, branch, all_valid_colleges)
                if combined_df.empty:
                    combined_df = branch_df
                else:
                    combined_df = combined_df.join(branch_df, how='outer')

            st.write("### Matching Colleges Across Branches")
            # Check if DataFrame has any columns
            if not combined_df.empty:
                default_sort_col = combined_df.columns[0]  # Use the first column as default
                sort_col = selected_branches[0] if selected_branches and selected_branches[0] in combined_df.columns else default_sort_col

                combined_df.sort_values(by=sort_col, inplace=True)

            st.dataframe(combined_df)
