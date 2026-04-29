import React from 'react';

function App() {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1 style={{ color: '#2563eb', marginBottom: '20px' }}>
        🎓 Early Warning System
      </h1>
      
      <div style={{ 
        backgroundColor: '#f8fafc', 
        padding: '20px', 
        borderRadius: '8px',
        marginBottom: '20px',
        border: '1px solid #e2e8f0'
      }}>
        <h2 style={{ color: '#1e293b', marginBottom: '10px' }}>System Status</h2>
        <p style={{ color: '#64748b', margin: '5px 0' }}>✅ React Frontend: Running</p>
        <p style={{ color: '#64748b', margin: '5px 0' }}>✅ FastAPI Backend: Running</p>
        <p style={{ color: '#64748b', margin: '5px 0' }}>✅ ML Model: Loaded</p>
      </div>

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
        gap: '20px',
        marginBottom: '20px'
      }}>
        <div style={{ 
          backgroundColor: '#3b82f6', 
          color: 'white', 
          padding: '20px', 
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 10px 0', fontSize: '18px' }}>Total Students</h3>
          <p style={{ margin: '0', fontSize: '32px', fontWeight: 'bold' }}>1,247</p>
        </div>
        
        <div style={{ 
          backgroundColor: '#ef4444', 
          color: 'white', 
          padding: '20px', 
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 10px 0', fontSize: '18px' }}>At Risk</h3>
          <p style={{ margin: '0', fontSize: '32px', fontWeight: 'bold' }}>186</p>
        </div>
        
        <div style={{ 
          backgroundColor: '#f59e0b', 
          color: 'white', 
          padding: '20px', 
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 10px 0', fontSize: '18px' }}>Interventions</h3>
          <p style={{ margin: '0', fontSize: '32px', fontWeight: 'bold' }}>42</p>
        </div>
        
        <div style={{ 
          backgroundColor: '#10b981', 
          color: 'white', 
          padding: '20px', 
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 10px 0', fontSize: '18px' }}>Success Rate</h3>
          <p style={{ margin: '0', fontSize: '32px', fontWeight: 'bold' }}>73.2%</p>
        </div>
      </div>

      <div style={{ 
        backgroundColor: 'white', 
        padding: '20px', 
        borderRadius: '8px',
        border: '1px solid #e2e8f0',
        marginBottom: '20px'
      }}>
        <h3 style={{ color: '#1e293b', marginBottom: '15px' }}>High-Risk Students</h3>
        
        <div style={{ marginBottom: '10px', padding: '10px', backgroundColor: '#fef2f2', borderRadius: '6px', border: '1px solid #fecaca' }}>
          <strong style={{ color: '#dc2626' }}>Alex Johnson (STU00001)</strong>
          <p style={{ margin: '5px 0', color: '#6b7280' }}>Computer Science • Risk Score: 87 • Critical</p>
        </div>
        
        <div style={{ marginBottom: '10px', padding: '10px', backgroundColor: '#fff7ed', borderRadius: '6px', border: '1px solid #fed7aa' }}>
          <strong style={{ color: '#ea580c' }}>Maria Garcia (STU00002)</strong>
          <p style={{ margin: '5px 0', color: '#6b7280' }}>Engineering • Risk Score: 76 • High</p>
        </div>
        
        <div style={{ marginBottom: '10px', padding: '10px', backgroundColor: '#fef2f2', borderRadius: '6px', border: '1px solid #fecaca' }}>
          <strong style={{ color: '#dc2626' }}>David Chen (STU00003)</strong>
          <p style={{ margin: '5px 0', color: '#6b7280' }}>Business • Risk Score: 82 • Critical</p>
        </div>
      </div>

      <div style={{ 
        backgroundColor: '#f1f5f9', 
        padding: '15px', 
        borderRadius: '8px',
        textAlign: 'center',
        color: '#64748b'
      }}>
        <p style={{ margin: '0', fontSize: '14px' }}>
          🚀 Production-ready B2B SaaS Early Warning System
        </p>
        <p style={{ margin: '5px 0 0 0', fontSize: '12px' }}>
          React: http://localhost:3000 | API: http://localhost:8000 | Streamlit: http://localhost:8501
        </p>
      </div>
    </div>
  );
}

export default App;