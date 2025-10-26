import React, { useEffect, useState } from 'react';
import './IncidentDashboard.css';

const IncidentDashboard = ({ incident: incidentProp }) => {
  const [incident, setIncident] = useState(incidentProp || null);
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'light');

  useEffect(() => {
    if (incidentProp) setIncident(incidentProp);
  }, [incidentProp]);

  useEffect(() => {
    if (incidentProp) return;
    const candidates = ['/AngelOps/data.json', '/data.json', './data.json'];
    let cancelled = false;
    (async () => {
      for (const url of candidates) {
        try {
          const res = await fetch(`${url}?t=${Date.now()}`, { cache: 'no-store' });
          if (!res.ok) continue;
          const json = await res.json();
          if (!cancelled) setIncident(json);
          break;
        } catch (e) { continue; }
      }
    })();
    return () => { cancelled = true; };
  }, [incidentProp]);

  const manualRefresh = async () => {
    const candidates = ['/AngelOps/data.json', '/data.json', './data.json'];
    for (const url of candidates) {
      try {
        const res = await fetch(`${url}?t=${Date.now()}`, { cache: 'no-store' });
        if (!res.ok) continue;
        const json = await res.json();
        setIncident(json);
        return;
      } catch (e) { continue; }
    }
    window.location.reload();
  };

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
  };

  // Extract key data from incident JSON
  const errorData = incident?.error_analyzer_output?.dashboard_ready?.error_timeline || [];
  const topErrors = incident?.error_analyzer_output?.dashboard_ready?.top_errors || [];
  const fileImpact = incident?.error_analyzer_output?.dashboard_ready?.file_impact || {};
  const deploy = incident?.error_analyzer_output?.dashboard_ready?.deployment_info || {};
  const stats = incident?.error_analyzer_output?.basic_stats || {};

  // ===== Chart Renderer =====
  const renderChart = () => {
    if (!errorData.length) return <p>No chart data.</p>;

    const width = 600;
    const height = 220;
    const padding = 50;
    const maxVal = Math.max(...errorData.map(d => d[1]));

    const points = errorData.map((d, i) => ({
      label: d[0],
      x: padding + (i / (errorData.length - 1)) * (width - 2 * padding),
      y: height - padding - (d[1] / maxVal) * (height - 2 * padding),
      value: d[1]
    }));

    const path = points.map((p, i) =>
      `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`
    ).join(' ');

    return (
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" height="240">
        {/* X axis */}
        <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke={theme === 'dark' ? '#9ca3af' : '#9ca3af'} strokeWidth="1" />
        {/* Y axis */}
        <line x1={padding} y1={padding} x2={padding} y2={height - padding} stroke={theme === 'dark' ? '#9ca3af' : '#9ca3af'} strokeWidth="1" />

        {/* Data line */}
        <path d={path} fill="none" stroke="#ff9900" strokeWidth="3" />

        {/* Points */}
        {points.map((p, i) => (
          <circle key={i} cx={p.x} cy={p.y} r="4" fill="#ff9900" />
        ))}

        {/* X axis labels (time) */}
        {points.map((p, i) => (
          <text
            key={`x-${i}`}
            x={p.x}
            y={height - padding + 20}
            fontSize="10"
            textAnchor="middle"
            fill={theme === 'dark' ? '#f9fafb' : '#6b7280'}
          >
            {p.label.split(' ')[1]}
          </text>
        ))}

        {/* Y axis labels */}
        {[0, maxVal].map((val, i) => (
          <text
            key={`y-${i}`}
            x={padding - 30}
            y={height - padding - (val / maxVal) * (height - 2 * padding)}
            fontSize="10"
            textAnchor="end"
            fill={theme === 'dark' ? '#f9fafb' : '#6b7280'}
          >
            {val}
          </text>
        ))}

        {/* Axis titles */}
        <text x={width / 2} y={height - 10} textAnchor="middle" fontSize="12" fill={theme === 'dark' ? '#f9fafb' : '#374151'}>
          Time (HH:MM)
        </text>
        <text
          x="15"
          y={height / 2}
          textAnchor="middle"
          fontSize="12"
          fill={theme === 'dark' ? '#f9fafb' : '#374151'}
          transform={`rotate(-90, 15, ${height / 2})`}
        >
          Error Count
        </text>
      </svg>
    );
  };

  // ===== Main JSX Layout =====
  return (
    <div className={`dashboard ${theme}`}>
      <header className="dashboard-header">
        <h1>AWS Incident Response</h1>
        <div className="header-controls">
          <span className="status">
            Service Status: {incident?.status || 'Unknown'}
          </span>
          <button className="refresh-btn" onClick={manualRefresh}>Refresh</button>
          <button className="refresh-btn" onClick={toggleTheme}>
            {theme === 'light' ? 'Dark Mode' : 'Light Mode'}
          </button>
        </div>
      </header>

      <main className="dashboard-grid">
        {/* Chart */}
        <section className="chart-section card">
          <h2>Error Timeline</h2>
          {renderChart()}
        </section>

        {/* Deployment Info */}
        <section className="real-time-metrics card">
          <h2>Deployment Info</h2>
          {deploy ? (
            <ul>
              <li><strong>Commit SHA:</strong> {deploy.sha}</li>
              <li><strong>Message:</strong> {deploy.message}</li>
              <li><strong>Timestamp:</strong> {deploy.timestamp}</li>
              <li><strong>Changed Files:</strong></li>
              <ul>
                {deploy.changed_files?.map((f, i) => <li key={i}>{f}</li>)}
              </ul>
            </ul>
          ) : (
            <p>No deployment info available.</p>
          )}
        </section>

        {/* File Impact */}
        <section className="service-health card">
          <h2>File Impact</h2>
          <table>
            <thead>
              <tr><th>File</th><th>Error Count</th></tr>
            </thead>
            <tbody>
              {Object.entries(fileImpact).map(([file, count], i) => (
                <tr key={i}><td>{file}</td><td>{count}</td></tr>
              ))}
            </tbody>
          </table>
        </section>

        {/* Top Errors */}
        <section className="incident-timeline card">
          <h2>Top Errors</h2>
          <ul>
            {topErrors.map((err, i) => (
              <li key={i}>
                <strong>{err['@timestamp']}</strong>
                <pre style={{
                  whiteSpace: 'pre-wrap',
                  fontSize: '0.85rem',
                  background: theme === 'dark' ? '#1f2937' : '#f3f4f6',
                  padding: '0.5rem',
                  borderRadius: '6px',
                  overflowX: 'auto',
                  color: theme === 'dark' ? '#f9fafb' : '#111'
                }}>
                  {err['@message']}
                </pre>
              </li>
            ))}
          </ul>
        </section>

        {/* Summary */}
        <section className="analysis-summary card">
          <h2>Summary</h2>
          <p>Total Errors: {stats.total_errors}</p>
          <p>Unique Exemplars: {stats.unique_exemplars}</p>
          <p>Deploy SHA: {stats.deploy_sha}</p>
          <p>Deploy Message: {stats.deploy_message}</p>
        </section>
      </main>

      <footer>
        <a href={incident?.prLink} target="_blank" rel="noopener noreferrer">View GitHub PR</a>
        <button>Initiate Rollback</button>
      </footer>
    </div>
  );
};

export default IncidentDashboard;