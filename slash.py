import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Slash Dynamics", layout="wide")
st.title("📊 Slash Report - Multi Campaign & Process Insights")

# File upload
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

        # Convert DATE-TIME to DATE
        if 'DATE-TIME' in df.columns:
            df['DATE'] = pd.to_datetime(df['DATE-TIME'], errors='coerce').dt.date

        # Queue time conversion
        if 'QUEUE TIME' in df.columns:
            df['QUEUE TIME'] = pd.to_numeric(df['QUEUE TIME'], errors='coerce').fillna(0)

        # Flag failed calls
        if 'CALL TIME' in df.columns:
            df['CALL TIME'] = df['CALL TIME'].astype(str).str.strip()
            df['Failed Call'] = df['CALL TIME'] == '0:00'
        else:
            df['Failed Call'] = False

        # Campaign filter
        if 'CAMPAIGN' in df.columns:
            campaigns = df['CAMPAIGN'].dropna().unique().tolist()
            selected_campaigns = st.multiselect("Select Campaign(s):", campaigns, default=campaigns)
            df = df[df['CAMPAIGN'].isin(selected_campaigns)]

        # Process filter
        if 'PROCESS' in df.columns:
            processes = df['PROCESS'].dropna().unique().tolist()
            selected_processes = st.multiselect("Select Process(es):", processes, default=processes)
            df = df[df['PROCESS'].isin(selected_processes)]

        # Summary KPIs
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

        # Daily Call Volume
        if 'DATE' in df.columns:
            st.subheader("📈 Daily Call Volume")
            daily_calls = df.groupby('DATE').size().reset_index(name='Call Count')
            fig = px.bar(daily_calls, x='DATE', y='Call Count', title='Calls per Day')
            fig.update_layout(template='plotly_dark', xaxis_tickangle=-45, font=dict(size=14))
            st.plotly_chart(fig, use_container_width=True)

        # Disposition Pie Chart
        if 'DISPOSE' in df.columns:
            st.subheader("📊 Disposition Distribution")
            fig = px.pie(df, names='DISPOSE', title='Disposition Split')
            fig.update_layout(template='plotly_dark', font=dict(size=14))
            st.plotly_chart(fig, use_container_width=True)

        # Agent-wise Talk Time
        if 'TALKTIME' in df.columns:
            df['TALKTIME'] = pd.to_numeric(df['TALKTIME'], errors='coerce').fillna(0)
            df = df[df['TALKTIME'] >= 0]
            agent_talk = df.groupby('AGENT NAME')['TALKTIME'].sum().reset_index()
            st.subheader("🎙 Agent-wise Talk Time")
            fig = px.bar(agent_talk.sort_values(by='TALKTIME', ascending=False),
                         x='AGENT NAME', y='TALKTIME', color='TALKTIME',
                         title='Total Talk Time by Agent',
                         labels={'TALKTIME': 'Talk Time (sec)', 'AGENT NAME': 'Agent'})
            fig.update_layout(template='plotly_dark', xaxis_tickangle=-45, font=dict(size=14))
            st.plotly_chart(fig, use_container_width=True)

        # Raw Data Table
        st.subheader("📋 Raw Data Preview")
        st.dataframe(df.head(100))

else:
    st.info("Please upload a .csv or .xlsx file to begin.")
