import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ParallaxSection from '../components/ParallaxSection';
import { api } from '../services/api';

export default function Home() {
  const navigate = useNavigate();
  const [stats, setStats] = useState({ records: 0, consultations: 0 });

  useEffect(() => {
    async function loadStats() {
      try {
        const vaultData = await api.getRecords();
        const metricsData = await api.getMetrics();
        setStats({
          records: vaultData.count || 0,
          consultations: metricsData.total_requests || 0,
        });
      } catch (e) {
        console.error("Failed to load stats", e);
      }
    }
    loadStats();
  }, []);

  return (
    <div className="animate-fade-in">
      <div className="page-header" style={{ textAlign: 'center', marginTop: '60px' }}>
        <h1 style={{ fontSize: '3.5rem', marginBottom: '16px' }}>
          Your Data. <span className="text-gradient">Your Control.</span>
        </h1>
        <p style={{ fontSize: '1.2rem', maxWidth: '600px', margin: '0 auto' }}>
          Privacy-first medical records management powered by on-device AI. 
          No PII ever leaves your machine.
        </p>
      </div>

      <div style={{ display: 'flex', gap: '24px', justifyContent: 'center', marginBottom: '60px' }}>
        <button className="btn-primary" onClick={() => navigate('/vault')} style={{ fontSize: '1.1rem', padding: '16px 32px' }}>
          Browse Records
        </button>
        <button className="btn-secondary" onClick={() => navigate('/chat')} style={{ fontSize: '1.1rem', padding: '16px 32px' }}>
          Ask AI Assistant
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '24px', marginBottom: '40px' }}>
        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2.5rem', fontWeight: '800', color: 'var(--accent-primary)' }}>{stats.records}</div>
          <div style={{ color: 'var(--text-secondary)' }}>Secured Records</div>
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2.5rem', fontWeight: '800', color: 'var(--accent-purple)' }}>{stats.consultations}</div>
          <div style={{ color: 'var(--text-secondary)' }}>AI Consultations</div>
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2.5rem', fontWeight: '800', color: 'var(--accent-green)' }}>100%</div>
          <div style={{ color: 'var(--text-secondary)' }}>Local Processing</div>
        </div>
      </div>

      {/* Parallax Section - Privacy Bridge Architecture */}
      <ParallaxSection 
        speed={0.3} 
        bgImage="https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&q=80&w=2000"
        overlayColor="rgba(10, 10, 12, 0.85)"
      >
        <div style={{ textAlign: 'center', maxWidth: '800px', margin: '0 auto' }}>
          <h2 style={{ fontSize: '2.5rem', marginBottom: '24px' }}>The Privacy Bridge</h2>
          <p style={{ fontSize: '1.1rem', color: 'var(--text-secondary)', marginBottom: '40px' }}>
            We use a local Large Language Model to strip Personal Identifiable Information (PII) 
            from your clinical data before securely routing to top specialists.
          </p>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '20px' }}>
            <div className="glass-panel" style={{ padding: '24px', flex: '1', minWidth: '150px' }}>
              <div style={{ fontSize: '2rem', marginBottom: '12px' }}>📱</div>
              <h4 style={{ color: 'var(--accent-primary)' }}>Local Vault</h4>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Raw Data</p>
            </div>
            <div style={{ color: 'var(--text-muted)' }}>→</div>
            <div className="glass-panel" style={{ padding: '24px', flex: '1', minWidth: '150px' }}>
              <div style={{ fontSize: '2rem', marginBottom: '12px' }}>🤖</div>
              <h4 style={{ color: 'var(--accent-purple)' }}>On-Device AI</h4>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>PII Stripping</p>
            </div>
            <div style={{ color: 'var(--text-muted)' }}>→</div>
            <div className="glass-panel" style={{ padding: '24px', flex: '1', minWidth: '150px' }}>
              <div style={{ fontSize: '2rem', marginBottom: '12px' }}>🏥</div>
              <h4 style={{ color: 'var(--accent-green)' }}>Care Router</h4>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Anonymized Match</p>
            </div>
          </div>
        </div>
      </ParallaxSection>
      
      <div style={{ height: '100px' }}></div>
    </div>
  );
}
