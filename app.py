import streamlit as st
import pandas as pd
import random

# Streamlit app title
st.title("SWEE Case Assigner")

# File uploader widget
uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx", "xls"])

# Define team segmentation and expertise
team_data = {
    'Leadership': {
        'Haikel': ['Work', 'Anxiety', 'Depression'],
        'Zhengqin': ['Body Image']
    },
    'Senior': {
        'Kirsty': ['Work', 'Anxiety', 'Depression'],
        'Dominic': ['Work', 'Anxiety', 'Depression'],
        'Jiaying': ['Work', 'Anxiety', 'Depression']
    },
    'Junior': {
        'Oliver': ['Work', 'Anxiety', 'Depression'],
        'Janice': ['Work', 'Anxiety', 'Depression'],
        'Andrew': ['Work', 'Anxiety', 'Depression']
    }
}

# Flatten team members into a list
def get_team_members(selected_groups):
    return [member for group, members in team_data.items() if group in selected_groups for member in members.keys()]

# Define the assignment methods
assignment_methods = ["Random Assignment", "Expertise-Based"]

# Group exclusion options
st.sidebar.header("Group Exclusion Options")
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
            # Load the Excel file into a Pandas ExcelFile object
            excel_file = pd.ExcelFile(uploaded_file)
            
            # Display sheet names
            st.subheader("Available Sheets:")
            sheet_names = excel_file.sheet_names
            st.write(sheet_names)
            
            # Automatically select "Sheet2" if it exists, otherwise select the first sheet
            selected_sheet = "Sheet2" if "Sheet2" in sheet_names else sheet_names[0]
            
            # Load the selected sheet into a DataFrame
            df = excel_file.parse(selected_sheet)
            
            # Display selected sheet name
            st.write(f"Displaying data from: {selected_sheet}")
            
            if 'Still Pending' in df.columns and 'Priority Score' in df.columns and 'Case Type' in df.columns:
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

                    # Get the filtered list of team members based on selected groups
                    team_members = get_team_members(selected_groups)
                    if not team_members:
                        st.warning("No team members available for the selected groups.")
                        st.stop()

                    # Round-robin index tracker for expertise-based assignments
                    round_robin_indices = {member: 0 for member in team_members}

                    if method == "Random Assignment":
                        for index, row in filtered_df.iterrows():
                            assigned_member = random.choice(team_members)
                            assignments.append((assigned_member, row['Name'], row['Priority Score'], row['Case Type']))

                    elif method == "Expertise-Based":
                        for index, row in filtered_df.iterrows():
                            case_name = row['Name']
                            case_type = row['Case Type']
                            case_types = [t.strip() for t in case_type.split(',')]

                            # Find team members with matching expertise
                            matched_members = [member for group, members in team_data.items() if group in selected_groups
                                               for member, expertise in members.items()
                                               if any(ct in expertise for ct in case_types)]

                            if matched_members:
                                # Use round-robin within the matched members
                                assigned_member = matched_members[round_robin_indices[matched_members[0]] % len(matched_members)]
                                round_robin_indices[matched_members[0]] += 1
                            else:
                                # If no matching expertise, assign to a random team member
                                assigned_member = random.choice(team_members)

                            # Add the assignment
                            assignments.append((assigned_member, case_name, row['Priority Score'], row['Case Type']))

                    # Display assignments and reasoning
                    for assigned_member, case_name, priority, case_type in assignments:
                        st.text(f"Case '{case_name}' assigned to {assigned_member} (Priority: {priority})")

                        if method == "Expertise-Based":
                            case_types = [t.strip() for t in case_type.split(',')]
                            matched_members = [member for group, members in team_data.items() if group in selected_groups
                                               for member, expertise in members.items()
                                               if any(ct in expertise for ct in case_types)]
                            
                            if assigned_member in matched_members:
                                possible_alternatives = [m for m in matched_members if m != assigned_member]
                                reasoning = f"{assigned_member} was chosen because their expertise matches the case type(s). Possible alternatives: {', '.join(possible_alternatives)}" if possible_alternatives else f"{assigned_member} was chosen because they are the best match."
                            else:
                                reasoning = f"{assigned_member} was randomly selected as no matching expertise was found."
                            
                            st.write(f"**Reasoning for Case '{case_name}':** {reasoning}")
                        else:
                            st.write(f"**Reasoning for Case '{case_name}':** {assigned_member} was randomly selected.")

            else:
                st.warning("The 'Still Pending', 'Priority Score', or 'Case Type' column is not found in this sheet.")
            
        except Exception as e:
            st.error(f"An error occurred while reading the file: {e}")
    else:
        st.info("Please upload an Excel file to proceed.")















