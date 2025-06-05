import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { api } from '../services/api'

function Chat() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [historyLoaded, setHistoryLoaded] = useState(false) // NEW: Track if history is loaded
  const { user } = useAuth()

  // FIXED: Load chat history when component mounts
  useEffect(() => {
    loadChatHistory()
  }, [])

  // FIXED: Send initial greeting only after history is loaded and if no messages exist
  useEffect(() => {
    // Only send greeting if we have user data, history is loaded, no existing messages, and not currently loading
    if (user && historyLoaded && messages.length === 0 && !loading) {
      // Add a small delay to ensure component is fully mounted
      const timer = setTimeout(() => {
        sendInitialGreeting()
      }, 100)
      
      return () => clearTimeout(timer)
    }
  }, [user, historyLoaded, messages.length, loading]) // CHANGED: Watch for historyLoaded instead of user

  // FIXED: Auto-scroll to bottom when messages change
  useEffect(() => {
    const messagesContainer = document.querySelector('.chat-messages')
    if (messagesContainer) {
      // CHANGED: Added timeout to ensure DOM is updated
      setTimeout(() => {
        messagesContainer.scrollTop = messagesContainer.scrollHeight
      }, 50)
    }
  }, [messages])

  // FIXED: Updated to set historyLoaded flag
  const loadChatHistory = async () => {
    try {
      const history = await api.getChatHistory()
      if (history.messages && history.messages.length > 0) {
        setMessages(history.messages)
      }
      // CHANGED: Always set historyLoaded to true, regardless of whether there are messages
      setHistoryLoaded(true)
    } catch (err) {
      console.error('Failed to load chat history:', err)
      // CHANGED: Set historyLoaded to true even on error so greeting can be sent
      setHistoryLoaded(true)
    }
  }

  // FIXED: Removed async and made function synchronous
  const sendInitialGreeting = () => {
    // CHANGED: Check if user exists before accessing properties
    if (!user) return
    
    const greetingMessage = `¡Hola ${user.username}! ¿De qué te gustaría hablar hoy?`
    
    const botMessage = {
      id: `greeting-${Date.now()}`, // CHANGED: Unique ID to prevent conflicts
      content: greetingMessage,
      sender: 'bot',
      timestamp: new Date().toISOString(),
      intent: 'chat',
      audio_language: user.learningLanguage
    }
    
    setMessages([botMessage])
  }

  const sendMessage = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setError('')
    setLoading(true)

    // Add user message to UI immediately
    const newUserMessage = {
      id: Date.now(),
      content: userMessage,
      sender: 'user',
      timestamp: new Date().toISOString()
    }
    setMessages(prev => [...prev, newUserMessage])

    try {
      // Send message to backend
      const response = await api.sendChatMessage(userMessage)
      
      // Add bot response to UI
      const botMessage = {
        id: Date.now() + 1,
        content: response.response,
        sender: 'bot',
        timestamp: new Date().toISOString(),
        intent: response.intent,
        audio_language: response.audio_language
      }
      
      setMessages(prev => [...prev, botMessage])
      
    } catch (err) {
      setError('Failed to send message. Please try again.')
      console.error('Chat error:', err)
      
      // Remove the user message if sending failed
      setMessages(prev => prev.filter(msg => msg.id !== newUserMessage.id))
    } finally {
      setLoading(false)
    }
  }

  // FIXED: Updated to reset historyLoaded flag and send new greeting
  const startNewSession = async () => {
    try {
      await api.startNewChatSession()
      setMessages([])
      setError('')
      setHistoryLoaded(false) // CHANGED: Reset history loaded flag
      
      // CHANGED: Send new greeting after clearing messages
      setTimeout(() => {
        if (user) {
          sendInitialGreeting()
        }
      }, 100)
    } catch (err) {
      console.error('Failed to start new session:', err)
    }
  }

  // CHANGED: Added loading check and user check for better UX
  if (!user) {
    return <div className="page-content">Loading...</div>
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        {/* CHANGED: Improved header layout */}
        <div>
          <h2>Practice {user.learningLanguage}</h2>
          <p>Your AI language partner is ready to help!</p>
        </div>
        <button onClick={startNewSession} className="new-session-btn">
          New Conversation
        </button>
      </div>
      
      {error && (
        <div className="chat-error">
          {error}
        </div>
      )}
      
      <div className="chat-messages">
        {/* REMOVED: Welcome message section since we now auto-send greeting */}
        
        {messages.map((message) => (
          <div key={message.id} className={`message ${message.sender}`}>
            <div className="message-bubble">
              {message.content}
            </div>
          </div>
        ))}
        
        {loading && (
          <div className="message bot">
            <div className="message-bubble typing">
              Thinking...
            </div>
          </div>
        )}
      </div>
      
      <form className="chat-input" onSubmit={sendMessage}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={`Type in ${user.learningLanguage} or ${user.nativeLanguage}...`}
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          {loading ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  )
}

export default Chat