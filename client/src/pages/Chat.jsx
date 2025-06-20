import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext'
import { api } from '../services/api'
import { getGreeting, getPlaceholder, getErrorMessage } from '../config/LanguageConfig'
import AudioRecorder from '../components/AudioRecorder'
import '../styles/AudioRecorder.css'


function Chat() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [historyLoaded, setHistoryLoaded] = useState(false)
  const [audioSpeed, setAudioSpeed] = useState(0.8) // Default 80% speed
  const [playingAudioId, setPlayingAudioId] = useState(null)

  const [isTranscribing, setIsTranscribing] = useState(false)
  const [inputMode, setInputMode] = useState('text') // 'text' or 'audio'
  
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
    const greetingMessage = getGreeting(user.learningLanguage, user.username)
    
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

  const handleAudioRecording = async (audioBlob) => {
    setIsTranscribing(true)
    setError('')
    
    try {
      // Get language hint from user's learning language
      const languageMap = {
        'Spanish': 'es',
        'French': 'fr',
        'German': 'de',
        'Italian': 'it',
        'Portuguese': 'pt',
        'Russian': 'ru',
        'Chinese': 'zh',
        'Japanese': 'ja',
        'Korean': 'ko',
        'Arabic': 'ar',
        'Hindi': 'hi'
      }
      
      const languageCode = languageMap[user.learningLanguage] || null
      
      // Transcribe audio
      const transcription = await api.transcribeAudio(audioBlob, languageCode)
      
      // Set transcribed text in input
      setInput(transcription.text)
      
      // Switch back to text mode
      setInputMode('text')
      
    } catch (err) {
      setError('Failed to transcribe audio. Please try again.')
      console.error('Transcription error:', err)
    } finally {
      setIsTranscribing(false)
    }
  }

  // New function to handle speed changes directly
  const handleSpeedChange = async (e) => {
    const newSpeed = parseFloat(e.target.value)
    console.log('[DEBUG] Speed dropdown changed to', newSpeed)
    setAudioSpeed(newSpeed)
    
    // Directly regenerate the last bot message audio
    const lastBotMessage = messages
      .filter(msg => msg.sender === 'bot' && msg.audio_data)
      .pop()
    
    if (lastBotMessage) {
      console.log('[DEBUG] Found message to regenerate:', lastBotMessage.id)
      
      try {
        const response = await api.regenerateAudio(
          lastBotMessage.content,
          lastBotMessage.audio_language,
          newSpeed  // Use newSpeed directly, not audioSpeed state
        )
        
        console.log('[DEBUG] Got new audio response')
        
        if (response.audio_data) {
          // Update the message with new audio
          setMessages(prev => prev.map(msg => 
            msg.id === lastBotMessage.id 
              ? { ...msg, audio_data: response.audio_data }
              : msg
          ))
          
          // Clear old audio reference
          if (audioRefs.current[lastBotMessage.id]) {
            delete audioRefs.current[lastBotMessage.id]
          }
          
          // Stop current playback and play new audio
          stopAudio()
          setTimeout(() => {
            playAudio(lastBotMessage.id, response.audio_data)
          }, 100)
        }
      } catch (err) {
        console.error('[DEBUG] Failed to regenerate audio:', err)
      }
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
              onChange={handleSpeedChange}
              className="speed-selector"
            >
              <option value={0.5}>50%</option>
              <option value={0.6}>60%</option>
              <option value={0.7}>70%</option>
              <option value={0.8}>80%</option>
              <option value={0.9}>90%</option>
              <option value={1.0}>100%</option>
              <option value={1.2}>120%</option>
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
        <div className="input-wrapper">
          {inputMode === 'text' ? (
            <>
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={isTranscribing ? 'Transcribing...' : getPlaceholder(user.learningLanguage, user.nativeLanguage)}
                disabled={loading || isTranscribing}
              />
              <button
                type="button"
                className="input-mode-toggle"
                onClick={() => setInputMode('audio')}
                disabled={loading || isTranscribing}
                title="Switch to voice input"
              >
                🎤
              </button>
            </>
          ) : (
            <div className="audio-input-container">
              <AudioRecorder 
                onRecordingComplete={handleAudioRecording}
                disabled={loading || isTranscribing}
              />
              {isTranscribing && <span className="transcribing-text">Transcribing...</span>}
              <button
                type="button"
                className="input-mode-toggle text-mode"
                onClick={() => setInputMode('text')}
                disabled={loading || isTranscribing}
                title="Switch to text input"
              >
                ⌨️
              </button>
            </div>
          )}
        </div>
        <button type="submit" disabled={loading || !input.trim() || isTranscribing}>
          {loading ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  )
}

export default Chat