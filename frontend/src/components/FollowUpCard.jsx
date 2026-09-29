import React from 'react';
import { HelpCircle, ChevronRight, Sparkles } from 'lucide-react';

export default function FollowUpCard({ followUp, onSelectOption, isLoading = false }) {
  if (!followUp) return null;

  const {
    text,
    options = [],
    round_number = 1,
    max_rounds = 5,
    category,
    category_confidence,
  } = followUp;

  // Domain styling helper
  const getDomainClass = (catStr) => {
    if (!catStr) return 'performance';
    const lower = catStr.toLowerCase();
    if (lower.includes('battery')) return 'battery';
    if (lower.includes('display') || lower.includes('screen')) return 'display';
    if (lower.includes('camera')) return 'camera';
    return 'performance';
  };

  const domainClass = getDomainClass(category);

  return (
    <div className="followup-card">
      <div className="followup-top-row">
        <div className="followup-header">
          <HelpCircle size={20} className="followup-header-icon" />
          <span>Let's narrow this down</span>
        </div>

        {category && (
          <div className="followup-category-container">
            <span className={`domain-badge ${domainClass}`}>
              <Sparkles size={12} style={{ marginRight: '4px' }} />
              {category}
            </span>
            {category_confidence && (
              <span className="followup-conf-pill">
                {Math.round(category_confidence * 100)}% Confidence
              </span>
            )}
          </div>
        )}
      </div>

      <h3 className="followup-question">{text}</h3>

      <div className="followup-options">
        {options.map((option, idx) => {
          const label = typeof option === 'string' ? option : option.label;
          const optionIndex = typeof option === 'object' && option.index !== undefined ? option.index : idx;
          const letter = String.fromCharCode(65 + idx);

          return (
            <button
              key={optionIndex}
              type="button"
              className="followup-option"
              onClick={() => onSelectOption && onSelectOption(optionIndex)}
              disabled={isLoading}
            >
              <span className="option-letter">{letter}</span>
              <span className="option-label">{label}</span>
              <ChevronRight size={18} className="option-chevron" />
            </button>
          );
        })}
      </div>

      <div className="followup-progress">
        Step {round_number} of {max_rounds}
      </div>
    </div>
  );
}
