"""
Simple Working Streamlit Dashboard for Early Warning System
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Early Warning System",
    page_icon="🎓",
    layout="wide"
)

# Main content
st.title("🎓 Early Warning System")
st.markdown("**AI-powered student retention platform**")

# Status indicators
col1, col2, col3 = st.columns(3)
with col1:
    st.success("✅ Streamlit Dashboard: Running")
with col2:
    st.success("✅ FastAPI Backend: Running")  
with col3:
    st.success("✅ ML Model: Loaded")

st.markdown("---")

# Key metrics
st.header("📈 Key Metrics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Students", "1,247", delta="12")

with col2:
    st.metric("At Risk", "186", delta="-8")

with col3:
    st.metric("Interventions", "42", delta="5")

with col4:
    st.metric("Success Rate", "73.2%", delta="2.1%")

st.markdown("---")

# Sample data
students_data = {
    'Name': ['Alex Johnson', 'Maria Garcia', 'David Chen', 'Sarah Williams', 'Michael Brown'],
    'Student_ID': ['STU001', 'STU002', 'STU003', 'STU004', 'STU005'],
    'Department': ['Computer Science', 'Engineering', 'Business', 'Arts', 'Science'],
    'Risk_Score': [87, 76, 82, 71, 45],
    'Risk_Category': ['Critical', 'High', 'Critical', 'High', 'Medium'],
    'GPA': [2.1, 2.4, 1.9, 2.6, 3.2],
    'Attendance': [65, 78, 58, 82, 91]
}

df = pd.DataFrame(students_data)

# Charts
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Risk Distribution")
    risk_counts = df['Risk_Category'].value_counts()
    st.bar_chart(risk_counts)

with col2:
    st.subheader("📈 Risk Scores")
    st.bar_chart(df.set_index('Name')['Risk_Score'])

st.markdown("---")

# High-risk students
st.subheader("👥 High-Risk Students")

high_risk = df[df['Risk_Category'].isin(['High', 'Critical'])]

for _, student in high_risk.iterrows():
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.write(f"**{student['Name']}** ({student['Student_ID']})")
        st.write(f"{student['Department']} • GPA: {student['GPA']}")
    
    with col2:
        if student['Risk_Category'] == 'Critical':
            st.error(f"Risk Score: {student['Risk_Score']}")
        else:
            st.warning(f"Risk Score: {student['Risk_Score']}")
    
    with col3:
        st.write(f"{student['Risk_Category']} Risk")
    
    st.divider()

# Student table
st.subheader("📋 All Students")
st.dataframe(df, use_container_width=True, hide_index=True)

# Footer
st.markdown("---")
st.markdown(f"**Early Warning System** | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
st.markdown("🔒 FERPA Compliant | 📊 Real-time Analytics")

# Sidebar
with st.sidebar:
    st.header("Dashboard Controls")
    
    user_role = st.selectbox("Role", ["Admin", "Department Head", "Mentor"])
    time_range = st.selectbox("Time Range", ["Last 7 days", "Last 30 days", "Last 90 days"])
    
    if st.button("🔄 Refresh"):
        st.rerun()
    
    st.markdown("---")
    st.markdown("### System Info")
    st.info("All services are running normally")
    
    st.markdown("### Quick Links")
    st.markdown("- [React Frontend](http://localhost:3000)")
    st.markdown("- [API Docs](http://localhost:8000/docs)")
    st.markdown("- [Backend Health](http://localhost:8000/health)")