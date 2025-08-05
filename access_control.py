import streamlit as st

def page_lock(page_title):
    """
    Shows a locked page message if the user isn't authenticated.
    Blocks access to the rest of the page.
    """
    if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
        st.markdown(f"## 🔒 {page_title}")
        st.warning("This page is restricted. Please log in to access it.")
        st.stop()

def show_locked_sidebar():
    """
    Displays the page list in the sidebar with lock icons for restricted pages.
    """
    PAGES = {
        "Home": "Home",
        "Grant Application Reviewer": "🔒 Grant Application Reviewer",
        "Grant Application Toolkit": "🔒 Grant Application Toolkit",
        "Grant Email Composer": "🔒 Grant Email Composer",
        "Singapore Grant Newsfeed": "🔒 Singapore Grant Newsfeed"
    }

    st.sidebar.title("Pages")
    for page, title in PAGES.items():
        st.sidebar.markdown(f"- {title}")

