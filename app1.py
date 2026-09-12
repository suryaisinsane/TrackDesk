from db import get_applications,create_application,update_application,delete_application,get_application_status_counts
import streamlit as st
import datetime 
today = datetime.date.today()
platforms = [
    "LinkedIn",
    "Indeed",
    "Naukri",
    "Wellfound",
    "Company Website",
    "Referral",
    "Other"
]
applications = get_applications()
status_counts = get_application_status_counts()

st.write("Status counts:", status_counts)
if "editing_id" not in st.session_state:
    st.session_state["editing_id"] = None
if "show_dashboard_details" not in st.session_state:
    st.session_state["show_dashboard_details"] = False



st.title("Jobplication")
st.write("Track and manage your job applications in one place.")
st.subheader("📊 Dashboard")

total_applications = len(applications)
if total_applications == 0:
    st.info("👋 No applications yet. Add your first job application below.")
status_counts = {
    status: count
    for status, count in get_application_status_counts()
}
st.metric("Total Applications", total_applications)

if st.session_state["show_dashboard_details"]:
    button_label = "Hide details"
else:
    button_label = "Show details"

if st.button(button_label):
    st.session_state["show_dashboard_details"] = not st.session_state["show_dashboard_details"]
    st.rerun()

if st.session_state["show_dashboard_details"]:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Applied", status_counts["Applied"])

    with col2:
        st.metric("Interviews", status_counts["Interview"])

    with col3:
        st.metric("Offers", status_counts["Offer"])

    with col4:
        st.metric("Rejected", status_counts["Rejected"])
follow_up_count = 0
upcoming_follow_up_count = 0
due_today_count = 0

for app in applications:
    if app.get("follow_up"):
        follow_up_count += 1

        if app["follow_up"] > today:
            upcoming_follow_up_count += 1
        elif app["follow_up"] == today:
            due_today_count += 1
follow_col1, follow_col2, follow_col3 = st.columns(3)

with follow_col1:
    st.metric("Follow-ups", follow_up_count)

with follow_col2:
    st.metric("Upcoming Follow-ups", upcoming_follow_up_count)

with follow_col3:
    st.metric("Due Today", due_today_count)

st.subheader("➕ Create Application")
com_col1,role_col2 = st.columns(2)
with com_col1:
    company = st.text_input("Company name")
with role_col2:
    role = st.text_input("Interested Role or Previous Role")
source_col1,status_col2 = st.columns(2)
with source_col1:
    source = st.selectbox(
    "Source Platform",
    platforms
)

with status_col2:
    status = st.selectbox("Status",["Applied","Interview","Offer","Rejected"])
job_url = st.text_input("Job URL (optional)")
follow_up_date = st.date_input("Follow-up Date")
notes = st.text_area("Notes (Optional)")

if st.button("➕ Add Application"):
   if company and role:
     create_application(
       company,
       role,
       source,
       status,
       job_url,
       follow_up_date,
       notes
)
     st.success("Saved successfully")
     st.rerun()
   else:
     st.error("Please enter valid values")

st.subheader("🔎 Search & Filter")

filter_status = st.selectbox(
    "filter by Status",
    ["All", "Applied", "Interview", "Offer", "Rejected"]
)

search = st.text_input("Search applications")

status_value = None if filter_status == "All" else filter_status
search_value = search if search else None

filtered_apps = get_applications(
    status=status_value,
    search=search_value,
)

st.subheader("💼 Applications")
if not filtered_apps:
    st.info("No applications found.")
for app in filtered_apps:
    st.divider()

    st.markdown(f"### {app['company']} — {app['role']}")

    info_col1, info_col2 = st.columns(2)

    with info_col1:
        st.markdown(f"**Status:** {app['status']}")

    with info_col2:
        st.caption(f"**Source:** {app.get('source', 'N/A')}")
    if app["job_url"]:
        st.write(f"Job URL: {app['job_url']}")
        st.markdown(f"[Open Job Posting]({app['job_url']})")
    if app.get("follow_up"):
        st.info(f"📅 **Follow-up:** {app['follow_up']}")
    if app.get("notes"):
       st.markdown(f"📝 **Notes:** {app['notes']}")
    action_col1, action_col2 = st.columns(2)

    with action_col1:
      if st.button("Delete", key=f"delete_{app['id']}"):
          delete_application(app["id"])
          st.success("Application Deleted!")
          st.rerun()
    with action_col2:
      if st.button("Edit", key=f"edit_{app['id']}"):
          st.session_state["editing_id"] = app["id"]

editing_app = None
for app in applications:
  if app["id"] == st.session_state["editing_id"]:
      editing_app= app
      break
st.write("DEBUG editing_id:", st.session_state["editing_id"])
st.write("DEBUG applications:", applications)
if editing_app:
    st.subheader("✏️ Edit Application")
    status_options = ["Applied", "Interview", "Offer", "Rejected"]
    current_status_index = status_options.index(editing_app["status"])
    current_source = editing_app.get("source","Other")
    edit_source = st.selectbox("Source Platform",platforms,index=platforms.index(current_source),key="edit_source")
    
    edit_company = st.text_input("Company name", value=editing_app["company"],key="edit_company")
    edit_role = st.text_input("Interested Role or Previous Role", value=editing_app["role"],key="edit_role")
    edit_status = st.selectbox("Status", status_options, index=current_status_index,key="edit_status")
    edit_job_url = st.text_input("Job_url(Optional)",value=editing_app.get("job_url",""),key="edit_job_url")
    edit_follow_up_date = st.date_input("follow_up",value=editing_app.get("follow_up"),key="edit_follow_up_date")
    edit_notes = st.text_area("Notes (Optional)",value =editing_app.get("notes",""),key="edit_notes")

    if st.button("Update"):
      update_application(
        editing_app["id"],
        edit_company,
        edit_role,
        edit_source,
        edit_status,
        edit_job_url,
        edit_follow_up_date,
        edit_notes
      )

      st.session_state["editing_id"] = None
      st.success("Application updated!")
      st.rerun()
