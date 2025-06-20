import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Slash Dynamics", layout="wide")

# Theme toggle
theme = st.radio("Choose Theme:", ["Dark", "Light"], horizontal=True)
plotly_theme = "plotly_dark" if theme == "Dark" else "plotly_white"

# Assistant + Logo
st.image("https://github.com/user-attachments/assets/fe6dcdc0-bb78-42c7-a60f-f019fc910378", width=200)
st.markdown("## 👋 Welcome to **Slash Dynamics**!")
st.markdown("I'm your friendly assistant 🤖 here to help you analyze your call data.")

# Upload section
uploaded_file = st.file_uploader("📄 Upload your call log file (.csv or .xlsx)", type=["csv", "xlsx"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error reading file: {e}")
    else:
        df.columns = df.columns.str.strip()
        df = df.dropna(axis=1, how='all')

        if 'DATE-TIME' in df.columns:
            df['DATE'] = pd.to_datetime(df['DATE-TIME'], errors='coerce').dt.date
            df['HOUR'] = pd.to_datetime(df['DATE-TIME'], errors='coerce').dt.hour
            df['DAY_NAME'] = pd.to_datetime(df['DATE-TIME'], errors='coerce').dt.day_name()

        if 'QUEUE TIME' in df.columns:
            df['QUEUE TIME'] = pd.to_numeric(df['QUEUE TIME'], errors='coerce').fillna(0)

        if 'CALL TIME' in df.columns:
            df['CALL TIME'] = df['CALL TIME'].astype(str).str.strip()
            df['Failed Call'] = df['CALL TIME'] == '0:00'
        else:
            df['Failed Call'] = False

        if 'TALKTIME' in df.columns:
            df['TALKTIME'] = pd.to_numeric(df['TALKTIME'], errors='coerce').fillna(0)
            df = df[df['TALKTIME'] >= 0]

        if 'CAMPAIGN' in df.columns:
            campaigns = df['CAMPAIGN'].dropna().unique().tolist()
            selected_campaigns = st.multiselect("Select Campaign(s):", campaigns, default=campaigns)
            df = df[df['CAMPAIGN'].isin(selected_campaigns)]

        if 'PROCESS' in df.columns:
            processes = df['PROCESS'].dropna().unique().tolist()
            selected_processes = st.multiselect("Select Process(es):", processes, default=processes)
            df = df[df['PROCESS'].isin(selected_processes)]

        option = st.radio("What would you like to explore today?", [
            "Call Volume Trends",
            "Agent Performance (Talktime, Dispositions, Call Count)",
            "Daily/Hourly Call Patterns",
            "Answered vs Unanswered Calls",
            "Disposition Flow",
            "Process/Campaign Summary",
            "Repeat Callers",
            "Weekday Patterns"
        ])

        if option == "Call Volume Trends":
            if 'DATE' in df.columns:
                daily_calls = df.groupby('DATE').size().reset_index(name='Call Count')
                fig = px.bar(daily_calls, x='DATE', y='Call Count', title='Calls per Day')
                fig.update_layout(template=plotly_theme, xaxis_tickangle=-45, font=dict(size=14))
                st.plotly_chart(fig, use_container_width=True)

        elif option == "Agent Performance (Talktime, Dispositions, Call Count)":
            if 'AGENT NAME' in df.columns:
                talk_df = df.groupby('AGENT NAME')['TALKTIME'].sum().reset_index()
                talk_df['TALKTIME_MIN'] = (talk_df['TALKTIME'] / 60).round(2)
                fig = px.bar(talk_df.sort_values(by='TALKTIME_MIN', ascending=False),
                             x='AGENT NAME', y='TALKTIME_MIN', color='TALKTIME_MIN',
                             title='Total Talk Time by Agent (in Minutes)',
                             labels={'TALKTIME_MIN': 'Talk Time (min)', 'AGENT NAME': 'Agent'})
                fig.update_layout(template=plotly_theme, xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

                dispo_df = df.groupby(['AGENT NAME', 'DISPOSE']).size().reset_index(name='Count')
                fig = px.bar(dispo_df, x='AGENT NAME', y='Count', color='DISPOSE', barmode='stack',
                             title='Agent Disposition Count')
                fig.update_layout(template=plotly_theme, xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

                call_count = df.groupby('AGENT NAME').size().reset_index(name='Call Count')
                fig = px.bar(call_count, x='AGENT NAME', y='Call Count', color='Call Count',
                             title='Agent Call Count')
                fig.update_layout(template=plotly_theme, xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

        elif option == "Daily/Hourly Call Patterns":
            if 'HOUR' in df.columns:
                hourly = df.groupby('HOUR').size().reset_index(name='Calls Per Hour')
                fig = px.bar(hourly, x='HOUR', y='Calls Per Hour', title='Hourly Call Distribution')
                fig.update_layout(template=plotly_theme)
                st.plotly_chart(fig, use_container_width=True)

        elif option == "Answered vs Unanswered Calls":
            counts = df.groupby('Failed Call').size().reset_index(name='Total Calls')
            counts['Status'] = counts['Failed Call'].map({True: 'Unanswered (0:00)', False: 'Answered'})
            fig = px.pie(counts, names='Status', values='Total Calls', title='Answered vs Unanswered Calls')
            fig.update_layout(template=plotly_theme)
            st.plotly_chart(fig, use_container_width=True)

        elif option == "Disposition Flow":
            flow = df['DISPOSE'].value_counts().reset_index()
            flow.columns = ['Disposition', 'Count']
            fig = px.bar(flow, x='Disposition', y='Count', title='Disposition Distribution')
            fig.update_layout(template=plotly_theme, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

        elif option == "Process/Campaign Summary":
            if 'PROCESS' in df.columns and 'CAMPAIGN' in df.columns:
                summary = df.groupby(['PROCESS', 'CAMPAIGN']).size().reset_index(name='Calls')
                st.dataframe(summary)

        elif option == "Repeat Callers":
            rpt = df.groupby('CALL TIME').size().reset_index(name='Occurrences')
            rpt = rpt[rpt['Occurrences'] > 1]
            st.dataframe(rpt)

        elif option == "Weekday Patterns":
            if 'DAY_NAME' in df.columns:
                weekday = df['DAY_NAME'].value_counts().reset_index()
                weekday.columns = ['Day', 'Calls']
                fig = px.bar(weekday, x='Day', y='Calls', title='Weekday Call Distribution')
                fig.update_layout(template=plotly_theme)
                st.plotly_chart(fig, use_container_width=True)
else:
    st.info("✨ Please upload a call log file to begin your analysis!")
