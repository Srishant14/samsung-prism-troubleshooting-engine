import React from 'react';

export default function PipelineSection() {
  return (
    <section className="pipeline-section">
      <div className="pipeline-card">
        <div className="pipeline-content">
          <div className="pipeline-text">
            <span className="pipeline-label">Multi-Tier Resolution Framework</span>
            <h3 className="pipeline-title">Autonomous Triaging Pipeline</h3>
            <p className="pipeline-desc">
              Every query routes through low-latency static pattern sets, escalates to the
              conversational Laya AI neural clarifier when ambiguous, and pins directly to
              validated Samsung OEM manuals.
            </p>
          </div>

          {/* Inline Technical Progress */}
          <div className="pipeline-stats">
            <div className="pipeline-ring">
              <div className="pipeline-ring-value">
                <svg viewBox="0 0 36 36">
                  <path
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="#313540"
                    strokeWidth="3.5"
                  />
                  <path
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="#4cd7f6"
                    strokeWidth="3.5"
                    strokeDasharray="94, 100"
                    strokeLinecap="round"
                  />
                </svg>
                <span className="pipeline-ring-label">94.2%</span>
              </div>
              <span className="pipeline-ring-caption">First-Pass Match</span>
            </div>

            <div className="pipeline-divider" />

            <div className="pipeline-metrics">
              <div className="pipeline-metric">
                <span className="dot success" />
                <span>OEM Spec Sync: Active</span>
              </div>
              <div className="pipeline-metric muted">
                <span className="dot primary" />
                <span>Rule Engine: 1,840 nodes</span>
              </div>
              <div className="pipeline-metric muted">
                <span className="dot tertiary" />
                <span>Corpus: One UI 6.1.1 Rev4</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
