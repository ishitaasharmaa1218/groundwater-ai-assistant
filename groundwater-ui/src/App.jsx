import { useState, useRef, useEffect } from "react"
import axios from "axios"
import "./App.css"

function App() {
  const [question, setQuestion] = useState("")
  const [messages, setMessages] = useState([])
  const [history, setHistory] = useState([])
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    const user = localStorage.getItem("user_id")
    if (user) {
      axios.get(`http://127.0.0.1:8000/history/${user}`).then(res => {
        // Reverse because backend sends newest first
        const loadedMessages = res.data.history.reverse().map(h => [
          { role: "user", content: h.question },
          { role: "assistant", content: h.answer }
        ]).flat();
        
        setMessages(loadedMessages);
        
        // Also populate the sidebar history list
        setHistory(res.data.history.map(h => h.question).reverse());
      }).catch(err => console.error("Error loading history", err));
    }
  }, []);

  async function askAI(customQuestion = null) {
    const q = customQuestion || question;
    if (!q.trim()) return

    const userMessage = { role: "user", content: q }
    setMessages(prev => [...prev, userMessage])
    
    // Add to history only if it's not already there
    setHistory(prev => {
      if(prev.includes(q)) return prev;
      return [q, ...prev];
    })
    
    setQuestion("")

    try {
      const user = localStorage.getItem("user_id")
      const params = { question: q }
      if (user) params.user_id = user
      const res = await axios.get("http://127.0.0.1:8000/ask", { params })
      const aiMessage = { 
        role: "assistant", 
        content: res.data.answer,
        chartUrl: res.data.chartUrl 
      }
      setMessages(prev => [...prev, aiMessage])
    } catch (error) {
      const aiMessage = { role: "assistant", content: "⚠️ Backend not responding. Please make sure the server is running." }
      setMessages(prev => [...prev, aiMessage])
    }
  }

  return (
    <div className="app-container">
      {/* Sidebar - Blue Theme */}
      <div className="sidebar">
        <div className="sidebar-header">
          <span>💧</span> Groundwater AI
        </div>
        <div className="new-chat">
          <button onClick={() => setMessages([])}>
            <span>+ New Chat</span>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 5v14M5 12h14"></path>
            </svg>
          </button>
        </div>
        <div className="history-list">
          <p className="history-title">Recent Questions</p>
          {history.length === 0 && <div className="history-item" style={{opacity: 0.5}}>No previous questions</div>}
          {history.map((h, i) => (
            <div 
              key={i} 
              className="history-item" 
              onClick={() => askAI(h)}
              title={h}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{flexShrink: 0}}>
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
              </svg>
              {h}
            </div>
          ))}
        </div>
      </div>

      {/* Main Chat Area - White Theme */}
      <div className="main-chat">
        
        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="empty-state">
              <h2>How can I help you analyze groundwater data today?</h2>
            </div>
          ) : (
            messages.map((m, i) => (
              <div key={i} className={`message-row ${m.role}`}>
                <div className="message-content">
                  {m.role === "assistant" && (
                    <div className="avatar assistant-avatar">
                      AI
                    </div>
                  )}
                  <div className="text text-bubble">
                    {m.content.split('\n').map((line, idx) => (
                      <span key={idx}>
                        {line.split('**').map((chunk, j) => j % 2 === 1 ? <strong key={j}>{chunk}</strong> : chunk)}
                        <br />
                      </span>
                    ))}
                    {m.chartUrl && (
                      <img src={m.chartUrl} alt="Data Visualization" className="chat-chart" />
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-container">
          <div className="input-wrapper">
            <div className="input-box">
              <input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && askAI()}
                placeholder="Ask about groundwater risk in Pune..."
              />
              <button onClick={() => askAI()} disabled={!question.trim()}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"></path>
                </svg>
              </button>
            </div>
            <div className="disclaimer">
              Groundwater AI provides automated analysis. Consider verifying important information.
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}

export default App