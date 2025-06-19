import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import io
import requests

st.set_page_config(page_title="Slash Dynamics", layout="wide")

# 🌙 Theme switch
theme = st.radio("Choose Theme:", ["Dark", "Light"], horizontal=True)
plotly_theme = "plotly_dark" if theme == "Dark" else "plotly_white"

# 👋 Cartoon avatar greeting
st.markdown("## 👋 Hello there!")
st.image("https://github.com/user-attachments/assets/fe6dcdc0-bb78-42c7-a60f-f019fc910378", width=120)  # A friendly cartoon image

st.markdown("""
### Welcome to *Slash Report*!  
I'm your friendly assistant 🙂  
What would you like to explore today?
""")

# 🎯 Report focus options
option = st.radio(
    "📊 Select a report section:",
    [
        "Call Volume Trends",
        "Agent Performance (Talktime, Dispositions, Call Count)",
        "Daily/Hourly Call Patterns",
        "Answered vs Unanswered Calls",
        "Disposition Flow",
        "Process/Campaign Summary",
        "Repeat Callers",
        "Weekday Patterns"
    ]
)

# Upload section
uploaded_file = st.file_uploader("📁 Upload your call log file (.csv or .xlsx)", type=["csv", "xlsx"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, low_memory=False)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error reading file: {e}")
    else:
        df.columns = df.columns.str.strip()
        df = df.dropna(axis=1, how='all')

        if 'DATE-TIME' in df.columns:
            df['DATE'] = pd.to_datetime(df['DATE-TIME'], errors='coerce').dt.date

        if 'QUEUE TIME' in df.columns:
            df['QUEUE TIME'] = pd.to_numeric(df['QUEUE TIME'], errors='coerce').fillna(0)

        if 'CALL TIME' in df.columns:
            df['CALL TIME'] = df['CALL TIME'].astype(str).str.strip()
            df['Failed Call'] = df['CALL TIME'] == '0:00'
        else:
            df['Failed Call'] = False

        if 'CAMPAIGN' in df.columns:
            campaigns = df['CAMPAIGN'].dropna().unique().tolist()
            selected_campaigns = st.multiselect("Select Campaign(s):", campaigns, default=campaigns)
            df = df[df['CAMPAIGN'].isin(selected_campaigns)]

        if 'PROCESS' in df.columns:
            processes = df['PROCESS'].dropna().unique().tolist()
            selected_processes = st.multiselect("Select Process(es):", processes, default=processes)
            df = df[df['PROCESS'].isin(selected_processes)]

        # 🔍 Report Sections
        if option == "Call Volume Trends":
            if 'DATE' in df.columns:
                st.subheader("📈 Daily Call Volume")
                daily_calls = df.groupby('DATE').size().reset_index(name='Call Count')
                fig = px.bar(daily_calls, x='DATE', y='Call Count', title='Calls per Day')
                fig.update_layout(template=plotly_theme, xaxis_tickangle=-45, font=dict(size=14))
                st.plotly_chart(fig, use_container_width=True)

        elif option == "Agent Performance (Talktime, Dispositions, Call Count)":
            if 'TALKTIME' in df.columns:
                df['TALKTIME'] = pd.to_numeric(df['TALKTIME'], errors='coerce').fillna(0)
                df = df[df['TALKTIME'] >= 0]
                agent_talk = df.groupby('AGENT NAME')['TALKTIME'].sum().reset_index()
                agent_talk['TALKTIME_MIN'] = (agent_talk['TALKTIME'] / 60).round(2)
                st.subheader("🎙 Agent Talk Time (Minutes)")
                fig = px.bar(agent_talk.sort_values(by='TALKTIME_MIN', ascending=False),
                             x='AGENT NAME', y='TALKTIME_MIN', color='TALKTIME_MIN',
                             title='Total Talk Time by Agent (Minutes)',
                             labels={'TALKTIME_MIN': 'Talk Time (min)', 'AGENT NAME': 'Agent'})
                fig.update_layout(template=plotly_theme, xaxis_tickangle=-45, font=dict(size=14))
                st.plotly_chart(fig, use_container_width=True)

            if 'DISPOSE' in df.columns:
                agent_disp = df.groupby(['AGENT NAME', 'DISPOSE']).size().reset_index(name='Count')
                st.subheader("🗂 Agent Disposition Count")
                fig = px.bar(agent_disp, x='AGENT NAME', y='Count', color='DISPOSE', barmode='stack')
                fig.update_layout(template=plotly_theme, xaxis_tickangle=-45, font=dict(size=14))
                st.plotly_chart(fig, use_container_width=True)

        elif option == "Disposition Flow":
            if 'DISPOSE' in df.columns:
                st.subheader("🔁 Disposition Flow")
                dispose_counts = df['DISPOSE'].value_counts().reset_index()
                dispose_counts.columns = ['Disposition', 'Count']
                fig = px.bar(dispose_counts, x='Disposition', y='Count',
                             title='Disposition Counts',
                             labels={'Count': 'Number of Calls'})
                fig.update_layout(template=plotly_theme, xaxis_tickangle=-45, font=dict(size=14))
                st.plotly_chart(fig, use_container_width=True)

        else:
            st.warning("📌 This section is under development. Stay tuned!")

else:
    st.info("📤 Please upload a call log file to get started.")
