import streamlit as st
from streamlit_timeline import timeline
from datetime import datetime, timedelta

st.title("Timeline Minimal Test")

timeline_events = []
base_date = datetime.now()

for i in range(3):
    timeline_events.append({
        "id": str(i+1),
        "content": f"Test Event {i+1}",
        "start": (base_date + timedelta(days=i)).strftime("%Y-%m-%d"),
        "type": "box"
    })

timeline_data = {
    "title": "Minimal Timeline Test",
    "events": timeline_events
}

timeline(timeline_data, height=300)
