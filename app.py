import streamlit as st
import pandas as pd

st.set_page_config(page_title="AI Job Hunter", layout="wide")

st.title("AI Job Hunter Dashboard")

try:
    df = pd.read_csv("jobs.csv")

    if not df.empty:
        top = df.sort_values("match_score", ascending=False).head(20)

        st.subheader("Top 20 Matches")
        st.dataframe(top, use_container_width=True)

        st.subheader("Best Jobs")
        for _, job in top.iterrows():
            st.markdown(f"""
### {job['title']}

**Organization:** {job['organization']}  
**Location:** {job['location']}  
**Salary:** {job['salary']}  
**Match Score:** {job['match_score']}  
**Source:** {job['source']}  
**Found:** {job['date_found']}  

[Open posting]({job['link']})
""")
            st.divider()
    else:
        st.write("No jobs found yet.")

except Exception as e:
    st.error(f"Could not load jobs.csv: {e}")
