import { useState, useRef, useEffect } from 'react';

export default function Chat() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am your Health AI assistant powered by local AI. I can answer questions about your medical records. Try asking: "What prescriptions do I have?"' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg, stream: true }),
      });

      if (!response.ok) throw new Error('Network response was not ok');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantMsg = '';

      setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.token) {
                assistantMsg += data.token;
                setMessages(prev => {
                  const newMsgs = [...prev];
                  newMsgs[newMsgs.length - 1].content = assistantMsg;
                  return newMsgs;
                });
              }
            } catch (err) {
              // Ignore parse errors on incomplete chunks
            }
          }
        }
      }
    } catch (e) {
      console.error(e);
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please ensure the local AI is running.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - var(--nav-height) - 40px)' }}>
      <div className="page-header" style={{ marginBottom: '20px' }}>
        <h1>💬 AI Assistant</h1>
        <p>Private, local intelligence at your fingertips.</p>
      </div>

      <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {messages.map((msg, idx) => (
            <div key={idx} style={{ 
              alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '80%',
              background: msg.role === 'user' ? 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))' : 'rgba(255,255,255,0.05)',
              color: msg.role === 'user' ? '#000' : 'var(--text-primary)',
              padding: '16px 20px',
              borderRadius: '20px',
              borderBottomRightRadius: msg.role === 'user' ? '4px' : '20px',
              borderBottomLeftRadius: msg.role === 'assistant' ? '4px' : '20px',
            }}>
              {msg.role === 'assistant' && <div style={{ fontSize: '0.8rem', opacity: 0.7, marginBottom: '8px' }}>🤖 Local AI</div>}
              <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.5' }}>{msg.content}</div>
            </div>
          ))}
          {loading && (
             <div style={{ alignSelf: 'flex-start', padding: '16px 20px', background: 'rgba(255,255,255,0.05)', borderRadius: '20px', borderBottomLeftRadius: '4px' }}>
               <span style={{ animation: 'pulse-glow 2s infinite', color: 'var(--accent-primary)' }}>Thinking...</span>
             </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={sendMessage} style={{ display: 'flex', padding: '20px', background: 'var(--bg-glass-hover)', borderTop: '1px solid var(--border-color)' }}>
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your health records..."
            style={{ 
              flex: 1, 
              background: 'transparent', 
              border: 'none', 
              color: 'var(--text-primary)',
              fontSize: '1rem',
              outline: 'none',
              padding: '0 16px'
            }}
          />
          <button type="submit" disabled={!input.trim() || loading} className="btn-primary" style={{ padding: '12px 24px' }}>
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
