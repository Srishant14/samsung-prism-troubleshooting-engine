import React from 'react';

export default function FeatureCards() {
  return (
    <section className="feature-grid">
      {/* Card 1: Local Decision Pipeline */}
      <div className="feature-card">
        <div className="feature-card-header">
          <div className="feature-icon primary">
            <span className="material-symbols-outlined">bolt</span>
          </div>
          <span className="feature-badge tertiary">~8ms</span>
        </div>
        <h4 className="feature-title">Local Decision Engine</h4>
        <p className="feature-desc">
          Instant client-side evaluation against known hardware fault signatures,
          hardware sensor codes, and Knox policies.
        </p>
        <div className="feature-link tertiary">
          <span>ZERO CLOUD OVERHEAD</span>
          <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>chevron_right</span>
        </div>
      </div>

      {/* Card 2: Laya AI Clarifier */}
      <div className="feature-card">
        <div className="feature-card-header">
          <div className="feature-icon tertiary">
            <span className="material-symbols-outlined">psychology</span>
          </div>
          <span className="feature-badge primary">LAYER 2</span>
        </div>
        <h4 className="feature-title">Laya AI Clarifier</h4>
        <p className="feature-desc">
          When symptoms overlap, intelligent probing asks targeted questions to
          distinguish software defects from hardware failures.
        </p>
        <div className="feature-link primary">
          <span>ADAPTIVE QUESTIONING</span>
          <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>chevron_right</span>
        </div>
      </div>

      {/* Card 3: Verified Corpus */}
      <div className="feature-card">
        <div className="feature-card-header">
          <div className="feature-icon secondary">
            <span className="material-symbols-outlined">verified_user</span>
          </div>
          <span className="feature-badge success">CERTIFIED</span>
        </div>
        <h4 className="feature-title">Verified Samsung Corpus</h4>
        <p className="feature-desc">
          Direct citations to certified Samsung Care service bulletins, factory
          schematics, and field diagnostic runbooks.
        </p>
        <div className="feature-link secondary">
          <span>AUTHORITATIVE REPAIR PATHS</span>
          <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>chevron_right</span>
        </div>
      </div>
    </section>
  );
}
