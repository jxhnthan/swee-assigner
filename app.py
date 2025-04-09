import streamlit as st
import pandas as pd
import random
import re

# Streamlit app title
st.title("SWEE Case Assigner")

# File uploader widget
uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx", "xls"])

# Define team segmentation and exclusion criteria (e.g., sensitive cases someone shouldn't handle)
team_data = {
    'Leadership': {
        'Haikel': [],
        'Zhengqin': []
    },
    'Senior': {
        'Kirsty': [],
        'Dominic': [],
        'Jiaying': []
    },
    'Junior': {
        'Oliver': ['Eating Disorders', 'Narcissism'],
        'Janice': ['Parenting', 'Occupational/Academic Issues', 'Mandarin-speaking'],
        'Andrew': []
    }
}

# Map client survey responses to case types
response_to_case_type = {
    "I've been feeling depressed": "Depression",
    "I feel anxious or overwhelmed": "Anxiety",
    "My mood is interfering with my job/school/performance": "Occupational/Academic Issues",
    "I struggle with building or maintaining relationships": "Relationship Issues",
    "I can't find purpose and meaning in my life": "Existential Crisis or Life Purpose",
    "I am grieving": "Grief and Loss",
    "I have experienced trauma": "Trauma",
    "I need to talk through a specific challenge": "Situational Stress or Personal Challenge",
    "I want to gain self confidence": "Self-Esteem/Confidence",
    "I want to improve myself but I don't know where to start": "Personal Growth/Development",
    "Recommended to me (friend, family, doctor, etc.)": "External Recommendation",
    "Sleep problems or appetite changes": "Sleep and Eating Disorders",
    "Recent major life event or transition": "Life Transition",
    "Work or academic stress": "Work/Academic Stress",
    "Other": "Miscellaneous"
}

def map_case_types(case_description):
    case_types = []
    # Try to match the case description to multiple predefined categories
    for key, value in response_to_case_type.items():
        if key.lower() in case_description.lower():
            case_types.append(value)
    
    return case_types if case_types else ["Miscellaneous"]  # Default to "Miscellaneous" if no match

# Flatten team members into a list based on selected groups
def get_team_members(selected_groups):
    return [member for group, members in team_data.items() if group in selected_groups for member in members.keys()]

# Assignment methods
assignment_methods = ["Random Assignment", "Exclusion-Based"]

# Sidebar options
st.sidebar.header("Group Inclusion Options")
selected_groups = st.sidebar.multiselect(
    "Select Groups to Include:",
    options=["Leadership", "Senior", "Junior"],
    default=["Leadership", "Senior", "Junior"]
)

if not selected_groups:
    st.warning("Please select at least one group to include.")
else:
    method = st.radio("Select Assignment Method:", assignment_methods)

    if uploaded_file is not None:
        try:
            excel_file = pd.ExcelFile(uploaded_file)
            st.subheader("Available Sheets:")
            sheet_names = excel_file.sheet_names
            st.write(sheet_names)

            selected_sheet = st.selectbox("Select sheet to use:", sheet_names, index=sheet_names.index("Sheet2") if "Sheet2" in sheet_names else 0)
            df = excel_file.parse(selected_sheet)
            st.write(f"Displaying data from: {selected_sheet}")

            if 'Still Pending' in df.columns and 'Priority Score' in df.columns and 'Case Description' in df.columns:
                st.subheader("Filter by 'Still Pending' Status:")
                status_options = df['Still Pending'].dropna().unique().tolist()
                status_options.append("All")
                default_status = ['YES'] if 'YES' in status_options else []
                selected_status = st.multiselect("Select status to filter:", status_options, default=default_status)

                if 'All' in selected_status:
                    filtered_df = df
                else:
                    filtered_df = df[df['Still Pending'].isin(selected_status)]

                filtered_df = filtered_df.sort_values(by="Priority Score", ascending=False)

                st.subheader("Filtered Pending Cases (Sorted by Priority)")
                st.dataframe(filtered_df)

                assign_button = st.button("Assign Cases")
                if assign_button and not filtered_df.empty:
                    st.subheader(f"Assigning Cases using '{method}' Method")
                    assignments = []

                    team_members = get_team_members(selected_groups)
                    if not team_members:
                        st.warning("No team members available for the selected groups.")
                        st.stop()

                    # Define current ongoing cases workload for each member
                    ongoing_cases = {
                        'Jiaying': 26,
                        'Janice': 16,
                        'Dominic': 6,
                        'Zhengqin': 5,
                        'Oliver': 19,
                        'Kirsty': 18,
                        'Andrew': 13,
                        'Haikel': 0
                    }

                    # Track how many cases each member has for balanced distribution
                    assignment_counts = {member: 0 for member in team_members}

                    for index, row in filtered_df.iterrows():
                        case_name = row['Name']
                        case_description = row['Case Description']  # Assuming 'Case Description' contains client responses
                        case_types = map_case_types(case_description)  # Get all mapped case types as a list
                        priority = row['Priority Score']

                        if method == "Random Assignment":
                            # Assign to the team member with the fewest ongoing cases
                            assigned_member = min(team_members, key=lambda m: ongoing_cases[m])

                        elif method == "Exclusion-Based":
                            # Build exclusion and eligible lists
                            excluded_members = []
                            for group in selected_groups:
                                for member, exclusions in team_data[group].items():
                                    if any(ct in exclusions for ct in case_types):
                                        excluded_members.append(member)

                            eligible_members = [m for m in team_members if m not in excluded_members]

                            if eligible_members:
                                # Assign to the one with the fewest ongoing cases
                                assigned_member = min(eligible_members, key=lambda m: ongoing_cases[m])
                            else:
                                # Fallback to full team if no eligible members
                                assigned_member = random.choice(team_members)

                        # Track the assignment count
                        assignment_counts[assigned_member] += 1
                        assignments.append((assigned_member, case_name, priority, case_types))  # Store all case types as a list

                    # Display results
                    results_df = pd.DataFrame(assignments, columns=["Assigned Member", "Case Name", "Priority", "Case Type"])
                    st.dataframe(results_df)

                    # Add reasoning for each case
                    st.subheader("Reasoning for Assignments")
                    for assigned_member, case_name, priority, case_types in assignments:
                        # List of eligible members for reasoning
                        excluded_members = []
                        for group in selected_groups:
                            for member, exclusions in team_data[group].items():
                                if any(ct in exclusions for ct in case_types):
                                    excluded_members.append(member)

                        excluded_reasoning = f"Excluded members due to case type restrictions: {', '.join(excluded_members)}." \
                            if excluded_members else "No members were excluded."
                        
                        alt_members = [m for m in eligible_members if m != assigned_member]

                        if method == "Random Assignment":
                            reasoning = f"{assigned_member} was assigned randomly due to no exclusions or priority criteria. " \
                                        + (f"Other options were: {', '.join(alt_members)}" if alt_members else "No other options available.")
                        else:
                            if assigned_member in eligible_members:
                                reasoning = f"{assigned_member} was assigned based on having the fewest ongoing cases. " \
                                            + f"{excluded_reasoning} Other eligible options were: {', '.join(alt_members)}."
                            else:
                                reasoning = f"{assigned_member} was randomly assigned because no other eligible members were found."

                        st.markdown(f"**{case_name}** → {assigned_member} — _{reasoning}_")

            else:
                st.warning("The sheet must contain 'Still Pending', 'Priority Score', and 'Case Description' columns.")

        except Exception as e:
            st.error(f"An error occurred while reading the file: {e}")
    else:
        st.info("Please upload an Excel file to proceed.")















