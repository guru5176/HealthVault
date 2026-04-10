import { useState, useRef, useEffect } from 'react';
import './index.css';

type Message = {
  id: string;
  sender: 'user' | 'ai' | 'system';
  text: string;
  image?: string;
  extractedData?: {
    recordType: string;
    date: string;
    findings: string;
    doctor: string;
  };
};

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [modelStatus, setModelStatus] = useState('Gemini 2.5 Flash · Ready');
  const [uploadedImages, setUploadedImages] = useState<string[]>([]);
  const [activeView, setActiveView] = useState<'chat' | 'vault'>('chat');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  // Check backend health on mount
  useEffect(() => {
    fetch('http://localhost:5000/api/health')
      .then(r => r.json())
      .then(() => setModelStatus('Gemini 2.5 Flash · Ready'))
      .catch(() => setModelStatus('Backend offline'));
  }, []);

  const handleScanClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Show image preview
    const imageUrl = URL.createObjectURL(file);
    setUploadedImages(prev => [...prev, imageUrl]);
    setIsScanning(true);

    // Add user image message
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      sender: 'user',
      text: '',
      image: imageUrl,
    }]);

    // Upload to backend
    const formData = new FormData();
    formData.append('document', file);

    try {
      const res = await fetch('http://localhost:5000/api/upload', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();

      if (res.ok) {
        setMessages(prev => [...prev, {
          id: (Date.now() + 1).toString(),
          sender: 'ai',
          text: `Extracted structured data from your ${data.data.recordType}.`,
          extractedData: data.data,
        }]);
      } else {
        setMessages(prev => [...prev, {
          id: (Date.now() + 1).toString(),
          sender: 'ai',
          text: 'Failed to process document. Please try again.',
        }]);
      }
    } catch {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: 'Network error — is the backend server running?',
      }]);
    } finally {
      setIsScanning(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleSend = async () => {
    const text = input.trim();
    if (!text) return;

    setInput('');
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      sender: 'user',
      text,
    }]);
    setIsTyping(true);

    try {
      const res = await fetch('http://localhost:5000/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: text }),
      });
      const data = await res.json();

      if (res.ok) {
        setMessages(prev => [...prev, {
          id: (Date.now() + 1).toString(),
          sender: 'ai',
          text: data.answer,
        }]);
      } else {
        setMessages(prev => [...prev, {
          id: (Date.now() + 1).toString(),
          sender: 'ai',
          text: 'Sorry, I encountered an error.',
        }]);
      }
    } catch {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: 'Network error. Is the backend running?',
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleClearHistory = () => {
    setMessages([]);
    setUploadedImages([]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="app-container">
      {/* ===== HEADER ===== */}
      <header className="app-header">
        <div className="header-row">
          <div className="status-dot" />
          <span className="header-title">Health Passport</span>
          <span className="privacy-badge">on-device</span>
        </div>
        <div className="model-status">{modelStatus}</div>
      </header>

      {/* ===== SCAN HERO CARD ===== */}
      <div className="scan-hero-card" onClick={handleScanClick}>
        {isScanning ? (
          <div className="scan-processing">
            <div className="spinner" />
            Extracting data...
          </div>
        ) : (
          <>
            <svg className="scan-icon" viewBox="0 0 24 24" fill="none">
              <path d="M4 8V4h4M20 8V4h-4M4 16v4h4M20 16v4h-4" stroke="#10b981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <rect x="9" y="7" width="6" height="10" rx="0.5" stroke="#f2f2f2" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M11 10h2M11 12.5h2M11 15h1" stroke="#808080" strokeWidth="1" strokeLinecap="round"/>
            </svg>
            <span className="scan-title">Scan Document</span>
            <span className="scan-subtitle">Tap to capture a medical record</span>
          </>
        )}
      </div>

      <input
        type="file"
        accept="image/*,application/pdf"
        ref={fileInputRef}
        onChange={handleFileSelect}
        className="file-input-hidden"
      />

      {/* ===== IMAGE STRIP ===== */}
      {uploadedImages.length > 0 && (
        <div className="image-strip">
          {uploadedImages.map((img, i) => (
            <img key={i} src={img} alt={`scan ${i + 1}`} className="image-thumb" />
          ))}
        </div>
      )}

      {/* ===== QUICK ACTION BUTTONS ===== */}
      <div className="quick-actions">
        <button
          className={`btn-quick ${activeView === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveView('chat')}
        >
          Health Vault
        </button>
        <button
          className={`btn-quick ${activeView === 'vault' ? 'active' : ''}`}
          onClick={() => setActiveView('vault')}
        >
          Settings
        </button>
      </div>

      {/* ===== DIVIDER ===== */}
      <div className="divider" />

      {/* ===== CHAT AREA ===== */}
      <div className="chat-area">
        {messages.length === 0 && (
          <div className="message-row ai animate-in">
            <div className="message-bubble system">
              Capture a medical document to extract structured data on-device.
            </div>
          </div>
        )}

        {messages.map(msg => (
          <div key={msg.id} className={`message-row ${msg.sender} animate-in`}>
            <div className={`message-bubble ${msg.sender}`}>
              {msg.image && (
                <img src={msg.image} alt="uploaded document" className="chat-image" />
              )}
              {msg.text}
              {msg.extractedData && (
                <div className="extracted-card">
                  <h4>Extracted Data</h4>
                  <div className="extracted-row">
                    <span className="extracted-label">Type</span>
                    <span className="extracted-value">{msg.extractedData.recordType}</span>
                  </div>
                  <div className="extracted-row">
                    <span className="extracted-label">Date</span>
                    <span className="extracted-value">{msg.extractedData.date}</span>
                  </div>
                  <div className="extracted-row">
                    <span className="extracted-label">Doctor</span>
                    <span className="extracted-value">{msg.extractedData.doctor}</span>
                  </div>
                  <div className="extracted-row">
                    <span className="extracted-label">Findings</span>
                    <span className="extracted-value">{msg.extractedData.findings}</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="message-row ai animate-in">
            <div className="message-bubble ai">
              <div className="typing-indicator">
                <div className="typing-dot" />
                <div className="typing-dot" />
                <div className="typing-dot" />
              </div>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* ===== INPUT BOX ===== */}
      <div className="input-box">
        <textarea
          className="input-text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your health records..."
          rows={1}
        />
        <div className="input-actions">
          <button className="btn-clear" onClick={handleClearHistory}>Clear</button>
          <button
            className="btn-send"
            onClick={handleSend}
            disabled={isTyping || !input.trim()}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
