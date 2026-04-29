"""
Generate highly realistic synthetic student data with complex interactions.
"""
import pandas as pd
import numpy as np
from pathlib import Path

def generate_realistic_student_data(n_students=15000, random_state=42):
    """Generate realistic student dataset with complex feature interactions."""
    np.random.seed(random_state)
    
    # Demographics
    genders = ['Male', 'Female', 'Other']
    departments = ['Computer Science', 'Engineering', 'Business', 'Arts', 'Science', 
                  'Health Sciences', 'Education', 'Mathematics']
    regions = ['Urban', 'Suburban', 'Rural']
    socioeconomic_statuses = ['Low', 'Medium', 'High']
    
    data = []
    
    for i in range(n_students):
        # Demographics with realistic distributions
        gender = np.random.choice(genders, p=[0.47, 0.50, 0.03])
        department = np.random.choice(departments)
        region = np.random.choice(regions, p=[0.50, 0.30, 0.20])
        socioeconomic_status = np.random.choice(socioeconomic_statuses, p=[0.22, 0.58, 0.20])
        
        # Semester (1-8) - dropout risk decreases with semester
        semester = np.random.choice(range(1, 9), p=[0.20, 0.18, 0.15, 0.13, 0.12, 0.10, 0.07, 0.05])
        
        # Base risk factors
        ses_risk = {'Low': 0.12, 'Medium': 0.03, 'High': -0.08}[socioeconomic_status]
        semester_risk = max(0, (4 - semester) / 12)
        dept_risk = {
            'Computer Science': -0.02, 'Engineering': -0.01, 'Business': 0.01,
            'Arts': 0.04, 'Science': 0.00, 'Health Sciences': -0.03,
            'Education': 0.02, 'Mathematics': -0.01
        }[department]
        
        # Student type factors
        is_part_time = 1 if np.random.random() < 0.12 else 0
        is_first_generation = 1 if (socioeconomic_status == 'Low' and np.random.random() < 0.55) else 0
        has_financial_aid = 1 if (socioeconomic_status in ['Low', 'Medium'] and np.random.random() < 0.60) else 0
        
        # Calculate base dropout probability
        base_dropout_prob = np.clip(
            0.15 + ses_risk + semester_risk + dept_risk + 
            (0.08 if is_part_time else 0) + 
            (0.06 if is_first_generation else 0),
            0.05, 0.75
        )
        
        # Generate correlated academic features
        # GPA is primary predictor
        gpa_mean = 3.2 - (base_dropout_prob * 1.5)
        gpa = np.clip(np.random.normal(gpa_mean, 0.5), 0.0, 4.0)
        
        # Attendance strongly correlated with GPA
        attendance_base = 0.75 + (gpa / 4.0) * 0.20
        attendance_rate = np.clip(np.random.normal(attendance_base, 0.10), 0.30, 1.0)
        
        # Assignment submission correlated with attendance
        submission_base = attendance_rate * 0.90
        assignment_submission_rate = np.clip(np.random.normal(submission_base, 0.08), 0.20, 1.0)
        
        # Exam scores correlated with GPA
        exam_base = (gpa / 4.0) * 85 + 10
        exam_scores = np.clip(np.random.normal(exam_base, 10), 0, 100)
        
        # Behavioral features
        # LMS logins - engagement indicator
        login_mean = 15 * (1 - base_dropout_prob)
        lms_login_frequency = max(0, int(np.random.gamma(shape=max(1, login_mean/2), scale=2)))
        
        # Late submissions - negative indicator
        late_mean = base_dropout_prob * 8
        late_submissions = max(0, int(np.random.poisson(late_mean)))
        
        # Participation correlated with engagement
        participation_base = 70 - (base_dropout_prob * 50)
        participation_score = np.clip(np.random.normal(participation_base, 15), 0, 100)
        
        # Forum activity
        forum_mean = 10 * (1 - base_dropout_prob)
        forum_posts = max(0, int(np.random.poisson(forum_mean)))
        
        # Resource access
        resource_mean = 35 * (1 - base_dropout_prob)
        resource_access_count = max(0, int(np.random.poisson(resource_mean)))
        
        # Time spent (hours per week)
        time_mean = 20 * (1 - base_dropout_prob)
        time_spent_hours = max(0, np.random.gamma(shape=max(1, time_mean/3), scale=3))
        
        # GPA trend (for returning students)
        if semester > 1:
            gpa_trend = np.random.normal(-base_dropout_prob * 0.4, 0.12)
        else:
            gpa_trend = 0
        
        # Calculate final dropout probability with realistic weights
        dropout_probability = np.clip(
            0.35 * (1 - gpa/4.0) +
            0.20 * (1 - attendance_rate) +
            0.15 * (1 - assignment_submission_rate) +
            0.10 * (1 - exam_scores/100) +
            0.08 * (late_submissions / 20) +
            0.05 * (1 - participation_score/100) +
            0.04 * semester_risk +
            0.03 * (1 if is_part_time else 0),
            0, 1
        )
        
        # Add realistic noise
        dropout_probability = dropout_probability * 0.90 + np.random.beta(2, 5) * 0.10
        
        # Determine dropout
        dropped_out = 1 if np.random.random() < dropout_probability else 0
        
        data.append({
            'student_id': f'STU{i+1:06d}',
            'gender': gender,
            'department': department,
            'region': region,
            'socioeconomic_status': socioeconomic_status,
            'semester': semester,
            'attendance_rate': round(attendance_rate, 3),
            'gpa': round(gpa, 2),
            'gpa_trend': round(gpa_trend, 3),
            'assignment_submission_rate': round(assignment_submission_rate, 3),
            'exam_scores': round(exam_scores, 2),
            'lms_login_frequency': lms_login_frequency,
            'late_submissions': late_submissions,
            'participation_score': round(participation_score, 2),
            'forum_posts': forum_posts,
            'resource_access_count': resource_access_count,
            'time_spent_hours': round(time_spent_hours, 2),
            'has_financial_aid': has_financial_aid,
            'is_part_time': is_part_time,
            'is_first_generation': is_first_generation,
            'dropped_out': dropped_out
        })
    
    return pd.DataFrame(data)

def main():
    """Generate and save enhanced realistic data."""
    data_dir = Path('data/raw')
    data_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*80)
    print("Generating Enhanced Realistic Student Data")
    print("="*80)
    print("\n🔄 Generating 15,000 student records with realistic patterns...")
    print("   This may take a moment...\n")
    
    df = generate_realistic_student_data(n_students=15000)
    
    # Save to CSV
    output_path = data_dir / 'students.csv'
    df.to_csv(output_path, index=False)
    
    print(f"✅ Generated {len(df):,} student records")
    print(f"✅ Saved to {output_path}\n")
    
    print("="*80)
    print("📊 Dataset Statistics")
    print("="*80)
    print(f"\n🎯 Target Variable:")
    print(f"   Dropout rate: {df['dropped_out'].mean():.2%}")
    print(f"   Retained: {(df['dropped_out']==0).sum():,} ({(df['dropped_out']==0).mean():.1%})")
    print(f"   Dropped out: {(df['dropped_out']==1).sum():,} ({(df['dropped_out']==1).mean():.1%})")
    
    print(f"\n📈 Academic Metrics:")
    print(f"   Average GPA: {df['gpa'].mean():.2f} (±{df['gpa'].std():.2f})")
    print(f"   Average Attendance: {df['attendance_rate'].mean():.1%} (±{df['attendance_rate'].std():.1%})")
    print(f"   Average Submission Rate: {df['assignment_submission_rate'].mean():.1%}")
    print(f"   Average Exam Score: {df['exam_scores'].mean():.1f}/100")
    
    print(f"\n👥 Demographics:")
    print(f"   Part-time students: {df['is_part_time'].sum():,} ({df['is_part_time'].mean():.1%})")
    print(f"   First-gen students: {df['is_first_generation'].sum():,} ({df['is_first_generation'].mean():.1%})")
    print(f"   Financial aid: {df['has_financial_aid'].sum():,} ({df['has_financial_aid'].mean():.1%})")
    
    print(f"\n🏫 Department Distribution:")
    dept_counts = df['department'].value_counts()
    for dept, count in dept_counts.items():
        print(f"   {dept:.<30} {count:>5,} ({count/len(df):.1%})")
    
    print(f"\n💰 Socioeconomic Status:")
    ses_counts = df['socioeconomic_status'].value_counts()
    for ses, count in ses_counts.items():
        print(f"   {ses:.<30} {count:>5,} ({count/len(df):.1%})")
    
    print(f"\n📊 Semester Distribution:")
    sem_counts = df['semester'].value_counts().sort_index()
    for sem, count in sem_counts.items():
        print(f"   Semester {sem:.<24} {count:>5,} ({count/len(df):.1%})")
    
    print(f"\n🔍 Dropout Rate by Key Factors:")
    print(f"   Low SES: {df[df['socioeconomic_status']=='Low']['dropped_out'].mean():.1%}")
    print(f"   Medium SES: {df[df['socioeconomic_status']=='Medium']['dropped_out'].mean():.1%}")
    print(f"   High SES: {df[df['socioeconomic_status']=='High']['dropped_out'].mean():.1%}")
    print(f"   Part-time: {df[df['is_part_time']==1]['dropped_out'].mean():.1%}")
    print(f"   Full-time: {df[df['is_part_time']==0]['dropped_out'].mean():.1%}")
    print(f"   First-gen: {df[df['is_first_generation']==1]['dropped_out'].mean():.1%}")
    print(f"   Non first-gen: {df[df['is_first_generation']==0]['dropped_out'].mean():.1%}")
    
    print(f"\n="*80)
    print("✅ Data Generation Complete!")
    print("="*80)
    print(f"\n💡 Next step: Run 'python ml/train.py' to train the model\n")

if __name__ == '__main__':
    main()
