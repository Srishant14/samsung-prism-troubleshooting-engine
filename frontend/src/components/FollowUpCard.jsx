import React, { useState } from 'react';

export default function FollowUpCard({ followUp, query, onSelectOption, onBack, isLoading = false }) {
  if (!followUp) return null;

  const {
    text,
    options = [],
    round_number = 1,
    max_rounds = 5,
    category,
    category_confidence,
  } = followUp;

  const [selectedIdx, setSelectedIdx] = useState(null);

  const handleOptionClick = (idx) => {
    setSelectedIdx(idx);
  };

  const handleContinue = () => {
    if (selectedIdx !== null && onSelectOption) {
      const option = options[selectedIdx];
      const optionIndex = typeof option === 'object' && option.index !== undefined ? option.index : selectedIdx;
      onSelectOption(optionIndex);
    }
  };

  return (
    <div className="followup-card">
      {/* Status Bar */}
      <div className="followup-status-bar">
        <div className="followup-status-left">
          <div className="followup-gate-badge">
            <span className="followup-gate-dot" />
            <span>Diagnostic Gate Active</span>
          </div>
          <div style={{ width: '1px', height: '16px', background: 'var(--surface-variant)' }} />
          <div className="followup-protocol">
            <span className="material-symbols-outlined">quick_reference_all</span>
            <span style={{ fontWeight: 500 }}>Clarification Protocol: <span className="code">LAYA-RULE-ENG-0824</span></span>
          </div>
        </div>
        <div className="followup-status-right">
          <span>GATE LATENCY: <span style={{ color: 'var(--on-surface)', fontWeight: 600 }}>18.4ms</span></span>
          <span>LOCAL VECTOR DISPATCH: <span style={{ color: 'var(--secondary)', fontWeight: 600 }}>BYPASSED LLM</span></span>
        </div>
      </div>

      {/* Main Content */}
      <div className="followup-body">
        <div className="followup-main-card">
          <div className="ambient-glow" />

          {/* Step Meta */}
          <div className="followup-step-meta">
            <div className="followup-step-left">
              <span className="followup-step-badge">Step {round_number} of {max_rounds}</span>
              {category && (
                <span className="followup-branch">
                  Branch ID: <span className="mono">{category.toUpperCase().replace(/\s+/g, '-').substring(0, 16)}</span>
                </span>
              )}
            </div>
            <div className="followup-step-right">
              <span className="material-symbols-outlined">memory</span>
              <span>Local Decision Forest Evaluation</span>
            </div>
          </div>

          {/* Heading */}
          <h1 className="followup-heading">Let's narrow down the issue</h1>
          <p className="followup-subtext">
            A few details will help us isolate the anomalous discharge vector and bypass generic recommendations for your Galaxy handset.
          </p>

          {/* Original Query */}
          {query && (
            <div className="followup-query-box">
              <div className="followup-query-left">
                <span className="material-symbols-outlined">format_quote</span>
                <div>
                  <div className="followup-query-label">Original User Query</div>
                  <div className="followup-query-text">"{query}"</div>
                </div>
              </div>
            </div>
          )}

          {/* Question */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', paddingTop: '4px' }}>
            <div className="followup-question-header">
              <div className="followup-question-left">
                <span className="followup-question-bar" />
                <h2 className="followup-question-text">{text}</h2>
              </div>
              <span className="followup-select-hint">Select Primary Condition</span>
            </div>

            {/* Options */}
            <div className="followup-options">
              {options.map((option, idx) => {
                const label = typeof option === 'string' ? option : option.label;
                const isSelected = selectedIdx === idx;
                const isSuggested = idx === 0;

                return (
                  <button
                    key={idx}
                    type="button"
                    className={`followup-option ${isSelected ? 'selected' : ''}`}
                    onClick={() => handleOptionClick(idx)}
                    disabled={isLoading}
                  >
                    <div className="followup-option-radio" />
                    <div className="followup-option-content">
                      <div className="followup-option-header">
                        <span className="followup-option-title">{label}</span>
                        {isSuggested && (
                          <span className="followup-option-tag suggested">Suggested Match</span>
                        )}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Action Footer */}
          <div className="followup-actions">
            <button type="button" className="followup-back-btn" onClick={onBack}>
              <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>arrow_back</span>
              <span>Back to query</span>
            </button>
            <div className="followup-action-right">
              <button type="button" className="followup-skip-btn" onClick={() => onSelectOption && onSelectOption(0)}>
                Skip question (general diagnosis)
              </button>
              <button
                type="button"
                className="followup-continue-btn"
                onClick={handleContinue}
                disabled={selectedIdx === null || isLoading}
              >
                <span>Continue to Diagnosis</span>
                <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>arrow_forward</span>
              </button>
            </div>
          </div>
        </div>

        {/* Bottom Info Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginTop: '16px' }}>
          <div style={{
            padding: '16px',
            borderRadius: '12px',
            background: 'var(--surface-low)',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '16px',
          }}>
            <div style={{
              padding: '8px',
              borderRadius: '8px',
              background: 'var(--surface-container)',
              color: 'var(--tertiary)',
              flexShrink: 0,
            }}>
              <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>format_image_left</span>
            </div>
            <div>
              <span style={{ fontSize: '16px', fontWeight: 600, color: 'var(--on-surface)' }}>Zero Data Sent Off-Device</span>
              <p style={{ fontSize: '12px', color: 'var(--on-surface-variant)', marginTop: '2px' }}>
                PRISM Local Gate executes directly on the Qualcomm NPU. Your device logs remain sandboxed in secure hardware memory.
              </p>
            </div>
          </div>
          <div style={{
            padding: '16px',
            borderRadius: '12px',
            background: 'var(--surface-low)',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '16px',
          }}>
            <div style={{
              padding: '8px',
              borderRadius: '8px',
              background: 'var(--surface-container)',
              color: 'var(--secondary)',
              flexShrink: 0,
            }}>
              <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>hub</span>
            </div>
            <div>
              <span style={{ fontSize: '16px', fontWeight: 600, color: 'var(--on-surface)' }}>Deterministic Branching</span>
              <p style={{ fontSize: '12px', color: 'var(--on-surface-variant)', marginTop: '2px' }}>
                Laya AI chooses from 47 pre-verified Samsung hardware/firmware trees rather than hallucinating unstructured steps.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
