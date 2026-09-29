import React from 'react';

export default function NoMatchCard({ message, onReset }) {
  return (
    <div className="no-match-card">
      <div className="no-match-icon">
        <span className="material-symbols-outlined">search_off</span>
      </div>
      <h3 className="no-match-title">We couldn't find a direct fix</h3>
      <p className="no-match-desc">
        {message || "This issue isn't in the verified Samsung corpus yet. Try rewording your problem description or contact Samsung Support."}
      </p>
      {onReset && (
        <button type="button" className="btn-restart" onClick={onReset} style={{ marginTop: '8px' }}>
          <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>sync</span>
          <span>Try another diagnosis</span>
        </button>
      )}
    </div>
  );
}
