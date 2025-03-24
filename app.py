import streamlit as st
import pandas as pd
import random

# Streamlit app title
st.title("SWEE Case Assigner")

# File uploader widget
uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx", "xls"])

# Define your team members and their expertise (more dynamic structure)
expertise = {
    'Andrew': ['Work', 'Anxiety', 'Depression'],
    'Dominic': ['Work', 'Anxiety', 'Depression'],
    'Kirsty': ['Work', 'Anxiety', 'Depression'],
    'Oliver': ['Work', 'Anxiety', 'Depression'],
    'Janice': ['Work', 'Anxiety', 'Depression'],
    'Jiaying': ['Work', 'Anxiety', 'Depression'],
    'Zhengqin': ['Body Image'],
    'Haikel': ['Work', 'Anxiety', 'Depression']
}

# Team members
team_members = list(expertise.keys())

# Define the different assignment methods
assignment_methods = ["Round-Robin", "Random Assignment", "Expertise-Based"]

# Display assignment method selection
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
        
        # Check if 'Still Pending', 'Priority Score', and 'Case Type' columns exist
        if 'Still Pending' in df.columns and 'Priority Score' in df.columns and 'Case Type' in df.columns:
            st.subheader("Filter by 'Still Pending' Status:")

            # Get unique values in the 'Still Pending' column
            status_options = df['Still Pending'].dropna().unique().tolist()
            status_options.append("All")  # Add 'All' option to show all data
            
            # Set default to 'YES'
            default_status = ['YES'] if 'YES' in status_options else []  # Default to 'YES' if it exists
            selected_status = st.multiselect("Select status to filter:", status_options, default=default_status)

            # Filter data based on selected status
            if 'All' in selected_status:
                filtered_df = df  # Show all rows if 'All' is selected
            else:
                filtered_df = df[df['Still Pending'].isin(selected_status)]  # Filter by selected statuses

            # Sort cases by 'Priority Score' in descending order (highest priority first)
            filtered_df = filtered_df.sort_values(by="Priority Score", ascending=False)

            # Display the filtered and sorted DataFrame (pending cases)
            st.subheader("Filtered Pending Cases (Sorted by Priority)")
            st.dataframe(filtered_df)

            # Assign cases to team members when the button is clicked
            assign_button = st.button("Assign Cases")
            if assign_button and not filtered_df.empty:
                st.subheader(f"Assigning Cases using '{method}' Method")

                # Initialize list to store assignments
                assignments = []

                # Different assignment methods
                if method == "Round-Robin":
                    # Round-robin case assignment based on priority
                    team_member_index = 0  # Start with the first team member

                    for index, row in filtered_df.iterrows():
                        assigned_member = team_members[team_member_index]
                        case_name = row['Name']  # Use "Name" column for the case name
                        assignments.append((assigned_member, case_name, row['Priority Score']))
                        team_member_index = (team_member_index + 1) % len(team_members)

                elif method == "Random Assignment":
                    # Random case assignment
                    for index, row in filtered_df.iterrows():
                        assigned_member = random.choice(team_members)
                        case_name = row['Name']
                        assignments.append((assigned_member, case_name, row['Priority Score']))

                elif method == "Expertise-Based":
                    # Expertise-based assignment (team member expertise logic)
                    for index, row in filtered_df.iterrows():
                        case_name = row['Name']
                        case_type = row['Case Type']  # Get the case type from the data
                        
                        # Split the case type into a list of individual types if they are comma-separated
                        case_types = [t.strip() for t in case_type.split(',')]  # Clean up spaces around each type

                        matched_members = []

                        # Iterate over team members and check if any expertise matches case types
                        for member in team_members:
                            # Check if any expertise matches any case type
                            if any(case_type in expertise[member] for case_type in case_types):
                                matched_members.append(member)

                        if matched_members:
                            # Prioritize the team member based on the priority score and expertise
                            assigned_member = random.choice(matched_members)  # Randomly assign within matched team members
                            assignments.append((assigned_member, case_name, row['Priority Score']))
                        else:
                            # No exact match found, randomly assign
                            assigned_member = random.choice(team_members)
                            assignments.append((assigned_member, case_name, row['Priority Score']))

                # Now, display the assignments with reasoning after each case
                for assigned_member, case_name, priority in assignments:
                    st.text(f"Case '{case_name}' assigned to {assigned_member} (Priority: {priority})")

                    # Provide reasoning
                    if method == "Expertise-Based":
                        case_type = filtered_df.loc[filtered_df['Name'] == case_name, 'Case Type'].values[0]
                        case_types = [t.strip() for t in case_type.split(',')]  # Clean up spaces around each type
                        matched_members = [member for member in team_members if any(ct in expertise[member] for ct in case_types)]
                        
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















