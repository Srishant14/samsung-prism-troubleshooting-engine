import React, { useState } from 'react';
import { Search, X, Zap } from 'lucide-react';

const EXAMPLES = [
  "Battery dying fast",
  "Screen flickering",
  "Camera photos blurry",
  "Phone feels slow",
  "Phone overheating"
];

export default function SearchBar({ onSubmit, isLoading }) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (query.trim() && !isLoading) {
      onSubmit(query.trim());
    }
  };

  const handleChipClick = (example) => {
    setQuery(example);
    onSubmit(example);
  };

  return (
    <div className="search-section">
      <form onSubmit={handleSubmit} className="search-input-group">
        <input
          type="text"
          className="search-input"
          placeholder="Describe your device problem..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={isLoading}
        />
        {query && !isLoading && (
          <button 
            type="button" 
            className="clear-btn" 
            onClick={() => setQuery('')}
            aria-label="Clear input"
          >
            <X size={20} />
          </button>
        )}
        <button 
          type="submit" 
          className="diagnose-btn"
          disabled={!query.trim() || isLoading}
        >
          <Zap size={20} />
          Diagnose
        </button>
      </form>

      <div className="example-chips">
        {EXAMPLES.map((example, idx) => (
          <button
            key={idx}
            type="button"
            className="example-chip"
            onClick={() => handleChipClick(example)}
            disabled={isLoading}
          >
            <Search size={14} />
            {example}
          </button>
        ))}
      </div>
    </div>
  );
}
