import { useState, useRef } from 'react';

export default function ScanDocument() {
  const [isScanning, setIsScanning] = useState(false);
  const [result, setResult] = useState<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsScanning(true);
    setResult(null);

    const formData = new FormData();
    formData.append('document', file);

    try {
      const res = await fetch('http://localhost:5000/api/upload', { 
        method: 'POST', 
        body: formData 
      });
      const responseData = await res.json();
      
      if (res.ok) {
        setResult(responseData.data);
      } else {
        throw new Error(responseData.error || 'Upload failed');
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '32px' }}>
      {!result ? (
        <div style={{ maxWidth: '400px', width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '24px' }}>
          <div style={{
            width: '140px', height: '140px', borderRadius: '32px', 
            background: 'rgba(6,182,212,0.1)', border: '2px dashed var(--accent-cyan)',
            display: 'flex', justifyContent: 'center', alignItems: 'center',
            animation: isScanning ? 'pulse-glow 1.5s infinite' : 'none',
            transition: 'all 0.3s'
          }}>
            {isScanning ? (
              <div style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>Scanning...</div>
            ) : (
              <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="var(--accent-cyan)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"></path>
                <path d="M12 12v9"></path>
                <path d="m16 16-4-4-4 4"></path>
              </svg>
            )}
          </div>
          <div style={{ textAlign: 'center' }}>
            <h3 style={{ fontSize: '24px', fontWeight: 600, marginBottom: '12px' }}>Upload Document</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '15px', lineHeight: '1.6' }}>
              Capture a medical document to extract structured data on-device. We support parsing PDF, PNG, and JPEG files.
            </p>
            <div style={{ marginTop: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', background: 'rgba(34,211,238,0.05)', border: '1px solid rgba(34,211,238,0.2)', padding: '8px 16px', borderRadius: '16px' }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--accent-cyan)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
              <span style={{ fontSize: '12px', color: 'var(--accent-cyan)', fontWeight: 500 }}>All processing happens on-device. Your data never leaves your phone.</span>
            </div>
          </div>
          
          <input 
            type="file" 
            accept="image/*,application/pdf" 
            ref={fileInputRef} 
            onChange={handleUpload} 
            style={{ display: 'none' }} 
          />
          
          <button 
            className="glass-panel" 
            onClick={() => fileInputRef.current?.click()}
            disabled={isScanning}
            style={{
              padding: '18px 40px',
              borderRadius: '32px',
              background: 'linear-gradient(135deg, rgba(6,182,212,0.9), rgba(16,185,129,0.9))',
              color: 'white',
              fontWeight: 600,
              fontSize: '16px',
              border: '1px solid rgba(255,255,255,0.2)',
              marginTop: '10px',
              width: '100%',
              opacity: isScanning ? 0.7 : 1,
              boxShadow: '0 8px 24px rgba(6,182,212,0.25)'
            }}>
            {isScanning ? 'Processing via AI...' : 'Browse Computer'}
          </button>
        </div>
      ) : (
        <div className="glass-panel animate-slide-up" style={{ width: '100%', maxWidth: '600px', padding: '32px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
            <div style={{ width: '48px', height: '48px', background: 'var(--accent-green-glow)', borderRadius: '50%', display: 'flex', justifyContent: 'center', alignItems: 'center', color: 'var(--accent-green)', border: '1px solid rgba(16,185,129,0.3)' }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 6 9 17l-5-5"/></svg>
            </div>
            <div>
              <h3 style={{ fontSize: '20px', fontWeight: 600, color: 'white' }}>Extraction Complete</h3>
              <p style={{ fontSize: '14px', color: 'var(--text-muted)', marginTop: '4px' }}>{result.recordType} parsed on {new Date(result.date).toLocaleDateString()}</p>
            </div>
          </div>
          
          <div style={{ background: 'rgba(0,0,0,0.4)', padding: '24px', borderRadius: '16px', marginBottom: '24px', border: '1px solid var(--border-color)' }}>
             <h4 style={{ fontSize: '14px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--text-muted)', marginBottom: '12px' }}>Extracted Findings</h4>
             <p style={{ fontSize: '16px', color: '#f8fafc', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
               {result.findings}
             </p>
          </div>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <p style={{ fontSize: '14px', color: 'var(--text-muted)' }}>Detected Provider: <span style={{ color: 'white' }}>{result.doctor}</span></p>
            
            <button 
              onClick={() => setResult(null)}
              style={{
                padding: '12px 24px',
                borderRadius: '8px',
                border: '1px solid var(--accent-cyan)',
                color: 'var(--accent-cyan)',
                fontWeight: 600
              }}>
              Upload Another
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
