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
          {/* Samsung PRISM Glowing Cyan Triangle Logo */}
          <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M20 6L36 34H4L20 6Z" fill="#00F0FF" />
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
      </div>

      {/* Right Side Links */}
      <div className="header-right">
        <a href="/2d" target="_blank" rel="noreferrer" className="header-arch-link">
          <span>2D</span>
          <span>Architecture</span>
        </a>
      </div>
    </header>
  );
}
