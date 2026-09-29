import React from 'react';
import { CheckCircle2, ExternalLink, ShieldCheck } from 'lucide-react';

export default function TroubleshootResult({ result }) {
  if (!result) return null;

  const {
    title, domain, confidence, final_confidence, match_confidence,
    source, source_type, steps, action
  } = result;

  // Use final_confidence if available, else fall back to confidence
  const displayConfidence = final_confidence || confidence;

  // Domain coloring logic
  let domainClass = 'performance';
  if (domain && domain.toLowerCase().includes('battery')) domainClass = 'battery';
  else if (domain && domain.toLowerCase().includes('display')) domainClass = 'display';
  else if (domain && domain.toLowerCase().includes('camera')) domainClass = 'camera';

  // Confidence indicator
  let confLabel = 'Match';
  let confClass = 'conf-medium';
  if (displayConfidence >= 0.8) {
    confLabel = 'Strong Match';
    confClass = 'conf-high';
  } else if (displayConfidence >= 0.6) {
    confLabel = 'Good Match';
    confClass = 'conf-medium';
  } else {
    confLabel = 'Partial Match';
    confClass = 'conf-low';
  }

  return (
    <div className="result-card">
      <div className="result-header">
        <div className="result-title-group">
          <h2>{title || 'Identified Issue'}</h2>
          <div className="badges">
            <span className={`domain-badge ${domainClass}`}>
              {domain}
            </span>
            {displayConfidence && (
              <span className={`confidence-score ${confClass}`}>
                {(displayConfidence * 100).toFixed(0)}% {confLabel}
              </span>
            )}
          </div>
        </div>
        
        {source && (
          <div className="source-badge">
            <ShieldCheck size={16} />
            <span>{source}</span>
          </div>
        )}
      </div>

      <div className="steps-container">
        <h3>Recommended Steps</h3>
        <div className="steps-list">
          {steps && steps.length > 0 ? (
            steps.map((step, idx) => (
              <div key={idx} className="step-item">
                <div className="step-number">{idx + 1}</div>
                <div className="step-content">{step}</div>
              </div>
            ))
          ) : (
            <div className="step-item">
              <div className="step-number">1</div>
              <div className="step-content">No specific steps found. Please contact support.</div>
            </div>
          )}
        </div>
      </div>

      {action && action.deep_link && (
        <a href={`intent://#Intent;action=${action.deep_link};end`} className="action-button">
          <CheckCircle2 size={24} />
          <span>{action.label || 'Open Settings'}</span>
          <ExternalLink size={20} />
        </a>
      )}
    </div>
  );
}
