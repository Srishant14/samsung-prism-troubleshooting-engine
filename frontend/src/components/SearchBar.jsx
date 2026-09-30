import React, { useState, useRef, useEffect } from 'react';

const PRESETS = [
  { icon: 'bolt', label: 'Battery draining fast', fill: 'Battery draining quickly and phone feels warm after One UI 6.1 update' },
  { icon: 'smartphone', label: 'Screen flickering', fill: 'Screen flickers intermittently specifically when running at 120Hz adaptive refresh rate' },
  { icon: 'photo_camera', label: 'Camera photos blurry', fill: 'Camera photos appear blurry and 3x telephoto struggles to lock focus in low light' },
  { icon: 'local_fire_department', label: 'Phone overheating', fill: 'Device thermal throttling and overheating near camera module during regular charging' },
  { icon: 'settings', label: 'Phone running slowly', fill: 'System UI lag, frame drops during gesture navigation, and slow app launch times' },
];

export default function SearchBar({ onSubmit, isLoading }) {
  const [query, setQuery] = useState('');
  const textareaRef = useRef(null);

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (query.trim() && !isLoading) {
      onSubmit(query.trim());
    }
  };

  const handlePresetClick = (fill) => {
    setQuery(fill);
    if (textareaRef.current) textareaRef.current.focus();
  };

  const handleClear = () => {
    setQuery('');
    if (textareaRef.current) textareaRef.current.focus();
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && document.activeElement === textareaRef.current) {
        setQuery('');
      }
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        e.preventDefault();
        handleSubmit();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [query, isLoading]);

  return (
    <section className="console-card">
      <div className="console-inner">
        {/* Console Header Bar */}
        <div className="console-header">
          <div className="console-header-left">
            <span className="console-terminal-badge">
              <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>terminal</span>
            </span>
            <span className="console-label">SYS.DIAG_PROMPT</span>
            <span className="console-ready-badge">READY</span>
          </div>
          <div className="console-header-right">
            <span className="console-engine-dot" />
            <span>ENGINE V5.1 ACTIVE</span>
          </div>
        </div>

        {/* Main Input Field */}
        <div className="input-area">
          <div className="input-wrapper">
            <span className="input-prompt">&gt;</span>
            <textarea
              ref={textareaRef}
              className="diagnostic-textarea"
              placeholder="Describe the problem with your Samsung device (e.g., Battery draining quickly after One UI 6.1 update, screen flickering on 120Hz Adaptive mode, camera lens rattle during stabilization)..."
              rows={4}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={isLoading}
            />
          </div>
        </div>

        {/* Quick Presets */}
        <div className="presets-row">
          <span className="presets-label">QUICK PRESETS:</span>
          {PRESETS.map((preset, idx) => (
            <button
              key={idx}
              type="button"
              className="preset-chip"
              onClick={() => handlePresetClick(preset.fill)}
              disabled={isLoading}
            >
              <span className="material-symbols-outlined preset-icon">{preset.icon}</span>
              <span>{preset.label}</span>
            </button>
          ))}
        </div>

        {/* Console Footer & Action Bar */}
        <div className="console-footer">
          <div className="console-footer-left">
            <button type="button" className="clear-btn" onClick={handleClear}>
              <span className="material-symbols-outlined" style={{ fontSize: '15px' }}>backspace</span>
              <span>Clear Input</span>
              <span className="kbd">Esc</span>
            </button>
            <span className="char-count">{query.length} chars</span>
          </div>

          <button
            type="button"
            className="diagnose-btn"
            onClick={handleSubmit}
            disabled={!query.trim() || isLoading}
          >
            <span className="material-symbols-outlined diagnose-icon">auto_awesome</span>
            <span>{isLoading ? 'Parsing Issue...' : 'Diagnose Issue'}</span>
            <span className="kbd-hint">⌘ + ↵</span>
          </button>
        </div>
      </div>
    </section>
  );
}
