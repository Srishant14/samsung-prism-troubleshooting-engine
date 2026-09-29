import React, { useState, useCallback, useRef } from 'react';
import { Wrench } from 'lucide-react';
import SearchBar from './components/SearchBar';
import TroubleshootResult from './components/TroubleshootResult';
import NoMatchCard from './components/NoMatchCard';
import FollowUpCard from './components/FollowUpCard';

function App() {
  const [query, setQuery] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // AbortController ref — cancels in-flight requests when a new one starts
  const abortRef = useRef(null);

  const handleDiagnose = useCallback(async (queryText) => {
    // Cancel any in-flight request
    if (abortRef.current) abortRef.current.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setQuery(queryText);
    setSessionId(null);
    setIsLoading(true);
    setResult(null);
    setError(null);
    
    try {
      const response = await fetch('/api/v1/troubleshoot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: queryText }),
        signal: controller.signal,
      });
      
      if (!response.ok) {
        throw new Error('Server error');
      }
      
      const data = await response.json();
      setResult(data);
      if (data.session_id) {
        setSessionId(data.session_id);
      }
    } catch (err) {
      if (err.name === 'AbortError') return; // Superseded by newer request
      console.error(err);
      setError('Failed to connect to the troubleshooting service. Make sure the backend is running.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleSelectOption = useCallback(async (optionIndex) => {
    // Cancel any in-flight request
    if (abortRef.current) abortRef.current.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/troubleshoot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query,
          session_id: sessionId,
          selected_option: optionIndex
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error('Server error');
      }

      const data = await response.json();
      setResult(data);
      if (data.session_id) {
        setSessionId(data.session_id);
      }
    } catch (err) {
      if (err.name === 'AbortError') return;
      console.error(err);
      setError('Failed to connect to the troubleshooting service. Make sure the backend is running.');
    } finally {
      setIsLoading(false);
    }
  }, [query, sessionId]);

  const issueCount = result?.results?.length || 0;

  return (
    <div className="app-container">
      <header className="app-header">
        <Wrench className="header-icon" />
        <h1 className="gradient-text">Smart Troubleshooting Engine</h1>
        <p className="subtitle">
          AI-powered device troubleshooting — describe your problem, get verified fixes.
        </p>
        <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', marginTop: '12px', flexWrap: 'wrap' }}>
          <span className="prism-badge">Samsung PRISM v5.1</span>
          <a
            href="/api/3d"
            target="_blank"
            rel="noreferrer"
            className="prism-badge"
            style={{ textDecoration: 'none', background: 'rgba(0, 117, 255, 0.2)', borderColor: 'rgba(0, 117, 255, 0.5)', color: '#00f0ff', cursor: 'pointer' }}
          >
            🌐 3D Architecture Visualizer
          </a>
          <a
            href="/api/2d"
            target="_blank"
            rel="noreferrer"
            className="prism-badge"
            style={{ textDecoration: 'none', background: 'rgba(192, 132, 252, 0.2)', borderColor: 'rgba(192, 132, 252, 0.5)', color: '#c084fc', cursor: 'pointer' }}
          >
            📐 2D Archify Blueprint
          </a>
        </div>
      </header>

      <main>
        <SearchBar onSubmit={handleDiagnose} isLoading={isLoading} />

        {isLoading && (
          <div className="loading-state" style={{ marginTop: '24px' }}>
            <div className="loading-spinner"></div>
            <p className="loading-text">Diagnosing your issue...</p>
          </div>
        )}

        {!isLoading && result && result.status === 'follow_up' && (
          <div style={{ marginTop: '24px' }}>
            <FollowUpCard
              followUp={result.follow_up}
              onSelectOption={handleSelectOption}
              isLoading={isLoading}
            />
          </div>
        )}

        {!isLoading && result && result.status === 'success' && (
          <div style={{ marginTop: '24px' }}>
            {issueCount > 1 && (
              <div className="multi-issue-header">
                <span className="issue-count-badge">{issueCount} issues detected</span>
              </div>
            )}
            {result.results && result.results.length > 0 ? (
              result.results.map((issueResult, idx) => (
                <div key={`${issueResult.domain}-${issueResult.issue}-${idx}`} style={{ marginBottom: idx < issueCount - 1 ? '16px' : '0' }}>
                  <TroubleshootResult result={issueResult} />
                </div>
              ))
            ) : (
              /* Backward compat: use legacy single-result fields */
              <TroubleshootResult result={result} />
            )}
          </div>
        )}

        {!isLoading && result && result.status === 'no_match' && (
          <div style={{ marginTop: '24px' }}>
            <NoMatchCard message={result.message} />
          </div>
        )}

        {!isLoading && error && (
          <div className="error-card" style={{ marginTop: '24px' }}>
            <p>{error}</p>
          </div>
        )}
      </main>

      <footer className="app-footer">
        Built for Samsung PRISM Gen AI Hackathon 2026-27
      </footer>
    </div>
  );
}

export default App;
