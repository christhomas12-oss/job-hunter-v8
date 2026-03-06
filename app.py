import streamlit as st
import pandas as pd

st.title("AI Job Hunter Dashboard")

df = pd.read_csv("jobs.csv")

top = df.sort_values("match_score",ascending=False).head(5)

st.dataframe(top)

for _, job in top.iterrows():

    st.markdown(f"""
### {job['title']}

Organization: {job['organization']}

Location: {job['location']}

Salary: {job['salary']}

Match Score: {job['match_score']}

Apply: {job['link']}
""")
