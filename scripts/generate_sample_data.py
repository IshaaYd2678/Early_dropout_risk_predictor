"""
Generate synthetic student data for testing and development.
"""
import pandas as pd
import numpy as np
import os
from pathlib import Path

def generate_student_data(n_students=10000, random_state=42):
    """Generate synthetic student dataset with realistic correlations."""
    np.random.seed(random_state)
    
    # Student demographics
    genders = ['Male', 'Female', 'Other']
    departments = ['Computer Science', 'Engineering', 'Business', 'Arts', 'Science', 'Health Sciences', 'Education']
    regions = ['Urban', 'Suburban', 'Rural']
    socioeconomic_statuses = ['Low', 'Medium', 'High']
    
    data = []
    
    for i in range(n_students):
        # Demographics
        gender = np.random.choice(genders, p=[0.48, 0.48, 0.04])
        department = np.random.choice(departments)
        region = np.random.choice(regions, p=[0.45, 0.35, 0.20])
        socioeconomic_status = np.random.choice(socioeconomic_statuses, p=[0.25, 0.55, 0.20])
        
        # Semester (1-8) - higher dropout risk in early semesters
        semester = np.random.randint(1, 9)
        semester_risk_factor = max(0, (5 - semester) / 10)  # Higher risk in early semesters
        
        # Socioeconomic impact on base risk
        ses_risk = {'Low': 0.15, 'Medium': 0.05, 'High': -0.05}[socioeconomic_status]
        
        # Academic performance (correlated with dropout risk)
        base_risk = np.clip(np.random.beta(2, 5) + ses_risk + semester_risk_factor, 0, 1)
        
        # Attendance (lower for at-risk students) - strong predictor
        attendance_rate = max(0.2, min(1.0, np.random.normal(0.88 - base_risk * 0.35, 0.12)))
        
        # GPA (lower for at-risk students) - very strong predictor
        gpa = max(0.5, min(4.0, np.random.normal(3.2 - base_risk * 1.8, 0.6)))
        
        # Assignment submission rate - highly correlated with attendance
        assignment_submission_rate = max(0.1, min(1.0, 
            attendance_rate * 0.85 + np.random.normal(0, 0.08)))
        
        # Exam scores - correlated with GPA
        exam_scores = max(0, min(100, gpa * 20 + np.random.normal(10 - base_risk * 25, 12)))
        
        # LMS activity - engagement indicator
        lms_login_frequency = max(0, int(np.random.gamma(
            shape=max(1, 15 - base_risk * 10), scale=1)))
        
        # Late submissions - negative indicator
        late_submissions = max(0, int(np.random.poisson(base_risk * 6 + 1)))
        
        # Participation score - correlated with engagement
        participation_score = max(0, min(100, 
            np.random.normal(75 - base_risk * 45, 18)))
        
        # Forum posts - engagement indicator
        forum_posts = max(0, int(np.random.poisson(
            max(1, 8 - base_risk * 5))))
        
        # Resource access - learning engagement
        resource_access_count = max(0, int(np.random.poisson(
            max(5, 30 - base_risk * 15))))
        
        # Time spent (hours per week) - correlated with success
        time_spent_hours = max(0, np.random.gamma(
            shape=max(1, 20 - base_risk * 12), scale=1))
        
        # Previous semester GPA trend (for returning students)
        if semester > 1:
            gpa_trend = np.random.normal(-base_risk * 0.3, 0.15)
        else:
            gpa_trend = 0
        
        # Financial aid status
        has_financial_aid = 1 if socioeconomic_status == 'Low' and np.random.random() < 0.7 else 0
        
        # Part-time vs full-time
        is_part_time = 1 if np.random.random() < 0.15 else 0
        part_time_risk = 0.1 if is_part_time else 0
        
        # First generation student
        is_first_generation = 1 if socioeconomic_status == 'Low' and np.random.random() < 0.6 else 0
        first_gen_risk = 0.08 if is_first_generation else 0
        
        # Dropout label (based on multiple risk factors with realistic weights)
        dropout_probability = np.clip(
            0.25 * (1 - attendance_rate) +
            0.25 * (1 - gpa/4.0) +
            0.15 * (1 - assignment_submission_rate) +
            0.10 * (late_submissions / 15) +
            0.10 * (1 - participation_score/100) +
            0.05 * (1 - exam_scores/100) +
            0.05 * semester_risk_factor +
            0.03 * part_time_risk +
            0.02 * first_gen_risk,
            0, 1
        )
        
        # Add some randomness but keep it realistic
        dropout_probability = dropout_probability * 0.85 + np.random.random() * 0.15
        dropped_out = 1 if np.random.random() < dropout_probability else 0
        
        data.append({
            'student_id': f'STU{i+1:05d}',
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
    
    df = pd.DataFrame(data)
    return df

def main():
    """Generate and save sample data."""
    # Create directories
    data_dir = Path('data/raw')
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate data
    print("Generating enhanced sample student data...")
    print("This may take a minute for 10,000 students...")
    df = generate_student_data(n_students=10000)
    
    # Save to CSV
    output_path = data_dir / 'students.csv'
    df.to_csv(output_path, index=False)
    print(f"\n✅ Generated {len(df)} student records")
    print(f"✅ Saved to {output_path}")
    print(f"\n📊 Dataset Statistics:")
    print(f"   Dropout rate: {df['dropped_out'].mean():.2%}")
    print(f"   Average GPA: {df['gpa'].mean():.2f}")
    print(f"   Average Attendance: {df['attendance_rate'].mean():.2%}")
    print(f"   Part-time students: {df['is_part_time'].sum()} ({df['is_part_time'].mean():.1%})")
    print(f"   First-gen students: {df['is_first_generation'].sum()} ({df['is_first_generation'].mean():.1%})")
    print(f"\n📈 Department Distribution:")
    print(df['department'].value_counts())
    print(f"\n💰 Socioeconomic Status:")
    print(df['socioeconomic_status'].value_counts())
    print(f"\n🎓 Sample data (first 5 rows):")
    print(df.head())

if __name__ == '__main__':
    main()
