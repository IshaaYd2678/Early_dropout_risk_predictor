"""
Intervention tracking database and utilities.
"""
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel

class Intervention(BaseModel):
    """Intervention data model."""
    student_id: str
    intervention_type: str
    date: str
    notes: Optional[str] = None
    mentor_id: Optional[str] = None
    outcome: Optional[str] = None  # 'risk_reduced', 'retained', 'dropped_out', 'pending'

class InterventionTracker:
    """Track and manage student interventions."""
    
    def __init__(self, db_path='data/interventions.db'):
        """Initialize intervention tracker with database."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS interventions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    intervention_type TEXT NOT NULL,
                    date TEXT NOT NULL,
                    notes TEXT,
                    mentor_id TEXT,
                    outcome TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
        finally:
            conn.close()
    
    def add_intervention(self, intervention: Intervention) -> int:
        """Add a new intervention."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO interventions 
                (student_id, intervention_type, date, notes, mentor_id, outcome)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                intervention.student_id,
                intervention.intervention_type,
                intervention.date,
                intervention.notes,
                intervention.mentor_id,
                intervention.outcome
            ))
            
            intervention_id = cursor.lastrowid
            conn.commit()
            return intervention_id
        finally:
            conn.close()
    
    def get_interventions(self, student_id: Optional[str] = None) -> pd.DataFrame:
        """Get interventions, optionally filtered by student_id."""
        conn = sqlite3.connect(str(self.db_path))
        
        try:
            if student_id:
                df = pd.read_sql_query(
                    'SELECT * FROM interventions WHERE student_id = ? ORDER BY date DESC',
                    conn,
                    params=(student_id,)
                )
            else:
                df = pd.read_sql_query(
                    'SELECT * FROM interventions ORDER BY date DESC',
                    conn
                )
        except Exception as e:
            # Return empty DataFrame if table doesn't exist or query fails
            df = pd.DataFrame()
        finally:
            conn.close()
        
        return df
    
    def update_outcome(self, intervention_id: int, outcome: str):
        """Update intervention outcome."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE interventions 
            SET outcome = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (outcome, intervention_id))
        
        conn.commit()
        conn.close()
    
    def get_intervention_stats(self) -> Dict:
        """Get statistics about interventions."""
        conn = sqlite3.connect(self.db_path)
        
        # Total interventions
        total = pd.read_sql_query('SELECT COUNT(*) as count FROM interventions', conn)['count'][0]
        
        # By type
        by_type = pd.read_sql_query(
            'SELECT intervention_type, COUNT(*) as count FROM interventions GROUP BY intervention_type',
            conn
        )
        
        # By outcome
        by_outcome = pd.read_sql_query(
            'SELECT outcome, COUNT(*) as count FROM interventions GROUP BY outcome',
            conn
        )
        
        conn.close()
        
        return {
            'total_interventions': int(total),
            'by_type': by_type.to_dict('records'),
            'by_outcome': by_outcome.to_dict('records')
        }
