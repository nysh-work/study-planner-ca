import streamlit as st
import datetime
import pandas as pd
import json

# --- Load/Save Data (using JSON) ---
def load_data():
    try:
        with open("exam_data.json", "r") as f:
            data = json.load(f)
            # Convert date strings back to datetime.date objects
            if "schedule_data" in data:
                data["schedule_data"] = {datetime.date.fromisoformat(k): v for k, v in data["schedule_data"].items()}
            return data
    except FileNotFoundError:
        return {}

def save_data(data):
    # Convert datetime.date objects to strings for JSON serialization
    if "schedule_data" in data:
        data_to_save = data.copy() # Create the copy of the data
        data_to_save["schedule_data"] = {k.isoformat(): v for k, v in data["schedule_data"].items()}
    else:
        data_to_save = data
    with open("exam_data.json", "w") as f:
        json.dump(data_to_save, f, indent=4)


# --- Sidebar ---
st.sidebar.title("CA Final Exam Planner")
subjects = [
    "Financial Reporting", "Advanced Financial Management", "Advanced Auditing, Assurance, and Professional Ethics",
    "Direct Tax Law & Tax and International Taxation", "Indirect Tax & Laws", "Integrated Business Solutions"
]
menu_option = st.sidebar.selectbox("Menu", ["Dashboard"] + subjects + ["Schedule", "Resources", "Mock Tests"])

# --- Data Initialization ---
if 'subjects_data' not in st.session_state:
    st.session_state.subjects_data = load_data()
    # Initialize if empty
    if not st.session_state.subjects_data:
        for subject in subjects:
            st.session_state.subjects_data[subject] = {'progress': 0, 'topics': {}, 'due_date': None, 'resources': []}
        save_data(st.session_state.subjects_data)

if 'schedule_data' not in st.session_state:
    st.session_state.schedule_data = load_data().get("schedule_data", {})
    save_data(st.session_state.subjects_data)


# --- Dashboard ---
if menu_option == "Dashboard":
    st.title("Exam Preparation Dashboard")

    total_topics = 0
    completed_topics = 0
    for subject_data in st.session_state.subjects_data.values():
        for topic_data in subject_data['topics'].values():
            total_topics += len(topic_data)
            completed_topics += sum(1 for subtopic in topic_data.values() if isinstance(subtopic, dict) and subtopic['completed'])


    if total_topics > 0:
        overall_progress = (completed_topics / total_topics) * 100
        st.progress(overall_progress / 100)
        st.write(f"Overall Progress: {overall_progress:.2f}%")
    else:
        st.write("No topics added yet.")

    exam_date = datetime.date(2025, 5, 1)
    today = datetime.date.today()
    time_left = exam_date - today
    st.write(f"Time Left Until Exams: {time_left.days} days")

    # Subject-wise progress bars
    progress_data = {subject: data['progress'] for subject, data in st.session_state.subjects_data.items()}
    df = pd.DataFrame(list(progress_data.items()), columns=['Subject', 'Progress'])
    st.bar_chart(df.set_index('Subject'))

# --- Subject Pages ---
elif menu_option in subjects:
    st.title(menu_option)
    subject_data = st.session_state.subjects_data[menu_option]

    # --- Subject Progress ---
    st.write(f"Progress: {subject_data['progress']:.2f}%")
    st.progress(subject_data['progress'] / 100 if subject_data['progress'] else 0)


    # --- Topics ---
    with st.expander("Add Topic"):
        topic_name = st.text_input(f"Enter Topic for {menu_option}:")
        if st.button(f"Add Topic", key=f"add_topic_button_{menu_option}"):
            if topic_name and topic_name not in subject_data['topics']:
                subject_data['topics'][topic_name] = {}  # Initialize as an empty dictionary
                st.success(f"Topic '{topic_name}' added!")
                save_data(st.session_state.subjects_data)
            elif topic_name in subject_data['topics']:
                st.warning("Topic already exist")
            else:
                st.warning("Enter a topic name")

    #Display and manage Topics
    for topic, subtopics in subject_data['topics'].items():
        with st.expander(topic):
            # --- Subtopics ---
            subtopic_name = st.text_input(f"Enter Subtopic for {topic}:", key=f"subtopic_input_{menu_option}_{topic}")
            if st.button(f"Add Subtopic", key=f"add_subtopic_button_{menu_option}_{topic}"):
                if subtopic_name and subtopic_name not in subtopics:
                    subtopics[subtopic_name] = {'completed': False, 'resources': []}
                    st.success(f"Subtopic '{subtopic_name}' added!")
                    save_data(st.session_state.subjects_data)  # Save changes
                elif subtopic_name in subtopics:
                    st.warning("Subtopic already exist")
                else:
                    st.warning("Enter a subtopic name")


            for subtopic, subtopic_data in subtopics.items():
                if isinstance(subtopic_data, dict): # Check if subtopic_data is a dictionary
                    col1, col2, col3 = st.columns([4,1,2])
                    with col1:
                        completed = st.checkbox(subtopic, key=f"checkbox_{menu_option}_{topic}_{subtopic}", value=subtopic_data['completed'])
                    with col2:
                        if st.button("Delete", key=f"delete_{menu_option}_{topic}_{subtopic}"):
                            del subtopics[subtopic]
                            st.experimental_rerun()

                    with col3:
                        resource_link = st.text_input("Resource Link",key=f"resource_{menu_option}_{topic}_{subtopic}")
                        if st.button("Add/Update Resource", key=f"resource_button_{menu_option}_{topic}_{subtopic}"):
                            subtopic_data['resources'].append(resource_link)
                            st.success("Resource link added/updated!")
                            save_data(st.session_state.subjects_data)
                    if completed != subtopic_data['completed']:
                        subtopic_data['completed'] = completed
                        # Recalculate topic and subject progress
                        completed_subtopics = sum(1 for st_data in subtopics.values() if isinstance(st_data, dict) and st_data['completed'])
                        total_subtopics = len(subtopics)
                        topic_progress = (completed_subtopics / total_subtopics) * 100 if total_subtopics>0 else 0

                        completed_topics_count = 0
                        total_topics_count = 0
                        for topic_key, topic_value in subject_data['topics'].items():
                            if isinstance(topic_value, dict):
                                total_topics_count += 1
                                completed_subtopics_count = sum(1 for st_data in topic_value.values() if isinstance(st_data, dict) and st_data['completed'])
                                total_subtopics_count = len(topic_value)
                                if total_subtopics_count > 0 and completed_subtopics_count/total_subtopics_count == 1:
                                    completed_topics_count += 1

                        subject_data['progress'] = (completed_topics_count / total_topics_count) * 100 if total_topics_count> 0 else 0

                        st.experimental_rerun()  # Rerun to update UI

            if st.button(f"Delete Topic - {topic}", key=f"delete_topic_button_{menu_option}_{topic}"):
                del subject_data['topics'][topic]
                save_data(st.session_state.subjects_data)  #Save the updated dictionary
                st.experimental_rerun()

    if st.button(f"Delete Subject - {menu_option}", key=f"delete_subject_button_{menu_option}"):
        del st.session_state.subjects_data[menu_option]
        save_data(st.session_state.subjects_data)
        st.experimental_rerun()


# --- Schedule Page ---
elif menu_option == "Schedule":
    st.title("Study Schedule")

    selected_date = st.date_input("Select Date", key="date_input")
    st.write(f"Schedule for {selected_date}:")

    if selected_date not in st.session_state.schedule_data:
        st.session_state.schedule_data[selected_date] = {}

    for subject in subjects:
        hours = st.number_input(
            f"Hours for {subject}",
            min_value=0.0,
            max_value=24.0,
            step=0.5,
            key=f"hours_{subject}_{selected_date}",
            value=st.session_state.schedule_data[selected_date].get(subject, 0.0), # Get existing value, default to 0
            )

        if hours != st.session_state.schedule_data[selected_date].get(subject, 0.0):
             st.session_state.schedule_data[selected_date][subject] = hours
             save_data(st.session_state.subjects_data)

    # Display the schedule for the selected date
    if st.session_state.schedule_data[selected_date]:
        st.write("Allocated Hours:")
        for subject, hours in st.session_state.schedule_data[selected_date].items():
             if hours > 0:
                st.write(f"- {subject}: {hours} hours")
    else:
        st.write("No schedule for this date yet.")

    if st.button("Clear Schedule for this Date"):
        if selected_date in st.session_state.schedule_data:
            del st.session_state.schedule_data[selected_date]
            save_data(st.session_state.subjects_data)
            st.experimental_rerun()

# --- Resources Page ---
elif menu_option == "Resources":
    st.title("Study Resources")
    # Implementation (centralized view, filtering)

# --- Mock Tests Page ---
elif menu_option == "Mock Tests":
      st.title("Mock Test")
      subject_name = st.selectbox("Select subject", list(st.session_state.subjects_data.keys()))
      marks = st.number_input("Enter Marks", min_value=0)
      if st.button("Add Mock Test Details"):
          st.write("Added marks details")
