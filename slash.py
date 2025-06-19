import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Slash Dynamics", layout="wide")

# Theme toggle
theme = st.radio("Choose Theme:", ["Dark", "Light"], horizontal=True)
plotly_theme = "plotly_dark" if theme == "Dark" else "plotly_white"

st.title("📊 Slash Report - Multi Campaign & Process Insights")

uploaded_file = st.file_uploader("Upload your call log file (.csv or .xlsx)", type=["csv", "xlsx"])

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

        st.subheader("📌 Quick Summary")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📞 Total Calls", len(df))
        with col2:
            st.metric("👨‍💼 Unique Agents", df['AGENT NAME'].nunique())
        with col3:
            avg_queue_time = df[df.get('CALLING MODE', '').astype(str).str.lower().str.contains('inbound', na=False)]['QUEUE TIME'].mean() if 'CALLING MODE' in df.columns else 0
            st.metric("⏳ Avg Queue Time (Inbound)", round(avg_queue_time, 2))
        with col4:
            st.metric("📴 Failed Calls (0:00)", df['Failed Call'].sum())

        if 'DATE' in df.columns:
            st.subheader("📈 Daily Call Volume")
            daily_calls = df.groupby('DATE').size().reset_index(name='Call Count')
            fig = px.bar(daily_calls, x='DATE', y='Call Count', title='Calls per Day')
            fig.update_layout(template=plotly_theme, xaxis_tickangle=-45, font=dict(size=14))
            st.plotly_chart(fig, use_container_width=True)

        if 'DISPOSE' in df.columns:
            st.subheader("📊 Disposition Distribution")
            dispose_counts = df['DISPOSE'].value_counts().reset_index()
            dispose_counts.columns = ['Disposition', 'Count']
            fig = px.bar(dispose_counts, x='Disposition', y='Count',
                         title='Disposition Counts',
                         labels={'Count': 'Number of Calls'})
            fig.update_layout(template=plotly_theme, xaxis_tickangle=-45, font=dict(size=14))
            st.plotly_chart(fig, use_container_width=True)

        if 'TALKTIME' in df.columns:
            df['TALKTIME'] = pd.to_numeric(df['TALKTIME'], errors='coerce').fillna(0)
            df = df[df['TALKTIME'] >= 0]
            agent_talk = df.groupby('AGENT NAME')['TALKTIME'].sum().reset_index()
            agent_talk['TALKTIME_MIN'] = (agent_talk['TALKTIME'] / 60).round(2)
            st.subheader("🎙 Agent-wise Talk Time (Minutes)")
            fig = px.bar(agent_talk.sort_values(by='TALKTIME_MIN', ascending=False),
                         x='AGENT NAME', y='TALKTIME_MIN', color='TALKTIME_MIN',
                         title='Total Talk Time by Agent (in Minutes)',
                         labels={'TALKTIME_MIN': 'Talk Time (min)', 'AGENT NAME': 'Agent'})
            fig.update_layout(template=plotly_theme, xaxis_tickangle=-45, font=dict(size=14))
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("📋 Raw Data Preview")
        st.dataframe(df.head(100))

else:
    st.info("Please upload a .csv or .xlsx file to begin.")
