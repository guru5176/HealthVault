import { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function Vault() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadRecords();
  }, []);

  async function loadRecords() {
    try {
      const data = await api.getRecords();
      setRecords(data.records || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function handleFileUpload(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setUploading(true);
    try {
      await api.uploadPrescription(file);
      await loadRecords();
    } catch (err) {
      alert("Failed to process prescription.");
      console.error(err);
    } finally {
      setUploading(false);
      e.target.value = null; // reset input
    }
  }

  const filteredRecords = filter === 'all' 
    ? records 
    : records.filter(r => r.category === filter);

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <h1>🗄️ My Records</h1>
        <p>Your medical records — stored securely, processed locally.</p>
      </div>

      <div className="card" style={{ marginBottom: '40px', background: 'var(--bg-glass-hover)' }}>
        <h3 className="card-title">📝 Prescription Scanner</h3>
        <p className="card-subtitle" style={{ marginBottom: '20px' }}>Upload a handwritten prescription to automatically transcribe and index it using local AI.</p>
        
        <div style={{ 
          border: '2px dashed var(--border-color)', 
          borderRadius: '16px', 
          padding: '40px', 
          textAlign: 'center',
          transition: 'all 0.3s ease',
          cursor: uploading ? 'wait' : 'pointer'
        }}
        onClick={() => !uploading && document.getElementById('file-upload').click()}
        >
          {uploading ? (
            <div style={{ color: 'var(--accent-primary)', fontWeight: 'bold', animation: 'pulse-glow 2s infinite' }}>
              🧠 AI is analyzing prescription...
            </div>
          ) : (
            <>
              <div style={{ fontSize: '2rem', marginBottom: '12px' }}>📷</div>
              <div style={{ fontWeight: '600' }}>Click or drag to upload</div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '8px' }}>PNG, JPG, WEBP (Processed 100% offline)</div>
            </>
          )}
          <input type="file" id="file-upload" accept="image/*" style={{ display: 'none' }} onChange={handleFileUpload} disabled={uploading} />
        </div>
      </div>

      <div style={{ display: 'flex', gap: '12px', marginBottom: '24px' }}>
        {['all', 'medications', 'timeline', 'general'].map(cat => (
          <button 
            key={cat}
            onClick={() => setFilter(cat)}
            style={{
              padding: '8px 16px',
              borderRadius: '20px',
              border: '1px solid',
              borderColor: filter === cat ? 'var(--accent-primary)' : 'var(--border-color)',
              background: filter === cat ? 'rgba(0, 242, 254, 0.1)' : 'transparent',
              color: filter === cat ? 'var(--text-primary)' : 'var(--text-secondary)',
              textTransform: 'capitalize',
              transition: 'all 0.2s'
            }}
          >
            {cat}
          </button>
        ))}
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>Loading records...</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px' }}>
          {filteredRecords.map(r => (
            <div key={r.id} className="card" style={{ cursor: 'pointer' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                <div style={{ 
                  background: 'rgba(255,255,255,0.05)', 
                  padding: '8px 12px', 
                  borderRadius: '12px',
                  fontSize: '1.2rem'
                }}>
                  {r.category === 'medications' ? '💊' : r.category === 'timeline' ? '📅' : '📄'}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  {new Date(r.modified).toLocaleDateString()}
                </div>
              </div>
              <h4 className="card-title" style={{ fontSize: '1.1rem' }}>{r.title}</h4>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                {r.preview}
              </p>
            </div>
          ))}
          {filteredRecords.length === 0 && (
            <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '40px', color: 'var(--text-muted)', border: '1px dashed var(--border-color)', borderRadius: '16px' }}>
              No records found.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
