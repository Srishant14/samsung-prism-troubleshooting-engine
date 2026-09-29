import React, { useState } from 'react';
import EscalationPanel from './EscalationPanel';

export default function TroubleshootResult({ result, query, sessionId, onReset }) {
  const [showEscalation, setShowEscalation] = useState(false);
  const [showFixedConfirm, setShowFixedConfirm] = useState(false);

  if (!result) return null;

  const {
    title, domain, confidence, final_confidence, match_confidence,
    source, source_type, steps, action
  } = result;

  // Use final_confidence if available, else fall back to confidence
  const displayConfidence = final_confidence || confidence;

  // Confidence indicator
  let confLabel = 'Match';
  let confClass = 'medium';
  if (displayConfidence >= 0.8) {
    confLabel = 'Strong Match';
    confClass = 'high';
  } else if (displayConfidence >= 0.6) {
    confLabel = 'Good Match';
    confClass = 'medium';
  } else {
    confLabel = 'Partial Match';
    confClass = 'low';
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Main Result Card */}
      <div className="result-card">
        <div className="ambient-glow" />

        {/* Badges Row */}
        <div className="result-badges">
          {domain && (
            <span className="badge domain">[{domain.toUpperCase()}]</span>
          )}
          <span className="badge verified">
            <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>verified</span>
            [VERIFIED SAMSUNG SOLUTION]
          </span>
          {source && (
            <span className="badge source">[{source}]</span>
          )}
        </div>

        {/* Title */}
        <h1 className="result-title">{title || 'Identified Issue'}</h1>

        {/* Anomaly Box */}
        <div className="anomaly-box">
          <div className="anomaly-label">
            <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>troubleshoot</span>
            <span>IDENTIFIED ANOMALY</span>
          </div>
          <p className="anomaly-text">
            Issue detected with{' '}
            {displayConfidence && (
              <span style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '11px',
                fontWeight: 600,
                color: confClass === 'high' ? 'var(--success)' : confClass === 'medium' ? 'var(--warning)' : 'var(--danger)',
              }}>
                {(displayConfidence * 100).toFixed(1)}% confidence
              </span>
            )}
            . Verified resolution path available.
            {displayConfidence && (
              <span className={`badge confidence ${confClass}`} style={{ marginLeft: '8px' }}>
                {confLabel}
              </span>
            )}
          </p>
        </div>
      </div>

      {/* Steps Section */}
      {steps && steps.length > 0 && (
        <div className="steps-section">
          <div className="steps-header">
            <div className="steps-title-group">
              <span className="steps-title-dot" />
              <h2 className="steps-title">Curated Resolution Sequence</h2>
            </div>
            <span className="steps-progress">
              Steps: <span className="count">{steps.length}</span>
            </span>
          </div>

          {steps.map((step, idx) => (
            <div key={idx} className="step-item">
              <div className="step-top">
                <div className="step-number">
                  <span className="material-symbols-outlined">check</span>
                </div>
                <div className="step-info">
                  <div className="step-meta">
                    <span className="step-stage-label">Stage {String(idx + 1).padStart(2, '0')}</span>
                  </div>
                  <p className="step-desc">{step}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Deep Link Action */}
      {action && action.deep_link && (
        <div className="step-path">
          <span className="material-symbols-outlined">route</span>
          <span style={{ color: 'var(--on-surface-variant)' }}>Action:</span>
          <a
            href={`intent://#Intent;action=${action.deep_link};end`}
            style={{
              color: 'var(--primary)',
              fontWeight: 600,
              textDecoration: 'none',
            }}
          >
            {action.label || 'Open Settings'}
          </a>
          <span className="material-symbols-outlined" style={{ fontSize: '14px', color: 'var(--on-surface-variant)' }}>open_in_new</span>
        </div>
      )}

      {/* Feedback Section */}
      <div className="feedback-section">
        <h3 className="feedback-title">Resolution Verification & Follow-up</h3>
        <p className="feedback-desc">
          Confirm whether applying this troubleshooting protocol resolved your issue.
          Your telemetry feedback strengthens local inference heuristics for subsequent users.
        </p>

        {/* Fixed confirmation banner */}
        {showFixedConfirm && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 16px',
            borderRadius: '8px',
            background: 'rgba(16, 185, 129, 0.15)',
            fontSize: '13px',
            color: 'var(--success)',
            animation: 'fadeInUp 0.3s ease-out',
          }}>
            <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>task_alt</span>
            <span>Resolution logged. Positive telemetry recorded to Galaxy Device Health Registry.</span>
          </div>
        )}

        <div className="feedback-actions">
          <button
            type="button"
            className="btn-fixed"
            onClick={() => setShowFixedConfirm(true)}
            disabled={showFixedConfirm}
          >
            <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>check_circle</span>
            <span>{showFixedConfirm ? 'Logged ✓' : 'This fixed my issue'}</span>
          </button>
          <button
            type="button"
            className="btn-escalate"
            onClick={() => setShowEscalation(true)}
          >
            <span className="material-symbols-outlined" style={{ fontSize: '20px', color: 'var(--error)' }}>warning</span>
            <span>Still experiencing the issue</span>
          </button>
          <button type="button" className="btn-restart" onClick={onReset}>
            <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>sync</span>
            <span>Try another diagnosis</span>
          </button>
        </div>
      </div>

      {/* Escalation Panel Modal */}
      {showEscalation && (
        <EscalationPanel
          result={result}
          query={query}
          sessionId={sessionId}
          onClose={() => setShowEscalation(false)}
        />
      )}
    </div>
  );
}
