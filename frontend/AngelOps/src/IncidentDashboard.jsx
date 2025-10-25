import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer } from 'recharts';
import './IncidentDashboard.css';

const IncidentDashboard = () => {
  const [incident, setIncident] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchIncident = async () => {
    try {
      const response = await fetch('http://localhost:4000/latest-incident');
      const data = await response.json();
      setIncident(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch incident:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncident();
    const interval = setInterval(fetchIncident, 30000);
    return () => clearInterval(interval);
  }, []);

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'high': return '#d32f2f';
      case 'medium': return '#f57c00';
      case 'low': return '#388e3c';
      default: return '#757575';
    }
  };

  const handleRollback = () => {
    if (incident?.proposed_action?.rollback_sha) {
      console.log('Initiating rollback to:', incident.proposed_action.rollback_sha);
    }
  };

  if (loading) return <div className="loading">Loading incident data...</div>;
  if (!incident) return <div className="error">No incident data available</div>;

  return (
    <div className="dashboard">
      <Header onRefresh={fetchIncident} />
      <div className="dashboard-content">
        <div className="left-column">
          <ErrorChart data={incident.series_data} />
        </div>
        <div className="right-column">
          <SeverityBadge severity={incident.severity} color={getSeverityColor(incident.severity)} />
          <ConfidenceBar confidence={incident.confidence} />
          <FilesList files={incident.likely_files} />
          <AnalysisSummary summary={incident.plain_summary} />
          <ActionButtons 
            onRollback={handleRollback}
            prUrl={incident.pr_url}
            hasRollback={!!incident.proposed_action?.rollback_sha}
          />
        </div>
      </div>
    </div>
  );
};

// Subcomponents
const Header = ({ onRefresh }) => (
  <div className="header">
    <h1>AWS Incident Response</h1>
    <div className="header-controls">
      <span className="status">Service Status: Active</span>
      <button onClick={onRefresh} className="refresh-btn">Refresh</button>
    </div>
  </div>
);

const ErrorChart = ({ data }) => (
  <div className="chart-container">
    <h3>Error Rates Over Time</h3>
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <XAxis dataKey="time" />
        <YAxis />
        <Line type="monotone" dataKey="errors" stroke="#d32f2f" strokeWidth={2} />
      </LineChart>
    </ResponsiveContainer>
  </div>
);

const SeverityBadge = ({ severity, color }) => (
  <div className="severity-badge" style={{ backgroundColor: color }}>
    Severity: {severity}
  </div>
);

const ConfidenceBar = ({ confidence }) => (
  <div className="confidence-container">
    <div className="confidence-label">Confidence: {confidence}%</div>
    <div className="confidence-bar">
      <div className="confidence-fill" style={{ width: `${confidence}%` }} />
    </div>
  </div>
);

const FilesList = ({ files }) => (
  <div className="files-list">
    <h4>Suspected Files</h4>
    {files?.map((file, index) => (
      <div key={index} className="file-item">
        <div className="file-path">{file.path}</div>
        <div className="file-confidence">{file.confidence}%</div>
        <div className="file-reason">{file.reason}</div>
      </div>
    ))}
  </div>
);

const AnalysisSummary = ({ summary }) => (
  <div className="analysis-summary">
    <h4>🧠 Bedrock Analysis</h4>
    <p>{summary}</p>
  </div>
);

const ActionButtons = ({ onRollback, prUrl, hasRollback }) => (
  <div className="action-buttons">
    {hasRollback && (
      <button onClick={onRollback} className="rollback-btn">
        Initiate Rollback
      </button>
    )}
    {prUrl && (
      <a href={prUrl} target="_blank" rel="noopener noreferrer" className="pr-link">
        View GitHub PR
      </a>
    )}
  </div>
);

export default IncidentDashboard;