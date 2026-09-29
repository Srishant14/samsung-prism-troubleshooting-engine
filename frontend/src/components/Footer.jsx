import React from 'react';

export default function Footer() {
  return (
    <footer className="app-footer">
      <div className="footer-left">
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span className="footer-latency-dot" />
          <span>LATENCY: <span className="bold">&lt;42ms</span></span>
        </div>
        <span className="separator">|</span>
        <span>CORPUS BUILD: <span className="mono">v5.1.2024.11-SEC</span></span>
        <span className="separator">|</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span className="material-symbols-outlined verified-icon">verified</span>
          <span>LOCAL ENGINE VERIFIED</span>
        </div>
      </div>
      <div className="footer-right">
        <a href="#" className="footer-link">Diagnostic Logs</a>
        <a href="#" className="footer-link">Telemetry Stream</a>
        <a href="#" className="footer-link">Enterprise Support</a>
        <span className="footer-copyright">© 2024 Samsung PRISM Engineering</span>
      </div>
    </footer>
  );
}
