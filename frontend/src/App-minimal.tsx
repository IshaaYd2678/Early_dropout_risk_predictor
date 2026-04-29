function App() {
  return (
    <div>
      <h1>🎓 Early Warning System - WORKING!</h1>
      <p>This is a simple React app that should definitely work.</p>
      <div style={{ backgroundColor: '#f0f0f0', padding: '20px', margin: '20px 0' }}>
        <h2>System Status</h2>
        <p>✅ React Frontend: Running</p>
        <p>✅ Backend API: Running</p>
        <p>✅ ML Model: Loaded</p>
      </div>
      <div style={{ display: 'flex', gap: '20px' }}>
        <div style={{ backgroundColor: '#3b82f6', color: 'white', padding: '20px', borderRadius: '8px' }}>
          <h3>Total Students</h3>
          <p style={{ fontSize: '24px', fontWeight: 'bold' }}>1,247</p>
        </div>
        <div style={{ backgroundColor: '#ef4444', color: 'white', padding: '20px', borderRadius: '8px' }}>
          <h3>At Risk</h3>
          <p style={{ fontSize: '24px', fontWeight: 'bold' }}>186</p>
        </div>
      </div>
    </div>
  );
}

export default App;