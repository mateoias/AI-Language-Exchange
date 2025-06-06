import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext'
import { api } from '../services/api'

function Chat() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [historyLoaded, setHistoryLoaded] = useState(false)
  const [audioSpeed, setAudioSpeed] = useState(0.8) // Default 80% speed
  const [playingAudioId, setPlayingAudioId] = useState(null)
  
  const { user } = useAuth()
  const audioRefs = useRef({}) // Store audio elements by message ID
  const currentAudioRef = useRef(null) // Track currently playing audio

  // Load chat history when component mounts
  useEffect(() => {
    loadChatHistory()
  }, [])

  // Send initial greeting only after history is loaded and if no messages exist
  useEffect(() => {
    if (user && historyLoaded && messages.length === 0 && !loading) {
      const timer = setTimeout(() => {
        sendInitialGreeting()
      }, 100)
      
      return () => clearTimeout(timer)
    }
  }, [user, historyLoaded, messages.length, loading])

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    const messagesContainer = document.querySelector('.chat-messages')
    if (messagesContainer) {
      setTimeout(() => {
        messagesContainer.scrollTop = messagesContainer.scrollHeight
      }, 50)
    }
  }, [messages])

  // Cleanup audio on unmount
  useEffect(() => {
    return () => {
      if (currentAudioRef.current) {
        currentAudioRef.current.pause()
        currentAudioRef.current = null
      }
    }
  }, [])

  const loadChatHistory = async () => {
    try {
      const history = await api.getChatHistory()
      if (history.messages && history.messages.length > 0) {
        setMessages(history.messages)
      }
      setHistoryLoaded(true)
    } catch (err) {
      console.error('Failed to load chat history:', err)
      setHistoryLoaded(true)
    }
  }

  const sendInitialGreeting = async () => {
    if (!user) return
    
    const greetingMessage = `¡Hola ${user.username}! ¿De qué te gustaría hablar hoy?`
    
    // Generate audio for greeting
    try {
      const audioResponse = await api.regenerateAudio(
        greetingMessage,
        user.learningLanguage,
        audioSpeed
      )
      
      const botMessage = {
        id: `greeting-${Date.now()}`,
        content: greetingMessage,
        sender: 'bot',
        timestamp: new Date().toISOString(),
        intent: 'chat',
        audio_language: user.learningLanguage,
        audio_data: audioResponse.audio_data
      }
      
      setMessages([botMessage])
      
      // Play the greeting audio automatically
      setTimeout(() => playAudio(botMessage.id, audioResponse.audio_data), 100)
      
    } catch (err) {
      // If audio fails, still show the message
      const botMessage = {
        id: `greeting-${Date.now()}`,
        content: greetingMessage,
        sender: 'bot',
        timestamp: new Date().toISOString(),
        intent: 'chat',
        audio_language: user.learningLanguage
      }
      setMessages([botMessage])
    }
  }

  const playAudio = (messageId, audioData) => {
    // Stop any currently playing audio
    if (currentAudioRef.current) {
      currentAudioRef.current.pause()
      setPlayingAudioId(null)
    }

    if (!audioData) return

    try {
      // Create audio element if it doesn't exist
      if (!audioRefs.current[messageId]) {
        const audio = new Audio(`data:audio/mp3;base64,${audioData}`)
        audioRefs.current[messageId] = audio
        
        // Set up event listeners
        audio.addEventListener('ended', () => {
          setPlayingAudioId(null)
          currentAudioRef.current = null
        })
        
        audio.addEventListener('error', (e) => {
          console.error('Audio playback error:', e)
          setPlayingAudioId(null)
          currentAudioRef.current = null
        })
      }

      // Play the audio
      const audio = audioRefs.current[messageId]
      currentAudioRef.current = audio
      setPlayingAudioId(messageId)
      audio.play().catch(err => {
        console.error('Failed to play audio:', err)
        setPlayingAudioId(null)
      })
      
    } catch (err) {
      console.error('Audio setup error:', err)
    }
  }

  const stopAudio = () => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause()
      currentAudioRef.current.currentTime = 0
      setPlayingAudioId(null)
      currentAudioRef.current = null
    }
  }

  const regenerateAudioWithNewSpeed = async (message) => {
    try {
      const response = await api.regenerateAudio(
        message.content,
        message.audio_language,
        audioSpeed
      )
      
      if (response.audio_data) {
        // Update message with new audio
        setMessages(prev => prev.map(msg => 
          msg.id === message.id 
            ? { ...msg, audio_data: response.audio_data }
            : msg
        ))
        
        // Clear old audio reference
        if (audioRefs.current[message.id]) {
          delete audioRefs.current[message.id]
        }
        
        // Play new audio
        playAudio(message.id, response.audio_data)
      }
    } catch (err) {
      console.error('Failed to regenerate audio:', err)
    }
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
      // Send message to backend with audio speed preference
      const response = await api.sendChatMessage(userMessage, audioSpeed)
      
      // Add bot response to UI
      const botMessage = {
        id: Date.now() + 1,
        content: response.response,
        sender: 'bot',
        timestamp: new Date().toISOString(),
        intent: response.intent,
        audio_language: response.audio_language,
        audio_data: response.audio_data
      }
      
      setMessages(prev => [...prev, botMessage])
      
      // Auto-play audio for new bot message
      if (response.audio_data) {
        setTimeout(() => playAudio(botMessage.id, response.audio_data), 100)
      }
      
    } catch (err) {
      setError('Failed to send message. Please try again.')
      console.error('Chat error:', err)
      
      // Remove the user message if sending failed
      setMessages(prev => prev.filter(msg => msg.id !== newUserMessage.id))
    } finally {
      setLoading(false)
    }
  }

  const startNewSession = async () => {
    try {
      // Stop any playing audio
      stopAudio()
      
      // Clear audio references
      audioRefs.current = {}
      
      await api.startNewChatSession()
      setMessages([])
      setError('')
      setHistoryLoaded(false)
      
      setTimeout(() => {
        if (user) {
          sendInitialGreeting()
        }
      }, 100)
    } catch (err) {
      console.error('Failed to start new session:', err)
    }
  }

  if (!user) {
    return <div className="page-content">Loading...</div>
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div>
          <h2>Practice {user.learningLanguage}</h2>
          <p>Your AI language partner is ready to help!</p>
        </div>
        <div className="chat-controls">
          <div className="speed-control">
            <label>Speed:</label>
            <select 
              value={audioSpeed} 
              onChange={(e) => setAudioSpeed(parseFloat(e.target.value))}
              className="speed-selector"
            >
              <option value={0.6}>60%</option>
              <option value={0.7}>70%</option>
              <option value={0.8}>80%</option>
              <option value={0.9}>90%</option>
              <option value={1.0}>100%</option>
            </select>
          </div>
          <button onClick={startNewSession} className="new-session-btn">
            New Conversation
          </button>
        </div>
      </div>
      
      {error && (
        <div className="chat-error">
          {error}
        </div>
      )}
      
      <div className="chat-messages">
        {messages.map((message) => (
          <div key={message.id} className={`message ${message.sender}`}>
            <div className="message-bubble">
              {message.content}
              {message.sender === 'bot' && message.audio_data && (
                <button
                  className={`audio-btn ${playingAudioId === message.id ? 'playing' : ''}`}
                  onClick={() => {
                    if (playingAudioId === message.id) {
                      stopAudio()
                    } else {
                      playAudio(message.id, message.audio_data)
                    }
                  }}
                  title={playingAudioId === message.id ? 'Stop' : 'Play audio'}
                >
                  {playingAudioId === message.id ? '⏸️' : '🔊'}
                </button>
              )}
              {message.sender === 'bot' && !message.audio_data && (
                <button
                  className="audio-btn regenerate"
                  onClick={() => regenerateAudioWithNewSpeed(message)}
                  title="Generate audio"
                >
                  🔄
                </button>
              )}
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