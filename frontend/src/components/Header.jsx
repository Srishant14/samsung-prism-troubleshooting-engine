import React from 'react';

export default function Header({ activeStage = 'initial-input' }) {
  const stages = [
    { id: 'initial-input', label: '1. Initial Input' },
    { id: 'clarification-laya-ai', label: '2. Clarification (Laya AI)' },
    { id: 'diagnostic-analysis', label: '3. Diagnostic Analysis' },
    { id: 'verified-results', label: '4. Verified Results' },
    { id: 'architecture-spec', label: '5. Architecture Spec' },
  ];

  return (
    <header className="app-header">
      {/* Brand */}
      <div className="header-brand">
        <div className="header-logo">
          {/* Samsung PRISM Logo - Triangle SVG */}
          <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M20 4L36 34H4L20 4Z" fill="url(#prism-grad)" stroke="rgba(255,255,255,0.15)" strokeWidth="1"/>
            <defs>
              <linearGradient id="prism-grad" x1="20" y1="4" x2="20" y2="34" gradientUnits="userSpaceOnUse">
                <stop stopColor="#d2bbff"/>
                <stop offset="1" stopColor="#7c3aed"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <span className="header-title">PRISM Troubleshooting Engine</span>
        <span className="header-version">V5.1</span>
      </div>

      {/* Navigation Tabs */}
      <div className="header-nav">
        <div className="nav-tabs">
          {stages.map((stage) => (
            <span
              key={stage.id}
              className={`nav-tab ${activeStage === stage.id ? 'active' : ''}`}
            >
              {stage.label}
            </span>
          ))}
        </div>

        <div style={{ width: '1px', height: '16px', background: 'rgba(74,68,85,0.4)' }} />

        <div className="header-nav-links">
          <a href="/api/2d" target="_blank" rel="noreferrer" className="header-nav-link">
            2D Architecture
          </a>
          <a href="/api/3d" target="_blank" rel="noreferrer" className="header-nav-link">
            3D Architecture
          </a>
        </div>
      </div>

      {/* Right Side */}
      <div className="header-right">
        <div className="header-status">
          <span className="status-dot-container">
            <span className="status-dot-ping" />
            <span className="status-dot" />
          </span>
          <span className="status-text">
            <span className="status-text-highlight">System: Optimal</span>
            {' · Laya AI Online · Local Decision Engine Ready'}
          </span>
        </div>
      </div>
    </header>
  );
}
