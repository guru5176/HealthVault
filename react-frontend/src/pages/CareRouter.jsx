import { useState } from 'react';
import { api } from '../services/api';

export default function CareRouter() {
  const [input, setInput] = useState('John Smith, DOB 03/15/1995, takes escitalopram 10mg for anxiety. Recent lab shows A1C of 6.8%. Lives in San Francisco. SSN 123-45-6789.');
  const [anonymized, setAnonymized] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(0);

  const handleRoute = async () => {
    if (!input) return;
    setLoading(true);
    setStep(1); // Stripping
    setAnonymized(null);
    setResults(null);

    try {
      // Step 1: Anonymize
      const anonRes = await api.anonymizeData(input);
      setAnonymized(anonRes.anonymized);
      setStep(2); // Matching

      // Step 2: Route
      const routeRes = await api.routePatient(anonRes.anonymized, 'San Francisco');
      setResults(routeRes);
      setStep(3); // Done

    } catch (e) {
      console.error(e);
      alert("Routing failed");
      setStep(0);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <h1>🩺 Care Router</h1>
        <p>Privacy-preserving specialist routing — PII stripped on-device before analysis.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '40px' }}>
        <div className="card">
          <h3 className="card-title">Patient Data (Raw)</h3>
          <p className="card-subtitle" style={{ marginBottom: '16px' }}>Contains sensitive PII</p>
          <textarea 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            style={{
              width: '100%',
              height: '150px',
              background: 'rgba(0,0,0,0.3)',
              border: '1px solid var(--border-color)',
              borderRadius: '12px',
              color: 'var(--text-primary)',
              padding: '16px',
              fontFamily: 'var(--font-body)',
              resize: 'none'
            }}
          />
        </div>

        <div className="card">
          <h3 className="card-title">Anonymized Intent</h3>
          <p className="card-subtitle" style={{ marginBottom: '16px' }}>Safe for cloud processing</p>
          <div style={{
              width: '100%',
              height: '150px',
              background: 'rgba(0,0,0,0.3)',
              border: '1px solid var(--border-color)',
              borderRadius: '12px',
              color: 'var(--text-secondary)',
              padding: '16px',
              overflowY: 'auto'
          }}>
            {step === 1 ? (
               <span style={{ color: 'var(--accent-purple)', animation: 'pulse-glow 2s infinite' }}>🤖 Stripping PII locally...</span>
            ) : anonymized ? (
               <span style={{ color: 'var(--accent-green)' }}>{anonymized}</span>
            ) : (
               <span>Awaiting processing...</span>
            )}
          </div>
        </div>
      </div>

      <div style={{ textAlign: 'center', marginBottom: '40px' }}>
        <button className="btn-primary" onClick={handleRoute} disabled={loading || !input} style={{ padding: '16px 40px', fontSize: '1.2rem' }}>
          {loading ? 'Processing...' : 'Route to Specialist'}
        </button>
      </div>

      {results && (
        <div className="animate-fade-in">
          <h2 style={{ marginBottom: '24px' }}>Recommended Specialists</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
            {results.providers?.map((p, idx) => (
              <div key={idx} className="card" style={{ borderLeft: '4px solid var(--accent-primary)' }}>
                <h3 style={{ fontSize: '1.3rem', marginBottom: '4px' }}>{p.name}</h3>
                <div style={{ color: 'var(--accent-primary)', fontWeight: 'bold', marginBottom: '12px' }}>{p.specialty}</div>
                <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>🏥 {p.hospital} · {p.city}</div>
                <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>⭐ {p.rating}</div>
                <div style={{ display: 'inline-block', padding: '4px 12px', borderRadius: '12px', fontSize: '0.8rem', background: p.accepting_new ? 'rgba(0,230,118,0.1)' : 'rgba(255,59,48,0.1)', color: p.accepting_new ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                  {p.accepting_new ? 'Accepting Patients' : 'Not Accepting'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
