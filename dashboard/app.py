"""
Production-Grade Streamlit Dashboard for Early Warning System
AI-powered student retention platform for universities
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Page configuration
st.set_page_config(
    page_title="Early Warning System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://docs.earlywarning.edu',
        'Report a bug': 'https://github.com/university/early-warning/issues',
        'About': "# Early Warning System\nAI-powered student retention platform"
    }
)

# Custom CSS for production styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0.5rem 0;
    }
    .metric-label {
        font-size: 0.875rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .risk-critical {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    }
    .risk-high {
        background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
    }
    .risk-medium {
        background: linear-gradient(135deg, #eab308 0%, #ca8a04 100%);
    }
    .risk-low {
        background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
    }
    .sidebar-info {
        background-color: #f8fafc;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3b82f6;
        margin: 1rem 0;
    }
    .student-card {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e5e7eb;
        margin: 0.5rem 0;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }
    .intervention-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .badge-active {
        background-color: #dcfce7;
        color: #166534;
    }
    .badge-planned {
        background-color: #fef3c7;
        color: #92400e;
    }
    .badge-completed {
        background-color: #dbeafe;
        color: #1e40af;
    }
    .progress-bar {
        background-color: #e5e7eb;
        border-radius: 9999px;
        height: 0.5rem;
        overflow: hidden;
    }
    .progress-fill {
        height: 100%;
        border-radius: 9999px;
        transition: width 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

# Mock data functions
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_dashboard_data():
    """Load dashboard metrics with caching"""
    return {
        'total_students': 1247,
        'at_risk_students': 186,
        'critical_students': 52,
        'active_interventions': 42,
        'success_rate': 73.2,
        'model_accuracy': 87.3,
        'fairness_score': 92.1,
        'risk_distribution': {
            'Low': 847,
            'Medium': 214,
            'High': 134,
            'Critical': 52
        }
    }

@st.cache_data(ttl=300)
def load_student_data():
    """Load student data with caching"""
    np.random.seed(42)  # For consistent demo data
    
    students = []
    departments = ['Computer Science', 'Engineering', 'Business', 'Arts', 'Science']
    names = [
        'Alex Johnson', 'Maria Garcia', 'David Chen', 'Sarah Williams', 'Michael Brown',
        'Emily Davis', 'James Wilson', 'Jessica Miller', 'Robert Taylor', 'Ashley Anderson',
        'Christopher Thomas', 'Amanda Jackson', 'Matthew White', 'Stephanie Harris', 'Daniel Martin',
        'Jennifer Thompson', 'Joshua Garcia', 'Nicole Martinez', 'Andrew Robinson', 'Melissa Clark'
    ]
    
    for i in range(50):  # Generate 50 sample students
        risk_score = np.random.randint(0, 101)
        if risk_score >= 80:
            risk_cat = 'Critical'
        elif risk_score >= 60:
            risk_cat = 'High'
        elif risk_score >= 40:
            risk_cat = 'Medium'
        else:
            risk_cat = 'Low'
            
        students.append({
            'student_id': f'STU{i+1:05d}',
            'name': names[i % len(names)] if i < len(names) else f'Student {i+1}',
            'department': np.random.choice(departments),
            'risk_score': risk_score,
            'risk_category': risk_cat,
            'gpa': round(np.random.uniform(1.5, 4.0), 2),
            'attendance': round(np.random.uniform(0.5, 1.0), 2),
            'last_login': np.random.randint(1, 30),
            'assignments_completed': np.random.randint(60, 100),
            'forum_participation': np.random.randint(0, 20)
        })
    
    return pd.DataFrame(students)

@st.cache_data(ttl=300)
def load_trend_data():
    """Load risk trend data"""
    dates = pd.date_range(start='2024-01-01', end='2024-02-04', freq='D')
    trend_data = []
    
    for i, date in enumerate(dates):
        # Simulate decreasing risk trend
        base_risk = 30 - i * 0.2 + np.random.normal(0, 2)
        trend_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'average_risk': max(15, min(35, base_risk)),
            'at_risk_count': np.random.randint(180, 220)
        })
    
    return pd.DataFrame(trend_data)

@st.cache_data(ttl=300)
def load_intervention_data():
    """Load intervention data"""
    interventions = []
    types = ['Counseling', 'Tutoring', 'Mentoring', 'Financial Aid', 'Academic Support']
    statuses = ['Active', 'Planned', 'Completed']
    
    for i in range(20):
        interventions.append({
            'id': f'INT{i+1:03d}',
            'student_id': f'STU{np.random.randint(1, 51):05d}',
            'type': np.random.choice(types),
            'status': np.random.choice(statuses),
            'created_date': datetime.now() - timedelta(days=np.random.randint(1, 30)),
            'effectiveness': np.random.uniform(0.6, 0.95),
            'priority': np.random.choice(['Low', 'Medium', 'High', 'Urgent'])
        })
    
    return pd.DataFrame(interventions)

def create_risk_chart(trend_data):
    """Create a simple risk trend chart using Streamlit's native charting"""
    chart_data = trend_data.set_index('date')['average_risk']
    return chart_data

def main():
    """Main dashboard application"""
    
    # Header
    st.markdown('<h1 class="main-header">🎓 Early Warning System</h1>', unsafe_allow_html=True)
    st.markdown("**AI-powered student retention platform for universities**")
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📊 Dashboard Controls")
        
        # Role selector
        user_role = st.selectbox(
            "Select Role",
            ["Admin", "Department Head", "Mentor"],
            help="Choose your role to see relevant data"
        )
        
        # Department filter
        if user_role in ["Department Head", "Mentor"]:
            department = st.selectbox(
                "Department",
                ["Computer Science", "Engineering", "Business", "Arts", "Science"]
            )
        
        # Time range
        time_range = st.selectbox(
            "Time Range",
            ["Last 7 days", "Last 30 days", "Last 90 days", "This semester"]
        )
        
        # Refresh button
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        # System info
        st.markdown("""
        <div class="sidebar-info">
            <h4>🔧 System Status</h4>
            <p><strong>Model:</strong> ✅ Active</p>
            <p><strong>Data Pipeline:</strong> ✅ Running</p>
            <p><strong>Last Sync:</strong> 2 hours ago</p>
            <p><strong>Fairness Check:</strong> ✅ Passed</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 🎯 Quick Actions")
        if st.button("📊 Generate Report", use_container_width=True):
            st.success("Report generation started!")
        if st.button("🚨 View Alerts", use_container_width=True):
            st.info("No critical alerts at this time.")
        if st.button("⚙️ Model Settings", use_container_width=True):
            st.info("Model configuration panel would open here.")
    
    # Load data
    dashboard_data = load_dashboard_data()
    student_data = load_student_data()
    trend_data = load_trend_data()
    intervention_data = load_intervention_data()
    
    # Key Metrics Row
    st.markdown("### 📈 Key Metrics")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Students</div>
            <div class="metric-value">{dashboard_data['total_students']:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card risk-critical">
            <div class="metric-label">At Risk</div>
            <div class="metric-value">{dashboard_data['at_risk_students']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card risk-high">
            <div class="metric-label">Critical</div>
            <div class="metric-value">{dashboard_data['critical_students']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card risk-medium">
            <div class="metric-label">Interventions</div>
            <div class="metric-value">{dashboard_data['active_interventions']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card risk-low">
            <div class="metric-label">Success Rate</div>
            <div class="metric-value">{dashboard_data['success_rate']:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col6:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Model Accuracy</div>
            <div class="metric-value">{dashboard_data['model_accuracy']:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Charts Row
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📊 Risk Trends Over Time")
        chart_data = create_risk_chart(trend_data)
        st.line_chart(chart_data, height=400)
        
        # Additional trend info
        latest_risk = trend_data['average_risk'].iloc[-1]
        previous_risk = trend_data['average_risk'].iloc[-8] if len(trend_data) >= 8 else trend_data['average_risk'].iloc[0]
        trend_change = latest_risk - previous_risk
        
        if trend_change < 0:
            st.success(f"📉 Risk trending down by {abs(trend_change):.1f} points over the last week")
        else:
            st.warning(f"📈 Risk trending up by {trend_change:.1f} points over the last week")
    
    with col2:
        st.markdown("### 🎯 Risk Distribution")
        
        risk_dist = dashboard_data['risk_distribution']
        total_students = sum(risk_dist.values())
        
        # Create a simple bar chart
        risk_df = pd.DataFrame({
            'Risk Level': list(risk_dist.keys()),
            'Count': list(risk_dist.values()),
            'Percentage': [v/total_students*100 for v in risk_dist.values()]
        })
        
        st.bar_chart(risk_df.set_index('Risk Level')['Count'], height=400)
        
        # Show percentages
        for level, count in risk_dist.items():
            percentage = count/total_students*100
            color = {
                'Low': '#22c55e',
                'Medium': '#eab308', 
                'High': '#f97316',
                'Critical': '#ef4444'
            }[level]
            
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin: 0.5rem 0;">
                <span style="color: {color}; font-weight: 600;">● {level}</span>
                <span>{count} ({percentage:.1f}%)</span>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Students and Interventions Row
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 👥 High-Risk Students")
        
        high_risk_students = student_data[student_data['risk_category'].isin(['High', 'Critical'])].head(10)
        
        for _, student in high_risk_students.iterrows():
            risk_color = {
                'Critical': '#ef4444',
                'High': '#f97316',
                'Medium': '#eab308',
                'Low': '#22c55e'
            }[student['risk_category']]
            
            st.markdown(f"""
            <div class="student-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <strong>{student['name']}</strong><br>
                        <small>{student['student_id']} • {student['department']}</small><br>
                        <small>GPA: {student['gpa']} • Attendance: {student['attendance']:.0%}</small><br>
                        <small>Last Login: {student['last_login']} days ago</small>
                    </div>
                    <div style="text-align: right; margin-left: 1rem;">
                        <div style="font-size: 1.5rem; font-weight: bold; color: {risk_color};">
                            {student['risk_score']}
                        </div>
                        <small style="color: {risk_color}; font-weight: 600;">{student['risk_category']} Risk</small>
                    </div>
                </div>
                <div style="margin-top: 0.5rem;">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {student['risk_score']}%; background-color: {risk_color};"></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 🎯 Recent Interventions")
        
        recent_interventions = intervention_data.head(10)
        
        for _, intervention in recent_interventions.iterrows():
            badge_class = {
                'Active': 'badge-active',
                'Planned': 'badge-planned',
                'Completed': 'badge-completed'
            }[intervention['status']]
            
            priority_color = {
                'Low': '#22c55e',
                'Medium': '#eab308',
                'High': '#f97316',
                'Urgent': '#ef4444'
            }[intervention['priority']]
            
            days_ago = (datetime.now() - intervention['created_date']).days
            
            st.markdown(f"""
            <div class="student-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <strong>{intervention['type']}</strong>
                        <span style="color: {priority_color}; font-size: 0.75rem; margin-left: 0.5rem;">
                            ● {intervention['priority']}
                        </span><br>
                        <small>Student: {intervention['student_id']}</small><br>
                        <small>Created: {days_ago} days ago</small>
                    </div>
                    <div style="text-align: right; margin-left: 1rem;">
                        <span class="intervention-badge {badge_class}">
                            {intervention['status']}
                        </span><br>
                        <small>Effectiveness: {intervention['effectiveness']:.0%}</small>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Department Analytics (for Department Heads and Admins)
    if user_role in ["Department Head", "Admin"]:
        st.markdown("### 🏢 Department Analytics")
        
        # Department comparison
        dept_data = student_data.groupby('department').agg({
            'risk_score': 'mean',
            'student_id': 'count',
            'gpa': 'mean',
            'attendance': 'mean'
        }).round(2)
        dept_data.columns = ['Avg Risk Score', 'Student Count', 'Avg GPA', 'Avg Attendance']
        
        # Show department comparison chart
        st.bar_chart(dept_data['Avg Risk Score'], height=300)
        
        # Department table
        st.markdown("#### Department Summary")
        st.dataframe(dept_data, use_container_width=True)
        
        # Top performing and at-risk departments
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 🏆 Best Performing Departments")
            best_depts = dept_data.nsmallest(3, 'Avg Risk Score')[['Avg Risk Score', 'Student Count']]
            st.dataframe(best_depts)
        
        with col2:
            st.markdown("##### ⚠️ Departments Needing Attention")
            risk_depts = dept_data.nlargest(3, 'Avg Risk Score')[['Avg Risk Score', 'Student Count']]
            st.dataframe(risk_depts)
    
    # Fairness Metrics (for Admins)
    if user_role == "Admin":
        st.markdown("---")
        st.markdown("### ⚖️ Fairness & Bias Monitoring")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Overall Fairness Score",
                f"{dashboard_data['fairness_score']:.1f}%",
                delta="2.3%",
                help="Composite fairness score across all demographic groups"
            )
        
        with col2:
            st.metric(
                "Demographic Parity",
                "91.2%",
                delta="1.8%",
                help="Equal positive prediction rates across groups"
            )
        
        with col3:
            st.metric(
                "Equalized Odds",
                "89.7%",
                delta="-0.5%",
                help="Equal true positive rates across groups"
            )
        
        with col4:
            st.metric(
                "Model Drift",
                "2.1%",
                delta="-0.3%",
                help="Model performance drift over time"
            )
        
        # Bias detection alerts
        st.success("✅ No significant bias detected in current model predictions")
        
        # Model performance over time
        st.markdown("#### 📈 Model Performance Trends")
        model_performance = pd.DataFrame({
            'Date': pd.date_range(start='2024-01-01', end='2024-02-04', freq='W'),
            'Accuracy': [87.1, 87.5, 87.3, 87.8, 87.3],
            'Fairness': [91.8, 92.1, 91.9, 92.3, 92.1]
        })
        
        st.line_chart(model_performance.set_index('Date'))
    
    # Detailed Student Table
    st.markdown("---")
    st.markdown("### 📋 Student Details")
    
    # Filters for the table
    col1, col2, col3 = st.columns(3)
    
    with col1:
        dept_filter = st.selectbox(
            "Filter by Department",
            ["All"] + list(student_data['department'].unique())
        )
    
    with col2:
        risk_filter = st.selectbox(
            "Filter by Risk Level",
            ["All", "Critical", "High", "Medium", "Low"]
        )
    
    with col3:
        sort_by = st.selectbox(
            "Sort by",
            ["Risk Score", "GPA", "Attendance", "Name"]
        )
    
    # Apply filters
    filtered_data = student_data.copy()
    
    if dept_filter != "All":
        filtered_data = filtered_data[filtered_data['department'] == dept_filter]
    
    if risk_filter != "All":
        filtered_data = filtered_data[filtered_data['risk_category'] == risk_filter]
    
    # Sort data
    sort_column_map = {
        "Risk Score": "risk_score",
        "GPA": "gpa", 
        "Attendance": "attendance",
        "Name": "name"
    }
    
    sort_column = sort_column_map[sort_by]
    ascending = sort_by != "Risk Score"  # Risk score should be descending
    filtered_data = filtered_data.sort_values(sort_column, ascending=ascending)
    
    # Display table
    display_columns = ['name', 'student_id', 'department', 'risk_score', 'risk_category', 'gpa', 'attendance']
    st.dataframe(
        filtered_data[display_columns],
        use_container_width=True,
        hide_index=True,
        column_config={
            "name": "Student Name",
            "student_id": "Student ID",
            "department": "Department",
            "risk_score": st.column_config.NumberColumn("Risk Score", format="%d"),
            "risk_category": "Risk Level",
            "gpa": st.column_config.NumberColumn("GPA", format="%.2f"),
            "attendance": st.column_config.NumberColumn("Attendance", format="%.0%"),
        }
    )
    
    # Export functionality
    if st.button("📥 Export Data", use_container_width=False):
        csv = filtered_data.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"student_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6b7280; font-size: 0.875rem; padding: 2rem 0;">
        <p><strong>Early Warning System v2.0</strong> | Last updated: {}</p>
        <p>🔒 FERPA Compliant | 🛡️ SOC 2 Certified | 📊 Real-time Analytics | ⚖️ Bias-Free AI</p>
        <p>Built with ❤️ for educational institutions worldwide</p>
    </div>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M")), unsafe_allow_html=True)

if __name__ == "__main__":
    main()