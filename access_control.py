import streamlit as st

# Define which pages are restricted
RESTRICTED_PAGES = {
    "Grant Application Reviewer",
    "Grant Application Toolkit",
    "Grant Email Composer",
    "Singapore Grant Newsfeed"
}

def page_lock(page_title):
    """
    Shows a locked page message if the user isn't authenticated.
    Blocks access to the rest of the page.
    """
    if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
        st.markdown(f"## 🔒 {page_title}")
        st.warning("This page is restricted. Please log in to access it.")
        st.stop()

def show_sidebar_pages():
    """
    Displays only pages that are accessible (unrestricted or user authenticated).
    Locked pages are hidden from the sidebar.
    """
    ALL_PAGES = [
        "Home",
        "Grant Application Reviewer",
        "Grant Application Toolkit",
        "Grant Email Composer",
        "Singapore Grant Newsfeed"
    ]

    st.sidebar.title("Pages")

    # Show all unrestricted pages by default
    for page in ALL_PAGES:
        if page in RESTRICTED_PAGES:
            # Show restricted pages only if user is authenticated
            if st.session_state.get("authenticated"):
                st.sidebar.markdown(f"- {page}")
        else:
            # Unrestricted pages always show
            st.sidebar.markdown(f"- {page}")

