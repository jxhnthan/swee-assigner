import streamlit as st
import pandas as pd
import random
import re

# Streamlit app title
st.title("SWEE Case Assigner")

# File uploader widget
uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx", "xls"])

# Define team segmentation and exclusion criteria
team_data = {
    'Leadership': {
        'Haikel': [],
        'Zhengqin': []
    },
    'Senior': {
        'Kirsty': [],
        'Dominic': [],
        'Jiaying': []
        'Claudia': []
    },
    'Junior': {
        'Oliver': ['Eating Disorders', 'Narcissism'],
        'Janice': ['Parenting', 'Occupational/Academic Issues', 'Mandarin-speaking'],
        'Andrew': []
        'Seanna': []
        'Xiao Hui': []
    }
}

# Map survey responses to case types
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
    for key, value in response_to_case_type.items():
        if key.lower() in case_description.lower():
            case_types.append(value)
    return case_types if case_types else ["Miscellaneous"]

def get_team_members(selected_groups):
    return [member for group, members in team_data.items() if group in selected_groups for member in members.keys()]

# Sidebar options
st.sidebar.header("Group Inclusion Options")
selected_groups = st.sidebar.multiselect(
    "Select Groups to Include:",
    options=["Leadership", "Senior", "Junior"],
    default=["Leadership", "Senior", "Junior"]
)

# Track latest assigned therapist
latest_therapist = st.sidebar.selectbox(
    "Select the latest assigned therapist:",
    options=["None", "Haikel", "Zhengqin", "Kirsty", "Dominic", "Jiaying", "Oliver", "Janice", "Andrew"]
)

if not selected_groups:
    st.warning("Please select at least one group to include.")
else:
    method = "Exclusion-Based"  # always exclusion-based

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

                    # Get team members
                    team_members = get_team_members(selected_groups)
                    if not team_members:
                        st.warning("No team members available.")
                        st.stop()

                    ongoing_cases = {member: 0 for member in team_members}
                    assignment_counts = {member: 0 for member in team_members}

                    if latest_therapist != "None" and latest_therapist in team_members:
                        team_members = [m for m in team_members if m != latest_therapist]

                    last_assigned = None

                    for index, row in filtered_df.iterrows():
                        case_name = row['Name']
                        case_description = row['Case Description']
                        case_types = map_case_types(case_description)
                        priority = row['Priority Score']

                        # Determine eligible members
                        excluded_members = []
                        for group in selected_groups:
                            for member, exclusions in team_data[group].items():
                                if any(ct in exclusions for ct in case_types):
                                    excluded_members.append(member)

                        eligible_members = [m for m in team_members if m not in excluded_members]

                        # Remove last assigned therapist to avoid back-to-back
                        if last_assigned in eligible_members and len(eligible_members) > 1:
                            eligible_members.remove(last_assigned)

                        if eligible_members:
                            assigned_member = min(eligible_members, key=lambda x: ongoing_cases.get(x, 0))
                        else:
                            assigned_member = random.choice(team_members)

                        last_assigned = assigned_member
                        ongoing_cases[assigned_member] += 1
                        assignment_counts[assigned_member] += 1
                        assignments.append((assigned_member, case_name, priority, case_types))

                    # Display results
                    results_df = pd.DataFrame(assignments, columns=["Assigned WBSP", "Client Name", "Priority", "Case Type"])
                    st.dataframe(results_df)

                    # --- Clean Reasoning Section ---
                    st.subheader("Reasoning for Assignments")

                    for assigned_member, case_name, priority, case_types in assignments:
                        excluded_members = []
                        for group in selected_groups:
                            for member, exclusions in team_data[group].items():
                                if any(ct in exclusions for ct in case_types):
                                    excluded_members.append(member)

                        excluded_reasoning = f"Excluded members due to case type restrictions: {', '.join(excluded_members)}." if excluded_members else "No members were excluded."

                        alt_members = [m for m in team_members if m not in excluded_members and m != assigned_member]

                        with st.expander(f"{case_name} → {assigned_member}"):
                            st.markdown(f"""
                            **Assigned WBSP:** {assigned_member}  
                            **Case Priority:** {priority}  
                            **Case Nature:** {', '.join(case_types)}
                            
                            ---
                            **Assignment Reasoning:**  
                            - 📝 Assigned based on having the fewest ongoing cases.
                            - 🚫 {excluded_reasoning}
                            - 🤝 Other eligible members were: {', '.join(alt_members) if alt_members else 'None'}
                            """)

            else:
                st.warning("Sheet must contain 'Still Pending', 'Priority Score', and 'Case Description' columns.")

        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.info("Please upload an Excel file to proceed.")















