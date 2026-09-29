import React, { useState, useCallback, useRef } from 'react';
import SearchBar from './components/SearchBar';
import TroubleshootResult from './components/TroubleshootResult';
import NoMatchCard from './components/NoMatchCard';
import FollowUpCard from './components/FollowUpCard';
import Header from './components/Header';
import Footer from './components/Footer';
import HeroSection from './components/HeroSection';
import PipelineSection from './components/PipelineSection';
import FeatureCards from './components/FeatureCards';

function App() {
  const [query, setQuery] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // AbortController ref — cancels in-flight requests when a new one starts
  const abortRef = useRef(null);

  // Determine which "stage" we're at for the nav tabs
  const getActiveStage = () => {
    if (!result && !isLoading) return 'initial-input';
    if (isLoading) return 'diagnostic-analysis';
    if (result?.status === 'follow_up') return 'clarification-laya-ai';
    if (result?.status === 'success') return 'verified-results';
    return 'initial-input';
  };

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

  const handleReset = useCallback(() => {
    setQuery('');
    setSessionId(null);
    setResult(null);
    setError(null);
  }, []);

  const issueCount = result?.results?.length || 0;
  const activeStage = getActiveStage();
  const showInitialPage = !result && !isLoading && !error;

  return (
    <div className="app-shell">
      <Header activeStage={activeStage} />

      <main className="app-main">
        {/* Initial Input Page */}
        {showInitialPage && (
          <div className="initial-input-page">
            <div className="glow-primary" />
            <div className="glow-tertiary" />

            <HeroSection />
            <SearchBar onSubmit={handleDiagnose} isLoading={isLoading} />
            <PipelineSection />
            <FeatureCards />
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="initial-input-page">
            <div style={{ marginTop: '24px' }}>
              <div className="loading-state">
                <div className="loading-spinner" />
                <p className="loading-text">Diagnosing your issue…</p>
                <span style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '11px',
                  color: 'var(--on-surface-variant)'
                }}>
                  Routing through Local Decision Engine → Laya AI Clarifier → Verified Corpus
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Follow-up / Clarification */}
        {!isLoading && result && result.status === 'follow_up' && (
          <div className="initial-input-page" style={{ maxWidth: '1200px' }}>
            <FollowUpCard
              followUp={result.follow_up}
              query={query}
              onSelectOption={handleSelectOption}
              onBack={handleReset}
              isLoading={isLoading}
            />
          </div>
        )}

        {/* Success / Verified Results */}
        {!isLoading && result && result.status === 'success' && (
          <div className="initial-input-page" style={{ maxWidth: '1000px' }}>
            {issueCount > 1 && (
              <div className="multi-issue-header">
                <span className="issue-count-badge">
                  <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>warning</span>
                  {issueCount} issues detected
                </span>
              </div>
            )}
            {result.results && result.results.length > 0 ? (
              result.results.map((issueResult, idx) => (
                <div key={`${issueResult.domain}-${issueResult.issue}-${idx}`} style={{ marginBottom: idx < issueCount - 1 ? '16px' : '0' }}>
                  <TroubleshootResult result={issueResult} query={query} sessionId={sessionId} onReset={handleReset} />
                </div>
              ))
            ) : (
              /* Backward compat: use legacy single-result fields */
              <TroubleshootResult result={result} query={query} sessionId={sessionId} onReset={handleReset} />
            )}
          </div>
        )}

        {/* No Match */}
        {!isLoading && result && result.status === 'no_match' && (
          <div className="initial-input-page">
            <NoMatchCard message={result.message} onReset={handleReset} />
          </div>
        )}

        {/* Error */}
        {!isLoading && error && (
          <div className="initial-input-page">
            <div className="error-card">
              <p>{error}</p>
            </div>
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}

export default App;
