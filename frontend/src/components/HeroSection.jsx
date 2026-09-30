import React from 'react';

export default function HeroSection() {
  return (
    <section className="hero-section">
      {/* Micro Telemetry Pill */}
      <div className="hero-pill">
        <span className="hero-pill-dot" />
        <span className="hero-pill-text">
          AI-POWERED · VERIFICATION-FIRST · LOW-LATENCY &lt;42MS
        </span>
      </div>

      {/* Core Headline */}
      <h1 className="hero-title">
        Troubleshoot Smarter. <span className="gradient">Fix Faster.</span>
      </h1>

      <p className="hero-subtitle">
        Describe your Samsung device issue. Get instant deterministic triage,
        adaptive clarification via Laya AI, and verified hardware/firmware resolutions.
      </p>
    </section>
  );
}
