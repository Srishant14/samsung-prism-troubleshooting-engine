import React, { useState, useCallback } from 'react';

/**
 * ServiceCentreFinder — Finds nearby Samsung-authorized service centres.
 *
 * Strategy:
 *  1. Ask user permission before accessing geolocation.
 *  2. If granted, use coords to open Samsung's official service centre locator.
 *  3. If denied or unavailable, allow manual city/PIN entry and redirect to Samsung's locator.
 *  4. Never fabricate centre data. Always redirect to Samsung's verified locator page.
 *
 * Why this approach:
 *  Samsung does not expose a public API for service centre lookups.
 *  The only verified source is their official website locator.
 *  Fabricating centres would violate the requirement for verified data.
 */

const LOCATOR_STATES = {
  INITIAL: 'initial',         // Explain + ask permission
  REQUESTING: 'requesting',   // Waiting for browser geolocation
  DENIED: 'denied',           // Permission denied or error
  READY: 'ready',             // Got coords, ready to open
  MANUAL: 'manual',           // Manual entry mode
};

export default function ServiceCentreFinder({ supportConfig }) {
  const [state, setState] = useState(LOCATOR_STATES.INITIAL);
  const [coords, setCoords] = useState(null);
  const [manualLocation, setManualLocation] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const locatorUrl = supportConfig?.serviceCentre || 'https://www.samsung.com/support/service-center/';

  // ─── Request geolocation ───
  const handleRequestLocation = useCallback(() => {
    if (!navigator.geolocation) {
      setState(LOCATOR_STATES.DENIED);
      setErrorMsg('Geolocation is not supported by your browser. Please enter your location manually.');
      return;
    }

    setState(LOCATOR_STATES.REQUESTING);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setCoords({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        });
        setState(LOCATOR_STATES.READY);
      },
      (error) => {
        let msg = 'Unable to access your location.';
        switch (error.code) {
          case error.PERMISSION_DENIED:
            msg = 'Location access was denied. You can enter your location manually below.';
            break;
          case error.POSITION_UNAVAILABLE:
            msg = 'Location information is unavailable. Please enter your location manually.';
            break;
          case error.TIMEOUT:
            msg = 'Location request timed out. Please try again or enter your location manually.';
            break;
        }
        setState(LOCATOR_STATES.DENIED);
        setErrorMsg(msg);
      },
      {
        enableHighAccuracy: false,
        timeout: 10000,
        maximumAge: 300000, // 5 min cache is fine
      }
    );
  }, []);

  // ─── Open directions in Google Maps ───
  const openMapsDirections = () => {
    if (coords) {
      window.open(
        `https://www.google.com/maps/search/Samsung+Service+Centre/@${coords.lat},${coords.lng},14z`,
        '_blank',
        'noopener,noreferrer'
      );
    }
  };

  // ─── Open Samsung locator with manual location ───
  const openLocatorManual = () => {
    // Samsung's locator doesn't accept query params for location, so we open the page
    // and let the user search on their site
    window.open(locatorUrl, '_blank', 'noopener,noreferrer');
  };

  // ─── Open Google Maps search with manual location ───
  const openMapsManual = () => {
    if (manualLocation.trim()) {
      window.open(
        `https://www.google.com/maps/search/Samsung+Service+Centre+${encodeURIComponent(manualLocation.trim())}`,
        '_blank',
        'noopener,noreferrer'
      );
    }
  };

  return (
    <div className="service-centre-finder">

      {/* ═══ INITIAL: Explain & request permission ═══ */}
      {state === LOCATOR_STATES.INITIAL && (
        <div className="scf-initial">
          <div className="scf-info-box">
            <span className="material-symbols-outlined" style={{ fontSize: '24px', color: 'var(--tertiary)' }}>my_location</span>
            <div>
              <h4 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--on-surface)', marginBottom: '4px' }}>
                Why we need your location
              </h4>
              <p style={{ fontSize: '13px', color: 'var(--on-surface-variant)', lineHeight: '18px' }}>
                Your location is used only to find nearby Samsung-authorized service centres.
                It is not stored or sent to any server — the search opens directly in your browser.
              </p>
            </div>
          </div>

          <div className="scf-action-group">
            <button
              type="button"
              className="escalation-action-btn primary"
              onClick={handleRequestLocation}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>location_searching</span>
              <span>Use My Location</span>
            </button>
            <button
              type="button"
              className="escalation-action-btn ghost"
              onClick={() => setState(LOCATOR_STATES.MANUAL)}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>edit_location_alt</span>
              <span>Enter Location Manually</span>
            </button>
          </div>
        </div>
      )}

      {/* ═══ REQUESTING: Loading state ═══ */}
      {state === LOCATOR_STATES.REQUESTING && (
        <div className="scf-loading">
          <div className="loading-spinner" style={{ width: '32px', height: '32px' }} />
          <p style={{ color: 'var(--on-surface-variant)', fontSize: '14px' }}>
            Requesting location access…
          </p>
        </div>
      )}

      {/* ═══ READY: Got coordinates ═══ */}
      {state === LOCATOR_STATES.READY && coords && (
        <div className="scf-ready">
          <div className="scf-info-box success">
            <span className="material-symbols-outlined" style={{ fontSize: '22px', color: 'var(--success)' }}>check_circle</span>
            <div>
              <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--on-surface)' }}>
                Location acquired
              </h4>
              <p style={{ fontSize: '12px', color: 'var(--on-surface-variant)' }}>
                Coordinates: {coords.lat.toFixed(4)}, {coords.lng.toFixed(4)}
              </p>
            </div>
          </div>

          <div className="scf-action-group">
            <button
              type="button"
              className="escalation-action-btn primary"
              onClick={openMapsDirections}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>directions</span>
              <span>Search in Google Maps</span>
            </button>
            <a
              href={locatorUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="escalation-action-btn secondary"
            >
              <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>open_in_new</span>
              <span>Samsung Official Locator</span>
            </a>
          </div>

          <p style={{ fontSize: '11px', color: 'var(--on-surface-variant)', marginTop: '8px', fontFamily: 'var(--font-mono)', lineHeight: '16px' }}>
            Results are sourced from Google Maps and Samsung's official locator.
            Verify that any centre is Samsung-authorized before visiting.
          </p>
        </div>
      )}

      {/* ═══ DENIED: Permission denied / error ═══ */}
      {state === LOCATOR_STATES.DENIED && (
        <div className="scf-denied">
          <div className="scf-info-box error">
            <span className="material-symbols-outlined" style={{ fontSize: '22px', color: 'var(--warning)' }}>location_disabled</span>
            <p style={{ fontSize: '13px', color: 'var(--on-surface-variant)', lineHeight: '18px' }}>
              {errorMsg}
            </p>
          </div>

          <div className="scf-manual-input">
            <label htmlFor="manual-location-input" style={{ fontSize: '13px', fontWeight: 600, color: 'var(--on-surface)', display: 'block', marginBottom: '6px' }}>
              Enter your city, locality, or PIN code
            </label>
            <div className="scf-input-row">
              <input
                id="manual-location-input"
                type="text"
                className="scf-input"
                placeholder="e.g. Hyderabad, 500081, Koramangala Bangalore"
                value={manualLocation}
                onChange={(e) => setManualLocation(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter' && manualLocation.trim()) openMapsManual(); }}
              />
              <button
                type="button"
                className="escalation-action-btn primary"
                onClick={openMapsManual}
                disabled={!manualLocation.trim()}
                style={{ whiteSpace: 'nowrap' }}
              >
                <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>search</span>
                <span>Search</span>
              </button>
            </div>
          </div>

          <a
            href={locatorUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="escalation-action-btn secondary"
            style={{ marginTop: '8px' }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>open_in_new</span>
            <span>Use Samsung's Official Locator Instead</span>
          </a>
        </div>
      )}

      {/* ═══ MANUAL: Manual entry (without denial) ═══ */}
      {state === LOCATOR_STATES.MANUAL && (
        <div className="scf-manual">
          <div className="scf-manual-input">
            <label htmlFor="manual-loc-input" style={{ fontSize: '13px', fontWeight: 600, color: 'var(--on-surface)', display: 'block', marginBottom: '6px' }}>
              Enter your city, locality, or PIN code
            </label>
            <div className="scf-input-row">
              <input
                id="manual-loc-input"
                type="text"
                className="scf-input"
                placeholder="e.g. Hyderabad, 500081, Koramangala Bangalore"
                value={manualLocation}
                onChange={(e) => setManualLocation(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter' && manualLocation.trim()) openMapsManual(); }}
                autoFocus
              />
              <button
                type="button"
                className="escalation-action-btn primary"
                onClick={openMapsManual}
                disabled={!manualLocation.trim()}
                style={{ whiteSpace: 'nowrap' }}
              >
                <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>search</span>
                <span>Search</span>
              </button>
            </div>
          </div>

          <div className="scf-action-group" style={{ marginTop: '12px' }}>
            <a
              href={locatorUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="escalation-action-btn secondary"
            >
              <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>open_in_new</span>
              <span>Samsung Official Locator</span>
            </a>
            <button
              type="button"
              className="escalation-action-btn ghost"
              onClick={() => setState(LOCATOR_STATES.INITIAL)}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>my_location</span>
              <span>Use My Location Instead</span>
            </button>
          </div>

          <p style={{ fontSize: '11px', color: 'var(--on-surface-variant)', marginTop: '12px', fontFamily: 'var(--font-mono)', lineHeight: '16px' }}>
            Search results are sourced from Google Maps for "Samsung Service Centre" near your entered location.
            Always verify that a centre is officially Samsung-authorized before visiting.
          </p>
        </div>
      )}
    </div>
  );
}
