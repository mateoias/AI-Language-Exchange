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
  const currentQueueIndexRef = useRef(-1)
  const isProcessingQueueRef = useRef(false)

  const [audioQueue, setAudioQueue] = useState([])
  const [currentSegmentIndex, setCurrentSegmentIndex] = useState(-1)
  const [isProcessingQueue, setIsProcessingQueue] = useState(false)
  const audioQueueRef = useRef([])

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

  useEffect(() => {
    // Auto-focus input when component mounts
    const input = document.querySelector('.chat-input input');
    if (input) {
      input.focus();
    }
  }, []);

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
      console.error('Failed to generate greeting audio:', err)
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

  const handleFinishAndSave = async () => {
      try {
        // Call the finalize endpoint
        const response = await api.finalizeConversation();
        
        if (response.success) {
          // Start new conversation after saving
          await startNewSession();
          
          // Show success message (if you have a toast library)
          // toast.success('Conversation saved successfully!');
          console.log('Conversation saved successfully!');
        }
      } catch (error) {
        console.error('Error saving conversation:', error);
        setError('Failed to save conversation');
        setTimeout(() => setError(''), 3000);
      }
    };

// const handleFinishAndSave = async () => {
//       if (!conversationId) return;
      
//       try {
//         // Save conversation summary
//         const response = await fetch(`${API_URL}/api/conversations/${conversationId}/finish`, {
//           method: 'POST',
//           headers: {
//             'Content-Type': 'application/json',
//           },
//           body: JSON.stringify({
//             user_id: user.id,
//             learning_language: user.learningLanguage,
//             native_language: user.nativeLanguage
//           })
//         });

//         if (response.ok) {
//           // Start new conversation after saving
//           handleNewConversation();
//           toast.success('Conversation saved successfully!');
//         }
//       } catch (error) {
//         console.error('Error saving conversation:', error);
//         toast.error('Failed to save conversation');
//       }
//     };
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
          
          // Show user-friendly error
          setError('Audio playback failed. Please try again.')
          setTimeout(() => setError(''), 3000)
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

// Audio Queue Management - 
const processAudioQueue = () => {
  console.log('[DEBUG] processAudioQueue called, currentIndex:', currentQueueIndexRef.current, 'queueLength:', audioQueueRef.current.length, 'isProcessing:', isProcessingQueueRef.current)
  
  if (audioQueueRef.current.length === 0) {
    console.log('[DEBUG] Queue is empty, stopping')
    isProcessingQueueRef.current = false
    setIsProcessingQueue(false)
    currentQueueIndexRef.current = -1
    setCurrentSegmentIndex(-1)
    return
  }
  
  if (!isProcessingQueueRef.current) {
    console.log('[DEBUG] Queue processing stopped, aborting')
    return
  }
  
  // Check if we've reached the end
  if (currentQueueIndexRef.current >= audioQueueRef.current.length - 1) {
    console.log('[DEBUG] Reached end of queue, stopping')
    isProcessingQueueRef.current = false
    setIsProcessingQueue(false)
    currentQueueIndexRef.current = -1
    setCurrentSegmentIndex(-1)
    return
  }

  // Move to next segment
  currentQueueIndexRef.current += 1
  const nextIndex = currentQueueIndexRef.current
  setCurrentSegmentIndex(nextIndex) // Update state for UI
  
  console.log('[DEBUG] Moving to segment:', nextIndex, 'of', audioQueueRef.current.length)
  
  const segment = audioQueueRef.current[nextIndex]
  console.log('[DEBUG] Processing segment:', segment.type, 'hasAudio:', !!segment.audio_data)
  
  if (segment.audio_data) {
    // Only delay between segments, not for the first one
    const delay = nextIndex === 0 ? 0 : 800
    
    console.log('[DEBUG] Scheduling segment playback with delay:', delay)
    setTimeout(() => {
      playSegmentAudio(segment, nextIndex)
    }, delay)
  } else {
    // If no audio, move to next segment immediately
    console.log('[DEBUG] No audio for segment, moving to next')
    processAudioQueue()
  }
}

const playSegmentAudio = (segment, segmentIndex) => {
  console.log('[DEBUG] playSegmentAudio called for segment:', segment.type, 'index:', segmentIndex, 'isProcessing:', isProcessingQueueRef.current, 'currentIndex:', currentQueueIndexRef.current)
  
  // Check if we're still processing and this is the right segment
  if (!isProcessingQueueRef.current) {
    console.log('[DEBUG] Queue processing stopped, aborting playback')
    return
  }
  
  if (currentQueueIndexRef.current !== segmentIndex) {
    console.log('[DEBUG] Index mismatch, aborting playback. Expected:', currentQueueIndexRef.current, 'Got:', segmentIndex)
    return
  }
  
  // Stop any currently playing audio
  if (currentAudioRef.current) {
    console.log('[DEBUG] Stopping previous audio')
    currentAudioRef.current.pause()
    currentAudioRef.current = null
    setPlayingAudioId(null)
  }

  if (!segment.audio_data) {
    console.log('[DEBUG] No audio data for segment:', segment.type)
    processAudioQueue()
    return
  }

  try {
    const segmentId = `segment-${segment.type}-${segmentIndex}-${Date.now()}`
    console.log('[DEBUG] Creating audio element with ID:', segmentId)
    
    // Create audio element
    const audio = new Audio(`data:audio/mp3;base64,${segment.audio_data}`)
    currentAudioRef.current = audio
    setPlayingAudioId(segmentId)
    
    // Set up event listeners
    const onEnded = () => {
      console.log('[DEBUG] Audio ended for segment:', segment.type, 'index:', segmentIndex)
      
      // Double-check this is still the current audio
      if (currentAudioRef.current === audio) {
        setPlayingAudioId(null)
        currentAudioRef.current = null
        
        // Only continue if we're still processing the queue
        if (isProcessingQueueRef.current) {
          console.log('[DEBUG] Moving to next segment after audio ended')
          setTimeout(() => {
            processAudioQueue()
          }, 100)
        } else {
          console.log('[DEBUG] Queue processing stopped, not continuing')
        }
      }
    }
    
    const onError = (e) => {
      console.error('[DEBUG] Audio error for segment:', segment.type, 'error:', e)
      
      if (currentAudioRef.current === audio) {
        setPlayingAudioId(null)
        currentAudioRef.current = null
        
        // Continue to next segment even on error
        if (isProcessingQueueRef.current) {
          setTimeout(() => {
            processAudioQueue()
          }, 100)
        }
      }
    }
    
    // Add event listeners
    audio.addEventListener('ended', onEnded, { once: true })
    audio.addEventListener('error', onError, { once: true })
    
    // Play the audio
    console.log('[DEBUG] Starting audio playback for:', segment.type)
    audio.play().catch(err => {
      console.error('[DEBUG] Failed to play segment audio:', err)
      onError(err)
    })
    
  } catch (err) {
    console.error('[DEBUG] Audio setup error:', err)
    setTimeout(() => {
      processAudioQueue()
    }, 100)
  }
}

const startAudioQueue = (segments) => {
  console.log('[DEBUG] startAudioQueue called with segments:', segments.length)
  console.log('[DEBUG] Segments details:', segments.map(s => ({ type: s.type, hasAudio: !!s.audio_data })))
  
  // Stop any existing audio and clear queue
  stopAudio()
  
  // Reset queue state using refs (immediate) and state (for UI)
  audioQueueRef.current = segments
  currentQueueIndexRef.current = -1
  isProcessingQueueRef.current = true  // Set ref immediately
  
  setCurrentSegmentIndex(-1)
  setIsProcessingQueue(true)  // Set state for UI
  
  console.log('[DEBUG] Queue initialized, starting processing...')
  
  // Start processing immediately
  setTimeout(() => {
    console.log('[DEBUG] Starting queue processing...')
    processAudioQueue()
  }, 50)
}

// Updated stopAudio function
const stopAudio = () => {
  console.log('[DEBUG] stopAudio called')
  
  // Stop current audio
  if (currentAudioRef.current) {
    currentAudioRef.current.pause()
    currentAudioRef.current.currentTime = 0
    currentAudioRef.current = null
  }
  
  // Clear all queue state (refs immediately, state for UI)
  isProcessingQueueRef.current = false
  currentQueueIndexRef.current = -1
  audioQueueRef.current = []
  
  setIsProcessingQueue(false)
  setPlayingAudioId(null)
  setCurrentSegmentIndex(-1)
  
  console.log('[DEBUG] All audio stopped and queue cleared')
}
  const regenerateAudioWithNewSpeed = async (message) => {
    try {
      // Stop any currently playing audio first
      stopAudio()
      
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
    const userMessageId = Date.now()
    const newUserMessage = {
      id: userMessageId,
      content: userMessage,
      sender: 'user',
      timestamp: new Date().toISOString(),
      audio_language: user.learningLanguage
    }
    setMessages(prev => [...prev, newUserMessage])

    try {
      // Send message to backend with audio speed preference
      const response = await api.sendChatMessage(userMessage, audioSpeed)
      
      console.log('[DEBUG] Full response received:', response)
      
      // Check if we got the new segment structure
      if (response.segments) {
        console.log('[DEBUG] Processing segments:', response.segments.length)
        
        // Handle new segmented response
        const segments = response.segments
        
        // Find segments by type
        const rephraseSegment = segments.find(s => s.type === 'rephrase')
        const helpSegment = segments.find(s => s.type === 'help')
        const responseSegment = segments.find(s => s.type === 'response')
        
        console.log('[DEBUG] Found segments:', {
          rephrase: !!rephraseSegment,
          help: !!helpSegment,
          response: !!responseSegment
        })
        
        // Update user message with audio if we generated it
        if (response.user_audio_data) {
          setMessages(prev => prev.map(msg => 
            msg.id === userMessageId 
              ? { ...msg, audio_data: response.user_audio_data }
              : msg
          ))
        }
        
        // Add bot messages to UI
        const botMessages = []
        
        if (rephraseSegment && rephraseSegment.text) {
          console.log('[DEBUG] Adding rephrase segment with audio:', !!rephraseSegment.audio_data)
          botMessages.push({
            id: `rephrase-${Date.now()}`,
            content: rephraseSegment.text,
            sender: 'bot',
            timestamp: new Date().toISOString(),
            message_type: 'rephrase',
            audio_data: rephraseSegment.audio_data,
            audio_language: response.audio_language,
            persona: 'teacher' 
          })
        }
        
        if (helpSegment && helpSegment.text) {
          console.log('[DEBUG] Adding help segment with audio:', !!helpSegment.audio_data)
          botMessages.push({
            id: `help-${Date.now() + 1}`,
            content: helpSegment.text,
            sender: 'bot',
            timestamp: new Date().toISOString(),
            message_type: 'help',
            audio_data: helpSegment.audio_data,
            audio_language: user.nativeLanguage,
            persona: 'teacher'
          })
        }
        
        if (responseSegment && responseSegment.text) {
          console.log('[DEBUG] Adding response segment with audio:', !!responseSegment.audio_data)
          botMessages.push({
            id: `response-${Date.now() + 2}`,
            content: responseSegment.text,
            sender: 'bot',
            timestamp: new Date().toISOString(),
            message_type: 'response',
            audio_data: responseSegment.audio_data,
            audio_language: response.audio_language,
            persona: 'partner' 
          })
        }
        
        console.log('[DEBUG] Total bot messages to add:', botMessages.length)
        
        // Add all bot messages
        setMessages(prev => {
          const newMessages = [...prev, ...botMessages]
          console.log('[DEBUG] Messages state updated, total messages:', newMessages.length)
          return newMessages
        })
        
        // Prepare audio segments for queue
        const audioSegments = segments.filter(s => s.audio_data)
        console.log('[DEBUG] Audio segments found:', audioSegments.length)
        audioSegments.forEach((seg, idx) => {
          console.log(`[DEBUG] Audio segment ${idx}:`, {
            type: seg.type,
            hasAudio: !!seg.audio_data,
            audioLength: seg.audio_data ? seg.audio_data.length : 0
          })
        })
        
        // Use setTimeout to ensure React state updates complete before starting audio
        if (audioSegments.length > 0) {
          console.log('[DEBUG] Starting audio queue with delay...')
          setTimeout(() => {
            console.log('[DEBUG] Actually starting audio queue now')
            startAudioQueue(audioSegments)
          }, 100) // Small delay to ensure DOM updates
        } else {
          console.log('[DEBUG] No audio segments to play')
        }
        
      } else {
        console.log('[DEBUG] Using fallback for old response format')
        // Fallback for old response format
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
      }
      
    } catch (err) {
      console.error('[DEBUG] Chat error:', err)
      setError('Failed to send message. Please try again.')
      
      // Remove the user message if sending failed
      setMessages(prev => prev.filter(msg => msg.id !== userMessageId))
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
          <button 
            className="new-session-btn"
            onClick={messages.length > 0 ? handleFinishAndSave : startNewSession}
            disabled={loading}
          >
            {messages.length > 0 ? 'Finish & Save' : 'New Conversation'}
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
            <div key={message.id} className={`message ${message.sender} ${message.message_type || ''} ${message.persona || ''}`}>
              <div className="message-bubble">
                {message.message_type === 'rephrase' && (
                  <span className="message-type-indicator">👩‍🏫 </span>  // Changed to teacher emoji
                )}
                {message.message_type === 'help' && (
                  <span className="message-type-indicator">👩‍🏫 </span>  // Changed to teacher emoji
                )}
              {message.content}
              {message.audio_data && (
                <button
                  className={`audio-btn ${playingAudioId === message.id ? 'playing' : ''}`}
                  onClick={() => {
                    if (playingAudioId === message.id) {
                      stopAudio()
                    } else {
                      // Stop queue if playing individual message
                      setIsProcessingQueue(false)
                      playAudio(message.id, message.audio_data)
                    }
                  }}
                  title={playingAudioId === message.id ? 'Stop' : 'Play audio'}
                  disabled={isProcessingQueue && !playingAudioId?.includes(message.id)}
                >
                  {playingAudioId === message.id ? '⏸️' : '🔊'}
                </button>
              )}
              {!message.audio_data && message.audio_language && (
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

        {/* Add audio queue indicator */}
        {isProcessingQueue && (
          <div className="audio-queue-indicator">
            <span className="queue-dot"></span>
            Playing audio sequence...
          </div>
        )}
        
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