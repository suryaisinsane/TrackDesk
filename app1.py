import datetime
import os
import time

import requests
import streamlit as st
from streamlit_cookies_controller import CookieController

# ==================================================
# CONFIG
# ==================================================

st.set_page_config(
    page_title="TrackDesk",
    page_icon="💼",
    layout="wide",
)

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")
COOKIE_NAME = "trackdesk_token"
COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 days (keep <= backend token life)

PLATFORMS = [
    "LinkedIn",
    "Indeed",
    "Naukri",
    "Wellfound",
    "Company Website",
    "Referral",
    "Other",
]
STATUS_OPTIONS = ["Applied", "Interview", "Offer", "Rejected"]
STATUS_ICONS = {
    "Applied": "🔵",
    "Interview": "🟡",
    "Offer": "🟢",
    "Rejected": "🔴",
}

today = datetime.date.today()
cookies = CookieController()


def safe_cookie_get(name):
    """The cookie component isn't ready on the very first render,
    so .get()/.set()/.remove() can raise before it's initialized.
    Treat that the same as "no cookie yet"."""
    try:
        return cookies.get(name)
    except Exception:
        return None


def safe_cookie_set(name, value, max_age):
    try:
        cookies.set(name, value, max_age=max_age)
    except Exception:
        pass


def safe_cookie_remove(name):
    try:
        cookies.remove(name)
    except Exception:
        pass

# ==================================================
# SESSION STATE
# ==================================================

st.session_state.setdefault("token", None)
st.session_state.setdefault("logged_out", False)
st.session_state.setdefault("cookie_checked", False)
st.session_state.setdefault("editing_id", None)


# ==================================================
# RESTORE LOGIN AFTER PAGE RELOAD
# ==================================================
# On the first run after a reload, the cookie component has not
# loaded yet, so cookies.get() returns nothing. We wait briefly and
# rerun once before deciding the user is really logged out.

if st.session_state["token"] is None and not st.session_state["logged_out"]:
    saved_token = safe_cookie_get(COOKIE_NAME)

    if saved_token:
        st.session_state["token"] = saved_token
    elif not st.session_state["cookie_checked"]:
        st.session_state["cookie_checked"] = True
        time.sleep(0.6)
        st.rerun()


def log_out():
    st.session_state["token"] = None
    st.session_state["logged_out"] = True
    st.session_state["editing_id"] = None
    safe_cookie_remove(COOKIE_NAME)
    time.sleep(0.4)  # let the browser process the cookie removal
    st.rerun()


# ==================================================
# LOGIN / SIGN UP
# ==================================================

if not st.session_state["token"]:
    _, center, _ = st.columns([1, 1.2, 1])

    with center:
        st.title("💼 TrackDesk")
        st.caption("Track every job application in one place.")

        login_tab, signup_tab = st.tabs(["Login", "Sign Up"])

        with login_tab:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button(
                    "Login", use_container_width=True
                )

            if submitted:
                try:
                    response = requests.post(
                        f"{API_URL}/login",
                        json={"email": email, "password": password},
                        timeout=15,
                    )
                except requests.RequestException:
                    st.error("Cannot reach the TrackDesk server.")
                else:
                    if response.status_code == 200:
                        token = response.json()["access_token"]
                        st.session_state["token"] = token
                        st.session_state["logged_out"] = False
                        safe_cookie_set(COOKIE_NAME, token, COOKIE_MAX_AGE)
                        time.sleep(0.6)  # let the browser save the cookie
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")

        with signup_tab:
            with st.form("signup_form"):
                name = st.text_input("Name")
                signup_email = st.text_input("Email", key="signup_email")
                signup_password = st.text_input(
                    "Password (min 8 characters)",
                    type="password",
                    key="signup_password",
                )
                created = st.form_submit_button(
                    "Create Account", use_container_width=True
                )

            if created:
                if not name or not signup_email or not signup_password:
                    st.error("Please fill in all fields.")
                else:
                    try:
                        response = requests.post(
                            f"{API_URL}/users",
                            json={
                                "name": name,
                                "email": signup_email,
                                "password": signup_password,
                            },
                            timeout=15,
                        )
                    except requests.RequestException:
                        st.error("Cannot reach the TrackDesk server.")
                    else:
                        if response.status_code == 200:
                            st.success("Account created! Please log in.")
                        elif response.status_code == 409:
                            st.error("That email is already registered.")
                        else:
                            st.error(f"Could not create account: {response.text}")

    st.stop()


# ==================================================
# API HELPER
# ==================================================

headers = {"Authorization": f"Bearer {st.session_state['token']}"}


def api(method, path, **kwargs):
    """Call the backend. Returns a response, or None if unreachable.
    An expired/invalid token logs the user out cleanly."""
    try:
        response = requests.request(
            method,
            f"{API_URL}{path}",
            headers=headers,
            timeout=15,
            **kwargs,
        )
    except requests.RequestException:
        return None

    if response.status_code == 401:
        st.session_state["token"] = None
        safe_cookie_remove(COOKIE_NAME)
        time.sleep(0.4)
        st.rerun()

    return response


def parse_date(value):
    if not value:
        return None
    try:
        return datetime.date.fromisoformat(str(value))
    except ValueError:
        return None


# ==================================================
# LOAD DATA
# ==================================================

me_response = api("GET", "/me")
apps_response = api("GET", "/applications")

if apps_response is None or me_response is None:
    st.error("Cannot reach the TrackDesk server. Check that the API is running.")
    st.stop()

user_info = me_response.json() if me_response.status_code == 200 else {}
applications = []
if apps_response.status_code == 200 and isinstance(apps_response.json(), list):
    applications = [a for a in apps_response.json() if isinstance(a, dict)]
else:
    st.error(f"Could not load applications: {apps_response.text}")

status_counts = {s: 0 for s in STATUS_OPTIONS}
follow_up_total = upcoming = due = overdue = 0

for a in applications:
    if a.get("status") in status_counts:
        status_counts[a["status"]] += 1

    follow_date = parse_date(a.get("follow_up"))
    if follow_date:
        follow_up_total += 1
        if follow_date > today:
            upcoming += 1
        elif follow_date == today:
            due += 1
        elif a.get("status") in ("Applied", "Interview"):
            overdue += 1


# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:
    st.header("💼 TrackDesk")

    if user_info.get("name"):
        st.write(f"Hi, **{user_info['name']}** 👋")

    st.divider()
    st.subheader("📧 Email forwarding")

    if user_info.get("inbound_email"):
        st.caption("Forward your job emails to:")
        st.code(user_info["inbound_email"], language=None)

        if user_info.get("gmail_verified"):
            st.success("Gmail forwarding connected")
        elif user_info.get("gmail_verification_link"):
            st.warning("Gmail forwarding needs verification")
            st.link_button(
                "Verify Gmail forwarding",
                user_info["gmail_verification_link"],
                use_container_width=True,
            )
        else:
            st.info("Gmail forwarding not set up yet")
    else:
        st.error("Could not load your account details.")

    st.divider()
    if st.button("Logout", use_container_width=True):
        log_out()


# ==================================================
# DASHBOARD
# ==================================================

st.title("Your job search")

if not applications:
    st.info("👋 No applications yet. Add your first one in the **Add new** tab.")

metric_cols = st.columns(5)
metric_cols[0].metric("Total", len(applications))
metric_cols[1].metric("🔵 Applied", status_counts["Applied"])
metric_cols[2].metric("🟡 Interviews", status_counts["Interview"])
metric_cols[3].metric("🟢 Offers", status_counts["Offer"])
metric_cols[4].metric("🔴 Rejected", status_counts["Rejected"])

follow_cols = st.columns(3)
follow_cols[0].metric("📅 Upcoming follow-ups", upcoming)
follow_cols[1].metric("⏰ Due today", due)
follow_cols[2].metric("⚠️ Overdue", overdue)

st.divider()

list_tab, add_tab = st.tabs(["💼 Applications", "➕ Add new"])


# ==================================================
# ADD NEW APPLICATION
# ==================================================

with add_tab:
    with st.form("create_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        company = col1.text_input("Company name")
        role = col2.text_input("Role")

        col3, col4 = st.columns(2)
        source = col3.selectbox("Source platform", PLATFORMS)
        status = col4.selectbox("Status", STATUS_OPTIONS)

        job_url = st.text_input("Job URL (optional)")
        follow_up_date = st.date_input(
            "Follow-up date (optional)", value=None, min_value=today
        )
        notes = st.text_area("Notes (optional)")

        add_clicked = st.form_submit_button(
            "➕ Add application", use_container_width=True
        )

    if add_clicked:
        if not company.strip() or not role.strip():
            st.error("Please enter a company name and role.")
        else:
            response = api(
                "POST",
                "/applications",
                json={
                    "company": company.strip(),
                    "role": role.strip(),
                    "source": source,
                    "status": status,
                    "job_url": job_url.strip() or None,
                    "follow_up": follow_up_date.isoformat()
                    if follow_up_date
                    else None,
                    "notes": notes.strip() or None,
                },
            )
            if response is not None and response.status_code == 200:
                st.toast("Application saved ✅")
                st.rerun()
            else:
                detail = response.text if response is not None else "server unreachable"
                st.error(f"Failed to save application: {detail}")


# ==================================================
# APPLICATION LIST (search, filter, edit, delete)
# ==================================================

with list_tab:
    filter_col, search_col = st.columns([1, 2])
    filter_status = filter_col.selectbox("Filter by status", ["All"] + STATUS_OPTIONS)
    search = search_col.text_input(
        "Search", placeholder="Search by company or role"
    ).strip().lower()

    visible = [
        a
        for a in applications
        if (filter_status == "All" or a.get("status") == filter_status)
        and (
            not search
            or search in str(a.get("company", "")).lower()
            or search in str(a.get("role", "")).lower()
        )
    ]

    if applications and not visible:
        st.info("No applications match your filters.")

    for a in visible:
        app_id = a.get("id")
        if app_id is None:
            continue

        icon = STATUS_ICONS.get(a.get("status"), "⚪")
        title = f"{icon} **{a.get('company', 'Unknown')}** — {a.get('role', 'Unknown')}"

        with st.container(border=True):
            top_left, top_right = st.columns([4, 1])
            top_left.markdown(title)
            top_right.caption(f"{a.get('status', 'N/A')} · {a.get('source', 'N/A')}")

            follow_date = parse_date(a.get("follow_up"))
            if follow_date:
                if follow_date < today and a.get("status") in ("Applied", "Interview"):
                    st.warning(f"⚠️ Follow-up overdue: {follow_date}")
                elif follow_date == today:
                    st.warning(f"⏰ Follow-up due today")
                else:
                    st.caption(f"📅 Follow-up: {follow_date}")

            if a.get("job_url"):
                st.markdown(f"[Open job posting]({a['job_url']})")
            if a.get("notes"):
                st.caption(f"📝 {a['notes']}")

            edit_col, delete_col, _ = st.columns([1, 1, 4])

            if edit_col.button("✏️ Edit", key=f"edit_{app_id}"):
                st.session_state["editing_id"] = (
                    None if st.session_state["editing_id"] == app_id else app_id
                )
                st.rerun()

            if delete_col.button("🗑️ Delete", key=f"delete_{app_id}"):
                response = api("DELETE", f"/applications/{app_id}")
                if response is not None and response.status_code == 200:
                    if st.session_state["editing_id"] == app_id:
                        st.session_state["editing_id"] = None
                    st.toast("Application deleted")
                    st.rerun()
                else:
                    detail = response.text if response is not None else "server unreachable"
                    st.error(f"Failed to delete: {detail}")

            # ---- inline edit form (opens right under the card) ----
            if st.session_state["editing_id"] == app_id:
                st.divider()
                current_status = (
                    a.get("status") if a.get("status") in STATUS_OPTIONS else "Applied"
                )
                current_source = (
                    a.get("source") if a.get("source") in PLATFORMS else "Other"
                )

                with st.form(f"edit_form_{app_id}"):
                    ec1, ec2 = st.columns(2)
                    edit_company = ec1.text_input("Company name", value=a.get("company", ""))
                    edit_role = ec2.text_input("Role", value=a.get("role", ""))

                    ec3, ec4 = st.columns(2)
                    edit_source = ec3.selectbox(
                        "Source platform",
                        PLATFORMS,
                        index=PLATFORMS.index(current_source),
                    )
                    edit_status = ec4.selectbox(
                        "Status",
                        STATUS_OPTIONS,
                        index=STATUS_OPTIONS.index(current_status),
                    )

                    edit_job_url = st.text_input("Job URL", value=a.get("job_url") or "")
                    edit_follow_up = st.date_input(
                        "Follow-up date", value=parse_date(a.get("follow_up"))
                    )
                    edit_notes = st.text_area("Notes", value=a.get("notes") or "")

                    save_col, cancel_col = st.columns(2)
                    save = save_col.form_submit_button(
                        "Save changes", use_container_width=True
                    )
                    cancel = cancel_col.form_submit_button(
                        "Cancel", use_container_width=True
                    )

                if cancel:
                    st.session_state["editing_id"] = None
                    st.rerun()

                if save:
                    if not edit_company.strip() or not edit_role.strip():
                        st.error("Company and role can't be empty.")
                    else:
                        response = api(
                            "PUT",
                            f"/applications/{app_id}",
                            json={
                                "company": edit_company.strip(),
                                "role": edit_role.strip(),
                                "source": edit_source,
                                "status": edit_status,
                                "job_url": edit_job_url.strip() or None,
                                "follow_up": edit_follow_up.isoformat()
                                if edit_follow_up
                                else None,
                                "notes": edit_notes.strip() or None,
                            },
                        )
                        if response is not None and response.status_code == 200:
                            st.session_state["editing_id"] = None
                            st.toast("Application updated ✅")
                            st.rerun()
                        else:
                            detail = (
                                response.text if response is not None else "server unreachable"
                            )
                            st.error(f"Failed to update: {detail}")