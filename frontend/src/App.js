import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import './App.css';

const API_BASE = 'https://2eotoxerkj.execute-api.us-east-1.amazonaws.com/prod';

function App() {
  const [incident, setIncident] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchLatestIncident();
    const interval = setInterval(fetchLatestIncident, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchLatestIncident = async () => {
    try {
      const response = await fetch(`${API_BASE}/incidents`);
      const data = await response.json();
      setIncident(data);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading DevAngel Dashboard...</div>;
  if (error) return <div className="error">Error: {error}</div>;
  if (!incident) return <div className="no-data">No incident data available</div>;

  const timelineData = incident.charts?.error_timeline?.map(([time, count]) => ({
    time: time.split(' ')[1], // Just show time
    errors: count
  })) || [];

  const fileData = Object.entries(incident.charts?.file_impact || {}).map(([file, count]) => ({
    file: file.split('/').pop(), // Just filename
    errors: count
  }));

  return (
    <div className="dashboard">
      <header className="header">
        <h1>🛡️ DevAngel Dashboard</h1>
        <div className="status-badge" data-status={incident.status}>
          {incident.status?.toUpperCase()}
        </div>
      </header>

      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total Errors</h3>
          <div className="stat-value">{incident.summary?.total_errors || 0}</div>
        </div>
        <div className="stat-card">
          <h3>Affected Files</h3>
          <div className="stat-value">{incident.summary?.affected_files || 0}</div>
        </div>
        <div className="stat-card">
          <h3>Deploy SHA</h3>
          <div className="stat-value">{incident.summary?.deploy_sha?.substring(0, 7) || 'N/A'}</div>
        </div>
        <div className="stat-card">
          <h3>Update Type</h3>
          <div className="stat-value">{incident.update_type || 'N/A'}</div>
        </div>
      </div>

      <div className="charts-grid">
        <div className="chart-card">
          <h3>Error Timeline</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={timelineData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="errors" stroke="#ff6b6b" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>File Impact</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={fileData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="file" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="errors" fill="#4ecdc4" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="errors-section">
        <h3>Recent Errors</h3>
        <div className="errors-list">
          {incident.charts?.top_errors?.slice(0, 3).map((error, idx) => (
            <div key={idx} className="error-item">
              <div className="error-time">{error['@timestamp']}</div>
              <div className="error-message">{error['@message']}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="analysis-section">
        <h3>AI Analysis</h3>
        <div className="analysis-content">
          <p><strong>Status:</strong> {incident.analysis?.status || 'Processing...'}</p>
          <p><strong>Summary:</strong> {incident.analysis?.executive_summary || 'Analysis in progress...'}</p>
        </div>
      </div>
    </div>
  );
}

export default App;
