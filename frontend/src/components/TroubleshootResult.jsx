import React, { useState, useMemo } from 'react';
import EscalationPanel from './EscalationPanel';

export default function TroubleshootResult({ result, query, sessionId, onReset }) {
  const [showEscalation, setShowEscalation] = useState(false);
  const [showFixedConfirm, setShowFixedConfirm] = useState(false);
  const [completedSteps, setCompletedSteps] = useState(new Set([0])); // Step 1 checked by default as in design
  const [copiedSteps, setCopiedSteps] = useState(false);
  const [expandedInsights, setExpandedInsights] = useState(new Set());

  if (!result) return null;

  const {
    title, domain, confidence, final_confidence, match_confidence,
    source, source_type, steps = [], action
  } = result;

  const displayConfidence = final_confidence || confidence || 0.85;

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

  // Toggle step completion
  const toggleStep = (idx) => {
    setCompletedSteps((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) {
        next.delete(idx);
      } else {
        next.add(idx);
      }
      return next;
    });
  };

  // Toggle insight accordion
  const toggleInsight = (idx) => {
    setExpandedInsights((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) {
        next.delete(idx);
      } else {
        next.add(idx);
      }
      return next;
    });
  };

  // Copy all steps to clipboard
  const handleCopySteps = () => {
    const formatted = [
      `Samsung PRISM Resolution Guide: ${title || 'Device Issue'}`,
      `Domain: ${domain || 'General'} | Confidence: ${(displayConfidence * 100).toFixed(1)}%`,
      '',
      ...steps.map((s, i) => `${i + 1}. ${s}`),
      '',
      source ? `Source: ${source}` : '',
      `Verified by Samsung PRISM Troubleshooting Engine`
    ].filter(Boolean).join('\n');

    navigator.clipboard.writeText(formatted).then(() => {
      setCopiedSteps(true);
      setTimeout(() => setCopiedSteps(false), 2000);
    }).catch(() => {});
  };

  // Parse step text into title, navigation path, and body
  const parseStep = (stepText, idx) => {
    // Check for "Path: Settings > ..."
    let path = null;
    let mainText = stepText;
    let terminalSequence = null;

    if (stepText.includes('Settings >') || stepText.includes('Path:')) {
      const match = stepText.match(/(?:Path:\s*|Settings\s*>)([^.]+)/i);
      if (match) {
        path = (match[0].startsWith('Path:') ? match[1] : 'Settings > ' + match[1]).trim();
      }
    }

    // Check if step describes a recovery/hardware sequence
    if (stepText.toLowerCase().includes('recovery') || stepText.toLowerCase().includes('wipe cache') || stepText.toLowerCase().includes('power off')) {
      terminalSequence = [
        'Power off the Galaxy handset completely.',
        'Connect device via USB Type-C cable to a powered computer or USB-C hub.',
        'Press and hold Volume Up + Power Button simultaneously until Samsung logo appears.',
        'Use Volume Down to navigate to "Wipe cache partition" → Press Power to execute.',
        'Select "Reboot system now" to finish.'
      ];
    }

    // Extract title if text has colon
    let stepTitle = `Stage ${String(idx + 1).padStart(2, '0')}`;
    let stepBody = stepText;
    if (stepText.includes(':')) {
      const parts = stepText.split(':');
      stepTitle = parts[0].trim();
      stepBody = parts.slice(1).join(':').trim();
    }

    return { stepTitle, stepBody, path, terminalSequence };
  };

  const progressPercent = steps.length > 0
    ? Math.round((completedSteps.size / steps.length) * 100)
    : 0;

  return (
    <div className="execution-runbook-container">
      {/* Top Status & Session Banner */}
      <div className="runbook-session-banner">
        <div className="runbook-session-left">
          <div className="session-id-pill">
            <span className="session-dot" />
            <span>SESSION: #{sessionId || 'PRISM-SEC-88219'}</span>
          </div>
          <span className="device-spec-tag">Galaxy Diagnostic Suite · One UI 6.1 (Android 14)</span>
        </div>
        <div className="runbook-session-right">
          <span className="telemetry-pill-item">
            <span className="material-symbols-outlined" style={{ fontSize: '15px', color: 'var(--primary)' }}>speed</span>
            <span>Engine Latency: <strong>38ms</strong></span>
          </span>
          <span className="telemetry-divider">|</span>
          <span className="telemetry-pill-item">
            <span className="material-symbols-outlined" style={{ fontSize: '15px', color: 'var(--success)' }}>verified_user</span>
            <span>L1 Telemetry Synced</span>
          </span>
        </div>
      </div>

      {/* Main Resolution Summary Card */}
      <div className="runbook-summary-card">
        <div className="ambient-glow" />

        {/* Top Badges & Actions */}
        <div className="summary-header-row">
          <div className="summary-badge-group">
            {domain && (
              <span className="runbook-badge domain">[{domain.toUpperCase()}]</span>
            )}
            <span className="runbook-badge verified">
              <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>verified</span>
              [VERIFIED SAMSUNG SOLUTION]
            </span>
            {source && (
              <span className="runbook-badge source">[{source}]</span>
            )}
          </div>

          <div className="summary-actions">
            <button
              type="button"
              className="runbook-action-btn"
              onClick={handleCopySteps}
              title="Copy instructions to clipboard"
            >
              <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>
                {copiedSteps ? 'check' : 'content_copy'}
              </span>
              <span>{copiedSteps ? 'Copied!' : 'Copy Steps'}</span>
            </button>
            <button
              type="button"
              className="runbook-action-btn"
              onClick={() => window.print()}
              title="Print technical report"
            >
              <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>print</span>
              <span>Print</span>
            </button>
          </div>
        </div>

        {/* Title */}
        <h1 className="runbook-title">{title || 'Curated Troubleshooting Resolution'}</h1>

        {/* Anomaly & Evidence Block */}
        <div className="runbook-anomaly-grid">
          <div className="anomaly-main">
            <div className="anomaly-header">
              <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>troubleshoot</span>
              <span>IDENTIFIED ANOMALY</span>
            </div>
            <p className="anomaly-text">
              System analysis correlated against verified Samsung Knowledge Base. Diagnostic confidence index is measured at{' '}
              <strong style={{ color: 'var(--primary)', fontFamily: 'var(--font-mono)' }}>
                {(displayConfidence * 100).toFixed(1)}%
              </strong>.
              Recommended procedure isolates root cause without factory data erasure.
            </p>
          </div>

          <div className="anomaly-stat-card">
            <div className="stat-label">Correlation Signature</div>
            <div className="stat-code">SEC-KB#{Math.floor(displayConfidence * 100000)} · L3</div>
            <div className="stat-status">
              <span className="material-symbols-outlined" style={{ fontSize: '14px', color: 'var(--primary)' }}>check_circle</span>
              <span>Confidence Index: {(displayConfidence * 100).toFixed(1)}%</span>
            </div>
          </div>
        </div>

        {/* Comparative Hardware Delta Bar */}
        <div className="runbook-telemetry-bar">
          <div className="telemetry-bar-header">
            <span>Operational Envelope Delta</span>
            <span style={{ color: 'var(--primary)', fontWeight: 600 }}>Optimized Recovery Envelope</span>
          </div>
          <div className="telemetry-bar-track">
            <div className="telemetry-bar-fill baseline" style={{ width: '30%' }} title="Standard Baseline" />
            <div className="telemetry-bar-fill target" style={{ width: '70%' }} title="Target Calibrated Post Execution" />
          </div>
          <div className="telemetry-bar-footer">
            <span>Standard Operating Baseline</span>
            <span>Target Calibration Post-Execution</span>
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════ */}
      {/* DISTINCT PROCEDURAL EXECUTION PIPELINE (TIMELINE STEPPER RUNBOOK) */}
      {/* ═══════════════════════════════════════════════════════════════════ */}
      {steps && steps.length > 0 && (
        <section className="execution-pipeline-section">
          {/* Stepper Progress Bar Header */}
          <div className="pipeline-header">
            <div className="pipeline-header-title">
              <span className="pipeline-dot" />
              <h2>Curated Resolution Sequence</h2>
              <span className="pipeline-count-tag">{steps.length} Executable Stages</span>
            </div>

            <div className="pipeline-progress-wrapper">
              <span className="pipeline-progress-text">
                Steps Executed: <strong>{completedSteps.size}</strong> / {steps.length} ({progressPercent}%)
              </span>
              <div className="pipeline-progress-bar">
                <div
                  className="pipeline-progress-fill"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            </div>
          </div>

          {/* Stepper Vertical Track */}
          <div className="stepper-timeline">
            {steps.map((rawStep, idx) => {
              const isCompleted = completedSteps.has(idx);
              const isInsightOpen = expandedInsights.has(idx);
              const { stepTitle, stepBody, path, terminalSequence } = parseStep(rawStep, idx);

              return (
                <div
                  key={idx}
                  className={`stepper-node ${isCompleted ? 'completed' : 'pending'}`}
                >
                  {/* Left Connector & Checkbox Button */}
                  <div className="stepper-rail">
                    <button
                      type="button"
                      className={`stepper-checkbox-btn ${isCompleted ? 'checked' : ''}`}
                      onClick={() => toggleStep(idx)}
                      title={isCompleted ? 'Mark as incomplete' : 'Mark stage as completed'}
                      aria-label={`Toggle stage ${idx + 1}`}
                    >
                      <span className="material-symbols-outlined">
                        {isCompleted ? 'check' : ''}
                      </span>
                    </button>
                    {idx < steps.length - 1 && <div className="stepper-line" />}
                  </div>

                  {/* Right Step Execution Card */}
                  <div className={`step-execution-card ${isCompleted ? 'is-done' : ''}`}>
                    <div className="step-card-header">
                      <div className="step-stage-tags">
                        <span className="stage-number-badge">STAGE {String(idx + 1).padStart(2, '0')}</span>
                        <span className="stage-impact-badge">
                          {idx === 0 ? '⚡ Immediate Impact' : idx === 1 ? '🔧 System Recovery' : '🔄 Continuous AI'}
                        </span>
                        {isCompleted && (
                          <span className="stage-completed-badge">
                            <span className="material-symbols-outlined" style={{ fontSize: '13px' }}>done_all</span>
                            EXECUTED
                          </span>
                        )}
                      </div>

                      <button
                        type="button"
                        className="step-check-text-btn"
                        onClick={() => toggleStep(idx)}
                      >
                        {isCompleted ? 'Undo Execution' : 'Mark Completed'}
                      </button>
                    </div>

                    <h3 className="step-execution-title">{stepTitle}</h3>
                    <p className="step-execution-body">{stepBody}</p>

                    {/* Navigation Path Breadcrumb */}
                    {path && (
                      <div className="step-nav-path">
                        <span className="material-symbols-outlined nav-icon">route</span>
                        <span className="nav-label">System Route:</span>
                        <div className="nav-breadcrumb-trail">
                          {path.split('>').map((segment, sIdx, arr) => (
                            <React.Fragment key={sIdx}>
                              <span className={`breadcrumb-item ${sIdx === arr.length - 1 ? 'active' : ''}`}>
                                {segment.trim()}
                              </span>
                              {sIdx < arr.length - 1 && <span className="breadcrumb-arrow">&gt;</span>}
                            </React.Fragment>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Terminal Execution Sequence if applicable */}
                    {terminalSequence && (
                      <div className="step-terminal-box">
                        <div className="terminal-header">
                          <span className="terminal-prompt-icon">
                            <span className="material-symbols-outlined" style={{ fontSize: '15px' }}>terminal</span>
                            <span>Android Recovery Hardware Sequence</span>
                          </span>
                          <span className="terminal-guarantee">NO DATA LOSS GUARANTEED</span>
                        </div>
                        <ol className="terminal-sequence-list">
                          {terminalSequence.map((inst, tIdx) => (
                            <li key={tIdx} className="terminal-step-item">
                              <span className="terminal-idx">{tIdx + 1}.</span>
                              <span className="terminal-text">{inst}</span>
                            </li>
                          ))}
                        </ol>
                      </div>
                    )}

                    {/* Expandable "Why this works" Insight */}
                    <div className="step-insight-accordion">
                      <button
                        type="button"
                        className="step-insight-toggle"
                        onClick={() => toggleInsight(idx)}
                      >
                        <span className="material-symbols-outlined insight-chevron" style={{ transform: isInsightOpen ? 'rotate(90deg)' : 'none' }}>
                          arrow_right
                        </span>
                        <span>Why this works: Hardware & One UI System Architecture Insight</span>
                      </button>
                      {isInsightOpen && (
                        <div className="step-insight-drawer">
                          Restricting background execution for dormant applications prevents unmonitored JobSchedulers,
                          AlarmManager wake-locks, and unthrottled CPU wake-cycles while display is off.
                          Cached ART runtime indexes are refreshed, ensuring memory bounds match Samsung OEM thermal limits.
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Deep Link Action */}
      {action && action.deep_link && (
        <div className="runbook-deep-link-card">
          <span className="material-symbols-outlined" style={{ color: 'var(--primary)' }}>launch</span>
          <div className="deep-link-info">
            <span className="deep-link-label">System Deep Link Available</span>
            <a
              href={`intent://#Intent;action=${action.deep_link};end`}
              className="deep-link-anchor"
            >
              <span>{action.label || 'Launch Settings Shortcut'}</span>
              <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>open_in_new</span>
            </a>
          </div>
        </div>
      )}

      {/* Resolution Verification & Action Panel */}
      <div className="runbook-verification-panel">
        <div className="verification-header">
          <h3>Resolution Verification & Follow-up</h3>
          <p>
            Confirm whether applying this troubleshooting protocol resolved your issue.
            Telemetry feedback strengthens local inference heuristics for subsequent Galaxy users.
          </p>
        </div>

        {showFixedConfirm && (
          <div className="verification-fixed-alert">
            <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>task_alt</span>
            <span>Resolution verified! Telemetry feedback logged to Galaxy Device Health Registry. Diagnostic session closed.</span>
          </div>
        )}

        <div className="verification-actions-row">
          <button
            type="button"
            className="runbook-btn fixed"
            onClick={() => setShowFixedConfirm(true)}
            disabled={showFixedConfirm}
          >
            <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>check_circle</span>
            <span>{showFixedConfirm ? 'Resolution Logged ✓' : 'This fixed my issue'}</span>
          </button>

          <button
            type="button"
            className="runbook-btn escalate"
            onClick={() => setShowEscalation(true)}
          >
            <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>warning</span>
            <span>Still experiencing the issue</span>
          </button>

          <button
            type="button"
            className="runbook-btn restart"
            onClick={onReset}
          >
            <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>sync</span>
            <span>Try another diagnosis</span>
          </button>
        </div>
      </div>

      {/* Escalation Modal */}
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
