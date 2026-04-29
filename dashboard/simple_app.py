"""
Simple Streamlit Dashboard for Early Warning System
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="Early Warning System",
    page_icon="🎓",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.title("🎓 Early Warning System")
    st.markdown("**AI-powered student retention platform**")
    
    # Sidebar
    with st.sidebar:
        st.header("Dashboard Controls")
        user_role = st.selectbox("Role", ["Admin", "Department Head", "Mentor"])
        time_range = st.selectbox("Time Range", ["Last 7 days", "Last 30 days", "Last 90 days"])
        
        if st.button("🔄 Refresh"):
            st.rerun()
    
    # Key Metrics
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
    
    # Sample data
    np.random.seed(42)
    students_data = pd.DataFrame({
        'Name': ['Alex Johnson', 'Maria Garcia', 'David Chen', 'Sarah Williams', 'Michael Brown'],
        'Student_ID': ['STU001', 'STU002', 'STU003', 'STU004', 'STU005'],
        'Department': ['Computer Science', 'Engineering', 'Business', 'Arts', 'Science'],
        'Risk_Score': [87, 76, 82, 71, 45],
        'Risk_Category': ['Critical', 'High', 'Critical', 'High', 'Medium'],
        'GPA': [2.1, 2.4, 1.9, 2.6, 3.2],
        'Attendance': [0.65, 0.78, 0.58, 0.82, 0.91]
    })
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Risk Trends")
        
        # Generate trend data
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        trend_data = pd.DataFrame({
            'Date': dates,
            'Average_Risk': 30 - np.arange(30) * 0.3 + np.random.normal(0, 2, 30)
        })
        trend_data['Average_Risk'] = np.clip(trend_data['Average_Risk'], 15, 35)
        
        st.line_chart(trend_data.set_index('Date')['Average_Risk'])
    
    with col2:
        st.subheader("🎯 Risk Distribution")
        
        risk_dist = pd.DataFrame({
            'Risk_Level': ['Low', 'Medium', 'High', 'Critical'],
            'Count': [847, 214, 134, 52]
        })
        
        st.bar_chart(risk_dist.set_index('Risk_Level')['Count'])
    
    # High-Risk Students
    st.subheader("👥 High-Risk Students")
    
    high_risk = students_data[students_data['Risk_Category'].isin(['High', 'Critical'])]
    
    for _, student in high_risk.iterrows():
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.write(f"**{student['Name']}** ({student['Student_ID']})")
            st.write(f"{student['Department']} • GPA: {student['GPA']}")
        
        with col2:
            color = '#ef4444' if student['Risk_Category'] == 'Critical' else '#f97316'
            st.markdown(f"<div style='color: {color}; font-weight: bold; font-size: 1.2em;'>{student['Risk_Score']}</div>", unsafe_allow_html=True)
        
        with col3:
            st.write(f"{student['Risk_Category']} Risk")
        
        st.divider()
    
    # Department Analytics (for admins)
    if user_role in ["Admin", "Department Head"]:
        st.subheader("🏢 Department Analytics")
        
        dept_stats = students_data.groupby('Department').agg({
            'Risk_Score': 'mean',
            'GPA': 'mean',
            'Attendance': 'mean'
        }).round(2)
        
        st.dataframe(dept_stats, use_container_width=True)
        
        st.bar_chart(dept_stats['Risk_Score'])
    
    # Student Table
    st.subheader("📋 All Students")
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        dept_filter = st.selectbox("Filter by Department", ["All"] + list(students_data['Department'].unique()))
    with col2:
        risk_filter = st.selectbox("Filter by Risk", ["All", "Critical", "High", "Medium", "Low"])
    
    # Apply filters
    filtered_data = students_data.copy()
    if dept_filter != "All":
        filtered_data = filtered_data[filtered_data['Department'] == dept_filter]
    if risk_filter != "All":
        filtered_data = filtered_data[filtered_data['Risk_Category'] == risk_filter]
    
    st.dataframe(filtered_data, use_container_width=True, hide_index=True)
    
    # Footer
    st.markdown("---")
    st.markdown(f"**Early Warning System v2.0** | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    st.markdown("🔒 FERPA Compliant | 📊 Real-time Analytics")

if __name__ == "__main__":
    main()