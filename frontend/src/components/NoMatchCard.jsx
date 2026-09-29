import React from 'react';
import { AlertTriangle } from 'lucide-react';

export default function NoMatchCard({ message }) {
  return (
    <div className="no-match-card">
      <AlertTriangle className="no-match-icon" />
      <h3>We couldn't find a direct fix</h3>
      <p>{message || "This issue isn't supported yet. Please try rewording your problem or contact Samsung Support."}</p>
    </div>
  );
}
