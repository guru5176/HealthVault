import { useState, useRef, useEffect } from 'react';

type Message = {
  id: string;
  sender: 'user' | 'ai';
  text: string;
};

export default function HealthVault() {
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', sender: 'ai', text: 'Welcome to your Secure Health Vault. I have access to all your parsed documents. What medical insights can I provide today?' }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSend = async () => {
    if (!input.trim()) return;
    
    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { id: Date.now().toString(), sender: 'user', text: userMsg }]);
    setIsTyping(true);
    
    try {
      const res = await fetch('http://localhost:5000/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMsg })
      });
      const data = await res.json();
      
      if (res.ok) {
        setMessages(prev => [...prev, { id: Date.now().toString(), sender: 'ai', text: data.answer }]);
      } else {
        setMessages(prev => [...prev, { id: Date.now().toString(), sender: 'ai', text: 'Sorry, I encountered an error searching your vault.' }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, { id: Date.now().toString(), sender: 'ai', text: 'Network error. Is the backend running?' }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="animate-fade-in" style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <div style={{ width: '100%', maxWidth: '800px', flex: 1, display: 'flex', flexDirection: 'column', gap: '20px', paddingBottom: '24px', overflowY: 'auto' }}>
        
        {messages.map((msg, idx) => (
          <div key={msg.id} className="animate-slide-up" style={{ 
            alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
            maxWidth: '85%',
            animationDelay: `${idx * 0.05}s`
          }}>
            {msg.sender === 'user' ? (
              <div style={{ 
                background: 'linear-gradient(135deg, var(--accent-cyan), var(--accent-green))', 
                padding: '16px 24px', 
                borderRadius: '24px 24px 4px 24px', 
                color: 'white', 
                fontSize: '15px', 
                lineHeight: 1.5,
                boxShadow: '0 4px 15px rgba(6,182,212,0.2)'
              }}>
                {msg.text}
              </div>
            ) : (
              <div className="glass-panel" style={{ padding: '24px', borderRadius: '24px 24px 24px 4px', border: '1px solid rgba(255,255,255,0.05)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                  <div style={{ width: '28px', height: '28px', background: 'var(--accent-green)', borderRadius: '50%', display: 'flex', justifyContent: 'center', alignItems: 'center', fontSize: '13px', fontWeight: 'bold', color: 'white' }}>NX</div>
                  <span style={{ fontSize: '14px', color: 'var(--text-muted)', fontWeight: 600 }}>Health Assistant</span>
                </div>
                <p style={{ fontSize: '15px', color: '#f1f5f9', lineHeight: 1.7 }}>
                  {msg.text}
                </p>
              </div>
            )}
          </div>
        ))}

        {isTyping && (
          <div className="glass-panel animate-fade-in" style={{ padding: '16px 24px', borderRadius: '24px 24px 24px 4px', alignSelf: 'flex-start', width: 'fit-content' }}>
            <span style={{ fontSize: '14px', color: 'var(--accent-cyan)' }}>Searching semantic vault...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <div className="glass-panel" style={{ width: '100%', maxWidth: '800px', padding: '12px', display: 'flex', borderRadius: '24px', marginTop: 'auto', border: '1px solid var(--accent-cyan-glow)' }}>
         <input 
           type="text" 
           value={input}
           onChange={(e) => setInput(e.target.value)}
           onKeyDown={(e) => e.key === 'Enter' && handleSend()}
           placeholder="Ask about your health records (e.g., 'What is my eye prescription?')" 
           style={{ flex: 1, background: 'transparent', border: 'none', color: 'white', padding: '8px 16px', outline: 'none', fontSize: '16px' }}
         />
         <button 
           onClick={handleSend}
           disabled={isTyping || !input.trim()}
           style={{
             background: input.trim() ? 'var(--accent-green)' : 'rgba(255,255,255,0.05)',
             borderRadius: '16px',
             padding: '12px 24px',
             color: input.trim() ? 'white' : 'var(--text-muted)',
             fontWeight: 600,
             transition: 'all 0.2s ease',
             fontSize: '15px'
           }}>
           Send Query
         </button>
      </div>
    </div>
  );
}
